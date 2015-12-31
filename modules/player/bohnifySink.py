import sys
from threading import *
import time
import spotify
from array import *
__all__ = [
    'CustomAlsaSink',
    'BohnifyPortAudioSink',
]


class Sink(object):

    def on(self):
        """Turn on the audio sink.
        This is done automatically when the sink is instantiated, so you'll
        only need to call this method if you ever call :meth:`off` and want to
        turn the sink back on.
        """
        assert self._session.num_listeners(
            spotify.SessionEvent.MUSIC_DELIVERY) == 0
        self._session.on(
            spotify.SessionEvent.MUSIC_DELIVERY, self._on_music_delivery)

    def off(self):
        """Turn off the audio sink.
        This disconnects the sink from the relevant session events.
        """
        self._session.off(
            spotify.SessionEvent.MUSIC_DELIVERY, self._on_music_delivery)
        assert self._session.num_listeners(
            spotify.SessionEvent.MUSIC_DELIVERY) == 0
        self._close()

    def _on_music_delivery(self, session, audio_format, frames, num_frames):
        # This method is called from an internal libspotify thread and must
        # not block in any way.
        raise NotImplementedError

    def _close(self):
        pass


class CustomAlsaSink(Sink):


    """Audio sink for systems using ALSA, e.g. most Linux systems.
    This audio sink requires `pyalsaaudio
    <https://pypi.python.org/pypi/pyalsaaudio>`_. pyalsaaudio is probably
    packaged in your Linux distribution.
    For example, on Debian/Ubuntu you can install it from APT::
        sudo apt-get install python-alsaaudio
    Or, if you want to install pyalsaaudio inside a virtualenv, install the
    ALSA development headers from APT, then pyalsaaudio::
        sudo apt-get install libasound2-dev
        pip install pyalsaaudio
    The ``device`` keyword argument is passed on to :class:`alsaaudio.PCM`.
    Please refer to the pyalsaaudio documentation for details.
    Example::
        >>> import spotify
        >>> session = spotify.Session()
        >>> audio = spotify.AlsaSink(session)
        >>> loop = spotify.EventLoop(session)
        >>> loop.start()
        # Login, etc...
        >>> track = session.get_track('spotify:track:3N2UhXZI4Gf64Ku3cCjz2g')
        >>> track.load()
        >>> session.player.load(track)
        >>> session.player.play()
        # Listen to music...
    """

    def __init__(self, session, device='default', listener=None):
        self._session = session
        self._device_name = device

        import alsaaudio  # Crash early if not available
        self._alsaaudio = alsaaudio
        self._device = None
        self._listener = listener

        self.on()

    def _on_music_delivery(self, session, audio_format, frames, num_frames):
        assert (
            audio_format.sample_type == spotify.SampleType.INT16_NATIVE_ENDIAN)

        if self._device is None:
            if hasattr(self._alsaaudio, 'pcms'):  # pyalsaaudio >= 0.8
                self._device = self._alsaaudio.PCM(
                    mode=self._alsaaudio.PCM_NONBLOCK,
                    device=self._device_name)
            else:  # pyalsaaudio == 0.7
                self._device = self._alsaaudio.PCM(
                    mode=self._alsaaudio.PCM_NONBLOCK, card=self._device_name)
            if sys.byteorder == 'little':
                self._device.setformat(self._alsaaudio.PCM_FORMAT_S16_LE)
            else:
                self._device.setformat(self._alsaaudio.PCM_FORMAT_S16_BE)
            self._device.setrate(audio_format.sample_rate)
            self._device.setchannels(audio_format.channels)
            self._device.setperiodsize(num_frames * audio_format.frame_size())
        i = self._device.write(frames)
        self._listener.addtime(i)
        return i

    def _close(self):
        if self._device is not None:
            self._device.close()
            self._device = None