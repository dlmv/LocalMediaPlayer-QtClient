from PyQt4 import QtGui, QtCore, QtNetwork
import re, Queue
from playerutil import *
from playerdata import *



class ConnectManager(QtCore.QObject):

	def __init__(self, parent=None):
		QtCore.QObject.__init__(self, parent)
		self.uri = None
		self.loginManager = LoginManager(self)
		self.loginManager.loginOk.connect(self.onLogin)
		self.loginManager.loginCancel.connect(self.onLoginCancel)
		self.loginManager.loginError.connect(self.onLoginError)
		self.dialog = InputDialog(parent)
		self.dialog.okPressed.connect(self.tryConnect)
		self.dialog.thirdButton.clicked.connect(self.disconnect)
		self.dialog.optionButton.clicked.connect(self.showServers)		
		

	def onLogin(self, uri):
		server = str(self.dialog.edit1.text())
		port = int(self.dialog.edit2.text())
		if not Database.serverSaved(server, port):
			ret = QtGui.QMessageBox.question(self.dialog, "", "Save server?", QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
			if ret == QtGui.QMessageBox.Yes:
				name, ok = QtGui.QInputDialog.getText(self.dialog, "", "Enter name:")
				if ok and name:
					Database.saveServer(name, server, port)
		self.uri = server + ":" + str(port) + "/"
		self.dialog.setEnabled(True)
		self.dialog.close()

	def onLoginCancel(self):
		self.dialog.message.setText("Password required")
		self.dialog.message.show()
		self.dialog.setEnabled(True)
	
	def onLoginError(self, error):
		self.dialog.message.setText(error)
		self.dialog.message.show()
		self.dialog.setEnabled(True)		

	def showConnect(self, uri):
		self.dialog.label1.setText("Ip:")
		self.dialog.label2.setText("Port:")
		self.dialog.edit1.setText("http://")
		self.dialog.edit2.setText("8123")
		if uri:
			index = uri.rfind(":")
			self.dialog.edit1.setText(uri[0 : index])
			self.dialog.edit2.setText(uri[index + 1 : -1])
			self.dialog.thirdButton.show()
		else:
			self.dialog.thirdButton.hide()
		self.dialog.edit2.setValidator(QtGui.QIntValidator(0, 16384, self))
		self.dialog.optionButton.setText("Servers")
		self.dialog.okButton.setText("Connect")
		self.dialog.thirdButton.setText("Disconnect")
		self.dialog.message.hide()
		self.uri = uri
		self.dialog.exec_()

	def disconnect(self):
		self.uri = None
		self.dialog.close()

	def showServers(self):
		sdialog = ServersDialog()
		sdialog.opened.connect(lambda x: self.loadServerInfo(x))
		sdialog.exec_()

	def loadServerInfo(self, row):
		sdialog = QtCore.QObject.sender(self)
		sdialog.close()
		name, server, port = Database.getServers()[row]
		server = server.toString()
		port, ok = port.toInt()
		self.dialog.edit1.setText(server)
		self.dialog.edit2.setText(str(port))

	def tryConnect(self):
		server = str(self.dialog.edit1.text())
		port = int(self.dialog.edit2.text())
		self.dialog.setEnabled(False)
		if not server.startswith("http"):
			server = "http://" + server
		uri = server + ":" + str(port) + "/"
		self.loginManager.tryLogin(self.dialog, uri)

class LoginManager(QtCore.QObject):

	loginOk = QtCore.pyqtSignal(str)
	loginCancel = QtCore.pyqtSignal()
	loginError = QtCore.pyqtSignal(QtCore.QString)

	def __init__(self, parent=None):
		QtCore.QObject.__init__(self, parent)

	def tryLogin(self, widget, uri):
		url = QtCore.QUrl(uri + ServerPath.LOGIN)
		request = QtNetwork.QNetworkRequest(url)
		reply = QtGui.QApplication.instance().NAM.get(request)
		reply.finished.connect(lambda: self.onLoginReply(widget, uri))	

	def onLoginReply(self, widget, uri):
		reply = QtCore.QObject.sender(self)
		reply.deleteLater()
		if reply.error() == QtNetwork.QNetworkReply.NoError:
			self.loginOk.emit(uri)
		elif reply.error() == QtNetwork.QNetworkReply.AuthenticationRequiredError:
			self.login(widget, uri)
		else:
			self.loginError.emit(reply.errorString())

	def login(self, widget, uri):
		password, ok = QtGui.QInputDialog.getText(widget, "Auhtorization", "Password for \n%s" % uri)
		if ok:
			url = QtCore.QUrl(uri + ServerPath.LOGIN)
			url.addQueryItem(ServerPath.PASSWORD, password)
			request = QtNetwork.QNetworkRequest(url)
			reply = QtGui.QApplication.instance().NAM.get(request)
			reply.finished.connect(lambda: self.onLoginReply(widget, uri))
		else:
			self.loginCancel.emit()


class VolumeDialog(QtGui.QDialog):
	
	drop = QtCore.pyqtSignal(QtCore.QUrl)

	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)
		l = QtGui.QVBoxLayout(self)
		pLabel = QtGui.QLabel()
		pLabel.setText("Player  volume")
		self.pSlider = JumpSlider(QtCore.Qt.Horizontal)
		self.pSlider.setTracking(False)
		l.addWidget(pLabel)
		l.addWidget(self.pSlider)
		bLabel = QtGui.QLabel()
		bLabel.setText("Background  volume")
		self.bSlider = JumpSlider(QtCore.Qt.Horizontal)
		self.bSlider.setTracking(False)
		l.addWidget(bLabel)
		l.addWidget(self.bSlider)
		tl = QtGui.QHBoxLayout()
		self.openButton = createButton(":/images/browse.png", tl)		
		tLabel = QtGui.QLabel()
		tLabel.setText("Background file:")
		tl.addWidget(tLabel)
		l.addLayout(tl)
		self.backLabel = QtGui.QLabel()
		l.addWidget(self.backLabel)
		bl = QtGui.QHBoxLayout()
		self.playButton = createButton(":/images/play.png", bl)
		self.stopButton = createButton(":/images/stop_background.png", bl)
		bl.addStretch()
		l.addLayout(bl)
		self.setAcceptDrops(True)
		
	def dragEnterEvent(self, e):
		if e.mimeData().hasUrls() and len(e.mimeData().urls()) == 1:
			e.acceptProposedAction()
			
	def dragMoveEvent(self, e):
		if e.mimeData().hasUrls() and len(e.mimeData().urls()) == 1:
			e.acceptProposedAction()
	
	def dropEvent(self, e):
		self.drop.emit(e.mimeData().urls()[0])		
		

