import sys
sys.path.insert(0, '../')

from os.path import expanduser
from ConfigParser import SafeConfigParser

from playerManager import PlayerManager
from player import Player

playerModules = [{"moduleName":"spotify","className":"SpotifyPlayer","path":"/home/nolitsou/Documents/dev/homyPi/homyPi_raspberryApp/modules/spotify/spotify_player.py"}]

confPath = expanduser("~") + '/.hommyPi_conf'
config = SafeConfigParser()
config.read(confPath)

playerManager = PlayerManager(config, playerModules);
