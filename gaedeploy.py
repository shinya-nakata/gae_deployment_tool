# -*- coding: utf-8 -*-
import os
import logging
import yaml
import subprocess
import shutil
import traceback
from argparse import ArgumentParser
from datetime import datetime
from git import Git

# YAMLファイル項目名
DEPLOY_TOOL, YAML_FILES, TEMP_FOLDER, APPS, NAME, APPLICATION_ID, VERSION, PRIVATE_KEY, REPLACE_FILES, TYPE, SOURCE, \
LOCATION, SRC_FILE, DIST_FILE = (
    'deployTool', 'yamlFiles', 'tempFolder', 'apps', 'name', 'applicationId', 'version', 'privateKey',
    "replaceFiles", 'type', 'source', 'location', 'src_file', 'dist_file'
)

# 標準出力にINFOでログを出力するように設定
logger = logging.getLogger("gaedeploy")
handler = logging.StreamHandler()
handler.setLevel(logging.INFO)
logger.addHandler(handler)
logger.setLevel(logging.INFO)


def parse_args():
    """コマンドライン引数解析
    
    コマンドライン引数を解析して、デプロイ用のパラメータに変換する
    
    :return: 
        (tuple): tuple containing:
            
            args.applicationName(str): 設定ファイルのデプロイ対象のアプリケーション名  
            args.v(str): -v アプリケーションデプロイバージョン
            args.a(str): -a アプリケーションID
            args.c(str): -c 設定ファイル
    """
    usage = 'Usage: python {} applicationName [-v] '.format(os.path.basename(__file__))
    parser = ArgumentParser(usage=usage)
    parser.add_argument('applicationName',
                        help='target application name')
    parser.add_argument('-v',
                        help='app engine version')
    parser.add_argument('-a',
                        help='application id')
    parser.add_argument('-c',
                        help='configuration file')
    args = parser.parse_args()
    return args.applicationName, args.v, args.a, args.c


def load_yaml_file(config_file_path):
    """YAMLファイル読み込み処理
    
    指定されたパスのYAMLファイルを読み込む
    
    :param config_file_path: 
    :return: 
        BaseConstructor: YAMLファイルオブジェクト
    """
    try:
        with open(config_file_path, "r") as f:
            return yaml.load(f)
    except FileNotFoundError:
        raise YAMLFormatException("yaml file({0}) is not found.".format(config_file_path))


class Configuration:
    def __init__(self, config_file_path):
        """設定ファイルクラス
        
        指定されたファイルパスの設定ファイルを読み込み、オブジェクトに変換
        
        :param config_file_path: 設定YAMLファイルのファイルパス
        """
        # Yamlファイルの読み込み
        deploy_file = load_yaml_file(config_file_path)
        #
        self.deploy_tool = deploy_file.get(DEPLOY_TOOL, None)
        self.temp_folder = deploy_file.get(TEMP_FOLDER, None)
        # アプリケーション設定をパースして、Listに変換
        apps = deploy_file.get(APPS, [])
        self.conf_apps = [Application(self.deploy_tool, self.temp_folder, **_app) for _app in apps]

    def get_application(self, target_app):
        """アプリケーション取得
        
        指定されたアプリケーション名のインスタンス返却
        
        :param target_app: YAMLファイルから取得する対象のアプリケーション名
        
        :return:
            Application: target_appとApplication.nameが同一のもの
        """
        for conf_app in self.conf_apps:
            if target_app == conf_app.name:
                return conf_app
        # 指定アプリケーションがYAMLファイルから見つからない場合
        else:
            raise ApplicationNotFoundException("not found application:{}".format(target_app))