class SettingsDialog(QtGui.QDialog):

	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)
		l = QtGui.QVBoxLayout(self)
		
		launchGroupBox = QtGui.QGroupBox("Launch open action")
		radio1 = QtGui.QRadioButton("Replace playlist and start playing")
		radio2 = QtGui.QRadioButton("Add to playlist")
		if Database.launchOpenAction() == Database.ENQUEUE_AND_PLAY:
			radio1.setChecked(True)
		else:
			radio2.setChecked(True)
		radio1.toggled.connect(lambda: Database.setLaunchOpenAction(Database.ENQUEUE_AND_PLAY))
		radio2.toggled.connect(lambda: Database.setLaunchOpenAction(Database.ENQUEUE))
		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(radio1)
		vbox.addWidget(radio2)
		launchGroupBox.setLayout(vbox)
		l.addWidget(launchGroupBox)
		
		dropGroupBox = QtGui.QGroupBox("Drop to playlist action")
		radio1 = QtGui.QRadioButton("Replace playlist and start playing")
		radio2 = QtGui.QRadioButton("Add to playlist")
		radio1.toggled.connect(lambda: Database.setDropOpenAction(Database.ENQUEUE_AND_PLAY))
		radio2.toggled.connect(lambda: Database.setDropOpenAction(Database.ENQUEUE))		
		if Database.dropOpenAction() == Database.ENQUEUE_AND_PLAY:
			radio1.setChecked(True)
		else:
			radio2.setChecked(True)		
		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(radio1)
		vbox.addWidget(radio2)
		dropGroupBox.setLayout(vbox)
		l.addWidget(dropGroupBox)
		
		dialogGroupBox = QtGui.QGroupBox("Open dialog action")
		radio1 = QtGui.QRadioButton("Replace playlist and start playing")
		radio2 = QtGui.QRadioButton("Add to playlist")
		radio1.toggled.connect(lambda: Database.setDialogOpenAction(Database.ENQUEUE_AND_PLAY))
		radio2.toggled.connect(lambda: Database.setDialogOpenAction(Database.ENQUEUE))		
		if Database.dialogOpenAction() == Database.ENQUEUE_AND_PLAY:
			radio1.setChecked(True)
		else:
			radio2.setChecked(True)		
		vbox = QtGui.QVBoxLayout()
		vbox.addWidget(radio1)
		vbox.addWidget(radio2)
		dialogGroupBox.setLayout(vbox)
		l.addWidget(dialogGroupBox)			
		
		self.passButton = QtGui.QPushButton()
		self.passButton.setText("Set Password")
		l.addWidget(self.passButton)
		self.loginsButton = QtGui.QPushButton()
		self.loginsButton.setText("Saved logins")
		l.addWidget(self.loginsButton)	
		self.rewritingsButton = QtGui.QPushButton()
		self.rewritingsButton.setText("Path rewriting")
		l.addWidget(self.rewritingsButton)	


