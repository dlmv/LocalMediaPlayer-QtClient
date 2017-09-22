#!/usr/bin/python
import sys, math, os
sys.dont_write_bytecode = True
from PyQt4 import QtGui, QtCore, QtNetwork

import resources
from playerdata import *
from playerutil import *
from playerstatus import *

class PlaylistModel(QtCore.QAbstractTableModel):

	def __init__(self, parent=None):
		QtCore.QAbstractTableModel.__init__(self, parent)
		self.status = PlayerStatus()

	def rowCount(self, parent=QtCore.QModelIndex()):
		return len(self.status.playlist)

	def columnCount(self, parent=QtCore.QModelIndex()):
		return 2

	def data(self, index, role=QtCore.Qt.DisplayRole):
		if not index.isValid(): return None
		if index.column() == 0:
			if role == QtCore.Qt.DecorationRole:
				if self.status.currentTrackNo == index.row() and self.status.state == PlayerStatus.PLAYING:
					if index.row() == self.status.stopAfter:
						if self.status.stopAfterType == PlayerStatus.PAUSE:
							return QtGui.QPixmap(":/images/play_pause_after.png")
						else:
							return QtGui.QPixmap(":/images/play_stop_after.png")
					else:
						return QtGui.QPixmap(":/images/play_white.png")
				elif self.status.currentTrackNo == index.row() and self.status.state == PlayerStatus.PAUSED:
					if index.row() == self.status.stopAfter:
						if self.status.stopAfterType == PlayerStatus.PAUSE:
							return QtGui.QPixmap(":/images/pause_pause_after.png")
						else:
							return QtGui.QPixmap(":/images/pause_stop_after.png")
					else:
						return QtGui.QPixmap(":/images/pause_white.png")
				else:
					if index.row() == self.status.stopAfter:
						if self.status.stopAfterType == PlayerStatus.PAUSE:
							return QtGui.QPixmap(":/images/pause_after.png")
						else:
							return QtGui.QPixmap(":/images/stop_after.png")
					else:
						return QtGui.QPixmap(":/images/play_transparent.png")
			return None
		else:
			if role == QtCore.Qt.DisplayRole:
				return self.status.playlist[index.row()].getName()
			return None

	def setStatus(self, status):
		self.layoutAboutToBeChanged.emit()
		self.status = status
		self.layoutChanged.emit()

class Toolbar(QtGui.QWidget):

	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		l = QtGui.QHBoxLayout(self)

		self.prevButton = createButton(":/images/prev.png", l)
		self.playButton = createButton(":/images/play.png", l)
		self.stopButton = createButton(":/images/stop.png", l)
		self.nextButton = createButton(":/images/next.png", l)
		self.playtypeButton = createButton(":/images/linear.png", l)

		l.addStretch()
		self.reloadButton = createButton(":/images/reload.png", l)
		self.volumeButton = createButton(":/images/menu_volume.png", l)
		self.browseButton = createButton(":/images/browse.png", l)
		self.settingsButton = createButton(":/images/menu_settings.png", l)
		self.reloadButton.hide()
		self.volumeButton.hide()
		self.settingsButton.hide()
		self.browseButton.hide()
		self.connectButton = createButton(":/images/connect.png", l)
		

	def update(self, status):
		if status.state == PlayerStatus.PLAYING:
			updateButton(self.playButton, ":/images/pause.png")
		else:
			updateButton(self.playButton, ":/images/play.png")
		if status.type == PlayerStatus.CYCLIC:
			updateButton(self.playtypeButton, ":/images/cycle.png")
		else:
			updateButton(self.playtypeButton, ":/images/linear.png")
		if DataHolder.uri:
			updateButton(self.connectButton, ":/images/connected.png")
			self.reloadButton.show()
			self.volumeButton.show()
			self.settingsButton.show()
			self.browseButton.show()
		else:
			updateButton(self.connectButton, ":/images/connect.png")
			self.reloadButton.hide()
			self.volumeButton.hide()
			self.settingsButton.hide()
			self.browseButton.hide()

class Seekbar(QtGui.QWidget):

	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		l = QtGui.QHBoxLayout(self)
		self.current = QtGui.QLabel()
		self.current.setText("00:00")
		self.total = QtGui.QLabel()
		self.total.setText("00:00")
		self.playBar = JumpSlider(QtCore.Qt.Horizontal)
		self.playBar.setTracking(False)
		l.addWidget(self.current)
		l.addWidget(self.playBar)
		l.addWidget(self.total)

class Playlist(QtGui.QTableView):

	enter = QtCore.pyqtSignal()
	space = QtCore.pyqtSignal()
	
	drop = QtCore.pyqtSignal(list)
	
	def __init__(self, parent=None):
		QtGui.QTableView.__init__(self, parent)
		self.setAcceptDrops(True)
		
	def dragEnterEvent(self, e):
		if e.mimeData().hasUrls():
			e.acceptProposedAction()
			
	def dragMoveEvent(self, e):
		if e.mimeData().hasUrls():
			e.acceptProposedAction()
	
	def dropEvent(self, e):
		self.drop.emit(e.mimeData().urls())


	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Return:
			self.enter.emit()
		elif event.key() == QtCore.Qt.Key_Space:
			self.space.emit()
		else:
			QtGui.QWidget.keyPressEvent(self, event)
