# -*- coding: utf-8 -*-

from qgis.utils import iface
from PyQt4 import QtCore, QtGui
import os
from updater import PluginUpdaterDialog

actions = {}

def classFactory(iface):
    from github.plugin import GitHubPluginUpdaterPlugin
    return GitHubPluginUpdaterPlugin(iface)


def addUpdatePluginMenu(menu, username, reponame):
    global actions
    icon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), "plugin.png"))
    action = QtGui.QAction(icon, "Update plugin...", iface.mainWindow())
    action.triggered.connect(lambda: updatePlugin(username,reponame))
    actions[menu] = action
    iface.addPluginToMenu(menu, action)

def removeUpdatePluginMenu(menu):
	self.iface.removePluginMenu(menu, actions[menu])

def updatePlugin(username, reponame):
	dlg = PluginUpdaterDialog(username, reponame)
	dlg.exec_()