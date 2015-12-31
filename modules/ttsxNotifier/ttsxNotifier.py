import pyttsx
import threading


class TtsxNotifier:
	def __init__(self):
		self.thread = PyttsxThread()
		self.thread.start()
		self.notifySuccess("HomyPi starting")

	def notifySuccess(self, message):
		self.thread.engine.say(message)


class PyttsxThread (threading.Thread):
	def __init__(self):
		threading.Thread.__init__(self)
		self.daemon = True
		self.engine = pyttsx.init()
		self.engine.setProperty('rate', 150)
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