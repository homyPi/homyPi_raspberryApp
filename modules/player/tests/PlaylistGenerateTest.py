import sys
from ConfigParser import SafeConfigParser
from os.path import expanduser
import json

sys.path.append( "../" )
sys.path.append( "../../../src/python" )
from rabbitEmitter import ServerRequester
from dynamicModule import DynamicModule
from serverHttpRequest import ServerHttpRequest
from player import Player

confPath = expanduser("~") + '/.hommyPi_conf'

config = SafeConfigParser()
config.read(confPath)

players = [{"moduleName":"spotify","className":"SpotifyPlayer","path":"/home/nolitsou/Documents/dev/homyPi/homyPi_raspberryApp/modules/spotify/spotify_player.py"}]
modules = DynamicModule(players).load()

serverHttpRequest = ServerHttpRequest(config.get("Server", "url"),
                                                   config.get("Server", "username"),
                                                   config.get("Server", "password"))
server = ServerRequester("serverRequest.player")
player = Player("Jonny", modules, config, serverHttpRequest, server)



resp = serverHttpRequest.get('api/modules/music/playlists/generate?generator=musicgraph&musicSource=spotify')
if "error" not in resp:
	player.playlist.set(resp["data"]);
else:
	print "error"