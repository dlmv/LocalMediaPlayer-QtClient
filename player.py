#!/usr/bin/python
import sys, math, os
sys.dont_write_bytecode = True
from PyQt4 import QtGui, QtCore, QtNetwork

import resources
from playerdata import *
from playerutil import *
from playerdialogs import *
from playerstatus import *
from playerstyle import *
from playerwidgets import *


class Main(QtGui.QWidget):

	def __init__(self, parent=None):
		QtGui.QWidget.__init__(self, parent)
		self.lazyStatusInProgress = False
		self.setWindowTitle('Local Player')
		self.status = PlayerStatus()
		self.volumeBarIsAdjusting = False
		self.playBarIsAdjusting = False
		self.mpVolumeBarIsAdjusting = False
		self.backMpVolumeBarIsAdjusting = False
		self.trackNum = 0
		l = QtGui.QVBoxLayout(self)
		self.toolbar = Toolbar(self)
		l.addWidget(self.toolbar)

		connector = ConnectManager(self)
		self.toolbar.connectButton.clicked.connect(lambda: self.connect(connector))
		self.toolbar.reloadButton.clicked.connect(lambda: self.getStatus(False))
		self.toolbar.volumeButton.clicked.connect(self.showVolumeDialog)
		self.toolbar.settingsButton.clicked.connect(self.showSettingsDialog)
		self.toolbar.playButton.clicked.connect(self.onPlayButton)
		self.toolbar.stopButton.clicked.connect(self.onStopButton)
		self.toolbar.nextButton.clicked.connect(self.onNextButton)
		self.toolbar.prevButton.clicked.connect(self.onPrevButton)
		self.toolbar.playtypeButton.clicked.connect(self.onPlayTypeButton)
		self.toolbar.browseButton.clicked.connect(self.openFileDialog)
		

		self.seekbar = Seekbar(self)
		l.addWidget(self.seekbar)
		self.seekbar.playBar.sliderPressed.connect(self.onPlayPressed)
		self.seekbar.playBar.sliderMoved.connect(self.onPlayMoved)
		self.seekbar.playBar.sliderReleased.connect(self.onPlayReleased)
		self.seekbar.playBar.valueChanged.connect(self.onPlaySet)

		self.playlist = Playlist()
		self.playlist.horizontalHeader().hide()
		self.playlist.verticalHeader().hide()
		self.playlist.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.playlist.setSelectionMode(QtGui.QAbstractItemView.ContiguousSelection)
		self.playlist.setShowGrid(False)
		self.playlist.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.playlist.customContextMenuRequested.connect(self.popup)
		self.playlist.doubleClicked.connect(self.onDoubleClick)
		self.playlist.space.connect(self.onPlayButton)
		self.playlist.drop.connect(self.onDropUrls)
