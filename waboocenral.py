#!/usr/bin/python
# -*- coding: utf-8 -*-


about = """\
Waboocenral is a batch image downloader, using imageboards and other\
 image hosts as the main source for its images.

    Copyright (C) 2011 Shou

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.\
"""


# TODO: Make adapts load from files with something like ast.literal_eval().
# TODO: Add search history.
# TODO: Add more options. FREEDOM!
# TODO: Stop using the strings passed with verbose() and error() so you can
# parse them with regular expressions and add it to the GUI. That shit is dumb.
# TODO: Smoother total statusbar movement. Fix the above shit first.


import os
import sys
import re
import urllib
import urllib2
import bz2
from BeautifulSoup import BeautifulSoup
from subprocess import Popen
from getpass import getpass
from ast import literal_eval as leval
from PyQt4.QtGui import *
from PyQt4.QtCore import *


__version__ = 0.7
__description__ = """\
Waboocenral is a batch image downloader, using imageboards and other\
 image hosts as the main source for its images.\
"""


debug = False
run = False
application = None
app = None
DThread = None
path = os.path.join(os.path.expanduser("~"), "python-downloads")
types = ["danbooru", "pixiv", "gelbooru", "safebooru", "konachan",
         "oreno.imouto", "sankakucomplex"]

help = """Tags: Type up to however many tags the image host supports; \
for example basic Danbooru searches only allow two tags.
Example: touhou red

Board: Currently these image hosting sites are supported: %s. \
Type the name of which one you're downloading images from.
Example: pixiv

Pages: How many pages to download, optional customized starting point.
Example 1: 999
Will download images up until and including page 999. \
Works even if there are less than 999 pages, so large numbers can be used \
if the user wishes to download all pages.

Example 2: 7:17
Will download page 7 up until and including page 17.""" % ', '.join(types)

usage = """usage: %s [option] ... [arg] ...
Options and arguments:
-n		No GUI.
-h		Display the help page.
-u user		Login username.
-p pwd		Login password.
-b board		Imageboard to download from.
-t tags		Tagged images to download.
-P pages		How many pages to download.""" % sys.argv[0]


opener = urllib2.build_opener(urllib2.HTTPCookieProcessor())
opener.addheaders = [('User-agent', 'Mozilla/7.0')]


# Function ouputting general information
def verbose(m):
    try:
        DThread.emit(SIGNAL("output(QString)"), m)
    except:
        print m

# Function outputting errors
def error(m):
    try:
        DThread.emit(SIGNAL("output(QString)"), 'Error: ' + m)
    except:
        print 'Error: ' + m


# Parse HTML entities to regular characters
def parseEntity(s):
    if isinstance(s, unicode):
        s = s.encode('utf-8')
    replace = [["&nbsp;", " "],
              ["&lt;", "<"],
              ["&gt;", ">"],
              ["&#39;", "'"],
              ["&quot;", "\""],
              ["&#44;", ","],
              ["&deg;", "°"],
              ["&#33;", "!"],
              ["&#8217;", "\'"],
              ["&#8216;", "‘"],
              ["&#8230;", "…"],
              ["&amp;", "&"]]
    for e in replace:
        s = s.replace(e[0], e[1])
    s = re.sub('\&\S*?;', '', s, re.I)
    return s

# Sanitize filename per operating system
def sanitizeFilename(s):
    if sys.platform in ['linux2', 'darwin']:
        s = s.replace('/', '')
        return s
    elif sys.platform in ['win32', 'cygwin']:
        invalid_chars = ['/', '\\', '<', '>', ':', '"', '|', '?', '*']
        for c in invalid_chars:
            s = s.replace(c, '')
        return s


# Qt thread to run functions
class Thread(QThread):
    def __init__(self, parent = None):
        QThread.__init__(self)
        self.exiting = False
    
    def ex(self, func, *args, **kwargs):
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
        self.start()
    
    def run(self):
        self.func(*self.args, **self.kwargs)
        return


def MyParser(url, fileNameLength=200):
    """
    Parses a page and returns the image thumbnails and additional information
    if found.
    """
    main_url = '/'.join(url.split('/')[:3])
    req = urllib2.urlopen(url)
    soup = BeautifulSoup(req.read())
    imgs = soup.findAll("img")
    images = list()
    
    for img in imgs:
        attrD = dict(img.attrs)
        if 'class' in attrD.keys():
            if re.search('\s*preview\s*', attrD['class'], re.I):
                link = attrD['src']
                fileid = link.split('/')[-1].split('.')[0].replace('thumbnail_', '')
                info = parseEntity(attrD['title'])
                
                if re.search('^/', link):
                    link = main_url + link
                
                while len(info) > fileNameLength:
                    temp = info.split(' ')
                    tem = -1
                    while True:
                        if not re.search('^(rating|score|user):', temp[tem], re.I):
                            del temp[tem]
                            info = ' '.join(temp)
                            break
                        else:
                            tem -= 1
                
                rating = re.search('Rating\:\s?(\w+)', info, re.I)
                if rating:
                    rating = "Rating:" + rating.groups(1)[0]
                else:
                    rating = ''
                user = re.search('User\:\s?(\S+)', info, re.I)
                if user:
                    user = "User:" + user.groups(1)[0]
                else:
                    user = ''
                score = re.search('Score\:\s?(\S+)', info, re.I)
                if score:
                    score = "Score:" + score.groups(1)[0]
                else:
                    score = ''
                
                info = re.sub('\s?Rating\:\s?(\w+)?\s?', '', info, re.I)
                info = re.sub('\s?User\:\s?(\S+)?\s?', '', info, re.I)
                info = re.sub('\s?Score\:\s?(\S+)?\s?', '', info, re.I)
                info = re.sub('\s?Tags\:\s?(\S+)?\s?', '', info, re.I)
                
                image = dict()
                image['url'] = link
                image['rating'] = rating
                image['user'] = user
                image['score'] = score
                image['tags'] = info
                image['id'] = fileid
                images.append(image)
            
            elif attrD['class'] == 'ui-scroll-view':
                link = attrD['data-src']
                fileid = link.split('/')[-1].split('.')[0].replace('_s', '')
                info = parseEntity(img.findParent("p").findNext("h1").text)
                if len(info) > fileNameLength:
                    info = info[:fileNameLength] + '…'
                
                image = dict()
                image['url'] = link
                image['rating'] = ''
                image['user'] = ''
                image['score'] = ''
                image['tags'] = info
                image['id'] = fileid
                images.append(image)
    
    return images


