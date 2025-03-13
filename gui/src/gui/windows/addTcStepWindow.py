from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDesktopWidget, QMainWindow, QApplication, QPlainTextEdit, QPushButton, QWidget, QLabel, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon, QWindow
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.uic import loadUi
import logging
import os, shutil
from datetime import datetime
#from configure import load_json
import re

# #for testing: 
# import sys

class AddTcStepWindow(QWidget):
    ok_signal=pyqtSignal(str)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            if self.QPushButtonOk.hasFocus():
                self.QPushButtonOk_Pressed()
            elif self.QPushButtonCancel.hasFocus():
                self.close()

    def __init__(self, parent = None, default_directory='/home/htsirradiation/Documents/data/'):
        super(AddTcStepWindow, self).__init__(parent)
        #styles = load_json(fname='styles.json') 

        self.setGeometry(100, 100, 400, 200) # x, y, width, height FIXLATER
        QGridLayout = QtWidgets.QGridLayout(self)
        self.default_directory = default_directory

        #window setup
        self.setWindowTitle("Tc Measurement")
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width()-self.frameSize().width())/2), int((resolution.height()-self.frameSize().height())/2))
        
        #blurb
        self.QLabel_blurb = QtWidgets.QLabel(self)
        self.QLabel_blurb.setText("Fill in the following parameters for Tc measurement.")

        #add session note
        self.QLabel_description = QtWidgets.QLabel(self)
        self.QLabel_description.setText("Briefly describe this measurement:")
        self.QLineEdit_description = QtWidgets.QLineEdit(self)
        self.QLineEdit_description.setPlaceholderText("What measurement are you recording?")
        self.QLabel_err = QtWidgets.QLabel(self)
        self.QLabel_err.setText("")
        
        #start temp
        self.QLabel_startT = QtWidgets.QLabel(self)
        self.QLabel_startT.setText("Start temperature (K):")
        self.QDoubleSpinBox_startT = QtWidgets.QDoubleSpinBox(self)
        self.QDoubleSpinBox_startT.setRange(1, 400)
        self.QDoubleSpinBox_startT.setValue(85)
        self.QDoubleSpinBox_startT.setSingleStep(1)

        #stop temp
        self.QLabel_stopT = QtWidgets.QLabel(self)
        self.QLabel_stopT.setText("Stop temperature (K):")
        self.QDoubleSpinBox_stopT = QtWidgets.QDoubleSpinBox(self)
        self.QDoubleSpinBox_stopT.setRange(1, 400)
        self.QDoubleSpinBox_stopT.setValue(95)
        self.QDoubleSpinBox_stopT.setSingleStep(1)

        #ramp rate
        self.QLabel_ramp = QtWidgets.QLabel(self)
        self.QLabel_ramp.setText("Ramp rate (K/min)")
        self.QDoubleSpinBox_ramp = QtWidgets.QDoubleSpinBox(self)
        self.QDoubleSpinBox_ramp.setRange(0.1, 100)
        self.QDoubleSpinBox_ramp.setValue(0.5)
        self.QDoubleSpinBox_ramp.setSingleStep(0.1)

        #transport current
        self.QLabel_current = QtWidgets.QLabel(self)
        self.QLabel_current.setText("Transport Current [mA]")
        self.QComboBox_Current = QtWidgets.QComboBox(self)
        self.QComboBox_Current.addItems(["1","10","100"])

        #buttons
        # cancel and start new session buttons
        self.QPushButtonCancel = QtWidgets.QPushButton(self)
        self.QPushButtonCancel.setText("Cancel")
        self.QPushButtonCancel.clicked.connect(lambda:self.QPushButtonCancel_Pressed())
        self.QPushButtonOk = QtWidgets.QPushButton(self)
        self.QPushButtonOk.setText("OK")
        self.QPushButtonOk.clicked.connect(lambda:self.QPushButtonOk_Pressed())
        self.QPushButtonOk.setFocus()

        #layout
        layout=QGridLayout
        layout.addWidget(self.QLabel_blurb, 0, 0)

        layout.addWidget(self.QLabel_description, 1, 0)
        layout.addWidget(self.QLineEdit_description, 3, 0)
        layout.addWidget(self.QLabel_err, 2, 0)

        layout.addWidget(self.QLabel_startT, 4, 0)
        layout.addWidget(self.QDoubleSpinBox_startT, 4, 1)

        layout.addWidget(self.QLabel_stopT,5,0)
        layout.addWidget(self.QDoubleSpinBox_stopT,5,1)

        layout.addWidget(self.QLabel_ramp,6,0)
        layout.addWidget(self.QDoubleSpinBox_ramp,6,1)

        layout.addWidget(self.QLabel_current,7,0)
        layout.addWidget(self.QComboBox_Current,7,1)
        
        layout.addWidget(self.QPushButtonOk, 8,0)
        layout.addWidget(self.QPushButtonCancel, 8,1)
    
    def QPushButtonCancel_Pressed(self):
        self.close()
        
    def QPushButtonOk_Pressed(self):
        try:
            desc = self.QLineEdit_description.text()
        except Exception as e:
            print(e)
        regex = re.compile('[@ !#$%^&*()<>?/\|}{~:]')
        if(regex.search(desc) == None) and desc != "":
            self.ok_signal.emit('MeasureTc : Label = {} ; Start-Temperature = {} K; Stop-Temperature = {} K; Ramp-rate {} K/min; Transport-current = {} mA'.format(desc, self.QDoubleSpinBox_startT.value(), self.QDoubleSpinBox_stopT.value(),self.QDoubleSpinBox_ramp.value(), self.QComboBox_Current.currentText()))
            self.close()
        if desc == "":
            self.QLabel_err.setText("Description cannot be empty")
        else:
            self.QLabel_err.setText("Description cannot contain special characters, \nonly alphanumeric and - and _")