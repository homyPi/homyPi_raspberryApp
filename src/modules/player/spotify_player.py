from __future__ import unicode_literals
import sys
sys.path.append( "../server_link/" )
import logging
import threading
import time
import spotify
import sys
from os.path import expanduser
from operator import itemgetter
from ConfigParser import SafeConfigParser
from os.path import expanduser
import bohnifySink


LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
                 '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)
logging.basicConfig(filename='module.log',level=logging.DEBUG, format=LOG_FORMAT)


class SpotifyPlayer():
    idPlaying = 0
    playlist = []
    doc_header = 'Commands'
    prompt = 'spotify> '

    logger = logging.getLogger('shell.commander')

    def __init__(self, username = None, password = None, rabbitConnection = None, onTrackEnd=None):
        self.rabbitConnection = rabbitConnection
        self.onTrackEnd = onTrackEnd
        hdlr = logging.FileHandler(expanduser("~")+'/hapi.log')
        formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
        hdlr.setFormatter(formatter)
        self.listeners = [];
        self.position = 0;
        LOGGER.addHandler(hdlr) 
        LOGGER.setLevel(logging.INFO)
        self.logged_in = threading.Event()
        self.logged_out = threading.Event()
        self.logged_out.set()
        LOGGER.info('Initializing player')
        config = spotify.Config()
        print(expanduser("~") + '/spotify_appkey.key')
        config.load_application_key_file(expanduser("~") + '/spotify_appkey.key');

        self.session = spotify.Session(config)
        self.session.on(
            spotify.SessionEvent.CONNECTION_STATE_UPDATED,
            self.on_connection_state_changed)
        self.session.on(
            spotify.SessionEvent.END_OF_TRACK, self.on_end_of_track)
        try:
            self.audio_driver = bohnifySink.CustomAlsaSink(self.session,listener=self)
        except ImportError:
            try:
                self.audio_driver = spotify.AlsaSink(self.session)
            except ImportError:
                LOGGER.warning('No audio sink found; audio playback unavailable.')

        self.event_loop = spotify.EventLoop(self.session)
        self.event_loop.start()
        if username is not None and password is not None:
           self.login(username, password)
        LOGGER.info('Ready')
        self.currentTrack = None


    def on_connection_state_changed(self, session):
        if session.connection.state is spotify.ConnectionState.LOGGED_IN:
            self.logged_in.set()
            self.logged_out.clear()
        elif session.connection.state is spotify.ConnectionState.LOGGED_OUT:
            self.logged_in.clear()
            self.logged_out.set()

    def on_end_of_track(self, session):
        self.position = 0;
        if self.onTrackEnd is not None and self.onTrackEnd() is None:
            self.session.player.play(False)

    def exit(self):
        if self.logged_in.is_set():
            print('Logging out...')
            self.session.logout()
            self.logged_out.wait()
        self.event_loop.stop()
        #self.audio_driver.stop()
        print('')
        return True

    def login(self, username, password):
        self.session.login(username, password, remember_me=True)
        self.logged_in.wait()

    def relogin(self):
        try:
            self.session.relogin()
            self.logged_in.wait()
        except spotify.Error as e:
            LOGGER.error(e)

    def forget_me(self):
        self.session.forget_me()

    def logout(self):
        self.session.logout()
        self.logged_out.wait()

    def play(self, track, loadOnly=False):
        self.stop();
        trackUri = track.uri;
        LOGGER.info("playing uri " + trackUri)
        if not self.logged_in.is_set():
            LOGGER.warning('You must be logged in to play')
            return False
        try:
            self.currentTrack = self.session.get_track(trackUri)
            self.currentTrack.load()
        except (ValueError, spotify.Error) as e:
            LOGGER.warning(e)
            return False
        LOGGER.info('Loading track into player')
        try:
            self.session.player.load(self.currentTrack)
            LOGGER.info('Playing track')
            if not loadOnly:
                self.position = 0;
                self.session.player.play()
                #self.audio_driver.new_track()
            return True
        except (ValueError, spotify.Error) as e:
            LOGGER.warning(e)
            return False
                           
    def pause(self):
        LOGGER.info('Pausing track')
        self.session.player.play(False)
        #self.audio_driver.pause()

    def resume(self):
        LOGGER.info("resuming")
        if self.currentTrack is None:
            if len(self.playlist) > 0:
                self.idPlaying = 0
                self.play(self.playlist[self.idPlaying])
            else:
                LOGGER.info("playlist empty")
        else:
            LOGGER.info('Resuming track')
            self.session.player.play()
            #self.audio_driver.resume()

    def stop(self):
        LOGGER.info('Stopping track')
        self.session.player.play(False)
        self.session.player.unload()

    def seek(self, ms):
        if not self.logged_in.is_set():
            LOGGER.warning('You must be logged in to play')
            return
        # TODO Check if playing
        self.session.player.seek(ms)
        self.position = ms;
        #self.audio_driver.new_track()

    def musiclistener(self,audio_format, frames, num_frames):
        for lisener in self.listeners:
            lisener.got_music(frames)

    def addtime(self, frames):
        self.position = self.position + ((frames*1000)/44100)

    def endprogram(self):
        self.audio_driver.stop()


    def startlisten(self,listener):
        self.listeners.append(listener)

    def stoplisten(self,listener):
        try:
          self.listeners.remove(listener)
        except:
          pass

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    player = SpotifyPlayer()
    try:
        player.play_uri("spotify:track:22e6sT2Pu8kXpJeItO0xGg")
        while True:
              time.sleep(0.2)
    except KeyboardInterrupt:
           player.exit()
           sys.exit(0)
