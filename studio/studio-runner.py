#!/usr/bin/python

import os
import sys
import subprocess
import argparse
import uuid
import yaml
import hashlib
import pip
import logging
logging.basicConfig()

import model
import studiologging

from apscheduler.schedulers.background import BackgroundScheduler
from configparser import ConfigParser

class LocalExecutor(object):
    """Runs job while capturing environment and logging results.

    TODO: capturing state and results.
    """

    def __init__(self, configFile=None):
        self.config = self.getDefaultConfig()
        if configFile:
            with open(configFile) as f:
                self.config.update(yaml.load(f))

        self.db = self.getDbProvider()
        self.sched = BackgroundScheduler()
        self.sched.start()
        self.logger = logging.getLogger('LocalExecutor')
        self.logger.setLevel(10)

    def run(self, filename, args):
        experimentName = self.getUniqueExperimentName() 
        self.logger.info("Experiment name: " + experimentName)

        keyBase = 'experiments/' + experimentName + '/'
        self.db[keyBase + 'args'] = [filename] + args 
        self.saveDir(".", keyBase + "workspace/")
        self.savePythonEnv(keyBase)


        

        with open(self.config['log']['name'], self.config['log']['mode']) as outputFile:
            env = os.environ.copy()
            studiologging.setup_model_directory(env, experimentName)

            p = subprocess.Popen(["python", filename] + args, stdout=outputFile, stderr=subprocess.STDOUT, env=env)
            ptail = subprocess.Popen(["tail", "-f", self.config['log']['name']]) # simple hack to show what's in the log file

            self.sched.add_job(lambda: self.saveDir(env['TFSTUDIO_MODEL_PATH'], keyBase + "modeldir/"), 'interval', minutes = self.config['saveWorkspaceFrequency'])
            self.sched.add_job(lambda: self.saveDir(".", keyBase + "workspace_latest/"), 'interval', minutes = self.config['saveWorkspaceFrequency'])

            p.wait()
            ptail.kill()
    
        
    def getUniqueExperimentName(self):
        return str(uuid.uuid4())

    def getDbProvider(self):
        assert 'database' in self.config.keys()
        dbConfig = self.config['database']
        assert dbConfig['type'].lower() == 'firebase'.lower()
        return model.FirebaseProvider(dbConfig['url'], dbConfig['secret'])

    def saveDir(self, localFolder, keyBase):
        self.logger.debug("saving workspace to keyBase = " + keyBase)
        for root, dirs, files in os.walk(localFolder, topdown=False):
            for name in files:
                fullFileName = os.path.join(root, name)
                self.logger.debug("Saving " + fullFileName)
                with open(fullFileName) as f:
                    data = f.read()
                    sha = hashlib.sha256(data).hexdigest()
                    self.db[keyBase + sha + "/data"] = data
                    self.db[keyBase + sha + "/name"] = name
                    
        self.logger.debug("Done saving")

    def savePythonEnv(self, keyBase):
            packages = [p._key + '==' + p._version for p in pip.pip.get_installed_distributions(local_only=True)]
            self.db[keyBase + "pythonenv"] = packages

    def getDefaultConfig(self):
        defaultConfigFile = os.path.dirname(os.path.realpath(__file__))+"/defaultConfig.yaml"
        with open(defaultConfigFile) as f:
            return yaml.load(f)

    def __del__(self):
        self.sched.shutdown()

def main(args):
    exec_filename, other_args = args.script_args[0], args.script_args[1:]
    # TODO: Queue the job based on arguments and only then execute.
    LocalExecutor(args.config).run(exec_filename, other_args)
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='TensorFlow Studio runner. Usage: studio-runner script <script_arguments>')
    parser.add_argument('script_args', metavar='N', type=str, nargs='+')
    parser.add_argument('--config', '-c', help='configuration file')

    args = parser.parse_args()
    main(args)