class ShareLoginManager(QtCore.QObject):
	
	success = QtCore.pyqtSignal()
	
	def __init__(self, parent=None):
		QtCore.QObject.__init__(self, parent)
		self.dialog = InputDialog(parent)
		self.dialog.okPressed.connect(self.check)
		self.dialog.optionButton.hide()
	
	@staticmethod
	def parseResponse(s):
		pass
		
	def showDialog(self, share):
		if share[:-1] != "/":
			share = share + "/"
		self.dialog.label1.setText("Login:")
		self.dialog.label2.setText("Password:")
		self.dialog.edit1.setText("")
		self.dialog.edit2.setText("")		
		self.dialog.titleMessage.setText("Login required for: \n%s" % share)
		self.dialog.titleMessage.show()
		self.share = share
		self.dialog.okButton.setText("Ok")
		self.dialog.exec_()
		
	def check(self):
		login = str(self.dialog.edit1.text())
		password = str(self.dialog.edit2.text())
		if not DataHolder.uri:
			return
		url = QtCore.QUrl(DataHolder.uri + ServerPath.CHECK)
		url.addQueryItem(ServerPath.PASSWORD, password)
		url.addQueryItem(ServerPath.LOGIN, login)
		url.addQueryItem(ServerPath.PATH, self.share)
		request = QtNetwork.QNetworkRequest(url)
		reply = QtGui.QApplication.instance().NAM.get(request)
		reply.finished.connect(self.onReply)

	def onReply(self):
		reply = QtCore.QObject.sender(self)
		reply.deleteLater()
		if reply.error() == QtNetwork.QNetworkReply.NoError:
			doc = QtXml.QDomDocument()
			doc.setContent(reply.readAll())
			root = doc.documentElement()
			if "response" != root.tagName():
				print "wrong tag!!!"
			valid = str(root.attribute("valid")) == "true"
			cause = str(root.attribute("reason"))
			if valid:
				self.success.emit()
				self.dialog.close()
			elif cause.startswith("loginNeeded:"):
				self.dialog.message.setText("Auhtorization failed")
				self.dialog.message.show()
			else:
				self.dialog.message.setText(cause)
				self.dialog.message.show()				
		else:
			self.dialog.message.setText(reply.errorString())
			self.dialog.message.show()


