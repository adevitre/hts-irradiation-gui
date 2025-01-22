from PyQt5 import QtCore, QtWidgets
from PyQt5.QtWidgets import QDesktopWidget, QMainWindow, QApplication, QPlainTextEdit, QPushButton, QWidget, QLabel, QMessageBox, QFileDialog
from PyQt5.QtGui import QIcon, QWindow
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.uic import loadUi
import logging
from GetDirWindow import launchWindow
import os, shutil
from datetime import datetime
from configure import load_json

class NewSessionWindow(QWidget):

    ok = pyqtSignal(str, str, str, bool, bool, bool)
    
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            if self.QPushButtonOk.hasFocus():
                self.QPushButtonOk_Pressed()
            elif self.QPushButtonCancel.hasFocus():
                self.close()

    def __init__(self, parent = None, default_directory='/home/htsirradiation/Documents/data'):
        super(NewSessionWindow, self).__init__(parent)
        styles = load_json(fname='styles.json')            # stylesheets for QtWidgets
        
        self.setGeometry(100, 100, 500, 325)               # x, y, width, height
        QGridLayout = QtWidgets.QGridLayout(self)
        
        self.default_directory = default_directory
        
        #home directory and name
        self.QLineEdit_homeDirectory = QtWidgets.QLineEdit(self)
        self.QLineEdit_homeDirectory.setEnabled(False)
        self.QLineEdit_homeDirectory.setText(default_directory)
        QPushButton_homeDirectory = QtWidgets.QPushButton(self)
        QPushButton_homeDirectory.setText("Select home directory")
        QPushButton_homeDirectory.clicked.connect(lambda:self.launch_GetDirWindow())
        
        #folder name 
        self.QLineEdit_folderName = QtWidgets.QLineEdit(self)
        self.QLineEdit_folderName.setText('_temp')
        QPushButton_folderName = QtWidgets.QPushButton(self)
        QPushButton_folderName.setText("Overwrite folder")
        QPushButton_folderName.clicked.connect(lambda: self.launch_GetFolWindow())
        
        # description
        self.QPlainTextEdit_description = QtWidgets.QPlainTextEdit(self)
        self.QPlainTextEdit_description.setPlaceholderText('What experiments are you conducting today?')
        
        # description
        self.QCheckBox_saveTemperature = QtWidgets.QCheckBox('Save time trace of temperature', self)
        self.QCheckBox_saveTemperature.setChecked(True)
        self.QCheckBox_savePressure = QtWidgets.QCheckBox('Save time trace of pressure', self)
        self.QCheckBox_savePressure.setChecked(True)
        self.QCheckBox_ln2Mode = QtWidgets.QCheckBox('LN2 mode', self)
        self.QCheckBox_ln2Mode.clicked.connect(lambda: self.QCheckBox_ln2Mode_Clicked())
        
        # cancel and start new session buttons
        self.QPushButtonCancel = QtWidgets.QPushButton(self)
        self.QPushButtonCancel.setText("Cancel")
        self.QPushButtonCancel.clicked.connect(lambda:self.QPushButtonCancel_Pressed())
        self.QPushButtonOk = QtWidgets.QPushButton(self)
        self.QPushButtonOk.setStyleSheet(styles['QPushButton_idle'])
        self.QPushButtonOk.setText("Ready to roll!")
        self.QPushButtonOk.clicked.connect(lambda:self.QPushButtonOk_Pressed())
        self.QPushButtonOk.setFocus()
        
        QGridLayout.addWidget(self.QLineEdit_homeDirectory, 0, 0, 1, 3)
        QGridLayout.addWidget(QPushButton_homeDirectory, 0, 3, 1, 2)
        
        QGridLayout.addWidget(self.QLineEdit_folderName, 1, 0, 1, 3)
        QGridLayout.addWidget(QPushButton_folderName, 1, 3, 1, 2)
        
        QGridLayout.addWidget(self.QPlainTextEdit_description, 3, 0, 5, 5)

        QGridLayout.addWidget(self.QCheckBox_saveTemperature, 8, 0, 1, 1)
        QGridLayout.addWidget(self.QCheckBox_savePressure, 8, 1, 1, 1)
        QGridLayout.addWidget(self.QCheckBox_ln2Mode, 8, 2, 1, 1)
        
        QGridLayout.addWidget(self.QPushButtonOk, 9, 0, 1, 4)
        QGridLayout.addWidget(self.QPushButtonCancel, 9, 4, 1, 1)
        
        #window setup
        self.setWindowTitle("Start new session")
        resolution = QDesktopWidget().screenGeometry()
        self.move(int((resolution.width()-self.frameSize().width())/2), int((resolution.height()-self.frameSize().height())/2))
            
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
        
    def QPushButtonCancel_Pressed(self):
        self.ok.emit(None, None, None, False, False, False)
        self.close()
        
    def QPushButtonOk_Pressed(self):
        try:
            folderName = self.QLineEdit_folderName.text()
            newDirectory = self.QLineEdit_homeDirectory.text()
            self.ok.emit(newDirectory, folderName, self.QPlainTextEdit_description.toPlainText(), self.QCheckBox_saveTemperature.isChecked(), self.QCheckBox_savePressure.isChecked(), self.QCheckBox_ln2Mode.isChecked())
            self.close()
        except Exception as e:
            print(e)

    def QCheckBox_ln2Mode_Clicked(self):
        if self.QCheckBox_ln2Mode.isChecked():
            self.QCheckBox_saveTemperature.setChecked(False)
            self.QCheckBox_savePressure.setChecked(False)