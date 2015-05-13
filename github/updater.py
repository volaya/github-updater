from PyQt4 import QtCore, QtGui
import os
from qgis.gui import *
import re
import shutil
import urllib
from qgis.utils import loadPlugin, updateAvailablePlugins, iface
import ConfigParser
import StringIO
import zipfile
import tempfile
import uuid
import time

class GitHubPlugin():

    def __init__(self, user, reponame, folder):
        self.user = user
        self.reponame = reponame
        self.folder = folder

    def _get(self, url):
        response = urllib.urlopen(url)
        return response.read()

    def isInstalled(self):
        return os.path.exists(self.folder)

    def isVersioned(self):
        return os.path.exists(self.commitIdFile())

    def commitIdFile(self):
        return os.path.join(self.folder, "lastgithubversion")


    def install(self, ref, progress = None):
        filename = tempFilename("zip")
        tmpFolder = tempSubFolder()
        url = "https://github.com/%s/%s/archive/%s.zip" % (self.user, self.reponame, ref)
        urllib.urlretrieve(url, filename, reporthook=progress)        
        with open(filename, 'rb') as f:
            z = zipfile.ZipFile(f)
            z.extractall(tmpFolder)
        packageName = os.path.basename(self.folder)
        path = os.path.join(tmpFolder, "%s-%s" % (self.reponame, ref), packageName)
        print path
        print filename
        print self.folder
        if os.path.exists(self.folder):
            shutil.rmtree(self.folder, True)
        #mkdir(self.folder)
        shutil.copytree(path, self.folder)
        with open(self.commitIdFile(), "w") as f:
            f.write("\n".join([ref, self.dateFromRef(ref)]))
        updateAvailablePlugins()
        
        loadPlugin(packageName)

    def dateFromRef(self, ref):
        html = self._get('https://github.com/%s/%s/commits/%s' % (self.user, self.reponame, ref))
        versiondate = re.search(r'time datetime=\"(.*?)\"', html).group(1)
        return versiondate

    def tags(self):
        html = self._get('https://github.com/%s/%s/tags' % (self.user, self.reponame))
        names = re.findall(r'"tag-name">(.*?)</span>', html)
        refs = re.findall(r'/%s/%s/commit/(.*?)"'  % (self.user, self.reponame), html)
        tags = []
        for name, ref in zip(names, refs):
            tags.append((name, ref))
        return tags

    def localVersionInfo(self):
        try:
            with open(self.commitIdFile()) as f:
                lines = f.readlines()
            return (lines[0].replace("\n", "").replace("\r", ""), 
                    lines[1].strip("\n").replace("\n", "").replace("\r", ""))
        except:
            return None
        

    def upstreamVersionInfo(self):
        html = self._get('https://github.com/%s/%s/commits/master' % (self.user, self.reponame))
        versiondate = re.search(r'time datetime=\"(.*?)\"', html).group(1)
        commitid = re.search(r'data-clipboard-text=\"(.*?)\"', html).group(1)
        return commitid, versiondate

    def isOutdated(self):
        if self.isInstalled():
            if self.isVersioned():
                commitId, versionDate = self.localVersionInfo()
                commitIdUpstream, versionDateUpstream = self.upstreamVersionInfo()
                return commitId != commitIdUpstream #and versionDate < versionDateUpstream
            else:
                return True
        else:
            return True

