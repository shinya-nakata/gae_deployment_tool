# -*- coding: utf-8 -*-
import os
import yaml
import subprocess
from argparse import ArgumentParser

def parse_args():
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
    return parser.parse_args()

class Configuration:
    def __init__(self, config_file):
        __config_file = yaml.load(config_file)
        print(__config_file)
        self.pythonDeployTool = __config_file['pythonDeployTool']
        self.javaDeployTool = __config_file['javaDeployTool']
        self.apps = self.__parse_apps(__config_file['apps'])

    def __parse_apps(self, apps):
        return [ self.__parse_app(app) for app in apps ]

    def __parse_app(self, app):
        # ランタイム環境によってデプロイツールを選択
        deployTool = self.javaDeployTool if app['runtime'] == 'java' else self.pythonDeployTool
        return Application(deployTool, **app)

    def get_app(self, target_app):
        for app in self.apps:
            if target_app == app.name: return app
        else:
            # TODO(nakata) add raise exception class
            raise

class Application:
    def __init__(self, deployTool, **kwards):
        self.name = kwards['name']
        self.applicationId = kwards['applicationId']
        self.version = kwards['version']
        self.privateKey = kwards['privateKey']
        self.replaceFiles = kwards['replaceFiles']
        self.runtime = kwards['runtime']
        self.source = kwards['source']
        # super class
        self.deployTool = deployTool

    def deploy(self, commandLine_args):
        deploy_args = [self.deployTool]
        deploy_args.append(self.__get_source())

        applicationId = commandLine_args.a or self.applicationId
        if applicationId is not None:
            deploy_args.append("-A")
            deploy_args.append(applicationId)

        version = commandLine_args.v or self.version
        if version is not None:
            deploy_args.append("-V")
            deploy_args.append(version)

        #subprocess.run([self.deployTool, 'update', '-A', self.applicationId, '-V', str(self.version)])
        print(deploy_args)
        pass

    def __get_source(self):
        if self.source['type'] == "local" : return self.source['location']
        # TODO git からソースを取ってくる
        return self.source

    def __get_private_key(self):
        pass

if __name__ == '__main__':
    commandLine_args = parse_args()

    config_file = commandLine_args.c or 'deploy.yml'
    with open(config_file, "r") as f:
        configuration = Configuration(f)
        app = configuration.get_app(commandLine_args.applicationName)
        app.deploy(commandLine_args)

