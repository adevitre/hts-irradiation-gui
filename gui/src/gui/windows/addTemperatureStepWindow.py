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

class AddTemperatureStepWindow(QWidget):
    ok_signal=pyqtSignal(str)
    '''
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            if self.QPushButtonOk.hasFocus():
                self.QPushButtonOk_Pressed()
            elif self.QPushButtonCancel.hasFocus():
                self.close()
    '''

    def __init__(self, parent = None, default_directory='/home/htsirradiation/Documents/data/'):
        super(AddTemperatureStepWindow, self).__init__(parent)

        self.setGeometry(100, 100, 400, 200) # x, y, width, height
        QGridLayout = QtWidgets.QGridLayout(self)
        self.default_directory = default_directory

        #window setup
        self.setWindowTitle("Set Temperature")
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width()-self.frameSize().width())/2), int((resolution.height()-self.frameSize().height())/2))
        
        # blurb
        self.QLabel_blurb = QtWidgets.QLabel(self)
        self.QLabel_blurb.setText("Fill in the following parameters for adjusting temperature:")
        
        self.QCheckBox_warmup = QtWidgets.QCheckBox('Warmup?', self)
        self.QCheckBox_warmup.clicked.connect(lambda: self.QCheckBox_warmup_clicked())

        # objective temp
        self.QLabel_objT = QtWidgets.QLabel(self)
        self.QLabel_objT.setText("Objective temperature (K):")
        self.QDoubleSpinBox_objT = QtWidgets.QDoubleSpinBox(self)
        self.QDoubleSpinBox_objT.setRange(15, 310)
        self.QDoubleSpinBox_objT.setSingleStep(1)
        self.QDoubleSpinBox_objT.setValue(19)

        # Stability margin
        self.QLabel_stabMargin = QtWidgets.QLabel(self)
        self.QLabel_stabMargin.setText("Stability margin (K):")
        self.QDoubleSpinBox_stabMargin = QtWidgets.QDoubleSpinBox(self)
        self.QDoubleSpinBox_stabMargin.setRange(.1, 2)
        self.QDoubleSpinBox_stabMargin.setSingleStep(.1)
        self.QDoubleSpinBox_stabMargin.setValue(.2)

        # Stabilization time
        self.QLabel_stabTime = QtWidgets.QLabel(self)
        self.QLabel_stabTime.setText("Time required for stability (s):")
        self.QSpinBox_stabTime = QtWidgets.QSpinBox(self)
        self.QSpinBox_stabTime.setRange(0, 1800)
        self.QSpinBox_stabTime.setSingleStep(10)
        self.QSpinBox_stabTime.setValue(60)

        #ramp rate
        self.QLabel_ramp = QtWidgets.QLabel(self)
        self.QLabel_ramp.setText("Ramp rate (K/min)")
        self.QDoubleSpinBox_ramp = QtWidgets.QDoubleSpinBox(self)
        self.QDoubleSpinBox_ramp.setRange(0, 10)
        self.QDoubleSpinBox_ramp.setSingleStep(.1)
        self.QDoubleSpinBox_ramp.setValue(0.)

        #buttons
        # cancel and start new session buttons
        self.QPushButtonCancel = QtWidgets.QPushButton(self)
        self.QPushButtonCancel.setText("Cancel")
        self.QPushButtonCancel.clicked.connect(lambda:self.QPushButtonCancel_Pressed())
        self.QPushButtonOk = QtWidgets.QPushButton(self)
        self.QPushButtonOk.setText("Ok")
        self.QPushButtonOk.clicked.connect(lambda:self.QPushButtonOk_Pressed())
        self.QPushButtonOk.setFocus()

        #layout
        self.layout=QGridLayout
        self.layout.addWidget(self.QLabel_blurb, 0, 0)
        self.layout.addWidget(self.QCheckBox_warmup, 1, 0)
        self.layout.addWidget(self.QLabel_objT, 3, 0)
        self.layout.addWidget(self.QDoubleSpinBox_objT, 3, 1)

        self.layout.addWidget(self.QLabel_stabMargin, 4, 0)
        self.layout.addWidget(self.QDoubleSpinBox_stabMargin, 4, 1)

        self.layout.addWidget(self.QLabel_stabTime, 5, 0)
        self.layout.addWidget(self.QSpinBox_stabTime, 5, 1)

        self.layout.addWidget(self.QLabel_ramp, 6, 0)
        self.layout.addWidget(self.QDoubleSpinBox_ramp, 6, 1)
        
        self.layout.addWidget(self.QPushButtonOk, 8, 0)
        self.layout.addWidget(self.QPushButtonCancel, 8, 1)
    
    def QPushButtonCancel_Pressed(self):
        self.close()
        
    def QPushButtonOk_Pressed(self):
        try:
            if self.QCheckBox_warmup.isChecked():
                step = 'Warmup'
            else:
                step = 'SetTemperature : Objective-temperature = {} K; Stability-margin = {} K; Stabilization-time = {} s; Ramp-rate = {} K/min'.format(self.QDoubleSpinBox_objT.value(),self.QDoubleSpinBox_stabMargin.value(),self.QSpinBox_stabTime.value(),self.QDoubleSpinBox_ramp.value())
            self.ok_signal.emit(step)
            self.close()
        except Exception as e:
            print('addTemperatureStepWindow::QPushButtonOk_Pressed raised:\n', e)
    
    def QCheckBox_warmup_clicked(self):
        if self.QCheckBox_warmup.isChecked():
            self.enable(False)
        else:
            self.enable(True)
        self.QCheckBox_warmup.setEnabled(True)

    def enable(self, enabled=True):
        self.QDoubleSpinBox_objT.setEnabled(enabled)
        self.QDoubleSpinBox_stabMargin.setEnabled(enabled)
        self.QSpinBox_stabTime.setEnabled(enabled)
        self.QDoubleSpinBox_ramp.setEnabled(enabled)
        self.QCheckBox_warmup.setEnabled(enabled)

# #for testing
# app = QApplication(sys.argv)
# w = AddTemperatureStepWindow()
# w.show()
# app.exec()