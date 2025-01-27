import os, shutil, logging
from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDesktopWidget, QMainWindow, QGridLayout, QHBoxLayout, QVBoxLayout, QApplication, QPlainTextEdit, QPushButton, QWidget, QLabel, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon, QWindow
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.uic import loadUi
from GetDirWindow import launchWindow
from horizontalline import HorizontalLine

from datetime import datetime
from configure import load_json

HARDWARE_PARAMETERS = load_json(fname='hwparams.json', location=os.getcwd()+'/config')

"""
    Tab_Login is a submodule of the GUI containing GUI objects and functions
    needed to start a recording session.

    @author Alexis Devitre (devitre@mit.edu)
    @last-modified July 2024
"""   
class Tab_Login(QWidget):
    
    signal_newsession = pyqtSignal(str, str, bool, bool, bool)
    setvoltagesign_signal = pyqtSignal(int)
    signal_stopsession = pyqtSignal()
    
    def __init__(self, parent=None, default_directory='/home/htsirradiation/Documents/data'):
        
        super(Tab_Login, self).__init__(parent)
        self.parent = parent

        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        self.default_directory = default_directory

        self.QLineEdit_homeDirectory = QtWidgets.QLineEdit(self)
        self.QLineEdit_homeDirectory.setEnabled(False)
        self.QLineEdit_homeDirectory.setText(default_directory)
        self.QLineEdit_homeDirectory.setMaximumWidth(500)
        self.QLineEdit_homeDirectory.setMinimumWidth(500)

        self.QPushButton_homeDirectory = QtWidgets.QPushButton(self)
        self.QPushButton_homeDirectory.setText("Select home directory")
        self.QPushButton_homeDirectory.clicked.connect(lambda:self.launch_GetDirWindow())
        self.QPushButton_homeDirectory.setMaximumWidth(200)
        self.QPushButton_homeDirectory.setMinimumWidth(200)
        
        self.QLineEdit_folderName = QtWidgets.QLineEdit(self)
        self.QLineEdit_folderName.setText('_temp')
        self.QLineEdit_folderName.setMaximumWidth(500)
        self.QLineEdit_folderName.setMinimumWidth(500)

        self.QPushButton_folderName = QtWidgets.QPushButton(self)
        self.QPushButton_folderName.setText("Overwrite folder")
        self.QPushButton_folderName.clicked.connect(lambda: self.launch_GetFolWindow())
        self.QPushButton_folderName.setMaximumWidth(200)
        self.QPushButton_folderName.setMinimumWidth(200)
        
        self.QCheckBox_saveTemperature = QtWidgets.QCheckBox('Save time trace of temperature', self)
        self.QCheckBox_saveTemperature.setChecked(True)
        self.QCheckBox_savePressure = QtWidgets.QCheckBox('Save time trace of pressure', self)
        self.QCheckBox_savePressure.setChecked(True)
        self.QCheckBox_ln2Mode = QtWidgets.QCheckBox('LN2 mode', self)
        self.QCheckBox_ln2Mode.clicked.connect(lambda: self.QCheckBox_ln2Mode_Clicked())
        self.checkboxSetVoltageSign = QtWidgets.QCheckBox('Reverse voltage sign?', self)
        self.checkboxSetVoltageSign.clicked.connect(self.checkBoxSetVoltageSign_clicked)

        self.QPushButtonStart = QtWidgets.QPushButton(self)
        self.QPushButtonStart.setText("Start Session...")
        self.QPushButtonStart.setStyleSheet(self.styles['QPushButton_idle'])
        self.QPushButtonStart.clicked.connect(lambda:self.QPushButtonStart_Pressed())
        self.QPushButtonStart.setMaximumWidth(250)
        self.QPushButtonStart.setMinimumWidth(250)
        

        vLayout = QVBoxLayout(self)
        vLayout.setSpacing(20)
        vLayout.addStretch()

        hLayout = QHBoxLayout()
        hLayout.setSpacing(0)
        hLayout.addStretch()
        hLayout.addWidget(self.QLineEdit_homeDirectory)
        hLayout.addWidget(self.QPushButton_homeDirectory)
        hLayout.addStretch()
        vLayout.addLayout(hLayout)

        hLayout = QHBoxLayout()
        hLayout.setSpacing(0)
        hLayout.addStretch()
        hLayout.addWidget(self.QLineEdit_folderName)
        hLayout.addWidget(self.QPushButton_folderName)
        hLayout.addStretch()
        vLayout.addLayout(hLayout)

        hLayout = QHBoxLayout()
        hLayout.addStretch()
        hLayout.addWidget(self.QCheckBox_saveTemperature)
        hLayout.addWidget(self.QCheckBox_savePressure)
        hLayout.addWidget(self.QCheckBox_ln2Mode)
        hLayout.addWidget(self.checkboxSetVoltageSign)
        hLayout.addStretch()
        vLayout.addLayout(hLayout)

        hLayout = QHBoxLayout()
        hLayout.addStretch()
        hLayout.addWidget(self.QPushButtonStart)
        hLayout.addStretch()
        vLayout.addLayout(hLayout)
        vLayout.addStretch()

    def launch_GetDirWindow(self):
        GetDirWindow = QFileDialog(directory=self.default_directory)
        GetDirWindow.setFileMode(QFileDialog.Directory)
        directory = GetDirWindow.getExistingDirectory(self,"Choose Directory")

        if directory is not None:
            self.QLineEdit_homeDirectory.setText(directory)

    def launch_GetFolWindow(self):
        GetDirWindow = QFileDialog(directory=self.default_directory)
        GetDirWindow.setFileMode(QFileDialog.Directory)
        if GetDirWindow.exec_():
            directory = GetDirWindow.selectedFiles()
            if directory is not []:
                self.QLineEdit_folderName.setText(directory[0].split('/')[-1])
                self.QLineEdit_homeDirectory.setText('/'.join(directory[0].split('/')[:-1]))
        
    def QPushButtonStart_Pressed(self):
        if self.QPushButtonStart.text() == "Start Session...":
            self.signal_newsession.emit(self.QLineEdit_homeDirectory.text(), self.QLineEdit_folderName.text(), self.QCheckBox_saveTemperature.isChecked(), self.QCheckBox_savePressure.isChecked(), self.QCheckBox_ln2Mode.isChecked())
            self.QPushButtonStart.setText('Change session...')
            self.QPushButtonStart.setStyleSheet(self.styles['QPushButton_acquiring'])
            self.enable(False)
        else:
            reply = QMessageBox.question(self, 'Change Session?', 'This will stop the current session.\nDo you want to proceed?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.signal_stopsession.emit()
                self.QPushButtonStart.setText('Start Session...')
                self.QPushButtonStart.setStyleSheet(self.styles['QPushButton_idle'])
                self.enable(True)

    def QCheckBox_ln2Mode_Clicked(self):
        if self.QCheckBox_ln2Mode.isChecked():
            self.QCheckBox_saveTemperature.setChecked(False)
            self.QCheckBox_savePressure.setChecked(False)
        else:
            self.QCheckBox_saveTemperature.setChecked(True)
            self.QCheckBox_savePressure.setChecked(True)

    def enable(self, enabled=True):
        self.QPushButton_folderName.setEnabled(enabled)
        self.QPushButton_homeDirectory.setEnabled(enabled)
        self.QCheckBox_ln2Mode.setEnabled(enabled)
        self.QCheckBox_savePressure.setEnabled(enabled)
        self.QCheckBox_saveTemperature.setEnabled(enabled)
        self.QLineEdit_folderName.setEnabled(enabled)
        self.checkboxSetVoltageSign.setEnabled(enabled)

    def checkBoxSetVoltageSign_clicked(self):
        if self.checkboxSetVoltageSign.isChecked():
            self.setvoltagesign_signal.emit(-1)
        else:
            self.setvoltagesign_signal.emit(1)
