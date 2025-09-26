from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QRadioButton, QButtonGroup, QHBoxLayout, QDesktopWidget, QMainWindow, QApplication, QPlainTextEdit, QPushButton, QWidget, QLabel, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon, QWindow
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.uic import loadUi
import logging
import os, shutil
from datetime import datetime
import re

class AddRelayStepWindow(QWidget):
    ok_signal=pyqtSignal(str)

    def __init__(self, parent = None, default_directory='/home/htsirradiation/Documents/data/'):
        super(AddRelayStepWindow, self).__init__(parent)

        self.setGeometry(100, 100, 400, 200) # x, y, width, height
        QGridLayout = QtWidgets.QGridLayout(self)
        self.default_directory = default_directory

        #window setup
        self.setWindowTitle("Select relays to trigger")
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width()-self.frameSize().width())/2), int((resolution.height()-self.frameSize().height())/2))
        
        self.coldhead_group_layout = QHBoxLayout()
        label = QLabel("Cold Head")
        self.coldhead_group_layout.addWidget(label)
        radio_on = QRadioButton("On")
        radio_off = QRadioButton("Off")
        radio_off.setChecked(True)
        self.coldhead_button_group = QButtonGroup(self)
        self.coldhead_button_group.addButton(radio_on)
        self.coldhead_button_group.addButton(radio_off)
        self.coldhead_group_layout.addWidget(radio_on)
        self.coldhead_group_layout.addWidget(radio_off)

        self.faradaycup_group_layout = QHBoxLayout()
        label = QLabel("Faraday Cup")
        self.faradaycup_group_layout.addWidget(label)
        radio_on = QRadioButton("On")
        radio_off = QRadioButton("Off")
        radio_off.setChecked(True)
        self.faradaycup_button_group = QButtonGroup(self)
        self.faradaycup_button_group.addButton(radio_on)
        self.faradaycup_button_group.addButton(radio_off)
        self.faradaycup_group_layout.addWidget(radio_on)
        self.faradaycup_group_layout.addWidget(radio_off)

        self.turbopump_group_layout = QHBoxLayout()
        label = QLabel("Turbo Pump Valve")
        self.turbopump_group_layout.addWidget(label)
        radio_on = QRadioButton("On")
        radio_off = QRadioButton("Off")
        radio_off.setChecked(True)
        self.turbopump_button_group = QButtonGroup(self)
        self.turbopump_button_group.addButton(radio_on)
        self.turbopump_button_group.addButton(radio_off)
        self.turbopump_group_layout.addWidget(radio_on)
        self.turbopump_group_layout.addWidget(radio_off)

        # cancel and ok buttons
        self.QPushButtonCancel = QtWidgets.QPushButton(self)
        self.QPushButtonCancel.setText("Cancel")
        self.QPushButtonCancel.clicked.connect(lambda:self.QPushButtonCancel_Pressed())
        self.QPushButtonOk = QtWidgets.QPushButton(self)
        self.QPushButtonOk.setText("Ok")
        self.QPushButtonOk.clicked.connect(lambda:self.QPushButtonOk_Pressed())
        self.QPushButtonOk.setFocus()

        #layout
        self.layout=QGridLayout
        self.layout.addLayout(self.turbopump_group_layout, 0, 0, 1, 1)
        self.layout.addLayout(self.coldhead_group_layout, 1, 0, 1, 1)
        self.layout.addLayout(self.faradaycup_group_layout, 2, 0, 1, 1)
        self.layout.addWidget(self.QPushButtonOk, 2, 1, 1, 2)
        self.layout.addWidget(self.QPushButtonCancel, 2, 3, 1, 2)
    
    def QPushButtonCancel_Pressed(self):
        self.close()
        
    def QPushButtonOk_Pressed(self):
        try:
            step='TriggerRelays Coldhead {} ; FaradayCup {} ; TurboValve {}'.format(self.coldhead_button_group.checkedButton().text(), self.faradaycup_button_group.checkedButton().text(), self.turbopump_button_group.checkedButton().text())
            self.ok_signal.emit(step)
            self.close()

        except Exception as e:
            print('addRelayStepWindow::QPushButtonOk_Pressed raised:\n', e)
    
    def QCheckBox_wait_for_pressure_clicked(self):
        self.enable_pressure_threshold(self.QCheckBox_wait_for_pressure.isChecked())
        
    def enable_pressure_threshold(self, enabled=True):
        self.QSpinBox_value.setEnabled(enabled)
        self.QSpinBox_exponent.setEnabled(enabled)