class PluginUpdaterDialog(QtGui.QDialog):

    def __init__(self, username, reponame, folder):
        QtGui.QDialog.__init__(self, iface.mainWindow(), QtCore.Qt.WindowSystemMenuHint | QtCore.Qt.WindowTitleHint)
        self.plugin = GitHubPlugin(username, reponame, folder)
        self.setupUi()
        self.fillPluginDescription()


    def setupUi(self):
        self.resize(500, 350)
        self.setWindowTitle("Update plugin")
        self.layout = QtGui.QVBoxLayout()
        self.layout.setSpacing(2)
        self.layout.setMargin(0)
        self.pluginDescription = QtGui.QTextBrowser()
        self.layout.addWidget(self.pluginDescription)
        self.progressbar = QtGui.QProgressBar()
        self.progressbar.setMinimum(0)
        self.progressbar.setMaximum(100)
        self.layout.addWidget(self.progressbar)
        self.setLayout(self.layout)
        self.pluginDescription.connect(self.pluginDescription, QtCore.SIGNAL("anchorClicked(const QUrl&)"), self.linkClicked)
        self.pluginDescription.setOpenLinks(False)



    def linkClicked(self, url):
        url = url.toString()
        if url.startswith("install:"):
            sha = url.split(":")[1]
            QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
            try:
                self.lastPercent = 0
                self.plugin.install(sha, self.progress)   
                QtGui.QApplication.restoreOverrideCursor()
                QtGui.QMessageBox.information(self, "Plugin updated",
                          "The plugin was succesfully updated",
                          QtGui.QMessageBox.Ok)             
            except Exception, e:
                import traceback
                traceback.print_exc()
                QtGui.QApplication.restoreOverrideCursor()
                QtGui.QMessageBox.critical(self, "Error updating plugin",
                          "The plugin could not be updated",
                          QtGui.QMessageBox.Ok)
            finally:
                self.close()
        else:
            pass

    def progress(self, count, blockSize, totalSize):
        percent = int(count*blockSize*100/totalSize)
        if percent != self.lastPercent:
            self.progressbar.setValue(percent)
            QtCore.QCoreApplication.processEvents()
            self.lastPercent = percent

    def fillPluginDescription(self):
        QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
        try:
            plugin = self.plugin
            tags = plugin.tags()
            body = "<h2>Plugin status</h2>"
            if plugin.isInstalled():
                if plugin.isVersioned():
                    commitid, date = plugin.localVersionInfo()
                    installedVersion = "%s [%s]" % (commitid[:10], date)
                    tagsDict = {ref: name for name, ref in tags}
                    if commitid in tagsDict:
                        installedVersion += "[Release version %s]" % tagsDict[commitid]
                else:
                    installedVersion = "Plugin is installed but version is not available"
            else:
                installedVersion = "Plugin is not installed"
            body += "<p><b>Installed version:</b> %s</p>" % installedVersion
            commitid, date = plugin.upstreamVersionInfo()
            tagIcon = "<img src='" + os.path.dirname(__file__) + "/tag.gif'>"
            body += "<p><b>Latest development version:</b> %s [%s] &nbsp;" % (commitid[:10], date)
            if plugin.isOutdated():
                body += "<a href='install:%s'> Install </a></p>" % commitid
            body += "<p><b>Release versions:</b><p>"
            if tags:
                body +=  "<dl>%s</dl>" % "".join(["<dd>" + tagIcon + " %s &nbsp; <a href='install:%s'> Install </a></dd>" % (name, ref)
                                                for name, ref in tags]) + "</dl>"
            else:
                body += "<dl><dd> No stable versions available</dd></dl>"            
        except:
            body ="<h2>Could not determining plugin status</h2>" 
            import traceback
            traceback.print_exc()           
        finally:
            html = '''<!DOCTYPE html PUBLIC "-//W3C//DTD HTML 4.01//EN" "http://www.w3.org/TR/html4/strict.dtd">
                <html>
                <head>
                <style type="text/css">
                    .summary { margin-left: 10px; margin-right: 10px; }
                    h2 { color: #555555; padding-bottom: 15px; }
                    a { text-decoration: none; color: #3498db; font-weight: bold; }
                    p { color: #666666; }
                    b { color: #333333; }
                    dl dd { margin-bottom: 5px; }
                </style>
                </head>
                <body>
                %s <br>
                </body>
                </html>
                ''' % body
            self.pluginDescription.setHtml(html)
            QtGui.QApplication.restoreOverrideCursor()

def pluginsFolder():
    folder = os.path.join(os.path.expanduser('~'), '.qgis2', 'python', 'plugins')
    mkdir(folder)
    return folder

_tempFolder = None
def tempFolder():
    global _tempFolder
    if _tempFolder is None:
        _tempFolder = tempfile.mkdtemp()
    return _tempFolder

def tempSubFolder():
    path = tempFolder()
    folder = os.path.join(path, str(uuid.uuid4()).replace("-", ""))
    mkdir(folder)
    return folder

def tempFilename(ext):
    path = tempFolder()
    ext = "" if ext is None else ext
    filename = path + os.sep + str(time.time()) + "." + ext
    return filename


def mkdir(newdir):
    if os.path.isdir(newdir):
        pass
    else:
        head, tail = os.path.split(newdir)
        if head and not os.path.isdir(head):
            mkdir(head)
        if tail:
            os.mkdir(newdir)