class RegexpRewritingGuesser:
	def guess(self, s):
		m = re.match(self.regex, s)
		if m:
			return m.group(0), re.sub(self.regex, self.substitute, m.group(0))
		else:
			return None, None

class NautilusSmbGuesser(RegexpRewritingGuesser):
	
	def __init__(self):
		self.regex = r"/run/user/1000/gvfs/smb-share:server=(.*?),share=(.*?)/"
		self.substitute = r"smb://\1/\2/"
		
class RewritingManager(QtCore.QObject):
	def __init__(self, parent=None):
		QtCore.QObject.__init__(self, parent)
		self.dialog = InputDialog(parent)
		self.dialog.okButton.setText("Ok")
		self.dialog.okPressed.connect(self.checkRewrting)
		self.dialog.optionButton.setText("Rewritings")
		self.dialog.optionButton.clicked.connect(self.showRewritings)
		self.dialog.thirdButton.setText("Guess")
		self.dialog.thirdButton.clicked.connect(self.guessRewriting)
		self.dialog.thirdButton.show()		
		self.dialog.label1.setText("Local:")
		self.dialog.label2.setText("Remote:")
		self.localToRemote = True
		self.shareLoginManager = ShareLoginManager(parent)
		
		self.localToRemoteGuessers = [NautilusSmbGuesser()]
		self.remoteToLocalGuessers = []

	def checkRewrting(self):
		remote = unicode(self.dialog.edit2.text())
		if not DataHolder.uri:
			return
		url = QtCore.QUrl(DataHolder.uri + ServerPath.CHECK)
		url.addQueryItem(ServerPath.PATH, remote)
		
		request = QtNetwork.QNetworkRequest(url)
		reply = QtGui.QApplication.instance().NAM.get(request)
		reply.finished.connect(self.onCheckReply)
	
	def onCheckReply(self):
		reply = QtCore.QObject.sender(self)
		reply.deleteLater()
		if reply.error() == QtNetwork.QNetworkReply.NoError:
			doc = QtXml.QDomDocument()
			doc.setContent(reply.readAll())
			root = doc.documentElement()
			if "response" != root.tagName():
				print "wrong tag!!!"
			valid = str(root.attribute("valid")) == "true"
			cause = str(root.attribute("reason"))
			if valid:	
				self.onNewRewrting()
			elif cause.startswith("loginNeeded:"):
				share = cause[len("loginNeeded:") + 1:].strip()				
				self.shareLoginManager.showDialog(share)
			else:
				self.dialog.message.setText(cause)
				self.dialog.message.show()				
		else:
			self.dialog.message.setText(reply.errorString())
			self.dialog.message.show()		
	
	def showRewritings(self):
		sdialog = RewritingsDialog()
		sdialog.exec_()

	def onNewRewrting(self):
		local = unicode(self.dialog.edit1.text())
		remote = unicode(self.dialog.edit2.text())
		if remote and local:
			if not Database.rewritingSaved(local):
				Database.saveRewriting(remote, local)
				self.dialog.close()
			else:
				self.dialog.message.setText("Rewriting already exists for\n%s" % local)
				self.dialog.message.show()
	
	def guessRewriting(self):
		if self.localToRemote:
			local = unicode(self.dialog.edit1.text())
			for g in self.localToRemoteGuessers:
				l, r = g.guess(local)
				if l and r:
					self.dialog.edit1.setText(l)
					self.dialog.edit2.setText(r)
					return
			
	def rewriteLocalPath(self, path):
		self.localToRemote = True
		rewritings = Database.getRewritings()
		for remote, local in sorted(rewritings, key=lambda tup: tup[1], reverse=True):
			remote = unicode(remote.toString())
			local = unicode(local.toString())
			if path.startswith(local):
				return remote + path[len(local):]#TODO: windows paths?
		self.dialog.edit1.setText(path)
		self.dialog.edit2.setText("")
		self.dialog.message.hide()
		self.dialog.exec_()
		rewritings = Database.getRewritings()		
		for remote, local in sorted(rewritings, key=lambda tup: tup[1], reverse=True):
			remote = unicode(remote.toString())
			local = unicode(local.toString())
			if path.startswith(local):
				return remote + path[len(local):]
		return None

	def rewriteRemotePath(self, path):
		self.localToRemote = False
		rewritings = Database.getRewritings()
		for remote, local in sorted(rewritings, key=lambda tup: tup[1], reverse=True):
			remote = unicode(remote.toString())
			local = unicode(local.toString())
			if path.startswith(remote):
				return local + path[len(remote):]#TODO: windows paths?
		self.dialog.edit1.setText(path)
		self.dialog.edit2.setText("")
		self.dialog.message.hide()
		self.dialog.exec_()
		rewritings = Database.getRewritings()		
		for remote, local in sorted(rewritings, key=lambda tup: tup[1], reverse=True):
			remote = unicode(remote.toString())
			local = unicode(local.toString())
			if path.startswith(remote):
				return local + path[len(remote):]
		return None
		

