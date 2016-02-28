import sys
from ConfigParser import SafeConfigParser
from os.path import expanduser

sys.path.append( "../" )
sys.path.append( "../../../src/python" )
from rabbitEmitter import ServerRequester, RabbitEmitter
from serverHttpRequest import ServerHttpRequest
from alarm import Alarm

confPath = expanduser("~") + '/.hommyPi_conf'

config = SafeConfigParser()
config.read(confPath)

serverHttpRequest = ServerHttpRequest(config.get("Server", "url"),
                                                   config.get("Server", "username"),
                                                   config.get("Server", "password"))

Alarm.serverRequester = serverHttpRequest
Alarm.rabbitConnectionPlayer = RabbitEmitter("module.player", "module.player")

alarm = Alarm("TEST", 0, 0, False, False);
alarm.execute()