from PyQt4 import QtGui, QtCore, QtNetwork, QtXml
#import urllib

class PlaylistItem:

	def __init__(self, path):
		self.path = unicode(path)

	def getName(self):
		name = self.path
		if name[-1] == "/":
			name = name[:-1]

		divider = name.rfind("/")
		return name[divider + 1:]




class PlayerStatus:

	PLAYING = "PLAYING"
	PAUSED = "PAUSED"
	STOPPED = "STOPPED"
	WAITING = "WAITING"

	LINEAR = "LINEAR"
	CYCLIC = "CYCLIC"

	STOP = 0
	PAUSE = 1

	def nextType(self):
		if self.type == PlayerStatus.LINEAR:
			return PlayerStatus.CYCLIC
		return PlayerStatus.LINEAR


	def __init__(self):
		self.state = PlayerStatus.STOPPED
		self.type = PlayerStatus.LINEAR
		self.playlist = []
		self.currentTrackNo = 0
		self.currentTrackNo = 0
		self.currentDuration = 0
		self.currentPosition = 0
		self.bufferPercent = 0
		self.volume = 0
		self.maxVolume = 0
		self.stopAfter = -1
		self.stopAfterType = PlayerStatus.STOP
		self.mpVolume = 100
		self.mpMaxVolume = 100
		self.backMpVolume = 100
		self.backMpMaxVolume = 100
		self.backItem = None
		self.backState = PlayerStatus.STOPPED
		

	@staticmethod
	def fromDom(e):
		status = PlayerStatus()
		status.state = e.attribute("state")
		status.type = e.attribute("playtype")
		status.currentDuration = int(e.attribute("duration"))
		status.currentPosition = int(e.attribute("position"))
		status.volume = int(e.attribute("volume"))
		status.maxVolume = int(e.attribute("maxvolume"))
		status.mpVolume = int(e.attribute("mpvolume"))
		status.mpMaxVolume = int(e.attribute("mpmaxvolume"))
		status.backMpVolume = int(e.attribute("backmpvolume"))
		status.backMpMaxVolume = int(e.attribute("backmpmaxvolume"))
		status.backItem = None if e.attribute("backpath") == "" else PlaylistItem(QtCore.QUrl.fromPercentEncoding(str(e.attribute("backpath")).replace('+', ' ')))
		status.backState = e.attribute("backstate")
		status.currentTrackNo = int(e.attribute("playing"))
		status.stopAfter = int(e.attribute("stopAfter"))
		status.stopAfterType = int(e.attribute("stopType"))
		list1 = e.elementsByTagName("item")
		status.playlist = []
		for i in range(list1.length()):
			e1 = list1.item(i).toElement()
#			path = urllib.unquote(str(e1.attribute("path"))).decode('utf8')
			path = QtCore.QUrl.fromPercentEncoding(str(e1.attribute("path")).replace('+', ' '))
#			print unicode(path)
			it = PlaylistItem(path)
			status.playlist.append(it)

		return status

class Response:
	def __init__(self):
		self.valid = False
		self.cause = ""
		self.status = PlayerStatus()

	@staticmethod
	def parse(s):
		res = Response()
		doc = QtXml.QDomDocument()
		doc.setContent(s)
		root = doc.documentElement()


		if "response" != root.tagName():
			print "wrong tag!!!"
		res.valid = str(root.attribute("valid")) == "true"
		res.cause = str(root.attribute("reason"))

		ls = root.elementsByTagName("status")
		if len(ls) == 1:
			e = ls.item(0).toElement()
			res.status = PlayerStatus.fromDom(e)
		return res




