class Application:
    def __init__(self, deploy_tool=None, temp_folder=None, **kwards):
        """アプリケーションクラス
        
        デプロイ対象のアプリケーション設定情報
        
        :param deploy_tool: gcloudのパス 
        :param temp_folder: 作業用のテンポラリフォルダ
        :param kwards: アプリケーション設定情報
        """
        self.name = kwards.get(NAME, "")
        self.applicationId = kwards.get(APPLICATION_ID, "")
        self.version = kwards.get(VERSION, "")
        self.source = kwards.get(SOURCE, "")
        self.replace_files = kwards.get(REPLACE_FILES, "")
        self.yaml_file = kwards.get(YAML_FILES, "app.yaml")
        # super class
        self.deploy_tool = deploy_tool
        self.temp_folder = temp_folder or "/tmp"
        # 作業用フォルダー
        self.__work_folder = None

    def deploy(self, args_version=None, args_application_id=None):
        """アプリケーションデプロイ処理
        
        YAMLファイルに記載されている設定情報を元にGAE環境にアプリケーションをデプロイ
        デプロイ用のプロジェクトフォルダは一時フォルダにコピーを作成する
        
        :param args_version: GAEアプリケーションバージョン、コマンドラインで指定されている場合はそちらを優先
        :param args_application_id: GAEアプリケーションID、コマンドラインで指定されている場合はそちらを優先
        :return: 
        """
        try:
            # デプロイ用コマンドを生成
            deploy_command = self._create_deploy_command(args_version, args_application_id)
            logger.info("deploying start")
            logger.info("{}".format(deploy_command))

            # デプロイ実施
            proc = subprocess.Popen(deploy_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            out, err = proc.communicate(timeout=10)
            proc.communicate()
            logger.info(out)
            logger.info(err)
            logger.info("deploying completed")
        except Exception:
            raise DeployFailedException("Deploying failed")
        finally:
            # 作業フォルダを削除
            if os.path.exists(self.work_folder):
                shutil.rmtree(self.work_folder)

    def _create_deploy_command(self, args_version=None, args_application_id=None):
        """デプロイコマンド生成処理
        
        gcloudに渡すためのコマンド引数を生成する
        
        :param args_version: GAEアプリケーションバージョン、コマンドラインで指定されている場合はそちらを優先
        :param args_application_id: GAEアプリケーションID、コマンドラインで指定されている場合はそちらを優先
        :return: list: デプロイ用コマンドライン引数、[deploy_tool, "app", "deploy", "--porject=project_id", "-v", "-q"]
        """
        deploy_command = [self.deploy_tool, "app", "deploy"]

        # 指定された箇所からデプロイ用のソースを取得する
        target_file = self._get_source()
        deploy_command.append(target_file)

        # プロジェクトIDを取得
        project_id = args_application_id or self.applicationId
        if project_id is not None:
            deploy_command.append("--project=" + project_id)

        # デプロイバージョン取得
        deploy_version = args_version or self.version
        if deploy_version is not None:
            deploy_command.append("-v")
            deploy_command.append(str(deploy_version))

        # 対話的モードではなくデプロイを実施
        deploy_command.append("-q")

        return deploy_command

    def _get_source(self):
        """ソース取得処理
        
        GITが指定されている場合はGITリポジトリから取得する
        デプロイ用のプロジェクトフォルダは一時フォルダにコピーする
        
        :return: 
        """
        # 不要な一時フォルダがあれば削除
        if os.path.exists(self.work_folder):
            shutil.rmtree(self.work_folder)

        # ローカルファイルの場合は一時フォルダにコピー
        if self.source[TYPE] == "local":
            shutil.copytree(self.source[LOCATION], self.work_folder)
        # Gitの場合はリポジトリから取得
        else:
            Git().clone(self.source[LOCATION], self.work_folder)

        # ファイルの差し替え
        self._replace_files()

        return "".join(self.work_folder + "/" + self.yaml_file)

    @property
    def work_folder(self):
        """作業フォルダ取得
        
        デプロイで利用する作業フォルダ名を作成
        
        :return: 
        """
        if self.__work_folder is None:
            self.__work_folder = self.temp_folder + "/deploy_folder_" + datetime.now().strftime("%Y%m%d%H%M%S")
        return self.__work_folder

    def _replace_files(self):
        """ファイル置換え処理
        
        置換え対象のファイルが指定されている場合はファイルの置換えを行う
        
        :return: 
        """
        for replace_file in self.replace_files:
            src_file = replace_file[SRC_FILE]
            dist_file = replace_file[DIST_FILE]
            logger.info("replace src:{} to dist:{}".format(src_file, dist_file))


class Error(Exception):
    pass


class YAMLFormatException(Error):
    pass


class ApplicationNotFoundException(Error):
    pass


class DeployFailedException(Error):
    pass


if __name__ == '__main__':
    # コマンドライン引数をパース
    application_name, version, application_id, config_file = parse_args()
    # 対象YAMLファイルを設定
    config_file = config_file or 'deploy.yml'

    try:
        # 指定されたアプリケーション名をYAMLファイルから取得してデプロイ
        configuration = Configuration(config_file)
        app = configuration.get_application(application_name)
        app.deploy()
    # アプリケーションの処理でエラーが発生した場合
    except Error as e:
        logger.error(e)
        traceback.format.exec()
