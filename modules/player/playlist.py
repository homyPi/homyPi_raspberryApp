import logging
import traceback

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)

class Artist:
	def __init__(self, name, uri):
		self.uri = uri
		self.name = name
class Album:
	def __init__(self, source, uri, serviceId, _id=None,  name=None):
		self.source = source
		self.uri = uri
		self.serviceId = serviceId,
		self._id = _id
		self.name = name
class Track:
	def __init__(self, source, uri, serviceId, _id=None, name=None, jsonFull=None):
		self._id=_id
		self.serviceId = serviceId
		self.source = source;
		self.uri = uri;
		self.name = name;
		self.jsonFull = jsonFull;



class Playlist:
	rabbitConnection = None;
	serverHttpRequest = None;

	playerName = ""
	def __init__(self, playerName, serverHttpRequest, tracks=[]):
		self.serverHttpRequest = serverHttpRequest
		self.playerName = playerName;
		self.tracks = tracks;
		self.setCurrent(0);

	def add(self, track, fromDB=False):
		self.tracks.append(track)
		if not fromDB:
			LOGGER.info("getting track info")
			res = self.serverHttpRequest.post("api/modules/music/playlists/" + self.playerName, {
				"track": {
					"serviceId": track.serviceId,
					"source": track.source
				}
			});
			LOGGER.info("track = " + str(res))
			track._id = res["track"]["_id"]
			LOGGER.info("track._id = " + str(track._id))


	def set(self, data, fromDb=False, startAtTrack=None):
		self.clear(True)
		params = dict();
		if isinstance(data, dict) and "source" in data:
			params["source"] = data["source"]
		elif hasattr(data, "source"):
			params["source"] = data.source
		else:
			return False

		if isinstance(data, Track):
			LOGGER.info("sending request set to api/modules/music/playlists/" + self.playerName + "/set");
			params["track"] = dict()
			params["track"]["serviceId"] = data.serviceId
		elif isinstance(data, Album):
			LOGGER.info("sending request set to api/modules/music/playlists/" + self.playerName + "/set");
			params["album"] = dict()
			params["album"]["serviceId"] = data.serviceId
		elif "playlist" in data:
			params = data;
		else:
			LOGGER.info("unknown type of " + str(data.__class__))
			return False
		LOGGER.info("Parameters: " + str(params));
		res = self.serverHttpRequest.post("api/modules/music/playlists/" + self.playerName + "/set", params);
		LOGGER.info("Got playlist")
		print str(res)
		for track in res["playlist"]["tracks"]:
			self.tracks.append(Track(params["source"], track["uri"], track["serviceId"], track["_id"], track["name"], track));
		if startAtTrack is not None:
			self.setPlayingId(startAtTrack);
		return True

	def concat(self, trackset, fromDB=False):
		req = []
		for track in trackset:
			self.tracks.append(track)
			req.append({"uri": track.uri, "source": track.source})
		if not fromDB:
			LOGGER.info("getting track info " + str(req));
			res = self.serverHttpRequest.post("api/modules/music/playlists/" + self.playerName, {
				"trackset": req
			});
			LOGGER.info("track = " + str(res))
			if "trackset" in res:
				LOGGER.info("trackset = " + str(res["trackset"]))
				for i in range(len(res["trackset"])):
					trackset[i]._id = res["trackset"][i]["_id"]

	def setPlayingId(self, id):
		counter = 0;
		for track in self.tracks:
			if track.serviceId == id:
				self.current = counter
				return
			counter+=1;


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
			res = self.serverHttpRequest.delete("api/modules/music/playlists/" + self.playerName + "/" + self.tracks[key]._id);
			del self.tracks[key]
	def removeById(self, _id):
		for index in range(len(self.tracks)):
			if self.tracks[index]._id == _id:
				res = self.serverHttpRequest.delete("api/modules/music/playlists/" + self.playerName + "/"  + self.tracks[index]._id);
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
			res = self.serverHttpRequest.get("api/modules/music/playlists/" + self.playerName + "/clear");
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
			#Playlist.rabbitConnection.emit("playlist:playing:id", {"raspberry": {"name": self.playerName}, "_id": id})