#		self.playlist.setItemDelegate(LineDelegate(self.playlist))
		self.model = PlaylistModel(self.playlist)

		self.volumeBar = JumpSlider(QtCore.Qt.Vertical)
		self.volumeBar.setTracking(True)
		self.volumeBar.sliderPressed.connect(self.onVolumePressed)
		self.volumeBar.sliderReleased.connect(self.onVolumeReleased)
		self.volumeBar.valueChanged.connect(self.onVolumeSet)

		self.playlist.setModel(self.model)
		h = QtGui.QHBoxLayout()
		h.addWidget(self.playlist)
		v = QtGui.QVBoxLayout()
		volumeicon = createimageLabel(":/images/volume.png", v)
		v.addWidget(self.volumeBar)
		h.addLayout(v)
		l.addLayout(h)
		self.playlist.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.Stretch)
		self.playlist.setColumnWidth(0, 30)
		self.playlist.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.Fixed)

		self.lastPlayingPosition = 0
		self.lastUpdateTime = None

		tickTimer = QtCore.QTimer(self)
		tickTimer.timeout.connect(self.onTick)
		tickTimer.start(500)

		connectTimer = QtCore.QTimer(self)
		connectTimer.timeout.connect(lambda: self.getStatus(True))
		connectTimer.start(10000)

		self.volumeDialog = VolumeDialog()
		self.volumeDialog.pSlider.sliderPressed.connect(self.onMpVolumePressed)
		self.volumeDialog.pSlider.sliderReleased.connect(self.onMpVolumeReleased)
		self.volumeDialog.pSlider.valueChanged.connect(self.onMpVolumeSet)

		self.volumeDialog.bSlider.sliderPressed.connect(self.onBackMpVolumePressed)
		self.volumeDialog.bSlider.sliderReleased.connect(self.onBackMpVolumeReleased)
		self.volumeDialog.bSlider.valueChanged.connect(self.onBackMpVolumeSet)
		self.volumeDialog.playButton.clicked.connect(self.onPlayBackgroundButton)
		self.volumeDialog.stopButton.clicked.connect(self.stopBackground)
		self.volumeDialog.openButton.clicked.connect(self.openBackground)
		
		self.volumeDialog.drop.connect(self.onDropBackground)
		
		self.shareLoginManager = ShareLoginManager(self)
	
		self.rewritingManager = RewritingManager(self)		
		
		self.settingsDialog = SettingsDialog()
		self.settingsDialog.loginsButton.clicked.connect(self.requestLogins)
		self.settingsDialog.passButton.clicked.connect(self.requestPassword)
		self.settingsDialog.rewritingsButton.clicked.connect(self.rewritingManager.showRewritings)
		
		
		self.loginManager = LoginManager(self)
		self.loginManager.loginOk.connect(self.onLogin)
		self.loginManager.loginCancel.connect(self.onLoginCancel)
		self.loginManager.loginError.connect(self.onLoginError)	
		self.loginErrorHandled = False
		
		self.enqueueManager = EnqueueManager(self)
		
		

	def keyPressEvent(self, event):
		if event.key() == QtCore.Qt.Key_Space:
			self.onPlayButton()
		else:
			QtGui.QWidget.keyPressEvent(self, event)

	def onDoubleClick(self, mi):
		self.playNum(mi.row())

	def popup(self, pos):
		if self.playlist.selectionModel().selection().indexes():
			start = None
			finish = None
			for i in self.playlist.selectionModel().selection().indexes():
				if i.column() == 0:
					if not start:
						start = i.row()
						finish = i.row()
					else:
						start = min(i.row(), start)
						finish = max(i.row(), start)
			self.menu = QtGui.QMenu(self)
			if start == finish:
				playAction = QtGui.QAction('Play', self)
				playAction.triggered.connect(lambda: self.playNum(start))
				self.menu.addAction(playAction)
				playAction = QtGui.QAction('Play one track', self)
				playAction.triggered.connect(lambda: self.playSelected(start, finish))
				self.menu.addAction(playAction)
				openAction = QtGui.QAction('Open folder', self)
				openAction.triggered.connect(lambda: self.openFolder(self.status.playlist[start].path))
				self.menu.addAction(openAction)
				removeAction = QtGui.QAction('Remove', self)
				removeAction.triggered.connect(lambda: self.remove(start, start))
				self.menu.addAction(removeAction)
				if start > 0:
					removeBeforeAction = QtGui.QAction('Remove before', self)
					removeBeforeAction.triggered.connect(lambda: self.remove(0, start - 1))
					self.menu.addAction(removeBeforeAction)
				if finish < len(self.status.playlist) - 1:
					removeAfterAction = QtGui.QAction('Remove after', self)
					removeAfterAction.triggered.connect(lambda: self.remove(finish + 1, len(self.status.playlist) - 1))
					self.menu.addAction(removeAfterAction)
				clearAction = QtGui.QAction('Clear all', self)
				clearAction.triggered.connect(self.clearAll)
				self.menu.addAction(clearAction)
				stopAfterAction = QtGui.QAction('Stop after this', self)
				stopAfterAction.triggered.connect(lambda: self.setStopLabel(start, PlayerStatus.STOP))
				self.menu.addAction(stopAfterAction)
				pauseAfterAction = QtGui.QAction('Pause after this', self)
				pauseAfterAction.triggered.connect(lambda: self.setStopLabel(start, PlayerStatus.PAUSE))
				self.menu.addAction(pauseAfterAction)
				if self.status.stopAfter == start:
					clearStopAction = QtGui.QAction('Clear stop label', self)
					clearStopAction.triggered.connect(lambda: self.setStopLabel(-1, PlayerStatus.STOP))
					self.menu.addAction(clearStopAction)
			else:
				playAction = QtGui.QAction('Play selected', self)
				playAction.triggered.connect(lambda: self.playSelected(start, finish))
				self.menu.addAction(playAction)
				removeAction = QtGui.QAction('Remove', self)
				removeAction.triggered.connect(lambda: self.remove(start, finish))
				self.menu.addAction(removeAction)
				if start > 0:
					removeBeforeAction = QtGui.QAction('Remove before', self)
					removeBeforeAction.triggered.connect(lambda: self.remove(0, start - 1))
					self.menu.addAction(removeBeforeAction)
				if finish < len(self.status.playlist) - 1:
					removeAfterAction = QtGui.QAction('Remove after', self)
					removeAfterAction.triggered.connect(lambda: self.remove(finish + 1, len(self.status.playlist) - 1))
					self.menu.addAction(removeAfterAction)
				clearAction = QtGui.QAction('Clear all', self)
				clearAction.triggered.connect(self.clearAll)
				self.menu.addAction(clearAction)
			self.menu.popup(QtGui.QCursor.pos())


	def playNum(self, num):
		self.performMapRequest(ServerPath.PLAY_NUM, {ServerPath.NUM: str(num)})

	def playSelected(self, start, finish):
		self.setStopLabel(finish, PlayerStatus.STOP)
		self.playNum(start)

	def remove(self, start, finish):
		self.performMapRequest(ServerPath.REMOVE, {ServerPath.START: str(start), ServerPath.FINISH: str(finish)})

		self.playlist.clearSelection()

	def clearAll(self):
		self.performSimpleRequest(ServerPath.CLEAR)

	def setStopLabel(self, num, typ):
		self.performMapRequest(ServerPath.STOP_AFTER, {ServerPath.NUM: str(num), ServerPath.TYPE: str(typ)})

	def onPlayButton(self):
		if self.status.state == PlayerStatus.STOPPED or self.status.state == PlayerStatus.PAUSED:
			self.performSimpleRequest(ServerPath.PLAY)
		elif self.status.state == PlayerStatus.PLAYING:
			self.performSimpleRequest(ServerPath.PAUSE)
			
	def onPlayBackgroundButton(self):
		if self.status.backState == PlayerStatus.PAUSED:
			self.performSimpleRequest(ServerPath.RESUME_BACKGROUND)
		elif self.status.backState == PlayerStatus.PLAYING:
			self.performSimpleRequest(ServerPath.PAUSE_BACKGROUND)	

	def stopBackground(self):
		self.performSimpleRequest(ServerPath.STOP_BACKGROUND)

	def onStopButton(self):
		self.performSimpleRequest(ServerPath.STOP)

	def onNextButton(self):
		if (self.status.state == PlayerStatus.PLAYING or self.status.state == PlayerStatus.PAUSED) and ((self.status.currentTrackNo + 1) < len(self.status.playlist)):
			self.playNum(self.status.currentTrackNo + 1)

	def onPrevButton(self):
		if (self.status.state == PlayerStatus.PLAYING or self.status.state == PlayerStatus.PAUSED) and ((self.status.currentTrackNo - 1) >= 0):
			self.playNum(self.status.currentTrackNo - 1)

	def onPlayTypeButton(self):
		self.performMapRequest(ServerPath.SET_PLAYTYPE, {ServerPath.TYPE: str(self.status.nextType())})

	def onTick(self):
		if self.status.state == PlayerStatus.PLAYING:
			self.setPosition(0, False)
			self.setPlayBar()

	def setPosition(self, ms, sure):
		if sure:
			self.status.currentPosition = ms
			self.lastPlayingPosition = ms
			self.lastUpdateTime = QtCore.QDateTime.currentDateTime()
		else:
			self.status.currentPosition = int(self.lastPlayingPosition + QtCore.QDateTime.currentDateTime().toMSecsSinceEpoch() - self.lastUpdateTime.toMSecsSinceEpoch())

	def onVolumePressed(self):
		self.volumeBarIsAdjusting = True
	def onVolumeReleased(self):
		self.volumeBarIsAdjusting = False
	def onVolumeSet(self, value):
		self.performMapRequest(ServerPath.SET_VOLUME, {ServerPath.VOLUME: str(self.volumeBar.value())})

	def onMpVolumePressed(self):
		self.mpVolumeBarIsAdjusting = True
	def onMpVolumeReleased(self):
		self.mpVolumeBarIsAdjusting = False
	def onMpVolumeSet(self, value):
		self.performMapRequest(ServerPath.SET_MP_VOLUME, {ServerPath.VOLUME: str(self.volumeDialog.pSlider.value())})

	def onBackMpVolumePressed(self):
		self.backMpVolumeBarIsAdjusting = True
	def onBackMpVolumeReleased(self):
		self.backMpVolumeBarIsAdjusting = False
	def onBackMpVolumeSet(self, value):
		self.performMapRequest(ServerPath.SET_BACKMP_VOLUME, {ServerPath.VOLUME: str(self.volumeDialog.bSlider.value())})

	def onPlayPressed(self):
		self.playBarIsAdjusting = True
		self.trackNum = self.status.currentTrackNo
		self.seekbar.current.setText(timeFormat(self.seekbar.playBar.value()))
	def onPlayMoved(self, value):
		self.seekbar.current.setText(timeFormat(value))
	def onPlayReleased(self):
		self.playBarIsAdjusting = False
	def onPlaySet(self):
		self.performMapRequest(ServerPath.SEEK_TO, {ServerPath.NUM: str(self.trackNum), ServerPath.POSITION : str(self.seekbar.playBar.value() * 1000)})

	def showVolumeDialog(self):
		self.volumeDialog.exec_()


	def showSettingsDialog(self):
		self.settingsDialog.exec_()

	def connect(self, connector):
		connector.showConnect(DataHolder.uri)
		self.setUri(connector.uri)

	def setUri(self, uri):
		self.loginErrorHandled = False
		DataHolder.uri = uri
		DataHolder.uri
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		settings.setValue("lasturi", uri)
		r = Response()
		r.status = PlayerStatus()
		r.valid = uri != None
		r.cause = "" if uri != None else "Disconnected"
		self.init(r)

		self.getStatus(False)
	
	
	def createRequestUri(self, path):
		if not DataHolder.uri:
			return None
		return QtCore.QUrl(DataHolder.uri + path)

	def performSimpleRequest(self, path):
		uri = self.createRequestUri(path)
		if uri:
			self.performRequest(uri, False, False)

	def performMapRequest(self, path, params):
		uri = self.createRequestUri(path)
		if uri:
			for k in params.keys():
				uri.addQueryItem(k, params[k])
			self.performRequest(uri, False, False)
			
	def performRequest(self, uri, lazy, init):
		if not DataHolder.uri:
			return
		if lazy:
			self.lazyStatusInProgress = True
		else:
			pass
		request = QtNetwork.QNetworkRequest(uri)
		reply = QtGui.QApplication.instance().NAM.get(request)
		reply.finished.connect(lambda: self.onRequestReply(lazy, init))

	def getStatus(self, lazy):
		if not DataHolder.uri:
			return
		if lazy and self.lazyStatusInProgress:
			return
		uri = self.createRequestUri(ServerPath.LAZY_STATUS if lazy else ServerPath.STATUS)
		if uri:
			self.performRequest(uri, lazy, True)

	def onRequestReply(self, lazy, init):
		reply = QtCore.QObject.sender(self)
		reply.deleteLater()
		if lazy:
			self.lazyStatusInProgress = False
		if reply.error() == QtNetwork.QNetworkReply.NoError:
			if init:
				if DataHolder.uri:
					self.init(Response.parse(reply.readAll()))
		elif reply.error() == QtNetwork.QNetworkReply.AuthenticationRequiredError:
			if not self.loginErrorHandled:
				self.loginErrorHandled = True
				self.loginManager.tryLogin(self, DataHolder.uri)

	def init(self, r):
		self.getStatus(True)
		if not r.valid:
			if r.cause.startswith("loginNeeded:"):
				share = r.cause[len("loginNeeded:") + 1:].strip()
				self.shareLoginManager.showDialog(share)
			else:
				pass
		self.status = r.status
		self.setPosition(self.status.currentPosition, True)
		self.toolbar.update(self.status)
		self.setVolumeBar()
		self.setPlayBar()
		self.setVolumeDialog()
		self.model.setStatus(self.status)

	def setVolumeBar(self):
		if self.volumeBarIsAdjusting:
			return
		self.volumeBar.setMinimum(0)
		self.volumeBar.blockSignals(True)
		if self.status.maxVolume > 0 and self.status.volume >= 0 and self.status.volume <= self.status.maxVolume:
			self.volumeBar.setMaximum(self.status.maxVolume)

			self.volumeBar.setValue(self.status.volume)
		else:
			self.volumeBar.setMaximum(0)
			self.volumeBar.setValue(0)
		self.volumeBar.blockSignals(False)

	def setPlayBar(self):
		if self.playBarIsAdjusting:
			return
		self.seekbar.playBar.setMinimum(0)
		self.seekbar.playBar.blockSignals(True)
		if self.status.currentDuration > 0 and self.status.currentPosition >= 0 and self.status.currentPosition <= self.status.currentDuration:
			self.seekbar.playBar.setMaximum(self.status.currentDuration / 1000)
			self.seekbar.playBar.setValue(self.status.currentPosition / 1000)
		else:
			self.seekbar.playBar.setMaximum(0)
			self.seekbar.playBar.setValue(0)
		self.seekbar.playBar.blockSignals(False)
		self.seekbar.total.setText(timeFormat(self.status.currentDuration / 1000))
		self.seekbar.current.setText(timeFormat(self.status.currentPosition / 1000))

	def setVolumeDialog(self):
		if not self.mpVolumeBarIsAdjusting:
			self.volumeDialog.pSlider.blockSignals(True)
			if self.status.mpMaxVolume > 0 and self.status.mpVolume >= 0 and self.status.mpVolume <= self.status.mpMaxVolume:
				self.volumeDialog.pSlider.setMaximum(self.status.mpMaxVolume)
				self.volumeDialog.pSlider.setValue(self.status.mpVolume)
			else:
				self.volumeDialog.pSlider.setMaximum(0)
				self.volumeDialog.pSlider.setValue(0)
			self.volumeDialog.pSlider.blockSignals(False)
		if not self.backMpVolumeBarIsAdjusting:
			self.volumeDialog.bSlider.blockSignals(True)
			if (self.status.backMpMaxVolume > 0 and self.status.backMpVolume >= 0 and self.status.backMpVolume <= self.status.backMpMaxVolume):
				self.volumeDialog.bSlider.setMaximum(self.status.backMpMaxVolume)
				self.volumeDialog.bSlider.setValue(self.status.backMpVolume)
			else:
				self.volumeDialog.bSlider.setMaximum(0)
				self.volumeDialog.bSlider.setValue(0)
			self.volumeDialog.bSlider.blockSignals(False)
		if self.status.backItem != None:
			self.volumeDialog.backLabel.setText(self.status.backItem.getName())
		else:
			self.volumeDialog.backLabel.setText("Empty")
		if self.status.backState == PlayerStatus.PLAYING:
			self.volumeDialog.playButton.show()
			self.volumeDialog.stopButton.show()
			updateButton(self.volumeDialog.playButton, ":/images/pause.png")
		elif self.status.backState == PlayerStatus.PAUSED:
			self.volumeDialog.playButton.show()
			self.volumeDialog.stopButton.show()
			updateButton(self.volumeDialog.playButton, ":/images/play.png")	
		else:
			self.volumeDialog.playButton.hide()
			self.volumeDialog.stopButton.hide()			

	def closeEvent(self, event):
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		settings.setValue("geometry", self.saveGeometry())
		QtGui.QWidget.closeEvent(self, event)

	def showEvent(self, event):
		QtGui.QWidget.showEvent(self, event)
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		uri = str(settings.value("lasturi", None).toString())
		if uri:
			url = QtCore.QUrl(uri + ServerPath.STATUS)
			request = QtNetwork.QNetworkRequest(url)
			reply = QtGui.QApplication.instance().NAM.get(request)
			reply.finished.connect(lambda: self.onStartReply(uri))
		

	def onStartReply(self, uri):
		reply = QtCore.QObject.sender(self)
		reply.deleteLater()
		if reply.error() == QtNetwork.QNetworkReply.NoError:
			self.setUri(uri)
			self.onCommandline(self.arg)
		elif reply.error() == QtNetwork.QNetworkReply.AuthenticationRequiredError:
			self.loginManager.tryLogin(self, uri)
	
	def onLogin(self, uri):
		self.setUri(uri)

	def onLoginCancel(self):
		self.setUri(None)
	
	def onLoginError(self, error):
		pass
	
	def requestLogins(self):
		uri = self.createRequestUri(ServerPath.LOGIN_LIST)
		if uri:
			request = QtNetwork.QNetworkRequest(uri)
			reply = QtGui.QApplication.instance().NAM.get(request)
			reply.finished.connect(self.onLoginsReply)	
	
	def onLoginsReply(self):
		reply = QtCore.QObject.sender(self)
		reply.deleteLater()
		if reply.error() == QtNetwork.QNetworkReply.NoError:
			shares, logins = LoginsDialog.parse(reply.readAll())
			ldialog = LoginsDialog(shares, logins)
			ldialog.exec_()
		elif reply.error() == QtNetwork.QNetworkReply.AuthenticationRequiredError:
			self.loginManager.tryLogin(self, uri)	
			
	def requestPassword(self):
		dialog = InputDialog()
		dialog.label1.setText("Master password:")
		dialog.label2.setText("New server password:")
		dialog.optionButton.hide()
		dialog.okButton.setText("Ok")
		dialog.okPressed.connect(lambda: self.setPassword(dialog))
		dialog.exec_()
	
	def setPassword(self, dialog):
		mpass = str(dialog.edit1.text())
		npass = str(dialog.edit2.text())
		uri = self.createRequestUri(ServerPath.SET_PASSWORD)
		if uri:
			uri.addQueryItem(ServerPath.MASTER_PASSWORD, mpass)
			uri.addQueryItem(ServerPath.PASSWORD, npass)
			request = QtNetwork.QNetworkRequest(uri)
			reply = QtGui.QApplication.instance().NAM.get(request)
			reply.finished.connect(lambda: self.onPasswordReply(dialog))
	
	def onPasswordReply(self, dialog):
		reply = QtCore.QObject.sender(self)
		reply.deleteLater()
		if reply.error() == QtNetwork.QNetworkReply.NoError:
			dialog.close()
		else:
			dialog.message.setText(reply.errorString())
			dialog.message.show()
	
	def openFolder(self, path):
		path = self.rewritingManager.rewriteRemotePath(path)
		dr = path[:path.rfind("/")]
		url = QtCore.QUrl.fromLocalFile(dr)
		QtGui.QDesktopServices.openUrl(url)

	separator = ":$&^*#&^;3*"

	def onCommandline(self, arg):
		if arg:
			files = unicode(arg).split(Main.separator)
			newfiles = []
			for f in files:
				nf = self.convertPath(f)
				if nf:
					newfiles.append(nf)
			self.onNewFiles(newfiles, Database.launchOpenAction() == Database.ENQUEUE_AND_PLAY)
	
	def convertUrl(self, url):
		f = unicode(url.toLocalFile())
		if f:
			return self.convertPath(f)
		elif url.scheme() == "smb":
			return unicode(url.toString())
		
	def convertPath(self, path):		
		return unicode(self.rewritingManager.rewriteLocalPath(path))
		
	
	def onDropUrls(self, urls):
		print urls
		newfiles = []
		for url in urls:
			nf = self.convertUrl(url)
			if nf:
				newfiles.append(nf)			
		self.onNewFiles(newfiles, Database.dropOpenAction() == Database.ENQUEUE_AND_PLAY)	
		
	def onDropBackground(self, url):
		nf = self.convertUrl(url)
		if nf:
			self.onBackgroundFile(nf)
			
	
	def openFileDialog(self):
		f = unicode(QtGui.QFileDialog.getExistingDirectory(self, "Open folder"))
		if f:
			f = self.convertPath(f)
			if f:
				self.onNewFiles([f], Database.dialogOpenAction() == Database.ENQUEUE_AND_PLAY)
	
	def openBackground(self):
		f = unicode(QtGui.QFileDialog.getOpenFileName(self, "Open background file"))
		if f:
			f = self.convertPath(f)
			if f:
				self.onBackgroundFile(f)
	
	def onBackgroundFile(self, f):
		self.enqueueManager.playBackground(f)
	
	
	def onNewFiles(self, files, reset):
		if files:
			if reset:
				self.enqueueManager.enqueueAndPlay(files[0])
			else:
				self.enqueueManager.enqueue(files[0])
			for f in files[1:]:
				self.enqueueManager.enqueue(f)

def main():
	app = QtSingleApplication(Keys.organization+"-"+Keys.app, sys.argv)
	print app.isRunning()
	args = [os.path.join(os.getcwd(), x) for x in sys.argv[1:]]
	arg = Main.separator.join(args).decode('utf-8')
	if (app.sendMessage(arg)):
		sys.exit(0)
	app.setStyleSheet(darkStyle1)
	w = Main()
	w.arg = arg
	w.show()
	app.setActivationWindow(w)
	app.messageReceived.connect(w.onCommandline)
	settings = QtCore.QSettings(Keys.organization, Keys.app)
	if settings.contains("geometry"):
		w.restoreGeometry(settings.value("geometry").toByteArray())

	sys.exit(app.exec_())

if __name__ == '__main__':
	main()


