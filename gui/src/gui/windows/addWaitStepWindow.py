from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDesktopWidget, QMainWindow, QApplication, QPlainTextEdit, QPushButton, QWidget, QLabel, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon, QWindow
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.uic import loadUi
import logging
import os, sys, shutil
from datetime import datetime
import re

class AddWaitStepWindow(QWidget):
    ok_signal=pyqtSignal(str)

    def __init__(self, parent = None, default_directory='/home/htsirradiation/Documents/data/'):
        super(AddWaitStepWindow, self).__init__(parent)

        self.setGeometry(100, 100, 400, 200) # x, y, width, height
        QGridLayout = QtWidgets.QGridLayout(self)
        self.default_directory = default_directory

        #window setup
        self.setWindowTitle("Wait for...")
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width()-self.frameSize().width())/2), int((resolution.height()-self.frameSize().height())/2))
        
        # Wait time
        self.QLabel_time = QtWidgets.QLabel(self)
        self.QLabel_time.setText("Wait time [s]:")
        self.QSpinBox_time = QtWidgets.QSpinBox(self)
        self.QSpinBox_time.setRange(0, sys.maxint)
        self.QSpinBox_time.setSingleStep(60)
        self.QSpinBox_time.setValue(600)

        # wait for pressure
        self.QCheckBox_wait_for_pressure = QtWidgets.QCheckBox('Wait for pressure?', self)
        self.QCheckBox_wait_for_pressure.connect(lambda: self.QCheckBox_wait_for_pressure_clicked())

        self.QSpinBox_value = QtWidgets.QSpinBox(self)
        self.QSpinBox_value.setRange(0, 9)
        self.QSpinBox_value.setSingleStep(1)
        self.QSpinBox_value.setValue(1)
        self.QLabel_exponent = QtWidgets.QLabel(self)
        self.QLabel_exponent.setText("e")
        self.QSpinBox_exponent = QtWidgets.QSpinBox(self)
        self.QSpinBox_exponent.setRange(-7, 3)
        self.QSpinBox_exponent.setSingleStep(1)
        self.QSpinBox_exponent.setValue(-1)
        self.QLabel_unit = QtWidgets.QLabel(self)
        self.QLabel_unit.setText("torr")
        
        # cancel and ok buttons
        self.QPushButtonCancel = QtWidgets.QPushButton(self)
        self.QPushButtonCancel.setText("Cancel")
        self.QPushButtonCancel.clicked.connect(lambda:self.QPushButtonCancel_Pressed())
        self.QPushButtonOk = QtWidgets.QPushButton(self)
        self.QPushButtonOk.setText("Ok")
        self.QPushButtonOk.clicked.connect(lambda:self.QPushButtonOk_Pressed())
        self.QPushButtonOk.setFocus()

        self.enable_pressure_threshold(False)
        self.QCheckBox_wait_for_pressure.setChecked(False)
        
        #layout
        self.layout=QGridLayout
        self.layout.addWidget(self.QLabel_time, 0, 0)
        self.layout.addWidget(self.QSpinBox_time, 0, 1)
        self.layout.addWidget(self.QCheckBox_wait_for_pressure, 2, 0)
        self.layout.addWidget(self.QSpinBox_value, 3, 0)
        self.layout.addWidget(self.QLabel_exponent, 3, 1)
        self.layout.addWidget(self.QSpinBox_exponent, 3, 2)
        self.layout.addWidget(self.QLabel_unit, 3, 3)
        self.layout.addWidget(self.QPushButtonOk, 8, 0)
        self.layout.addWidget(self.QPushButtonCancel, 8, 1)
    
    def QPushButtonCancel_Pressed(self):
        self.close()
        
    def QPushButtonOk_Pressed(self):
        try:
            pressure_threshold = ''
            if self.QCheckBox_wait_for_pressure.isChecked():
                pressure_threshold = float('; pressure threshold {:2.1f}e{:2.1f} torr'.format(self.QSpinBox_value.value(), self.QSpinBox_exponent.value())
            step='Wait {} seconds'.format()+pressure_threshold
            self.ok_signal.emit(step)
            self.close()
        except Exception as e:
            print('addWaitStepWindow::QPushButtonOk_Pressed raised:\n', e)
    
    def QCheckBox_warmup_clicked(self):
        self.enable_pressure_threshold(self.QCheckBox_wait_for_pressure.isChecked())
        
    def enable_pressure_threshold(self, enabled=True):
        self.QSpinBox_value.setEnabled(enabled)
        self.QSpinBox_exponent.setEnabled(enabled)