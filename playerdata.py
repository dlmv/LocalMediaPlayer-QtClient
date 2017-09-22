from PyQt4 import QtGui, QtCore, QtNetwork, QtXml
from playerutil import *

class DataHolder:
	uri = None

class Keys:
	organization = "dlmv"
	app = "localplayer-qtclient"

class Database():
	def __init__(self):
		pass

	@staticmethod
	def getServers():
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		return [l.toList() for l in settings.value("servers", []).toList()]

	@staticmethod
	def serverSaved(server, port):
		servers = Database.getServers()
		for name1, server1, port1 in servers:
			server1 = server1.toString()
			port1, ok = port1.toInt()
			if server1 == server and port1 == port:
				return True
		return False

	@staticmethod
	def saveServer(name, server, port):
		if Database.serverSaved(server, port):
			return
		servers = Database.getServers()
		servers.append([name, server, port])
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		settings.setValue("servers", servers)

	@staticmethod
	def deleteServer(server, port):
		servers = Database.getServers()
		newservers = []
		for name1, server1, port1 in servers:
			server1 = server1.toString()
			port1, ok = port1.toInt()
			if server1 == server and port1 == port:
				continue
			newservers.append([name1, server1, port1])
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		settings.setValue("servers", newservers)

	@staticmethod
	def getRewritings():
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		return [l.toList() for l in settings.value("rewritings", []).toList()]

	@staticmethod
	def rewritingSaved(local):
		rewritings = Database.getRewritings()
		for remote1, local1 in rewritings:
			local1 = local1.toString()
			if local1 == local:
				return True
		return False

	@staticmethod
	def saveRewriting(remote, local):
		if Database.rewritingSaved(local):
			return
		rewritings = Database.getRewritings()
		rewritings.append([remote, local])
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		settings.setValue("rewritings", rewritings)

	@staticmethod
	def deleteRewriting(local):
		rewritings = Database.getRewritings()
		newrewritings = []
		for remote1, local1 in rewritings:
			local1 = local1.toString()
			if local1 == local:
				continue
			newrewritings.append([remote1, local1])
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		settings.setValue("rewritings", newrewritings)

	ENQUEUE = "enqueue"
	ENQUEUE_AND_PLAY = "enqueueAndPlay"

	@staticmethod
	def launchOpenAction():
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		return str(settings.value("launchOpenAction", Database.ENQUEUE_AND_PLAY).toString())
	
	@staticmethod
	def setLaunchOpenAction(action):
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		settings.setValue("launchOpenAction", action)

	@staticmethod
	def dropOpenAction():
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		return str(settings.value("dropOpenAction", Database.ENQUEUE).toString())
	
	@staticmethod
	def setDropOpenAction(action):
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		settings.setValue("dropOpenAction", action)
		

	@staticmethod
	def dialogOpenAction():
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		return str(settings.value("dialogOpenAction", Database.ENQUEUE).toString())
	
	@staticmethod
	def setDialogOpenAction(action):
		settings = QtCore.QSettings(Keys.organization, Keys.app)
		settings.setValue("dialogOpenAction", action)		
		

class TableDialog(QtGui.QDialog):

	opened = QtCore.pyqtSignal(int)

	def __init__(self, parent=None):
		QtGui.QDialog.__init__(self, parent)
		l = QtGui.QVBoxLayout(self)
		self.ls = QtGui.QTableView()
		self.ls.horizontalHeader().hide()
		self.ls.verticalHeader().hide()
		self.ls.setSelectionBehavior(QtGui.QAbstractItemView.SelectRows)
		self.ls.setSelectionMode(QtGui.QAbstractItemView.SingleSelection)
#		self.ls.setShowGrid(False)
		self.model = self.createModel(self.ls)
		self.ls.setModel(self.model)
		l.addWidget(self.ls)
		self.ls.horizontalHeader().setResizeMode(0, QtGui.QHeaderView.ResizeToContents)
		self.ls.horizontalHeader().setResizeMode(1, QtGui.QHeaderView.ResizeToContents)
		self.ls.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
		self.ls.customContextMenuRequested.connect(self.popup)
		if self.openable():
			self.ls.doubleClicked.connect(self.doubleClickSlot)
			self.openButton = QtGui.QPushButton()
			self.openButton.setText("Open")
			l.addWidget(self.openButton)
			self.openButton.clicked.connect(self.openSlot)
			self.ls.selectionModel().selectionChanged.connect(self.updateButton)
			self.updateButton()
	
	def openable(self):
		return True

#	def keyPressEvent(self, event):
#		if event.key() == QtCore.Qt.Key_Enter:
#			print 'enter'
#			event.accept()
#		else:
#			QtGui.QDialog.keyPressEvent(self, event)


	def updateButton(self):
		self.openButton.setEnabled(len(self.ls.selectionModel().selection().indexes()) == 2)

	def popup(self, pos):
		if self.ls.selectionModel().selection().indexes():
			row = self.ls.selectionModel().selection().indexes()[0].row()
			self.menu = QtGui.QMenu(self)
			if self.openable():
				openAction = QtGui.QAction('Open', self)
				openAction.triggered.connect(self.openSlot)
				self.menu.addAction(openAction)
			deleteAction = QtGui.QAction('Delete', self)
			deleteAction.triggered.connect(self.deleteSlot)
			self.menu.addAction(deleteAction)
			self.menu.popup(QtGui.QCursor.pos())

	def createModel(ls):
		return None

	def deleteSlot(self, row):
		if self.ls.selectionModel().selection().indexes():
			row = self.ls.selectionModel().selection().indexes()[0].row()
			self.model.removeRows(row, 1)

	def openSlot(self, row):
		if self.ls.selectionModel().selection().indexes():
			row = self.ls.selectionModel().selection().indexes()[0].row()
			self.opened.emit(row)

	def doubleClickSlot(self, mi):
		row = mi.row()
		self.opened.emit(row)



