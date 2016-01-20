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

class RabbitEmitter(threading.Thread):
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
                    
    def emit(self, message, data = None, type = None):
        with self.connection.channel() as channel:
            LOGGER.info(message+": "+str(data)+ "  to "+str(self.EXCHANGE)+":"+str(self.ROUTING_KEY)+ "   type="+str(type))
            if data is None:
                if type is not None:
                    body = json.dumps({"message": message, "type": type})
                else:
                    body = json.dumps({"message": message})
            else:
                if type is not None:
                    body = json.dumps({"message": message,"data": data, "type": type})
                else:
                    body = json.dumps({"message": message,"data": data})                
            message = rabbitpy.Message(channel, body)
            message.publish(self.EXCHANGE, self.ROUTING_KEY)
        
class ServerRequester(RabbitEmitter):
    def __init__(self, routing_key):
        RabbitEmitter.__init__(self, "serverRequest", routing_key, exchange_type = "topic")

    def emit(self, message, data = None, type = None):
        with self.connection.channel() as channel:
            LOGGER.debug(message+": "+str(data)+ "  to "+str(self.EXCHANGE)+":"+str(self.ROUTING_KEY)+ "   type="+str(type))
            if data is None:
                if type is not None:
                    body = json.dumps({"message": message, "type": type})
                else:
                    body = json.dumps({"message": message})
            else:
                if type is not None:
                    body = json.dumps({"message": message,"data": data, "type": type})
                else:
                    body = json.dumps({"message": message,"data": data});
            message = rabbitpy.Message(channel, body);
            message.publish(self.EXCHANGE, self.ROUTING_KEY)