# Locally stored configuration settings
class Settings:
    def __init__(self):
        self.path = os.path.join(os.path.expanduser("~"), ".waboocenral")
        self.file = os.path.join(self.path, 'settings.conf')
        
        try:
            f = open(self.file)
            r = f.read()
        except:
            try:
                os.mkdir(self.path)
            except OSError, e:
                if errno != 17:
                    error('Unable to make configuration directory.')
            
            f = open(self.file, 'wb')
            f.close()
            f = open(self.file)
            r = f.read()
        
        try:
            self.r = leval(r)
        except:
            self.r = {}
        f.close()
    
    def get(self, key=None, **fallback):
        try:
            if key == None:
                return self.r
            else:
                return self.r[key]
        except:
            try:
                return fallback['fallback']
            except:
                return False
    
    def add(self, key, value):
        self.r[key] = value
        self.save()
    
    def rem(self, key):
        try:
            del self.r[key]
            self.save()
        except:
            pass
    
    def save(self):
        f = open(self.file, 'wb')
        f.write(str(self.r))
        f.close()
Settings = Settings()


# GUI
class Application(QMainWindow):
    
    queueList = []
    searchList = []
    historyList = []
    
    # Set window title, icon, menubar
    def __init__(self):
        super(Application, self).__init__()
        
        self.setWindowTitle('Waboocenral')
        self.setWindowIcon(QIcon('favicon.png'))
        self.setStyleSheet(" QPushButton { max-width: 100px; } ")
        
        # menubar
        self.menubar = self.menuBar()
        self.fileMenu = self.menubar.addMenu('&File')
        self.editMenu = self.menubar.addMenu('&Edit')
        self.viewMenu = self.menubar.addMenu('&View')
        self.helpMenu = self.menubar.addMenu('&Help')
        
        # menubar entries
        self.pathOpen = QAction('&Browse folder', self)
        self.quitApp = QAction('&Quit', self)
        self.preferencesEdit = QAction('&Preferences', self)
        self.mainView = QAction('&Main', self)
        self.previewView = QAction('P&review', self)
        self.queueView = QAction('&Queue', self)
        self.showHelp = QAction('&Help', self)
        self.showAbout = QAction('&About', self)
        
        # menubar actions
        self.fileMenu.addAction(self.pathOpen)
        self.fileMenu.addAction(self.quitApp)
        self.editMenu.addAction(self.preferencesEdit)
        self.viewMenu.addAction(self.mainView)
        self.viewMenu.addAction(self.previewView)
        self.viewMenu.addAction(self.queueView)
        self.helpMenu.addAction(self.showHelp)
        self.helpMenu.addAction(self.showAbout)
        
        # menubar shortcut keys
        self.pathOpen.setShortcut('Ctrl+B')
        self.quitApp.setShortcut('Alt+F4')
        self.preferencesEdit.setShortcut('Ctrl+P')
        self.mainView.setShortcut('Ctrl+M')
        self.previewView.setShortcut('Ctrl+R')
        self.queueView.setShortcut('Ctrl+Q')
        self.showHelp.setShortcut('F1')
        
        # menubar status tips
        self.pathOpen.setStatusTip('Open image directory')
        self.quitApp.setStatusTip('Close the program')
        self.preferencesEdit.setStatusTip('Configure the preferences')
        self.mainView.setStatusTip('Switch to main')
        self.previewView.setStatusTip('Switch to preview')
        self.queueView.setStatusTip('Switch to queue')
        self.showHelp.setStatusTip('Show help')
        self.showAbout.setStatusTip('Show about')
        
        # menubar events
        self.pathOpen.triggered.connect(openFileManager)
        self.quitApp.triggered.connect(qApp.quit)
        self.preferencesEdit.triggered.connect(self.displaySettings)
        self.mainView.triggered.connect(self.displayMain)
        self.previewView.triggered.connect(self.displayPreview)
        self.queueView.triggered.connect(self.displayQueue)
        self.showHelp.triggered.connect(self.displayHelp)
        self.showAbout.triggered.connect(self.displayAbout)
        
        # add the rest of the GUI
        self.initUI()
    
    # Set main GUI
    def initUI(self):
        self.mainStack = QStackedWidget(self)
        self.setCentralWidget(self.mainStack)
        
        # MAIN; gets focus when the program is started
        self.statusBar().showMessage('Ready')
        
        self.mainWidget = QWidget()
        
        self.options_title = QLabel('<b style="font-size:17px;">Options</b>')
        self.tags_input = QLineEdit()
        self.tags_input.setPlaceholderText("Search tags")
        self.board_option = QComboBox()
        self.pages_input = QLineEdit()
        self.pages_input.setPlaceholderText("Pages")
        self.spacer = QLabel()
        self.login_title = QLabel('<b style="font-size:17px;">Login (optional)</b>')
        self.user_input = QLineEdit()
        self.user_input.setPlaceholderText("Username")
        self.pass_text = QLabel('Password:')
        self.pass_input = QLineEdit()
        self.pass_input.setPlaceholderText("Password")
        self.submit_button = QPushButton('&Submit')
        self.queue_button = QPushButton('Add to &queue')
        self.cancel_button = QPushButton('&Cancel')
        self.download_title = QLabel('<b style="font-size:17px;">Information</b>')
        self.file_name = QLabel()
        self.file_progress = QProgressBar()
        self.file_errors = QTextEdit()
        self.total_progress = QProgressBar()
        
        self.mainGrid = QGridLayout(self.mainWidget)
        self.mainGrid.setSpacing(10)
        self.pass_input.setEchoMode(2)
        self.cancel_button.setEnabled(False)
        self.file_name.setMinimumWidth(300)
        self.file_name.setMaximumWidth(300)
        self.file_errors.setMaximumWidth(300)
        self.file_progress.setValue(0)
        self.total_progress.setValue(0)
        self.file_errors.setReadOnly(True)
        self.boardOptions()
        
        global DThread
        DThread = Thread()
        
        self.connect(DThread, SIGNAL("finished()"), self.finished)
        self.connect(DThread, SIGNAL("terminated()"), self.finished)
        self.connect(DThread, SIGNAL("output(QString)"), self.appendInfo)
        self.connect(self.submit_button,
                     SIGNAL('clicked()'), self.submit)
        self.connect(self.queue_button,
                     SIGNAL('clicked()'), self.queue)
        self.connect(self.cancel_button,
                     SIGNAL('clicked()'), self.cancel)
        self.connect(self.board_option,
                     SIGNAL('currentIndexChanged(QString)'), self.boardOptions)
        for i in range(len(types)):
            self.board_option.addItem(types[i])
        
        self.mainGrid.addWidget(self.options_title, 0, 0, 1, 0)
        self.mainGrid.addWidget(self.tags_input, 1, 0, 1, 2)
        self.mainGrid.addWidget(self.board_option, 2, 0, 1, 2)
        self.mainGrid.addWidget(self.pages_input, 3, 0, 1, 2)
        self.mainGrid.addWidget(self.spacer, 4, 0)
        self.mainGrid.addWidget(self.login_title, 5, 0, 1, 0)
        self.mainGrid.addWidget(self.user_input, 6, 0, 1, 2)
        self.mainGrid.addWidget(self.pass_input, 7, 0, 1, 2)
        self.mainGrid.addWidget(self.submit_button, 8, 0)
        self.mainGrid.addWidget(self.queue_button, 8, 1)
        self.mainGrid.addWidget(self.cancel_button, 8, 2)
        self.mainGrid.addWidget(self.download_title, 0, 2)
        self.mainGrid.addWidget(self.file_name, 1, 2)
        self.mainGrid.addWidget(self.file_progress, 2, 2)
        self.mainGrid.addWidget(self.total_progress, 3, 2)
        self.mainGrid.addWidget(self.file_errors, 4, 2, 4, 1)
        
        self.mainStack.addWidget(self.mainWidget)
        
        # SETTINGS
        self.settingsWidget = QWidget()
        
        self.settingsLayout = QGridLayout(self.settingsWidget)
        
        self.settingsTabs = QTabWidget()
        
        S = Settings.get('general', fallback={})
        try:
            spreview = S['preview']
        except:
            spreview = False
        try:
            snotify = S['notify']
        except:
            snotify = False
        try:
            sformat = S['format']
        except:
            sformat = '%id% %tags%%page%'
        try:
            stagslength = str(S['tagslength'])
        except:
            stagslength = "200"
        
        self.settings = {}
        self.settings['general'] = {}
        self.settings['general']['widget'] = QWidget()
        self.settings['general']['title'] = QLabel('<b style="font-size:17px;">General</b>')
        self.settings['general']['img_preview'] = QCheckBox("Auto preview on submit")
        self.settings['general']['spacer'] = QLabel()
        self.settings['general']['notify'] = QCheckBox("Notify on finish")
        self.settings['general']['format_input'] = QLineEdit(sformat)
        self.settings['general']['format_input'].setPlaceholderText("Save string formatting")
        self.settings['general']['tagsLength_input'] = QLineEdit(stagslength)
        self.settings['general']['tagsLength_input'].setPlaceholderText("Max character length of info")
        
        self.settingsGrid = {}
        self.settingsGrid['general'] = QGridLayout(self.settings['general']['widget'])
        self.settingsGrid['general'].setSpacing(10)
        self.settings['general']['img_preview'].setChecked(spreview)
        self.settings['general']['notify'].setChecked(snotify)
        
        self.connect(self.settings['general']['img_preview'],
                     SIGNAL('stateChanged()'), self.settingsEnableApply)
        self.connect(self.settings['general']['notify'],
                     SIGNAL('stateChanged()'), self.settingsEnableApply)
        self.connect(self.settings['general']['format_input'],
                     SIGNAL('textChanged(QString)'), self.settingsEnableApply)
        
        self.settingsGrid['general'].addWidget(self.settings['general']['title'], 0, 0)
        self.settingsGrid['general'].addWidget(self.settings['general']['img_preview'], 1, 0, 1, 2)
        self.settingsGrid['general'].addWidget(self.settings['general']['notify'], 2, 0, 1, 2)
        self.settingsGrid['general'].addWidget(self.settings['general']['format_input'], 3, 0, 1, 2)
        self.settingsGrid['general'].addWidget(self.settings['general']['tagsLength_input'], 4, 0, 1, 2)
        self.settingsGrid['general'].addWidget(self.settings['general']['spacer'], 5, 0)
        
        self.settingsTabs.addTab(self.settings['general']['widget'], 'general')
        
        for b in types:
            S = Settings.get(b, fallback={})
            try:
                pword = bz2.decompress(S['pword'])
            except:
                pword = str()
            try:
                uname = S['uname']
            except:
                uname = str()
            try:
                path = S['path']
            except:
                path = str()
            
            self.settings[b] = {}
            self.settings[b]['widget'] = QWidget()
            self.settings[b]['title'] = QLabel('<b style="font-size:17px;">%s</b>' % b)
            self.settings[b]['uname_input'] = QLineEdit(uname)
            self.settings[b]['uname_input'].setPlaceholderText('Username')
            self.settings[b]['pword_input'] = QLineEdit(pword)
            self.settings[b]['pword_input'].setPlaceholderText("Password")
            self.settings[b]['path'] = QLineEdit(path)
            self.settings[b]['path'].setPlaceholderText("Image directory")
            self.settings[b]['spacer'] = QLabel()
            
            self.settingsGrid[b] = QGridLayout(self.settings[b]['widget'])
            self.settingsGrid[b].setSpacing(10)
            self.settings[b]['pword_input'].setEchoMode(2)
            
            self.connect(self.settings[b]['uname_input'],
                         SIGNAL('textChanged(QString)'), self.settingsEnableApply)
            self.connect(self.settings[b]['pword_input'],
                         SIGNAL('textChanged(QString)'), self.settingsEnableApply)
            self.connect(self.settings[b]['path'],
                         SIGNAL('textChanged(QString)'), self.settingsEnableApply)
            
            self.settingsGrid[b].addWidget(self.settings[b]['title'], 0, 0, 1, 0)
            self.settingsGrid[b].addWidget(self.settings[b]['uname_input'], 1, 0, 1, 2)
            self.settingsGrid[b].addWidget(self.settings[b]['pword_input'], 2, 0, 1, 2)
            self.settingsGrid[b].addWidget(self.settings[b]['spacer'], 3, 0)
            self.settingsGrid[b].addWidget(self.settings[b]['path'], 4, 0, 1, 2)
            self.settingsGrid[b].addWidget(self.settings[b]['spacer'], 5, 0)
            
            self.settingsTabs.addTab(self.settings[b]['widget'], b)
        
        self.settingsButtons = QWidget()
        
        self.settingsButtonOk = QPushButton('&OK')
        self.settingsButtonCancel = QPushButton('&Cancel')
        self.settingsButtonApply = QPushButton('&Apply')
        
        self.settingsButtonGrid = QGridLayout(self.settingsButtons)
        self.settingsButtonGrid.setSpacing(10)
        self.settingsButtonApply.setEnabled(False)
        
        self.connect(self.settingsButtonOk,
                     SIGNAL('clicked()'), self.saveSettings)
        self.connect(self.settingsButtonCancel,
                     SIGNAL('clicked()'), self.displayMain)
        self.connect(self.settingsButtonApply,
                     SIGNAL('clicked()'), self.applySettings)
        
        self.settingsButtonGrid.addWidget(self.settingsButtonOk, 0, 0)
        self.settingsButtonGrid.addWidget(self.settingsButtonCancel, 0, 1)
        self.settingsButtonGrid.addWidget(self.settingsButtonApply, 0, 2)
        
        self.settingsLayout.addWidget(self.settingsTabs, 0, 0)
        self.settingsLayout.addWidget(self.settingsButtons, 1, 0)
        
        self.mainStack.addWidget(self.settingsWidget)
        
        # PREVIEW
        self.previewWidget = QWidget()
        
        self.preview_scroll = QScrollArea()
        self.preview_label = QLabel()
        self.preview_image = QImage()
        self.preview_pix = QPixmap(self.preview_image).scaled(self.previewWidget.width(),
                                   self.previewWidget.height(),
                                   Qt.KeepAspectRatio)
        
        self.preview_label.setPixmap(self.preview_pix)
        self.preview_scroll.setWidget(self.preview_label)
        self.preview_scroll.setWidgetResizable(1)
        
        self.previewHBox = QHBoxLayout()
        self.previewHBox.addWidget(self.preview_scroll)
        
        self.previewVBox = QVBoxLayout()
        self.previewVBox.addLayout(self.previewHBox)
        
        self.previewWidget.setLayout(self.previewVBox)
        
        self.mainStack.addWidget(self.previewWidget)
        
        # QUEUE
        self.queueTabs = QTabWidget()
        
        self.queueWidgets = []
        
        self.queueGrid = []
        
        self.mainStack.addWidget(self.queueTabs)
        
        # HELP
        self.queueTabs = QTabWidget()
        self.helpWidget = QWidget()
        
        self.help_title = QLabel('<b style="font-size:17px;">Help</b>')
        self.help_text = QTextEdit()
        self.help_return_button = QPushButton('&Return')
        
        self.helpGrid = QGridLayout(self.helpWidget)
        self.helpGrid.setSpacing(10)
        self.help_text.setText(help)
        self.help_text.setReadOnly(True)
        
        self.connect(self.help_return_button, SIGNAL('clicked()'),
                     self.displayMain)
        
        self.helpGrid.addWidget(self.help_title, 0, 0)
        self.helpGrid.addWidget(self.help_text, 1, 0)
        self.helpGrid.addWidget(self.help_return_button, 2, 0)
        
        self.mainStack.addWidget(self.helpWidget)
        
        # ABOUT
        self.aboutWidget = QWidget()
        
        self.about_title = QLabel('<b style="font-size:17px;">About</b>')
        self.about_text = QTextEdit()
        self.about_return_button = QPushButton('&Return')
        
        self.aboutGrid = QGridLayout(self.aboutWidget)
        self.aboutGrid.setSpacing(10)
        self.about_text.setText(about)
        self.about_text.setReadOnly(True)
        
        self.connect(self.about_return_button, SIGNAL('clicked()'),
                     self.displayMain)
        
        self.aboutGrid.addWidget(self.about_title, 0, 0)
        self.aboutGrid.addWidget(self.about_text, 1, 0)
        self.aboutGrid.addWidget(self.about_return_button, 2, 0)
        
        self.mainStack.addWidget(self.aboutWidget)
    
    def displayMain(self):
        self.setWindowTitle('Waboocenral')
        self.mainStack.setCurrentIndex(0)
    
    def displaySettings(self):
        self.setWindowTitle('Waboocenral - Settings')
        self.mainStack.setCurrentIndex(1)
    
    def displayPreview(self):
        self.setWindowTitle('Waboocenral - Preview')
        self.mainStack.setCurrentIndex(2)
    
    def displayQueue(self):
        self.setWindowTitle('Waboocenral - Queue')
        self.mainStack.setCurrentIndex(3)
    
    def displayHelp(self):
        self.setWindowTitle('Waboocenral - Help')
        self.mainStack.setCurrentIndex(4)
    
    def displayAbout(self):
        self.setWindowTitle('Waboocenral - About')
        self.mainStack.setCurrentIndex(5)
    
    def displayNotification(self, t=str(), m=str(), tm=5000):
        self.trayicon = QSystemTrayIcon(self)
        if self.trayicon.supportsMessages():
            self.icon = QIcon(os.path.join(Settings.path, 'favicon.ico'))
            self.trayicon.setIcon(self.icon)
            self.trayicon.show()
            self.trayicon.showMessage(t, m, msecs=tm)
    
    def boardOptions(self):
        temp = str(self.board_option.currentText())
        temp = Settings.get(temp, fallback={})
        try:
            self.user_input.setText(temp['uname'])
        except:
            self.user_input.setText(str())
        try:
            self.pass_input.setText(bz2.decompress(temp['pword']))
        except:
            self.pass_input.setText(str())
    
    def submit(self):
        self.statusBar().showMessage('Initializing...')
        self.submit_button.setEnabled(False)
        self.queue_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.file_errors.setReadOnly(False)
        self.file_errors.clear()
        self.file_errors.setReadOnly(True)
        if Settings.get('general', fallback={'preview', False})['preview']:
            self.displayPreview()
        if len(self.queueList) < 1:
            self.queue()
        self.total_progress.setValue(0)
        DThread.ex(analyze, self.queueList)
    
    def queue(self):
        queueItem = {}
        queueItem['tags'] = unicode(self.tags_input.text())
        queueItem['board'] = unicode(self.board_option.currentText())
        queueItem['pages'] = unicode(self.pages_input.text())
        queueItem['uname'] = unicode(self.user_input.text())
        queueItem['pword'] = unicode(self.pass_input.text())
        
        i = len(self.queueList)
        
        self.queueWidgets.append({})
        self.queueWidgets[i]['widget'] = QWidget()
        self.queueWidgets[i]['options_title'] = QLabel('<b style="font-size:17px;">Item %s</b>' % i)
        self.queueWidgets[i]['tags_input'] = QLineEdit()
        self.queueWidgets[i]['tags_input'].setPlaceholderText("Search tags")
        self.queueWidgets[i]['board_option'] = QComboBox()
        self.queueWidgets[i]['pages_input'] = QLineEdit()
        self.queueWidgets[i]['pages_input'].setPlaceholderText("Pages")
        self.queueWidgets[i]['spacer'] = QLabel()
        self.queueWidgets[i]['login_title'] = QLabel('<b style="font-size:17px;">Login</b>')
        self.queueWidgets[i]['user_input'] = QLineEdit()
        self.queueWidgets[i]['user_input'].setPlaceholderText("Username")
        self.queueWidgets[i]['pass_input'] = QLineEdit()
        self.queueWidgets[i]['pass_input'].setPlaceholderText("Password")
        self.queueWidgets[i]['save_button'] = QPushButton('&Save')
        self.queueWidgets[i]['remove_button'] = QPushButton('Remove')
        self.queueWidgets[i]['return_button'] = QPushButton('&Return')
        
        self.queueGrid.append({})
        self.queueGrid[i] = QGridLayout(self.queueWidgets[i]['widget'])
        self.queueGrid[i].setSpacing(10)
        for x in range(len(types)):
            self.queueWidgets[i]['board_option'].addItem(types[x])
        for x in range(self.queueWidgets[i]['board_option'].count()):
            if self.queueWidgets[i]['board_option'].itemText(x) == queueItem['board']:
                self.queueWidgets[i]['board_option'].setCurrentIndex(x)
        self.queueWidgets[i]['tags_input'].setText(queueItem['tags'])
        self.queueWidgets[i]['pages_input'].setText(queueItem['pages'])
        self.queueWidgets[i]['user_input'].setText(queueItem['uname'])
        self.queueWidgets[i]['pass_input'].setText(queueItem['pword'])
        self.queueWidgets[i]['save_button'].setEnabled(False)
        
        self.connect(self.queueWidgets[i]['save_button'],
                     SIGNAL('clicked()'), self.saveQueueItem)
        self.connect(self.queueWidgets[i]['remove_button'],
                     SIGNAL('clicked()'), self.removeQueueItem)
        self.connect(self.queueWidgets[i]['return_button'],
                     SIGNAL('clicked()'), self.displayMain)
        def tagsChanged(s): self.queueWidgets[i]['save_button'].setEnabled(True)
        self.connect(self.queueWidgets[i]['tags_input'],
                     SIGNAL('textChanged(QString)'), tagsChanged)
        def boardChanged(s): self.queueWidgets[i]['save_button'].setEnabled(True)
        self.connect(self.queueWidgets[i]['board_option'],
                     SIGNAL('currentIndexChanged(QString)'), boardChanged)
        def pagesChanged(s): self.queueWidgets[i]['save_button'].setEnabled(True)
        self.connect(self.queueWidgets[i]['pages_input'],
                     SIGNAL('textChanged(QString)'), pagesChanged)
        def userChanged(s): self.queueWidgets[i]['save_button'].setEnabled(True)
        self.connect(self.queueWidgets[i]['user_input'],
                     SIGNAL('textChanged(QString)'), userChanged)
        def passChanged(s): self.queueWidgets[i]['save_button'].setEnabled(True)
        self.connect(self.queueWidgets[i]['pass_input'],
                     SIGNAL('textChanged(QString)'), passChanged)
        
        self.queueGrid[i].addWidget(self.queueWidgets[i]['options_title'], 0, 0, 1, 0)
        self.queueGrid[i].addWidget(self.queueWidgets[i]['tags_input'], 1, 0, 1, 2)
        self.queueGrid[i].addWidget(self.queueWidgets[i]['board_option'], 2, 0, 1, 2)
        self.queueGrid[i].addWidget(self.queueWidgets[i]['pages_input'], 3, 0, 1, 2)
        self.queueGrid[i].addWidget(self.queueWidgets[i]['spacer'], 4, 0)
        self.queueGrid[i].addWidget(self.queueWidgets[i]['login_title'], 5, 0, 1, 0)
        self.queueGrid[i].addWidget(self.queueWidgets[i]['user_input'], 6, 0, 1, 2)
        self.queueGrid[i].addWidget(self.queueWidgets[i]['pass_input'], 7, 0, 1, 2)
        self.queueGrid[i].addWidget(self.queueWidgets[i]['save_button'], 8, 0)
        self.queueGrid[i].addWidget(self.queueWidgets[i]['remove_button'], 8, 1)
        self.queueGrid[i].addWidget(self.queueWidgets[i]['return_button'], 8, 2)
        
        self.queueTabs.insertTab(i, self.queueWidgets[i]['widget'], "Item %s" % i)
        self.mainStack.insertWidget(3, self.queueTabs)
        
        self.queueList.append(queueItem)
        self.statusBar().showMessage('Added item %s to the queue.' % i)
    
    def saveQueueItem(self):
        i = self.queueTabs.currentIndex()
        
        queueItem = {}
        queueItem['tags'] = unicode(self.queueWidgets[i]['tags_input'].text())
        queueItem['board'] = unicode(self.queueWidgets[i]['board_option'].currentText())
        queueItem['pages'] = unicode(self.queueWidgets[i]['pages_input'].text())
        queueItem['uname'] = unicode(self.queueWidgets[i]['user_input'].text())
        queueItem['pword'] = unicode(self.queueWidgets[i]['pass_input'].text())
        
        self.queueList[i] = queueItem
        self.statusBar().showMessage('Saved changes to item %s.' % i)
        self.queueWidgets[i]['save_button'].setEnabled(False)
    
    def removeQueueItem(self):
        i = self.queueTabs.currentIndex()
        
        self.queueWidgets.pop(i)
        self.queueGrid.pop(i)
        self.queueTabs.removeTab(i)
        
        self.queueList.pop(i)
        self.statusBar().showMessage('Removed item %s from the queue.' % i)
    
    def cancel(self):
        DThread.terminate()
        DThread.wait()
        self.submit_button.setEnabled(True)
        self.queue_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
    
    def finished(self):
        self.queueList = []
        self.submit_button.setEnabled(True)
        self.queue_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.statusBar().showMessage('Finished')
        if Settings.get('general', fallback={'notify' : True})['notify']:
            if sys.platform in ['linux2']:
                try:
                    Popen(['notify-send', '--icon=%s' % os.path.join(Settings.path, 'favicon.ico'), 'Waboocenral has finished downloading.'])
                except:
                    self.displayNotification('Waboocenral', 'Waboocenral has finished downloading.')
            else:
                self.displayNotification('Waboocenral', 'Waboocenral has finished downloading.')
    
    def appendInfo(self, info):
        info = unicode(info)
        r = {'file_name' : re.search('^Downloading\:\s(\S*)', info, re.I),
             'page' : re.search('^Page\s(\d+\s/\s\d+)\:\s\d+\simages\.',
             info, re.I),
             'download_num' : re.search('^(Downloaded|Error\:\sFile).*\((\d{1,}\s?/\s?\d{1,})\)', info, re.I),
             'downloading' : re.search('^Downloading:\s\S*\s\((\d+\s/\s\d+)\)', info, re.I),
             'download_current' : re.search('^(\d*\s?/\s?\d*$)', 
             info, re.I),
             'zero_images' : re.search('^Total\simages:\s0$', info, re.I),
             'preview' : re.search('^Preview:\s(.*)$', info, re.I),
             'error' : re.search('^Error\:\s(.*)', info, re.I) }
        
        for key in r.keys():
            if r[key]:
                if key == 'file_name':
                    self.file_name.setText('<b style="font-size:9px;">%s</b>' % r[key].groups(1)[0] )
                elif key == 'download_current':
                    current, total = r[key].groups(1)[0].split(' / ')
                    current, total, = float(current), float(total)
                    percentage = (100.0 / total) * current
                    self.file_progress.setValue(percentage)
                elif key == 'download_num':
                    current, total = r[key].groups(0)[1].split(' / ')
                    current, total, = float(current), float(total)
                    percentage = (100.0 / total) * current
                    self.total_progress.setValue(percentage)
                elif key == 'downloading':
                    current, total = r[key].groups(0)[0].split(' / ')
                    self.statusBar().showMessage('Downloading: %s / %s' %(int(current), int(total) ) )
                elif key == 'page':
                    self.statusBar().showMessage('Parsing page %s' % r[key].groups(1) )
                elif key == 'zero_images':
                    self.file_errors.setReadOnly(False)
                    self.file_errors.append('No images found.')
                    self.file_errors.setReadOnly(True)
                elif key == 'preview':
                    self.preview_image = QImage(r[key].groups(1)[0])
                    self.preview_pix = QPixmap(self.preview_image)
                    width = self.previewWidget.width() - 25
                    height = self.previewWidget.height() - 25
                    if self.preview_pix.width() < width:
                        width = self.preview_pix.width()
                    if self.preview_pix.height() < height:
                        height = self.preview_pix.height()
                    self.preview_pix = self.preview_pix.scaled(width, height,
                                 Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.preview_label.setPixmap(self.preview_pix)
                elif key == 'error':
                    self.file_errors.setReadOnly(False)
                    self.file_errors.append( r[key].groups(1)[0] )
                    self.file_errors.setReadOnly(True)
        print info
    
    def saveSettings(self):
        self.applySettings()
        self.displayMain()
    
    def applySettings(self):
        self.statusBar().showMessage('Saving...')
        
        # general settings
        preview = self.settings['general']['img_preview'].isChecked()
        notify = self.settings['general']['notify'].isChecked()
        format = unicode(self.settings['general']['format_input'].text())
        tagslength = int(self.settings['general']['tagsLength_input'].text())
        
        Settings.add('general', {'preview' : preview,
                                 'notify' : notify,
                                 'format' : format,
                                 'tagslength' : tagslength})
        
        # board settings
        for b in types:
            uname = str(self.settings[b]['uname_input'].text())
            pword = str(self.settings[b]['pword_input'].text())
            path = str(self.settings[b]['path'].text())
            if not os.path.isdir(path) and path != '':
                try:
                    os.makedirs(path)
                except:
                    error('Unable to make directory "%s".' % path)
            
            Settings.add(b, {'uname' : uname,
                             'pword' : bz2.compress(pword),
                             'path' : path})
        self.settingsButtonApply.setEnabled(False)
        self.statusBar().showMessage('Ready')
    
    def settingsEnableApply(self):
        self.settingsButtonApply.setEnabled(True)

def openFileManager(p=None):
    if not isinstance(p, str):
        p = path
    browsers = {'linux2' : ['xdg-open'],
                'win32' : ['explorer'],
                'cygwin' : ['explorer'],
                'darwin' : ['open'] }
    
    for browser in browsers[sys.platform]:
        try:
            Popen([browser, p])
            break
        except:
            continue

def download(images):
    for i in range(len(images)):
        url, iurl, f = images[i]['url'], [], []
        
        # Danbooru, oreno.imouto, Sankaku
        if re.search('(donmai\.us|imouto\.org|sankaku\S*?\.com)',
                     url, re.I):
            ext, x = ['jpg', 'jpeg', 'png', 'gif'], 0
            while x < len(ext):
                try:
                    # Try other image file extensions
                    url = re.sub('\.(jpg|jpeg|png|gif)$', '.' + ext[x],
                                    url)
                    f = [opener.open(url)]
                    break
                except urllib2.HTTPError, e:
                    x += 1
                    if e.code != 404:
                        error("%s: %s" %(str(e), url))
                except urllib2.URLError, e:
                    error("%s: %s" %(str(e), url))
        
        # Pixiv
        elif re.search('pixiv\.net', url, re.I):
            # Pixiv needs Pixiv referrer
            opener.addheaders += [('Referer',
                'http://www.pixiv.net/member_illust.php?mode=big&illust_id=' + url.split('/')[-1].split('.')[0])]
            try:
                f = [opener.open(url)]
            except urllib2.HTTPError, e:
                if e.code == 404:
                    n = 0
                    iurl = []
                    while True:
                        try:
                            # In case the Pixiv artwork is a manga
                            iurl.append(re.sub('(\.(jpg|jpeg|png|gif)$)', '_p' + str(n) + '\g<0>', url, re.I))
                            f += [opener.open(iurl[n])]
                            n += 1
                        except urllib2.HTTPError, e:
                            if e.code != 404:
                                error("%s: %s" %(str(e), url))
                            break
                    url = iurl
                else:
                    error("%s: %s" %(str(e), url))
            except urllib2.URLError, e:
                error("%s: %s" %(str(e), url))
        
        # Which host is this you FAG?
        elif re.search('hanyuu\.net', url, re.I):
            try:
                f = [opener.open(url)]
            except urllib2.HTTPError, e:
                if e.code == 404:
                    extensions = ['png', 'gif', 'jpg', 'jpeg']
                    for e in extensions:
                        try:
                            url = re.sub('\.(jpe?g|gif|png)', '.' + e,
                                re.sub('victorica\.', 'kana.',
                                url, re.I), re.I)
                            f = [opener.open(url)]
                            break
                        except urllib2.HTTPError, e:
                            if e.code == 404:
                                try:
                                    url = re.sub('\.(jpe?g|gif|png)',
                                        '.' + e, re.sub('kana\.',
                                        'victorica.',
                                        url, re.I))
                                    f = [opener.open(url)]
                                    break
                                except urllib2.HTTPError, e:
                                    if e.code != 404:
                                        error("%s: %s" %(str(e), url))
                                except urllib2.URLError, e:
                                    error("%s: %s" %(str(e), url))
                            else:
                                error("%s: %s" %(str(e), url))
                        except urllib2.URLError, e:
                            error("%s: %s" %(str(e), url))
                else:
                    error("%s: %s" %(str(e), url))
            except urllib2.URLError, e:
                error("%s: %s" %(str(e), url))
        
        # WHAT a FACK mann xDDDDDD epic win /b/ro
        # Also, what fucking boards go here?
        # How are others supposed to have fun reading this source when they
        # can't even be helped with something simple like THIS?
        else:
            try:
                # File extension does not require modification
                f = [opener.open(url)]
            except urllib2.HTTPError, e:
                error("%s: %s" %(str(e), url))
            except urllib2.URLError, e:
                error("%s: %s" %(str(e), url))
        
        for ii in range(len(f)):
            if not isinstance(url, list):
                url = [url]
            
            meta = f[ii].info()
            ext = re.sub('\?\S+', '', url[ii].split('/')[-1], re.I)
            
            suffix = str()
            is_pixiv_page = re.search('(_p\d+)\.\w+$', ext, re.I)
            if is_pixiv_page:
                suffix = is_pixiv_page.groups(0)[0]
            
            format = Settings.get('general', fallback={'format' : '%id% %tags%%page%'})['format']
            format = format.replace('%id%', '%(id)s')
            format = format.replace('%tags%', '%(tags)s')
            format = format.replace('%page%', '%(page)s')
            format = format.replace('%user%', '%(user)s')
            format = format.replace('%rating%', '%(rating)s')
            format = format.replace('%score%', '%(score)s')
            
            obj = dict()
            obj['tags'] = images[i]['tags']
            obj['user'] = images[i]['user']
            obj['rating'] = images[i]['rating']
            obj['score'] = images[i]['score']
            obj['page'] = suffix
            obj['id'] = images[i]['id']
            
            ext = ext.split('.')[-1]
            # Sanitize filename in case of illegal characters
            name = sanitizeFilename(format % obj) + "." + ext
            if 'text/html' in meta['Content-Type']:
                error('Wrong mime-type on image; possible redirect.')
                continue
            filename = os.path.join(directory, name)
            size = float(meta['Content-Length'])
            hsize, b, unit = size, 0, ['B', 'KB', 'MB', 'GB', 'TB']
            while b < len(unit) and hsize > 1024:
                # Get the correct byte unit for the filesize
                hsize = hsize // 1024
                b += 1
            hsize = "%s %s" %(str(hsize), unit[b]); del b, unit
            
            if os.path.isfile(filename) and \
                os.stat(filename).st_size >= size:
                # Image file already exists, skip it
                error("File '%s' (%d / %d) already exists.\n" %(filename, 
                        i + 1, len(images)))
                continue
            
            verbose("Downloading: %s (%s / %s)\n" %(name, i + 1,
                    len(images) ) )
            file = open(filename, 'ab')
            progress, chunk = 0, 10240
            while True:
                d = f[ii].read(chunk)
                if not d:
                    verbose("Downloaded: %s (%s / %s)\n" %(name, i + 1,
                            len(images) ) )
                    break
                file.write(d)
                progress += len(d)
                verbose("%d / %d" %(progress, int(size)))
            file.close()
            
            if Settings.get('general', fallback={'preview' : True})['preview'] and not run:
                verbose('preview: %s' % filename)
        
        if len(opener.addheaders) > 1:
            # Delete the Pixiv referer in header
            del opener.addheaders[1]
    verbose("Finished.")

def login(board, username, password):
    """
    Attempt to login to board
    """
    
    # Login POST request parameters
    adapt = {'pixiv' : {'params' : {'mode' : 'login', 'pixiv_id' : username, 'pass' : password},
                'url' : 'http://www.pixiv.net/login.php',
                'regex' : '<span class=\'error\'>(.*?)<\/span>'},
            'danbooru' : {'params' : {'commit' : 'Login', 'url' : '', 'user[name]' : username, 'user[password]' : password},
                'url' : 'http://danbooru.donmai.us/user/authenticate',
                'regex' : '<div id="notice">(.*?)</div>'},
            'gelbooru' : {'params' : {'pass' : password, 'submit' : 'Log in', 'user' : username},
                'url' : 'http://gelbooru.com/index.php?page=account&s=login&code=00', 'regex' : ''},
            'safebooru' : {'params' : {'pass' : password, 'submit' : 'Log in', 'user' : username},
                'url' : 'http://safebooru.org/index.php?page=account&s=login&code=00', 'regex' : ''},
            'konachan' : {'params' : {'username' : username, 'password' : password},
                'url' : 'http://konachan.net/user/check.json', 'regex' : '"response":"(.*?)"'},
            'oreno.imouto' : {'params' : {'username' : username, 'password' : password},
                'url' : 'http://oreno.imouto.org/user/check.json', 'regex' : '"response":"(.*?)"'},
            'sankakucomplex' : {'params' : {'url' : '', 'user%5Bname%5D' : username, 'user%5Bpass%5D' : password, 'commit' : 'Login'},
                'url' : 'http://chan.sankakucomplex.com/user/authenticate', 'regex' : '<div id="notice">(.*?)</div>'}}
    if board in adapt.keys():
        q = urllib.urlencode(adapt[board]['params'])
        f = opener.open(adapt[board]['url'], q).read()
        r = re.search(adapt[board]['regex'], f, 0)
        try:
            error("%s" % r.group(1))
            return False
        except:
            return True
    else:
        return False

def scrap(tags, board, pages):
    """
    Scrapes the page for thumbnail or full image links.
    """
    
    # XXX: Should load this from a configuration file; use literal_eval along
    # with string formatting to make it possible. Then people can easily
    # replace the old adapt with something new, and possibly grab it from a
    # server automatically. BOTNET BOTNET BOTNET!
    # Search URL format and regex to find images thumbnails.
    adapt = {
        'danbooru' : {
            'url' : 'http://danbooru.donmai.us/post/index?tags=%s',
            'page' : '&page=',
            'mi' : [0, 1],
            'findall' : '\/ssd\/data\/preview\/[a-zA-Z0-9-]*?\.jpg',
            'sub' : [['ssd\/data\/preview\/', 'data/'], ['^\/', 'http://sonohara.donmai.us/']]},
        'gelbooru' : {
            'url' : 'http://gelbooru.com/index.php?page=post&s=list&tags=%s',
            'page' : '&pid=',
            'mi' : [1, 25],
            'findall' : '(http:\/\/[a-zA-Z0-9-]*?\.gelbooru\.com\/thumbs\/\d*?\/thumbnail_[a-zA-Z0-9-]*?\.(jpg|jpeg|png|gif))',
            'sub' : [['thumbs\/', 'images/'], ['thumbnail_', '']]},
        'pixiv' : {
            'url' : 'http://www.pixiv.net/search.php?s_mode=s_tag&word=%s',
            'page' : '&p=',
            'mi' : [0, 1],
            'findall' : '(http:\/\/[a-zA-Z0-9-]*?\.pixiv\.net\/img\/[a-zA-Z0-9-_]*?\/[a-zA-Z0-9-]*?_s\.(jpg|jpeg|png|gif))',
            'sub' : [['_s\.', '.']]},
        'safebooru' : {
            'url' : 'http://safebooru.org/index.php?page=post&s=list&tags=%s',
            'page' : '&pid=',
            'mi' : [1, 25],
            'findall' : '(http:\/\/[a-zA-Z0-9-]*?\.booru\.org\/safe\/\d*?\/thumbnail_[a-zA-Z0-9-]*?\.(jpg|jpeg|png|gif))',
            'sub' : [['safe\/', 'images/'], ['^http:\/\/[a-zA-Z0-9-]*?\.booru\.', 'http://safebooru.'], ['thumbnail_', '']]},
        'konachan' : {
            'url' : 'http://konachan.com/post?tags=%s',
            'page' : '&page=',
            'mi' : [0, 1],
            'findall' : '(http://konachan\.com/(jpeg|image)/\S*?\.(png|jpe?g|gif|bmp))', 'sub' : [['data/preview/[a-zA-Z0-9]{1,3}/[a-zA-Z0-9]{1,3}/([a-zA-Z0-9]*?\.(png|jpe?g|gif|bmp))', 'image/\g<1>']]},
        'oreno.imouto' : {
            'url' : 'http://oreno.imouto.org/post?tags=%s',
            'page' : '&page=',
            'mi' : [0, 1],
            'findall' : '(http://[a-zA-Z0-9]*?\.imouto\.org/data/preview/[a-zA-Z0-9-]{1,3}/[a-zA-Z0-9-]{1,3}/\S*?\.(png|jpe?g|gif|bmp))', 'sub' : [['data/preview/[a-zA-Z0-9]{1,3}/[a-zA-Z0-9]{1,3}/([a-zA-Z0-9]*?\.(png|jpe?g|gif|bmp))', 'image/\g<1>']]},
        'sankakucomplex' : {
            'url' : 'http://chan.sankakucomplex.com/?tags=%s',
            'page' : '&page=', 'mi' : [0, 1],
            'findall' : '(http://[a-zA-Z0-9]{1,3}\.sankakustatic\.com/data/preview/[a-zA-Z0-9]{1,3}/[a-zA-Z0-9]{1,3}/\S*?\.(png|jpe?g|gif))', 'sub' : [['http://[a-zA-Z0-9]{1,3}\.', 'http://chan.'], ['preview/', '']]},
        'e-shuushuu' : {
            'url' : 'http://e-shuushuu.net/search/process/?source=%%22%s%%22',
            'page' : '&page=',
            'mi' : [0, 1],
            'findall' : '',
            'sub' : [[]]}
    }

    url = adapt[board]['url'] % urllib.quote_plus(tags)
    verbose("URL: %s" % url)
    
    # Custom page start number
    # Page start
    ps = 1
    if pages.find(':') != -1:
        ps = int(pages.split(':')[0])
    # Page end
    pe = int(pages.split(':')[-1])
    
    images = []
    
    for i in range(ps, pe + 1):
        pn = str((i - adapt[board]['mi'][0]) * adapt[board]['mi'][1])
        
        pageurl = url + adapt[board]['page'] + pn
        tagslength = Settings.get("general", fallback={"tagslength" : 200})["tagslength"]
        pageimages = MyParser(pageurl, tagslength)
        
        # No more images found, stop parsing pages
        #
        # XXX: May not work with some hosts (Danbooru) due to removing certain
        # images depending on the status (logged in, premium member, etc) of
        # the user downloading, leading to empty pages.
        if len(pageimages) < 1:
            verbose("No more pages.")
            break
        
        for ii in range(0, len(pageimages)):
            for iii in range(0, len(adapt[board]['sub'])):
                # URLs from thumbnail to full image
                pageimages[ii]['url'] = re.sub(adapt[board]['sub'][iii][0],
                                        adapt[board]['sub'][iii][1],
                                        pageimages[ii]['url'], re.I)
        
        # print amount of images found on page of pages found
        verbose("Page %d / %d: %d images." %(i, pe, len(pageimages)))
        
        # Add found images
        images += pageimages
    
    verbose("Total images: %d" % len(images))
    return images

def analyze(items):
    """
    Makes directories if missing and loops over items
    """
    
    for item in items:
        global directory
        tags = item['tags']
        board = item['board']
        pages = item['pages']
        if len(tags) < 1 or len(board) < 1 or len(pages) < 1:
            continue
        if 'pword' in item and 'uname' in item:
            if len(item['pword']) > 0 and len(item['uname']) > 0:
                uname = item['uname']
                pword = item['pword']
                if not login(board, uname, pword):
                    error('Login returned false')
        
        board_dir = board
        tag_dir = sanitizeFilename(tags)
        settings_dir = Settings.get(board, fallback={'path' : ''})['path']
        if settings_dir == '':
            settings_dir = os.path.join(path, board_dir)
        directory = os.path.join(settings_dir, tag_dir)
        try:
            # Recursively making directories for file storage
            os.makedirs(directory)
            verbose("Made directory: %s" % directory)
        except OSError, e:
            if e.errno != 17:
                error(e)
                sys.exit(1)
        download(scrap(tags, board, pages))

def main():
    global run, app, application
    
    if len(sys.argv) > 1:
        for i in range(len(sys.argv)):
            if re.search('^--?h(elp)?', sys.argv[i]):
                print usage
                os.system("pause")
                sys.exit(0)
            else:
                if re.search('^--?n(ogui)?', sys.argv[i]):
                    run = True
                if re.search('^--?b(oard)?', sys.argv[i]):
                    board = sys.argv[i + 1]
                    for b in types:
                        if board in b:
                            board = b
                    if not board in types:
                        print usage
                        sys.exit(1)
                if re.search('^--?u(ser(name)?)?', sys.argv[i]):
                    username = sys.argv[i + 1]
                if re.search('^--?p(ass(word)?)?', sys.argv[i]):
                    password = sys.argv[i + 1]
                if re.search('^--?t(ags)?', sys.argv[i]):
                    tags = sys.argv[i + 1]
                if re.search('^--?P(ages)?', sys.argv[i]):
                    pages = sys.argv[i + 1]
    
    # Run is only true if the --nogui argument is used.
    if run:
        if len(sys.argv) > 2:
            try:
                login(board, username, password)
            except:
                try:
                    username, board
                    password = getpass.getpass('Password: ')
                    login(board, username, password)
                except:
                    pass
            try:
                tags, board, pages
            except:
                try:
                    tags
                except:
                    tags = str()
                    while len(tags) < 1:
                        tags = raw_input("Tags are required: ")
                try:
                    board
                except:
                    board = str()
                    while len(board) < 1:
                        board = raw_input("Image host is required: ")
                    for b in types:
                        if board in b:
                            board = b
                    if not board in types:
                        print usage
                        sys.exit(1)
                try:
                    pages
                except:
                    pages = "1"
            items = []
            items.append({'tags' : tags, 'board' : board, 'pages' : pages})
            analyze(items)
        else:
            try:
                board
            except NameError:
                board = str()
                while len(board) < 1:
                    board = raw_input("Image host: ").lower()
                for b in types:
                    if board in b:
                        board = b
                if not board in types:
                    print usage
                    os.system("pause")
                    sys.exit(1)
            try:
                username
            except NameError:
                username = str()
                if len(username) < 1:
                    username = raw_input("Username (optional): ")
            if len(username) > 0:
                try:
                    password
                except NameError:
                    password = str()
                    while len(password) < 1:
                        password = getpass("Password: ")
            try:
                tags
            except NameError:
                tags = str()
                while len(tags) < 1:
                    tags = raw_input("Tags: ")
            try:
                pages
            except NameError:
                pages = str()
                while len(pages) < 1:
                    pages = raw_input("Pages: ")
            try:
                login(board, username, password)
            except:
                pass
            items = []
            items.append({'tags' : tags, 'board' : board, 'pages' : pages})
            analyze(items)
    else:
        app = QApplication(sys.argv)
        application = Application()
        application.show()
        sys.exit(app.exec_())

if __name__ == '__main__':
    main()
