import logging
import traceback

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

class Artist:
	def __init__(self, name, uri):
		self.uri = uri
		self.name = name
class Track:
	def __init__(self, source, uri, _id=None,  name=None, artists=None):
		self._id=_id
		self.source = source;
		self.uri = uri;
		self.name = name;
		self.artists = artists

class Playlist:
	rabbitConnection = None;
	serverHttpRequest = None;
	def __init__(self, tracks=[]):
		self.tracks = tracks;
		self.setCurrent(0);

	def add(self, track, fromDB=False):
		self.tracks.append(track)
		if not fromDB:
			LOGGER.info("getting track info")
			res = Playlist.serverHttpRequest.post("api/playlists/", {
				"track": {
					"uri": track.uri,
					"source": track.source
				}
			});
			LOGGER.info("track = " + str(res))
			track._id = res["track"]["_id"]

	def concat(self, trackset, fromDB=False):
		req = []
		for track in trackset:
			self.tracks.append(track)
			req.append({"uri": track.uri, "source": track.source})
		if not fromDB:
			LOGGER.info("getting track info " + str(req));
			res = Playlist.serverHttpRequest.post("api/playlists/", {
				"trackset": req
			});
			LOGGER.info("track = " + str(res))
			if "trackset" in res:
				LOGGER.info("trackset = " + str(res["trackset"]))	
				for i in range(len(res["trackset"])):
					trackset[i]._id = res["trackset"][i]["_id"]


	def get(self, key=None):
		if key is None:
			key = self.current
		if key < 0:
			return None
		if len(self.tracks) > 0:
			if len(self.tracks) > key:
				return self.tracks[key]
			else:
				setCurrent(0)
				return self.tracks[key]
		else:
			return None
	def remove(self, key):
		if key > 0 and len(self.tracks) > key:
			res = Playlist.serverHttpRequest.delete("api/playlists/" + self.tracks[key]._id);
			del self.tracks[key]
	def removeById(self, _id):
		for index in range(len(self.tracks)):
			if self.tracks[index]._id == _id:
				res = Playlist.serverHttpRequest.delete("api/playlists/" + self.tracks[index]._id);
				del self.tracks[index]
				LOGGER.info(str(res));
				break;


	def previous(self):
		if (self.current > 0):
			self.setCurrent(self.current - 1);
			return self.tracks[self.current]
		else:
			return self.tracks[self.current]
	def next(self):
		if (self.current < len(self.tracks) - 1):
			self.setCurrent(self.current + 1);
			return self.tracks[self.current]
		else:
			self.setCurrent(0)
			return None

	def clear(self, fromDb=False):
		LOGGER.info("clear playlist")
		if not fromDb:
			res = Playlist.serverHttpRequest.get("api/playlists/clear");
			LOGGER.info(str(res));
		self.tracks = [];
		self.setCurrent(0);

	def setCurrent(self, current, fromDb=False):
		self.current = current;
		if (Playlist.rabbitConnection is not None and not fromDb):
			currentTrack = self.get()
			id = None
			if currentTrack is not None:
				id = currentTrack._id;
			Playlist.rabbitConnection.emit("playlist:playing:id", {"_id": id})

