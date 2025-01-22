import os, subprocess
from PyQt5.QtGui import QKeySequence, QPixmap
from PyQt5.QtWidgets import QWidget, QCheckBox, QLineEdit, QVBoxLayout, QPlainTextEdit, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QShortcut, QPushButton, QComboBox, QLabel
from PyQt5.QtCore import pyqtSignal, Qt

from horizontalline import HorizontalLine
from configure import load_json

TEMPERATURE_CONTROLLER = 'LakeShore 336 Temperature Controller'
CURRENT_SOURCE = 'LakeShore 121 Current Source'
POWER_SUPPLY = 'Keithley 2231-A-30-3 Power Supply'
NANOVOLTMETER = 'Keithley 2182A Nanovoltmeter'
MULTIMETER = 'Keithley DMM6500 Digital Multimeter'
PRESSURE_CONTROLLER = 'Instrutech FlexRax 4000 Vacuum Gauge Controller'

"""
    Tab_Devices is a submodule of the GUI containing GUI objects and functions
    needed to monitor serial communication with the devices.

    @author Alexis Devitre (devitre@mit.edu)
    @last-modified July 2024
""" 

HARDWARE_PARAMETERS = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
     
class Tab_Devices(QWidget):
    
    log_signal = pyqtSignal(str, str)
    test_signal = pyqtSignal(str)
    setvoltagesign_signal = pyqtSignal(int)
    reset_signal = pyqtSignal()

    def __init__(self, parent=None):
        super(Tab_Devices, self).__init__(parent)
        self.parent = parent
        
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QWidgets
        
        default_device = '/home/htsirradiation/Documents/hts-irradiation-gui/gui/images/devices/LS121.png'

        self.vBoxLayoutTop = QVBoxLayout()
        self.vBoxLayoutLeft = QVBoxLayout()
        self.vBoxLayoutRight = QVBoxLayout()
        self.hBoxLayout = QHBoxLayout()
        
        self.labelDeviceManuals = QLabel('Device Parameters and Manuals')
        self.labelDeviceManualsDescription = QLabel('Use this menu to adjust the serial and ethernet communication parameters of peripheral devices, and to conveniently access their user manuals.')
        self.labelDeviceManuals.setStyleSheet(self.styles['QLabel_Subtitle'])

        self.vBoxLayoutTop.addWidget(self.labelDeviceManuals)
        self.vBoxLayoutTop.addWidget(self.labelDeviceManualsDescription)
        self.vBoxLayoutTop.addWidget(HorizontalLine())
        
        # Left panel widgets
        self.deviceImage = QLabel(self)
        self.deviceImage.setPixmap(QPixmap('/home/htsirradiation/Documents/hts-irradiation-gui/gui/images/devices/LS121.png'))
        self.vBoxLayoutLeft.addStretch()
        self.vBoxLayoutLeft.addWidget(self.deviceImage)
        self.vBoxLayoutLeft.addStretch()

        # Right panel widgets

        hBoxLayoutName = QHBoxLayout()
        self.comboBoxName = QComboBox(self)
        self.comboBoxName.addItems([HARDWARE_PARAMETERS['devices'][key]['name'] for key in HARDWARE_PARAMETERS['devices'].keys()])

        self.pushButtonLoadManual = QPushButton('Open User Manual')
        self.pushButtonEditParameters = QPushButton('Edit Parameters')
        self.pushButtonTryConnection = QPushButton('Try Connection')
        self.plainTextEditDeviceDescription = QPlainTextEdit()
        
        hBoxLayoutName.addWidget(self.comboBoxName)
        hBoxLayoutName.addWidget(self.pushButtonLoadManual)
        hBoxLayoutName.addStretch()
        hBoxLayoutName.addWidget(self.pushButtonEditParameters)
        hBoxLayoutName.addWidget(self.pushButtonTryConnection)

        self.vBoxLayoutRight.addLayout(hBoxLayoutName)
        self.vBoxLayoutRight.addWidget(self.plainTextEditDeviceDescription)

        self.lineEditUSBPort = QLineEdit()
        self.lineEditBaudRate = QLineEdit()
        self.lineEditByteSize = QLineEdit()
        self.lineEditParity = QLineEdit()
        self.lineEditStopBits = QLineEdit()
        self.lineEditTimeout = QLineEdit()
        self.lineEditFlowControl = QLineEdit()
        self.lineEditEnding = QLineEdit()
        self.lineEditGreeting = QLineEdit()
        self.lineEditResponse = QLineEdit()
        self.lineEditETHPort = QLineEdit()
        
        self.lineEdits = [
            self.lineEditUSBPort,
            self.lineEditETHPort,  
            self.lineEditEnding, 
            self.lineEditBaudRate,
            self.lineEditByteSize, 
            self.lineEditStopBits,
            self.lineEditParity, 
            self.lineEditFlowControl, 
            self.lineEditTimeout,
            self.lineEditGreeting,
            self.lineEditResponse
        ]

        lineEditLabels = [
            'USB Port:',
            'Ethernet Port:',
            'Termination:',
            'Baud rate:',
            'Byte size:',
            'Stop bits:',
            'Parity:',
            'Flow control (xonxoff):',
            'Timeout (s):',
            'Greeting:',
            'Greeting response:'
        ]
        for lineEdit, lineEditLabel in zip(self.lineEdits, lineEditLabels):
            hBoxLayout = QHBoxLayout()  
            lineEdit.setMaximumWidth(200)
            lineEdit.setMinimumWidth(200)
            lineEdit.setAlignment(Qt.AlignRight)
            hBoxLayout.addWidget(QLabel('{: <40}'.format(lineEditLabel)))
            hBoxLayout.addStretch()
            hBoxLayout.addWidget(lineEdit)
            self.vBoxLayoutRight.addLayout(hBoxLayout)
            
        self.vBoxLayoutRight.addStretch()

        self.hBoxLayout.addLayout(self.vBoxLayoutLeft)
        self.hBoxLayout.addLayout(self.vBoxLayoutRight)
        self.vBoxLayoutTop.addLayout(self.hBoxLayout)
        self.setLayout(self.vBoxLayoutTop)
        
        self.comboBoxName.currentTextChanged.connect(self.comboBoxName_selection_changed)
        self.pushButtonLoadManual.clicked.connect(lambda: self.openManual())
        self.comboBoxName.setCurrentIndex(1) #Trigger this function once to set the device parameters according to the combobox

    def openManual(self):
        path_to_manual = HARDWARE_PARAMETERS['devices'][self.device_key]['manual']
        subprocess.run(['xdg-open', path_to_manual], check=True)

    def displayDeviceParameters(self):
        params = HARDWARE_PARAMETERS['devices'][self.device_key]
        self.lineEditBaudRate.setText(str(params['baudrate']))
        self.lineEditByteSize.setText(str(params['bytesize']))
        self.lineEditEnding.setText(str(params['ending']))
        self.lineEditETHPort.setText(str(params['ethernet_port']))
        self.lineEditFlowControl.setText(str(params['xonxoff']))
        self.lineEditGreeting.setText(str(params['greeting']))
        self.lineEditParity.setText(str(params['parity']))
        self.lineEditResponse.setText(str(params['response']))
        self.lineEditStopBits.setText(str(params['stopbits']))
        self.lineEditTimeout.setText(str(params['timeout']))
        self.lineEditUSBPort.setText(str(params['port']))

    def comboBoxName_selection_changed(self):
        for key in list(HARDWARE_PARAMETERS['devices'].keys()):
            if HARDWARE_PARAMETERS['devices'][key]['name'] == self.comboBoxName.currentText():
                self.device_key = key
        self.displayDeviceParameters()

    def displaySerialDeviceStatus(self, device, connected):
        if connected:
            self.labelTestConnection.setText('{} connected!'.format(device))
        else:
            self.labelTestConnection.setText('{} not connected!'.format(device))

    def checkBoxSetVoltageSign_clicked(self):
        if self.checkboxSetVoltageSign.isChecked():
            self.setvoltagesign_signal.emit(-1)
        else:
            self.setvoltagesign_signal.emit(1)