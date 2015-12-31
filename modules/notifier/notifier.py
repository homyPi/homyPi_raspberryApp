#!/usr/bin/env python
import sys
import os
import argparse
pythonModulesPath = os.getenv('HOMYPI_PYTHON_MODULES');
sys.path.append( pythonModulesPath )
from rabbitConsumer import RabbitConsumer
from dynamicModule import DynamicModule
from os.path import expanduser
from ConfigParser import SafeConfigParser
import time
import json
import logging
import setproctitle

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='module.log',level=logging.DEBUG, format=LOG_FORMAT)

class Notifier:
    def __init__(self, config, notifierModules):
        LOGGER.info("starting logger module")
        print str(notifierModules)
        self.moduleLoader = DynamicModule(notifierModules)
        self.modules = []
        for m in self.moduleLoader.load():
            self.modules.append(m["class"]())
        self.rabbitConsumer = RabbitConsumer("module.notifier", "module.notifier")
        try:
            self.setHandlers()
            self.rabbitConsumer.start()
            while True:
                  time.sleep(0.2)
        except KeyboardInterrupt:
            print("stopping consuming")
            self.rabbitConsumer.stop()
            print("see ya later!")
            sys.exit(0)
    def notifySuccess(self, message):
        print str(message)
        if len(self.modules) > 0:
            self.modules[0].notifySuccess(message)
    def setHandlers(self):
        print "set handlers"
        LOGGER.info("set handlers")
        self.rabbitConsumer.addHandler("success", self.notifySuccess)

        
if __name__ == '__main__':
    setproctitle.setproctitle("homyPi_notifier")
    parser = argparse.ArgumentParser(description='Client for the HAPI server')
    parser.add_argument('--conf', help='Path to the configuration file')      
    parser.add_argument('--notifiers', help='Notifiers')     
    args = parser.parse_args()
    confPath = expanduser("~") + '/.hommyPi_conf'
    if args.conf is not None:
       confPath = args.conf
    if args.notifiers is not None:
        LOGGER.info(args.notifiers)
        notifiers = json.loads(args.notifiers);
    else:
        notifiers = [];
    print(confPath)
    config = SafeConfigParser()
    config.read(confPath)
    Notifier(config, notifiers)