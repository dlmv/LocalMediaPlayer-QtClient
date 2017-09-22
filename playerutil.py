from PyQt4 import QtGui, QtCore, QtNetwork

class InputDialog(QtGui.QDialog):

	okPressed = QtCore.pyqtSignal()

	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)
		self.setWindowTitle('Connect')
		self.label1 = QtGui.QLabel()
		self.label2 = QtGui.QLabel()
		self.edit1 = QtGui.QLineEdit()
		self.edit2 = QtGui.QLineEdit()
		self.optionButton = QtGui.QPushButton()
		self.okButton = QtGui.QPushButton()
		self.thirdButton = QtGui.QPushButton()
		self.thirdButton.hide()
		self.message = QtGui.QLabel()
		self.titleMessage = QtGui.QLabel()
		v = QtGui.QVBoxLayout(self)
		v.addWidget(self.titleMessage)
		g = QtGui.QGridLayout()
		g.addWidget(self.label1, 0, 0)
		g.addWidget(self.edit1, 0, 1)
		g.addWidget(self.label2, 1, 0)
		g.addWidget(self.edit2, 1, 1)
		v.addLayout(g)
		v.addWidget(self.message)
		self.message.hide()
		self.titleMessage.hide()
		h = QtGui.QHBoxLayout()
		h.addWidget(self.optionButton)
		h.addWidget(self.okButton)
		h.addWidget(self.thirdButton)
		v.addLayout(h)
		
		self.edit1.returnPressed.connect(self.onPress)
		self.edit2.returnPressed.connect(self.onPress)
		self.okButton.clicked.connect(self.onPress)

	def onPress(self):
		self.okPressed.emit()

def createButton(imagePath, layout):
	pixmap = QtGui.QPixmap(imagePath)
	icon = QtGui.QIcon(pixmap)
	button = QtGui.QPushButton()
	button.setIcon(icon)
	button.setIconSize(pixmap.rect().size())
	button.setFixedSize(pixmap.rect().size())
	layout.addWidget(button)
	return button

def createimageLabel(imagePath, layout):
	pixmap = QtGui.QPixmap(imagePath)
	label = QtGui.QLabel()
	label.setPixmap(pixmap)
	label.setFixedSize(pixmap.rect().size())
	layout.addWidget(label)
	return label

def updateButton(button, imagePath):
	pixmap = QtGui.QPixmap(imagePath)
	icon = QtGui.QIcon(pixmap)
	button.setIcon(icon)
	button.setIconSize(pixmap.rect().size())
	button.setFixedSize(pixmap.rect().size())

def timeFormat(s):
	hours = s / 3600
	minutes = s / 60 - hours * 60
	seconds = s - minutes * 60 - hours * 3600
	res = ""
	if hours > 0:
		res += (str(hours) + ":")

	minu = str(minutes)
	if len(minu) == 1 and hours > 0:
		minu = "0" + minu
	sec = str(seconds)
	if len(sec) == 1:
		sec = "0" + sec
	return res + minu + ":" + sec


class QtSingleApplication(QtGui.QApplication):

	messageReceived = QtCore.pyqtSignal(unicode)

	def __init__(self, id, *argv):

		super(QtSingleApplication, self).__init__(*argv)
		self._id = id
		self._activationWindow = None
		self._activateOnMessage = False

		# Is there another instance running?
		self._outSocket = QtNetwork.QLocalSocket()
		self._outSocket.connectToServer(self._id)
		self._isRunning = self._outSocket.waitForConnected()

		if self._isRunning:
			# Yes, there is.
			self._outStream = QtCore.QTextStream(self._outSocket)
			self._outStream.setCodec('UTF-8')
		else:
			# No, there isn't.
			self._outSocket = None
			self._outStream = None
			self._inSocket = None
			self._inStream = None
			self._server = QtNetwork.QLocalServer(self)
			self._server.listen(self._id)
			self._server.newConnection.connect(self._onNewConnection)
			self.NAM = QtNetwork.QNetworkAccessManager(self)
			

	def isRunning(self):
		return self._isRunning

	def id(self):
		return self._id

	def activationWindow(self):
		return self._activationWindow

	def setActivationWindow(self, activationWindow, activateOnMessage = True):
		self._activationWindow = activationWindow
		self._activateOnMessage = activateOnMessage

	def activateWindow(self):
		if not self._activationWindow:
			return
		# Unfortunately this *doesn't* do much of any use, as it won't 
		# bring the window to the foreground under KDE... sigh.
		self._activationWindow.setWindowState(
			self._activationWindow.windowState() & ~QtCore.Qt.WindowMinimized)
		self._activationWindow.raise_()
		self._activationWindow.activateWindow()

	def sendMessage(self, msg):
		if not self._outStream:
			return False
		self._outStream << msg << '\n'
		self._outStream.flush()
		return self._outSocket.waitForBytesWritten()
		

	def _onNewConnection(self):
		if self._inSocket:
			self._inSocket.readyRead.disconnect(self._onReadyRead)
		self._inSocket = self._server.nextPendingConnection()
		if not self._inSocket:
			return
		self._inStream = QtCore.QTextStream(self._inSocket)
		self._inStream.setCodec('UTF-8')
		self._inSocket.readyRead.connect(self._onReadyRead)
		if self._activateOnMessage:
			self.activateWindow()

	def _onReadyRead(self):
		while True:
			msg = self._inStream.readLine()
			if not msg: break
			self.messageReceived.emit(msg)

