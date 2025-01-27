import os
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import QWidget, QCheckBox, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QShortcut, QPushButton, QComboBox, QLabel
from PyQt5.QtCore import pyqtSignal

from horizontalline import HorizontalLine
from configure import load_json

TEMPERATURE_CONTROLLER = 'LakeShore 336 Temperature Controller'
CURRENT_SOURCE = 'LakeShore 121 Current Source'
POWER_SUPPLY = 'Keithley 2231-A-30-3 Power Supply'
NANOVOLTMETER = 'Keithley 2182A Nanovoltmeter'
MULTIMETER = 'Keithley DMM6500 Digital Multimeter'
PRESSURE_CONTROLLER = 'Instrutech FlexRax 4000 Vacuum Gauge Controller'

"""
    Tab_Logbook is a submodule of the GUI containing GUI objects and functions
    needed to keep track of every step in the experiment.

    @author Alexis Devitre (devitre@mit.edu)
    @last-modified July 2024
""" 
class Tab_Logbook(QWidget):
    
    log_signal = pyqtSignal(str, str)
    reset_signal = pyqtSignal()

    def __init__(self, parent=None):
        super(Tab_Logbook, self).__init__(parent)
        self.parent = parent
        
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets

        vBoxLayout = QVBoxLayout(self)
        
        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(0)
        self.tableWidget.setColumnCount(3)
        self.tableWidget.setHorizontalHeaderLabels(['Time', 'Event', 'Comment'])
        self.tableWidget.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.tableWidget.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        
        self.labelSessionLog1 = QLabel('Session event log')
        self.labelSessionLog1.setStyleSheet(self.styles['QLabel_Subtitle'])
        self.labelSessionLog2 = QLabel('A copy of the log is automatically saved with the data')

        self.labelTroubleshooting = QLabel('Troubleshooting')
        self.labelTroubleshooting.setStyleSheet(self.styles['QLabel_Subtitle'])
        
        self.pushButtonResetQPS = QPushButton('Reset QPS')
        self.pushButtonResetQPS.clicked.connect(lambda: self.reset_signal.emit())

        self.qShortcut_addLogEntry = QShortcut(QKeySequence('Ctrl+L'), self)
        self.qShortcut_addLogEntry.activated.connect(lambda: self.manualLog())
        
        vBoxLayout.addWidget(self.labelSessionLog1)
        vBoxLayout.addWidget(self.labelSessionLog2)
        vBoxLayout.addWidget(HorizontalLine())
        vBoxLayout.addWidget(self.tableWidget, stretch=8)
        vBoxLayout.addWidget(self.labelTroubleshooting)
        vBoxLayout.addWidget(HorizontalLine())

        hBoxLayout = QHBoxLayout()
        hBoxLayout.addWidget(self.pushButtonResetQPS)
        vBoxLayout.addLayout(hBoxLayout)

    def manualLog(self):
        note, ok = QInputDialog.getText(self, 'Manual log entry', 'Input note then press OK                  ')
        if ok:
            self.log_signal.emit('Note', note)

    def addLogEntry(self, when, what, comment):
        self.tableWidget.insertRow(0)
        self.tableWidget.setItem(0, 0, QTableWidgetItem(when))
        self.tableWidget.setItem(0, 1, QTableWidgetItem(what))
        self.tableWidget.setItem(0, 2, QTableWidgetItem(comment))