from PyQt5.QtWidgets import QWidget, QGridLayout, QLabel, QLineEdit, QSpinBox, QPushButton, QComboBox
from PyQt5 import QtGui
import re

from PyQt5.QtCore import pyqtSignal#, Qt, QObject, 

class PreferencesWindow(QWidget):
    
    ok = pyqtSignal(dict)
    
    def __init__(self, preferences, parent=None):
        
        super(PreferencesWindow, self).__init__(parent)
        self.setGeometry(100, 100, 600, 400)               # x, y, width, height
        gridLayout = QGridLayout(self)
        
        emaillist = ''
        if preferences['emails'] != []:
            emaillist = preferences['emails'][0]
            for email in preferences['emails'][1:]:
                emaillist += ', '+email
                
        labelEmailAddresses = QLabel('Alert email addresses:')
        self.lineEditEmailAddresses = QLineEdit(emaillist)
        
        #labelPlotMode = QLabel('Plot update mode:')
        #self.comboBoxPlotMode = QComboBox()
        #self.comboBoxPlotMode.addItems(['Dynamic', 'Static'])
        #if preferences['plotmode'] == 'Static':
        #    self.comboBoxPlotMode.setCurrentIndex(1)
        
        #labelDataPoints = QLabel('Points to display\nin dynamic mode:')
        #self.spinBoxDataPoints = QSpinBox()
        #self.spinBoxDataPoints.setRange(300, 3600)
        #self.spinBoxDataPoints.setValue(preferences['nsecs'])
        
        labelSaveRate = QLabel('Back up data every (s):')
        self.spinBoxSaveRate = QSpinBox()
        self.spinBoxSaveRate.setRange(30, 600)
        self.spinBoxSaveRate.setValue(preferences['saverate']/1000)
        
        # cancel and start new session buttons
        buttonCancel = QPushButton('Cancel')
        buttonOk = QPushButton('Ok')
        buttonCancel.clicked.connect(lambda:self.QPushButtonCancel_Pressed())
        buttonOk.clicked.connect(lambda:self.QPushButtonOk_Pressed())
        buttonOk.setFocus()
        
        gridLayout.addWidget(labelEmailAddresses, 0, 0, 1, 2)
        gridLayout.addWidget(self.lineEditEmailAddresses, 0, 2, 1, 1)
        #gridLayout.addWidget(labelPlotMode, 1, 0, 1, 2)
        #gridLayout.addWidget(self.comboBoxPlotMode, 1, 2, 1, 1)
        #gridLayout.addWidget(labelDataPoints, 2, 0, 1, 2)
        #gridLayout.addWidget(self.spinBoxDataPoints, 2, 2, 1, 1)
        gridLayout.addWidget(labelSaveRate, 3, 0, 1, 2)
        gridLayout.addWidget(self.spinBoxSaveRate, 3, 2, 1, 1)
        gridLayout.addWidget(buttonOk, 4, 0, 1, 1)
        gridLayout.addWidget(buttonCancel, 4, 1, 1, 1)
        
        # default_directory='/home/pi/Documents/LIFT1 data'
        
        #window setup
        self.setWindowTitle("Preferences")
        resolution = QtGui.QDesktopWidget().screenGeometry()
        self.move((resolution.width()-self.frameSize().width())/2, (resolution.height()-self.frameSize().height())/2)
    
    def QPushButtonCancel_Pressed(self):
        self.close()
        
    def QPushButtonOk_Pressed(self):
        validEmails = []
        for email in re.split('[,| ]+', self.lineEditEmailAddresses.text()):
            if re.search('^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$', email):
                validEmails.append(email)
        preferences = {
            'emails': validEmails,
            #'nsecs': self.spinBoxDataPoints.value(),
            #'plotmode': self.comboBoxPlotMode.currentText(),
            'saverate': self.spinBoxSaveRate.value()*1000 # QTimers work in ms
        }
        self.ok.emit(preferences)
        self.close()
            
