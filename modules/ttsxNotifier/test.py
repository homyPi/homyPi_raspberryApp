import pyttsx
import pyttsx
import time
import threading

import signal 
import sys


class myThread (threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.engine = pyttsx.init()
		self.engine.setProperty('rate', 130)
		self.engine.setProperty('voice', "english")
		self.engine.connect('started-utterance', self.onStart)
		self.engine.connect('started-word', self.onWord)
		self.engine.connect('finished-utterance', self.onEnd)
		self.engine.connect('error', self.onError)

	def run(self):
		self.engine.startLoop()
	def stop(self):
		self.engine.endLoop()

	def onStart(self, name):
		print 'starting', name
	def onWord(self, name, location, length):
		print 'word', name, location, length
	def onError(self, name, exeption):
		print 'error', name
		print str(exeption)
	def onEnd(self, name, completed):
		print "onEnd " + name

class tts:
	def __init__(self):
		self.thread1 = myThread()
		self.thread1.start()
		signal.signal(signal.SIGINT, self.signal_handler)

	def signal_handler(self, signal, frame):
		self.thread1.stop()
	def notifySuccess(self, message):
		self.thread1.engine.say(message)


t = tts()

var = None
while var != "quit":
	var = raw_input("Please enter something: ")
	t.notifySuccess(var)
#thread1.stop()