class ServersModel(QtCore.QAbstractTableModel):

	def rowCount(self, parent=QtCore.QModelIndex()):
		return len(Database.getServers())

	def columnCount(self, parent=QtCore.QModelIndex()):
		return 2

	def data(self, index, role=QtCore.Qt.DisplayRole):
		if not index.isValid(): return None
		if role == QtCore.Qt.DisplayRole:
			name, server, port = Database.getServers()[index.row()]
			name = name.toString()
			server =server.toString()
			port, ok = port.toInt()
			if index.column() == 0:
				return name
			else:
				return "%s:%d" % (server, port)
			return None
		return None

	def removeRows(self, row, count):
		if count != 1:
			return
		self.beginRemoveRows(QtCore.QModelIndex(), row, row)
		name, server, port = Database.getServers()[row]
		Database.deleteServer(server, port)
		self.endRemoveRows()


class ServersDialog(TableDialog):
	def __init__(self, parent=None):
		TableDialog.__init__(self, parent)

	def createModel(self, ls):
		return ServersModel(ls)


class LoginsModel(QtCore.QAbstractTableModel):
	
	def __init__(self, shares, logins, parent=None):
		QtCore.QAbstractTableModel.__init__(self, parent)
		self.shares = shares
		self.logins = logins

	def rowCount(self, parent=QtCore.QModelIndex()):
		return len(self.shares)

	def columnCount(self, parent=QtCore.QModelIndex()):
		return 2

	def data(self, index, role=QtCore.Qt.DisplayRole):
		if not index.isValid(): return None
		if role == QtCore.Qt.DisplayRole:
			if index.column() == 0:
				return self.logins[index.row()]
			else:
				return self.shares[index.row()]
			return None
		return None

	def removeRows(self, row, count):
		if count != 1:
			return
		if not DataHolder.uri:
			return		
		self.beginRemoveRows(QtCore.QModelIndex(), row, row)	
		uri = QtCore.QUrl(DataHolder.uri + ServerPath.FORGET_LOGIN)
		uri.addQueryItem(ServerPath.PATH, self.shares[row])
		request = QtNetwork.QNetworkRequest(uri)
		reply = QtGui.QApplication.instance().NAM.get(request)
		del self.shares[row]
		del self.logins[row]
		self.endRemoveRows()		




class LoginsDialog(TableDialog):
	def __init__(self, shares, logins, parent=None):
		self.shares = shares
		self.logins = logins		
		TableDialog.__init__(self, parent)
		
	def openable(self):
		return False		

	def createModel(self, ls):
		return LoginsModel(self.shares, self.logins, ls)
	
	
	@staticmethod
	def parse(s):
		doc = QtXml.QDomDocument()
		doc.setContent(s)
		root = doc.documentElement()
		
		shares = []
		logins = []

		if "response" != root.tagName():
			print "wrong tag!!!"
		valid = str(root.attribute("valid")) == "true"
		
		if valid:
			ls = root.elementsByTagName("loginlist")
			if len(ls) == 1:
				e = ls.item(0).toElement()
				list1 = e.elementsByTagName("share")
				for i in range(list1.length()):
					e1 = list1.item(i).toElement()
					share = QtCore.QUrl.fromPercentEncoding(str(e1.attribute("name")).replace('+', ' '))
					login = QtCore.QUrl.fromPercentEncoding(str(e1.attribute("login")).replace('+', ' '))
					shares.append(share)
					logins.append(login)
		return shares, logins	



class RewritingsModel(QtCore.QAbstractTableModel):

	def rowCount(self, parent=QtCore.QModelIndex()):
		return len(Database.getRewritings())

	def columnCount(self, parent=QtCore.QModelIndex()):
		return 2

	def data(self, index, role=QtCore.Qt.DisplayRole):
		if not index.isValid(): return None
		if role == QtCore.Qt.DisplayRole:
			remote, local = Database.getRewritings()[index.row()]
			remote = remote.toString()
			local = local.toString()
			if index.column() == 0:
				return remote
			else:
				return local
			return None
		return None

	def removeRows(self, row, count):
		if count != 1:
			return
		self.beginRemoveRows(QtCore.QModelIndex(), row, row)
		remote, local = Database.getRewritings()[row]
		Database.deleteRewriting(local)
		self.endRemoveRows()


class RewritingsDialog(TableDialog):
	def __init__(self, parent=None):
		TableDialog.__init__(self, parent)

	def createModel(self, ls):
		return RewritingsModel(ls)
	
	def openable(self):
		return False		
	