class EnqueueManager(QtCore.QObject):
	
	ENQUEUE = 0
	ENQUEUE_AND_PLAY = 1
	BACKGROUND = 2
	
	enqueued = QtCore.pyqtSignal()
	
	def __init__(self, parent=None):
		QtCore.QObject.__init__(self, parent)
		self.shareLoginManager = ShareLoginManager(parent)
		self.shareLoginManager.success.connect(self.onChecked)
		self.isWorking = False
		self.queue = Queue.Queue()
		self.enqueued.connect(self.checkQueue)
		self.action = self.ENQUEUE
		self.path = None
	
	def checkQueue(self):
		if not self.queue.empty() and not self.isWorking:
			path, action = self.queue.get(False)
			self.process(path, action)
		
	def enqueue(self, f):	
		self.queue.put_nowait((f, self.ENQUEUE))
		self.enqueued.emit()
		
	def enqueueAndPlay(self, f):	
		self.queue.put_nowait((f, self.ENQUEUE_AND_PLAY))
		self.enqueued.emit()
		
	def playBackground(self, f):	
		self.queue.put_nowait((f, self.BACKGROUND))
		self.enqueued.emit()
		
	def process(self, path, action):
		self.action = action
		self.path = path
		if not DataHolder.uri:
			return
		self.isWorking = True
		url = QtCore.QUrl(DataHolder.uri + ServerPath.CHECK)
		url.addQueryItem(ServerPath.PATH, self.path)
		request = QtNetwork.QNetworkRequest(url)
		reply = QtGui.QApplication.instance().NAM.get(request)
		reply.finished.connect(self.onReply)

	
	def onReply(self):
		reply = QtCore.QObject.sender(self)
		reply.deleteLater()
		if reply.error() == QtNetwork.QNetworkReply.NoError:
			doc = QtXml.QDomDocument()
			doc.setContent(reply.readAll())
			root = doc.documentElement()
			if "response" != root.tagName():
				print "wrong tag!!!"
			valid = str(root.attribute("valid")) == "true"
			cause = str(root.attribute("reason"))
			if valid:	
				self.onChecked()
			elif cause.startswith("loginNeeded:"):
				share = cause[len("loginNeeded:") + 1:].strip()				
				self.shareLoginManager.showDialog(share)
			else:
				self.isWorking = False
				self.enqueued.emit()			
		else:
			self.isWorking = False
			self.enqueued.emit()

	def onChecked(self):
		path = ServerPath.ENQUEUE if self.action == self.ENQUEUE else (ServerPath.ENQUEUE_AND_PLAY if self.action == self.ENQUEUE_AND_PLAY else ServerPath.PLAY_BACKGROUND)
		url = QtCore.QUrl(DataHolder.uri + path)
		url.addQueryItem(ServerPath.PATH, self.path)
		
		request = QtNetwork.QNetworkRequest(url)
		reply = QtGui.QApplication.instance().NAM.get(request)
		self.isWorking = False
		self.enqueued.emit()
		
