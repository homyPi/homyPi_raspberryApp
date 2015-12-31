#!/usr/bin/python
from concurrent import futures
import threading
import gobject
import pygst
pygst.require('0.10')
#import gst
import os
import time
class LocalPlayer(threading.Thread):
      def __init__(self):
          threading.Thread.__init__(self)
          self.setDaemon(True)
      def play(self, path):
          self.player = gst.element_factory_make("playbin", "player")
          self.player.set_property('uri','file://'+path)
          self.player.set_state(gst.STATE_PLAYING)
          
      def pause(self):
          self.player.set_state(gst.STATE_PAUSED)
          
      def run(self):
          while 1:
                time.sleep(1)
                              
          
if __name__ == "__main__":
   audioSrc = "./Woodkid-Iron.mp3"
   try:
      lP = LocalPlayer()
      lP.play(os.path.abspath(audioSrc))
      print("ok")
      time.sleep(5);
      time.sleep(2);
      lP.player.set_state(gst.STATE_PLAYING )
      time.sleep(5);
      print("pause")
   except KeyboardInterrupt:
          sys.exit(0)     
      

      