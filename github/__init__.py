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
    import inspect
    frm = inspect.stack()[1]
    mod = inspect.getmodule(frm[0])
    folder = os.path.dirname(mod.__file__)    
    icon = QtGui.QIcon(os.path.join(os.path.dirname(__file__), "plugin.png"))
    action = QtGui.QAction(icon, "Update plugin...", iface.mainWindow())
    action.triggered.connect(lambda: updatePlugin(username,reponame, folder))
    actions[menu] = action
    iface.addPluginToMenu(menu, action)

def removeUpdatePluginMenu(menu):
    try:
        iface.removePluginMenu(menu, actions[menu])
    except:
        pass

def updatePlugin(username, reponame, folder):
	dlg = PluginUpdaterDialog(username, reponame, folder)
	dlg.exec_()