class JumpSlider(QtGui.QSlider):

	def __init__(self, parent=None):
		QtGui.QSlider.__init__(self, parent)

	def mousePressEvent(self, event):
		opt = QtGui.QStyleOptionSlider()
		self.initStyleOption(opt)
		sr = self.style().subControlRect(QtGui.QStyle.CC_Slider, opt, QtGui.QStyle.SC_SliderHandle, self)
		if (event.button() == QtCore.Qt.LeftButton  and not sr.contains(event.pos())):
			inewVal = 0
			if (self.orientation() == QtCore.Qt.Vertical):
				halfHandleHeight = (0.5 * sr.height()) + 0.5
				adaptedPosY = self.height() - event.y()
				if adaptedPosY < halfHandleHeight:
							adaptedPosY = halfHandleHeight
				if adaptedPosY > self.height() - halfHandleHeight:
							adaptedPosY = self.height() - halfHandleHeight
				newHeight = (self.height() - halfHandleHeight) - halfHandleHeight
				normalizedPosition = (adaptedPosY - halfHandleHeight)	/ newHeight 

				newVal = self.minimum() + (self.maximum()-self.minimum()) * normalizedPosition
			else:
				halfHandleWidth = (0.5 * sr.width()) + 0.5
				adaptedPosX = event.x()
				if adaptedPosX < halfHandleWidth:
						adaptedPosX = halfHandleWidth
				if adaptedPosX > self.width() - halfHandleWidth:
						adaptedPosX = self.width() - halfHandleWidth
				newWidth = (self.width() - halfHandleWidth) - halfHandleWidth
				normalizedPosition = (adaptedPosX - halfHandleWidth)	/ newWidth 

				newVal = self.minimum() + ((self.maximum()-self.minimum()) * normalizedPosition)
			if (self.invertedAppearance()):
				self.setValue(int(maximum() - newVal))
			else:
				self.setValue(int(newVal))
			opt = QtGui.QStyleOptionSlider()
			self.initStyleOption(opt)
			sr = self.style().subControlRect(QtGui.QStyle.CC_Slider, opt, QtGui.QStyle.SC_SliderHandle, self)
			event = QtGui.QMouseEvent(QtCore.QEvent.MouseButtonPress, sr.center(), event.button(), event.buttons(), event.modifiers())
			QtGui.QSlider.mousePressEvent(self, event)
		else:
			QtGui.QSlider.mousePressEvent(self, event)

class ServerPath:
	LOGIN = "login"
	CHECK = "check"
	CHECK_SHARE = "checkShare"
	BROWSE = "browse"
	SEARCH = "search"
	STOP_SEARCH = "stopSearch"
	STATUS = "status"
	LAZY_STATUS = "lazyStatus"
	ENQUEUE = "enqueue"
	ENQUEUE_AND_PLAY = "enqueueAndPlay"
	SET_VOLUME = "setVolume"
	SET_MP_VOLUME = "setMpVolume"
	SET_BACKMP_VOLUME = "setBackMpVolume"
	VOLUME_UP = "volumeUp"
	VOLUME_DOWN = "volumeDown"
	PLAY = "play"
	PLAY_NUM = "playNum"
	PAUSE = "pause"
	STOP = "stop"
	REMOVE = "remove"
	SET_PLAYTYPE = "setPlaytype"
	STOP_AFTER = "stopAfter"
	SEEK_TO = "seekTo"
	CLEAR = "clear"
	IMAGE = "image"
	PLAY_BACKGROUND = "playBackground"
	PAUSE_BACKGROUND = "pauseBackground"
	RESUME_BACKGROUND = "resumeBackground"
	STOP_BACKGROUND = "stopBackground"
	LOGIN_LIST = "loginList"
	FORGET_LOGIN = "forgetLogin"
	SET_PASSWORD = "setPassword"

	PASSWORD = "password"
	MASTER_PASSWORD = "masterPassword"
	PATH = "path"
	REQUEST = "request"
	NUM = "num"
	VOLUME = "volume"
	TYPE = "type"
	POSITION = "position"
	START = "start"
	FINISH = "finish"





