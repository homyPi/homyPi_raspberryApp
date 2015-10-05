import sys
sys.path.append( "./../../python" )
from serverHttpRequest import ServerHttpRequest
from rabbitConnection import RabbitConnection
from alarm import Alarm

Alarm.rabbitConnectionPlayer = RabbitConnection("player", "module.player")
Alarm.serverRequester = ServerHttpRequest("http://localhost:3000", "admin", "admin")
a = Alarm("55f4d66a342223144cddff9f", 20,20,False, False)
a.execute()