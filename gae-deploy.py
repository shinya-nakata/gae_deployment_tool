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
        self.pythonDeployTool = __config_file['pythonDeployTool']
        self.javaDeployTool = __config_file['javaDeployTool']
        self.pythonRuntime = __config_file['pythonRuntime']
        self.javaRuntime = __config_file['javaRuntime']
        self.apps = self.__parse_apps(__config_file['apps'])

    def __parse_apps(self, apps):
        return [ self.__parse_app(app) for app in apps ]

    def __parse_app(self, app):
        # ランタイム環境によってデプロイツールを選択
        deployTool = self.javaDeployTool if app['type'] == 'java' else self.pythonDeployTool
        runtime = self.javaRuntime if app['type'] == 'java' else self.pythonRuntime
        return Application(deployTool, runtime, **app)

    def get_app(self, target_app):
        for app in self.apps:
            if target_app == app.name: return app
        else:
            # TODO(nakata) add raise exception class
            raise

class Application:
    def __init__(self, deployTool, runtime, **kwards):
        self.name = kwards['name']
        self.applicationId = kwards['applicationId']
        self.version = kwards['version']
        self.privateKey = kwards['privateKey']
        self.replaceFiles = kwards['replaceFiles']
        self.type = kwards['type']
        self.source = kwards['source']
        # super class
        self.deployTool = deployTool
        self.runtime = runtime

    # def deploy(self, commandLine_args):
        #deploy_args = [self.runtime, self.deployTool, 'update']
        # deploy_args = ["gcloud", self.deployTool, 'update']
        # deploy_args.append(self.__get_source())
        #
        # applicationId = commandLine_args.a or self.applicationId
        # if applicationId is not None:
        #     deploy_args.append("-A")
        #     deploy_args.append(applicationId)
        #
        # version = commandLine_args.v or self.version
        # if version is not None:
        #     deploy_args.append("-V")
        #     deploy_args.append(version)
        #
        # subprocess.call(deploy_args, shell=True)
        # print(deploy_args)
        # pass

    def deploy(self, commandLine_args):
        # deploy_args = [self.runtime , self.runtime, "--quiet", "app", "deploy"]
        deploy_args = [self.deployTool, "app", "deploy"]
        deploy_args.append(self.__get_source())

        applicationId = commandLine_args.a or self.applicationId
        if applicationId is not None:
            # deploy_args.append("--project")
            # deploy_args.append(applicationId)
            deploy_args.append("--project=" + applicationId)

        version = commandLine_args.v or self.version
        if version is not None:
            deploy_args.append("-v")
            deploy_args.append(version)

        #
        deploy_args.append("-q")

        proc = subprocess.Popen(deploy_args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        print("{}".format(deploy_args))
        print(proc.communicate()[0])
        # proc = subprocess.Popen(["ls", "-l"], shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


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

