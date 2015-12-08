#!/usr/bin/env python
#
import logging
LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
              '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='module.log',level=logging.DEBUG, format=LOG_FORMAT)

import pika
import sys
import argparse
import os

from apscheduler.schedulers.background import BackgroundScheduler
sched = BackgroundScheduler()
sched.start()

pythonModulesPath = os.getenv('HOMYPI_PYTHON_MODULES');
LOGGER.info(pythonModulesPath)
sys.path.append( pythonModulesPath )
from rabbitConsumer import RabbitConsumer
from rabbitEmitter import RabbitEmitter, ServerRequester
from spotify_player import SpotifyPlayer
from playerClasses import Track, Playlist
from serverHttpRequest import ServerHttpRequest
from dynamicModule import DynamicModule
import alsaaudio
from os.path import expanduser
from ConfigParser import SafeConfigParser
import json
import time
import traceback
import signal
import setproctitle
LOGGER.info("imports ready")

queue_name = "player"
class Player:
    spotifyPlayer = None
    def __init__(self, config, playersConfig):
        LOGGER.info("__init__ player")
        self.moduleLoader = DynamicModule(playersConfig)
        self.players = self.moduleLoader.load()
        self.playlist = Playlist(config.get("Server", "name"))
        self.job = None;
        self.name = config.get("Server", "name")
        self.serverHttpRequest = ServerHttpRequest(config.get("Server", "url"),
                                                   config.get("Server", "username"),
                                                   config.get("Server", "password"))
        Playlist.serverHttpRequest = self.serverHttpRequest;
        signal.signal(signal.SIGINT, self.stopApp)
        LOGGER.info("starting player module")
        self.server = ServerRequester("serverRequest.player")
        self.rabbitConnection = RabbitConsumer("module.player", "module.player")
        Playlist.rabbitConnection = self.server;
        try:
            #sp_user = config.get('Spotify', 'username');
            #sp_pwd = config.get('Spotify', 'password');
            for p in players:
                self.spotifyPlayer = p["class"](config, self.next)
            print("starting spotify player")
            #self.spotifyPlayer = SpotifyPlayer(config, self.next)
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
                "status": "PAUSED",
                "volume": self.getVolume()
            });

    def stopApp(self):
        try:
            if self.spotifyPlayer is not None:
                self.spotifyPlayer.exit()
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
                    self.server.emit("player:status", {"player": {"name": self.name, }, 'status':'PLAYING', "playingId": track._id})
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
    def getVolume(self):
        mixer = alsaaudio.Mixer("PCM");
        LOGGER.info("Volume = " + str(mixer.getvolume()[0]))
        vol = mixer.getvolume()[0];
        return ((vol-50)*2)
      
    def setVolume(self, data):
        mixer = alsaaudio.Mixer("PCM");
        LOGGER.info("SET Volume = " + str(data['volume']))
        volBase = int(data['volume'])
        vol = (volBase/2)+50
        mixer.setvolume(vol);
        self.rabbitConnection.emit("player:volume:isSet", {"volume": self.getVolume()}, type="server_request")
    
    def init(self):
        LOGGER.info("inititalize player data")
        res = self.serverHttpRequest.get("api/modules/music/playlists/" + self.name);
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
    LOGGER.info("Starting player module")  
    setproctitle.setproctitle("hommyPi_player")
    parser = argparse.ArgumentParser(description='Client for the HAPI server')
    parser.add_argument('--conf', help='Path to the configuration file')
    parser.add_argument('--players', help='Players')
    args = parser.parse_args()
    confPath = expanduser("~") + '/.hommyPi_conf'
    LOGGER.info("Checking args")
    try:
        if args.conf is not None:
           confPath = args.conf
        if args.players is not None:
            LOGGER.info(args.players)
            players = json.loads(args.players);
        else:
            players = [];
    except:
        LOGGER.error("player module crashed")
        LOGGER.error(traceback.format_exc())
    LOGGER.info("Checking config")
    config = SafeConfigParser()
    config.read(confPath)
    player = Player(config, players);