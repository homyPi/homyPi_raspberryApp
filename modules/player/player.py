import logging
LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='module.log',level=logging.INFO, format=LOG_FORMAT)

from playlist import Playlist

class Player:
	def __init__(self, name, modules, config, serverHttpRequest, serverMq):
		self.name = name
		self.serverMq = serverMq;
		self.playerModules = dict();
		for moduleClass in modules:
			print "loading player module " + moduleClass["moduleName"]
			self.playerModules[moduleClass["moduleName"]] = moduleClass["class"](config, self.next)
		self.playlist = Playlist(config.get("Server", "name"), serverHttpRequest);
		self.currentPlayer = None;
		self.job = None

	def getPlayer(self, name):
		LOGGER.info("getting player " + name)
		return self.playerModules[name]

	def switchPlayer(self, name):
		next = self.getPlayer(name)
		if self.currentPlayer is None or next != self.currentPlayer:
			if self.currentPlayer is not None:
				self.currentPlayer.pause()
			self.currentPlayer = next

	def play(self, track=None):
		track = track or self.playlist.get()
		if track is not None:
			LOGGER.info("playing (name: " + str(track.name) + ", uri: " + str(track.uri) + ") on: " + track.source)
			self.switchPlayer(track.source)
			if self.currentPlayer.play(track) is False:
				self.next();
			else:
				self.serverMq.emit("player:status", {'status':'PLAYING', "playingId": track._id, "track": track.jsonFull})
				#self.setSendProgressJob()
		else:
			if self.job is not None:
				self.job.remove()
			self.serverMq.emit("player:status", {'status':"PAUSED"})
			LOGGER.info("playlist empty")


	def resume(self):
		LOGGER.info("curent track = " + str(self.currentPlayer.currentTrack));
		if self.currentPlayer.currentTrack is None:
			self.play()
		else:
			self.currentPlayer.resume()
			LOGGER.info("emit 'player:status' => 'PLAYING'")
			self.serverMq.emit("player:status", {'status':'PLAYING'})
			self.setSendProgressJob()


	def pause(self):
		self.currentPlayer.pause()
		if self.job is not None:
			self.job.remove()
		self.serverMq.emit("player:status", {'status':"PAUSED"})


	def next(self):
		next = self.playlist.next();
		if next is None:
			LOGGER.info("Nothing after")
			self.pause()
			return None
		else:
			LOGGER.info("playing next")
			self.play(next)
			return next;


	def previous(self):
		previous = self.playlist.previous();
		if previous is not None:
			self.play(previous)
		else:
			self.pause()
