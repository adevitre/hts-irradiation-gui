from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDesktopWidget, QMainWindow, QApplication, QPlainTextEdit, QPushButton, QWidget, QLabel, QMessageBox, QFileDialog, QComboBox
from PyQt5.QtGui import QIcon, QWindow
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.uic import loadUi
import logging
import os, shutil
from datetime import datetime
#from configure import load_json
import re

#for testing: 
# import sys

LABEL_CS100A = 'HP6260B-120A'
LABEL_CS006A = '2231A-30-3-6A'

class AddIcStepWindow(QWidget):
    ok_signal = pyqtSignal(str)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            if self.QPushButtonOk.hasFocus():
                self.QPushButtonOk_Pressed()
            elif self.QPushButtonCancel.hasFocus():
                self.close()

    def __init__(self, parent = None, default_directory='/home/htsirradiation/Documents/data/'):
        super(AddIcStepWindow, self).__init__(parent)
        #styles = load_json(fname='styles.json') 

        self.setGeometry(100, 100, 400, 200)               # x, y, width, height FIXLATER
        QGridLayout = QtWidgets.QGridLayout(self)
        self.default_directory = default_directory

        #window setup
        self.setWindowTitle("Ic Measurement")
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width()-self.frameSize().width())/2), int((resolution.height()-self.frameSize().height())/2))
        
        #blurb
        self.QLabel_blurb = QtWidgets.QLabel(self)
        self.QLabel_blurb.setText("Fill in the following parameters for Ic measurement.")

        #add session note
        self.QLabel_description = QtWidgets.QLabel(self)
        self.QLabel_description.setText("Briefly describe this measurement:")
        self.QLineEdit_description = QtWidgets.QLineEdit(self)
        self.QLineEdit_description.setPlaceholderText("What measurement are you recording?")
        self.QLabel_err = QtWidgets.QLabel(self)
        self.QLabel_err.setText("")
        #

        self.comboBoxSelectCurrentSource = QComboBox(self)
        self.comboBoxSelectCurrentSource.addItems([LABEL_CS006A, LABEL_CS100A]) # WARNING: Changing these labels will affect the functionality of Ic measurements!
        self.comboBoxSelectCurrentSource.activated.connect(self.comboBoxSelectCurrentSource_activated)
        self.comboBoxSelectCurrentSource.setEnabled(True)

        #choose number of measurements
        self.QLabel_measurements = QtWidgets.QLabel(self)
        self.QLabel_measurements.setText("Number of measurements:")
        self.QSpinBox_measurements = QtWidgets.QSpinBox(self)
        self.QSpinBox_measurements.setRange(1,100)
        self.QSpinBox_measurements.setSingleStep(1)

        #ramp start
        self.QLabel_ramp = QtWidgets.QLabel(self)
        self.QLabel_ramp.setText("Current ramp start [A]")
        self.QDoubleSpinBox_ramp = QtWidgets.QDoubleSpinBox(self)
        self.QDoubleSpinBox_ramp.setRange(0,100)
        self.QDoubleSpinBox_ramp.setSingleStep(1)

        #step size
        self.QLabel_step = QtWidgets.QLabel(self)
        self.QLabel_step.setText("Current step size [A]")
        self.QDoubleSpinBox_stepSize = QtWidgets.QDoubleSpinBox(self)
        self.QDoubleSpinBox_stepSize.setRange(.001,5)
        self.QDoubleSpinBox_stepSize.setSingleStep(.05)
        self.QDoubleSpinBox_stepSize.setValue(.3)

        #voltage limit
        self.QLabel_vlimit = QtWidgets.QLabel(self)
        self.QLabel_vlimit.setText("Voltage limit [uV]")
        self.QDoubleSpinBox_vlimit = QtWidgets.QDoubleSpinBox(self)
        self.QDoubleSpinBox_vlimit.setRange(5,50)
        self.QDoubleSpinBox_vlimit.setSingleStep(5)
        self.QDoubleSpinBox_vlimit.setValue(20)

        #buttons
        # cancel and start new session buttons
        self.QPushButtonCancel = QtWidgets.QPushButton(self)
        self.QPushButtonCancel.setText("Cancel")
        self.QPushButtonCancel.clicked.connect(lambda:self.QPushButtonCancel_Pressed())
        self.QPushButtonOk = QtWidgets.QPushButton(self)
        #self.QPushButtonOk.setStyleSheet(styles['QPushButton_idle'])
        self.QPushButtonOk.setText("OK")
        self.QPushButtonOk.clicked.connect(lambda:self.QPushButtonOk_Pressed())
        self.QPushButtonOk.setFocus()

        #layout
        layout=QGridLayout
        layout.addWidget(self.QLabel_blurb, 0, 0)

        layout.addWidget(self.QLabel_description, 1, 0)
        layout.addWidget(self.QLineEdit_description, 3,0)
        layout.addWidget(self.QLabel_err, 2, 0)

        layout.addWidget(self.comboBoxSelectCurrentSource, 4, 0)
        layout.addWidget(self.QLabel_measurements,5,0)
        layout.addWidget(self.QSpinBox_measurements,5,1)

        layout.addWidget(self.QLabel_ramp,6,0)
        layout.addWidget(self.QDoubleSpinBox_ramp,6,1)

        layout.addWidget(self.QLabel_step,7,0)
        layout.addWidget(self.QDoubleSpinBox_stepSize,7,1)

        layout.addWidget(self.QLabel_vlimit,8,0)
        layout.addWidget(self.QDoubleSpinBox_vlimit,8,1)
        
        layout.addWidget(self.QPushButtonOk, 9,0)
        layout.addWidget(self.QPushButtonCancel, 9,1)
    
    def QPushButtonCancel_Pressed(self):
        self.close()
        
    def QPushButtonOk_Pressed(self):
        try:
            desc = self.QLineEdit_description.text()
        except Exception as e:
            print(e)
        regex = re.compile('[@ !#$%^&*()<>?/\|}{~:]')
        if(regex.search(desc) == None and desc != ""):
            self.ok_signal.emit('MeasureIc : Label = {} ; Repeats = {} ; Start-Current = {} A; Step-size {} A; Voltage-limit = {} uV; Current-Source = {}'.format(desc, self.QSpinBox_measurements.value(), self.QDoubleSpinBox_ramp.value(), self.QDoubleSpinBox_stepSize.value(), self.QDoubleSpinBox_vlimit.value(), self.comboBoxSelectCurrentSource.currentText()))
            self.close()
        if desc == "":
            self.QLabel_err.setText("Description cannot be empty")
        else:
            self.QLabel_err.setText("Description cannot contain special characters, \nonly alphanumeric and - and _")
            
    def comboBoxSelectCurrentSource_activated(self):
        if self.comboBoxSelectCurrentSource.currentText() == LABEL_CS100A:
            self.QDoubleSpinBox_stepSize.setDecimals(1)
            self.QDoubleSpinBox_stepSize.setSingleStep(0.1)
            self.QDoubleSpinBox_stepSize.setRange(0.3, 3.0)
            self.QDoubleSpinBox_stepSize.setValue(0.3)
            
        elif self.comboBoxSelectCurrentSource.currentText() == LABEL_CS006A:
            self.QDoubleSpinBox_stepSize.setDecimals(3)
            self.QDoubleSpinBox_stepSize.setSingleStep(0.001)
            self.QDoubleSpinBox_stepSize.setRange(0.001, 0.500)
            self.QDoubleSpinBox_stepSize.setValue(0.020)

#for testing
# app = QApplication(sys.argv)
# w = MeasureIcWindow()
# w.show()
# app.exec()



