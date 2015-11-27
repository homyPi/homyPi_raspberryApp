#!/usr/bin/env python
import pika
import sys
import argparse

from apscheduler.schedulers.background import BackgroundScheduler
sched = BackgroundScheduler()
sched.start()

sys.path.append( "./../../python" )
from rabbitConnection import RabbitConnection, ServerRequester
from spotify_player import SpotifyPlayer
from playerClasses import Track, Playlist
from serverHttpRequest import ServerHttpRequest
import alsaaudio
from os.path import expanduser
from ConfigParser import SafeConfigParser
import json
import time
import logging
import traceback
import signal
import setproctitle

LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='module.log',level=logging.DEBUG, format=LOG_FORMAT)
queue_name = "player"
class Player:
    spotifyPlayer = None
    def __init__(self, config):
        self.playlist = Playlist(config.get("Server", "name"))
        self.job = None;
        self.serverHttpRequest = ServerHttpRequest(config.get("Server", "url"),
                                                   config.get("Server", "username"),
                                                   config.get("Server", "password"))
        Playlist.serverHttpRequest = self.serverHttpRequest;
        signal.signal(signal.SIGINT, self.stopApp)
        LOGGER.info("starting player module")
        self.server = ServerRequester("serverRequest.player")
        self.rabbitConnection = RabbitConnection("module.player", "module.player")
        Playlist.rabbitConnection = self.rabbitConnection;
        try:
            sp_user = config.get('Spotify', 'username');
            sp_pwd = config.get('Spotify', 'password');
            print("starting spotify player")
            self.spotifyPlayer = SpotifyPlayer(sp_user, sp_pwd, self.server, self.next)
            self.setHandlers()
            self.rabbitConnection.onConnected(self.init)
            self.rabbitConnection.start()
            self.onSocketReconnect();
        
            while True:
                  time.sleep(0.2)
        except KeyboardInterrupt, SystemExit:
            self.stopApp()
        except:
            LOGGER.error("player module crashed")
            LOGGER.error(traceback.format_exc())
            self.stopApp()
    def setSendProgressJob(self):
        if self.job is not None:
            self.job.remove()
            self.job = None;
        self.job = sched.add_job(self.sendProgress, "interval", seconds=5)
        self.sendProgress();

    def onSocketReconnect(self):
        self.server.emit("raspberry:module:new", {
                "name": "music",
                "status": "PAUSED" 
            });

    def stopApp(self):
        try:
            if self.spotifyPlayer is not None:
                self.spotifyPlayer.exit()
            if self.server is not None:
                self.server.stop()
                self.server.join()
            if self.rabbitConnection is not None:
                self.rabbitConnection.stop()
                self.rabbitConnection.join()
            if self.job is not None:
                self.job.remove()
        except:
            LOGGER.error(traceback.format_exc())
        sys.exit(0)
            
    def play(self, track=None):
        if track is None:
            track = self.playlist.get()
        if track is not None:
            LOGGER.info("playing " + track.uri)
            if track.source == "spotify":
                if self.spotifyPlayer.play(track) is False:
                    self.next();
                else:
                    self.setSendProgressJob()
                    self.server.emit("player:status", {'status':'PLAYING', "playingId": track._id})
        else:
            if self.job is not None:
                self.job.remove()
            self.server.emit("player:status", {'status':"PAUSED"})
            LOGGER.info("playlist empty")
    def playTrackFromRequest(self, data):
        if "source" in data and "uri" in data:
            self.playlist.clear()
            LOGGER.info(str(data));
            self.playlist.add(Track(data["source"], data["uri"]))
            self.play()
            

    def resume(self):
        LOGGER.info("next track = " + str(self.spotifyPlayer.currentTrack));
        if self.spotifyPlayer.currentTrack is None:
            self.play()
        else:
            self.spotifyPlayer.resume()
            self.setSendProgressJob()
            self.server.emit("player:status", {'status':'PLAYING'})
    def pause(self):
        self.spotifyPlayer.pause()
        if self.job is not None:
            self.job.remove()
        self.server.emit("player:status", {'status':"PAUSED"})
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
    def playIdInPlaylist(self, data):
        self.spotifyPlayer.playIdInPlaylist(data)
    def playListAdd(self, data, fromDB=False):
        LOGGER.info(str(data))
        if "track" in data:
            if "source" in data["track"] and "uri" in data["track"]:
                self.playlist.add(Track(data["track"]["source"], data["track"]["uri"], data["track"].get("_id"), data["track"].get("name")), fromDB)
        elif "trackset" in data:
            for track in data["trackset"]:
                self.playlist.add(Track(track["source"], track["uri"], data["track"].get("_id"), data["track"].get("name")), fromDB)

    def playListSet(self, data, fromDb=False):
        LOGGER.info("set playlist: " + str(data.get("tracks")))
        LOGGER.info("from DB = " + str(fromDb))
        self.playlist.clear(fromDb);
        LOGGER.info("data = " + str(data));
        trackList = [];
        for track in data.get("trackset", []):
            if "source" in track and "uri" in track:
                LOGGER.info("adding " + str(track["uri"]) + "   _id=" + str(track.get("_id")))
                trackList.append(Track(track["source"], track["uri"], track.get("_id"), track.get("name")))
            else:
                LOGGER.warn("missing source or uri in: " + str(track))
        self.playlist.concat(trackList, fromDb);
        if not fromDb:    
            self.play();

    def removeInPlaylist(self, data):
        LOGGER.info("Remove in playlist: " + str(data));
        if "_id" in data:
            self.playlist.removeById(data["_id"])
        elif "key" in data:
            self.playlist.remove(data["key"])
    def playListLoad(self, data):
        self.spotifyPlayer.playListLoad(data)
    def play_local(self):
        print("local")
    def getVolume(self, data):
        mixer = alsaaudio.Mixer("PCM");
        self.rabbitConnection.emit("raspberry:sound:volume", {"volume": mixer.getvolume()}, type="server_request")
      
    def setVolume(self, data):
        mixer = alsaaudio.Mixer("PCM");
        mixer.setvolume(int(data['volume']));
        self.rabbitConnection.emit("raspberry:sound:volume", {"volume": mixer.getvolume()}, type="server_request")
    
    def init(self):
        LOGGER.info("inititalize player data")
        res = self.serverHttpRequest.get("api/modules/music/playlists");
        LOGGER.info("Got playlist: " + str(res));
        if "playlist" in res and "trackset" in res["playlist"]:
            self.playListSet(res["playlist"], True)

    def sendProgress(self):
        print(str(self.spotifyPlayer.position))
        self.server.emit("playlist:track:progress", {"progress": self.spotifyPlayer.position})
    def seek(self, data):
        if "progress_ms" in data:
            self.spotifyPlayer.seek(data["progress_ms"])
            self.sendProgress()
    def setHandlers(self):
        LOGGER.info("set handlers")
        self.rabbitConnection.addHandler("playTrack", self.playTrackFromRequest)
        self.rabbitConnection.addHandler("resume", self.resume)
        self.rabbitConnection.addHandler("pause", self.pause)
        self.rabbitConnection.addHandler("next", self.next)
        self.rabbitConnection.addHandler("previous", self.previous)
        self.rabbitConnection.addHandler("playIdInPlaylist", self.playIdInPlaylist)
        self.rabbitConnection.addHandler("playListAdd", self.playListAdd)
        self.rabbitConnection.addHandler("playListSet", self.playListSet)
        self.rabbitConnection.addHandler("removeInPlaylist", self.removeInPlaylist)
        self.rabbitConnection.addHandler("setVolume", self.setVolume)
        self.rabbitConnection.addHandler("getVolume", self.getVolume)
        self.rabbitConnection.addHandler("setVolume", self.setVolume)
        self.rabbitConnection.addHandler("seek", self.seek)
        self.rabbitConnection.addHandler("reconnected", self.onSocketReconnect)


if __name__ == '__main__':
    print("Starting player module")  
    setproctitle.setproctitle("hommyPi_player")
    parser = argparse.ArgumentParser(description='Client for the HAPI server')
    parser.add_argument('--conf', help='Path to the configuration file')           
    args = parser.parse_args()
    confPath = expanduser("~") + '/.hommyPi_conf'
    if args.conf is not None:
       confPath = args.conf
    config = SafeConfigParser()
    config.read(confPath)
    player = Player(config)