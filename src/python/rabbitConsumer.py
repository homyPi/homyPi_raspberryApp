import logging
import threading
import json
import inspect
import sys
import traceback
import rabbitpy
import time

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='module.log',level=logging.INFO, format=LOG_FORMAT)

class RabbitConsumer(threading.Thread):
    handlers = []
    def __init__(self, EXCHANGE, ROUTING_KEY, QUEUE = "", exchange_type = "direct"):
        threading.Thread.__init__(self)
        self.onConnectedCallback = None
        self.running = False
        self.EXCHANGE = EXCHANGE
        self.QUEUE = QUEUE
        self.ROUTING_KEY = ROUTING_KEY
        self.connection = rabbitpy.Connection()
            # Open the channel, declare and bind the exchange and queue
        with self.connection.channel() as channel:
            # Declare the exchange
            exchange = rabbitpy.Exchange(channel, self.EXCHANGE, exchange_type = exchange_type)
            exchange.declare()
            # Declare the queue
            queue = rabbitpy.Queue(channel, self.QUEUE, auto_delete = False)
            queue.declare()
            # Bind the queue to the exchange
            queue.bind(self.EXCHANGE, self.ROUTING_KEY)
            if self.QUEUE == "":
                self.QUEUE = str(queue.name)

        
        
    def consumer(self):
        """Consume
        :param rabbitpy.Connection connection: The connection to consume on
        """
        try:
            print("start consuming")
            print("waiting for messages")
            self.queueConsuming = rabbitpy.Queue(self.connection.channel(), self.QUEUE, auto_delete = True)
            for message in self.queueConsuming.consume():
                self.handleMessage(message.body)
                message.ack()
        except KeyboardInterrupt:
            print 'Exited consumer'
    def handleMessage(self, body):
        try:
            data = json.loads(str(body))
            if "message" in data:
                LOGGER.info("got message: "+str(data['message']))
                LOGGER.info("looking in " + str(len(self.handlers)) + " handlers")
                for handler in self.handlers:
                    LOGGER.info(str(data['message'])+" == "+str(handler[0]))
                    if data['message'] == handler[0]:
                        LOGGER.info("found "+str(handler[1]))
                        args = inspect.getargspec(handler[1]).args
                        if 'self' in args:
                            nbArg = len(args) - 1
                        else:
                            nbArg = len(args)
                        LOGGER.info("function takes " + str(nbArg) + " args");
                        if nbArg == 0:
                            try:
                               handler[1]()
                            except:
                                print "Unexpected error:", sys.exc_info()[0]
                                print sys.exc_info()[1]
                                print traceback.format_exc()
                        else:
                            try:
                                if "data" in data:
                                    LOGGER.info(data)
                                    handler[1](data["data"])
                                else:
                                    handler[1](None)
                            except:
                                print "Unexpected error:", sys.exc_info()[0]
                                print sys.exc_info()[1]
                                LOGGER.error(traceback.format_exc())
                        break;
        except ValueError:
            LOGGER.warn("unable to load " + str(body))
    def addHandler(self, message, callback):
        LOGGER.info("adding handler for " + message)
        self.handlers.append([message, callback])
    def connected(self):
        LOGGER.info("Sending connected callbacks")
        if self.onConnectedCallback is not None:
            self.onConnectedCallback()
    def onConnected(self, callback):
        self.onConnectedCallback = callback
    def run(self):
        print("run")
        self.running = True
        self.connected()
        self.consumer()
    def stop(self):
        print("stop")
        self.running = False
        self.queueConsuming.stop_consuming()
        
