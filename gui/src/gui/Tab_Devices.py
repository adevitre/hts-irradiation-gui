import os, subprocess
from PyQt5.QtGui import QKeySequence, QPixmap
from PyQt5.QtWidgets import QWidget, QCheckBox, QLineEdit, QVBoxLayout, QPlainTextEdit, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QShortcut, QPushButton, QComboBox, QLabel
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
        self.vBoxLayoutLeft.addWidget(self.deviceImage)

        self.plainTextEditDeviceDescription = QPlainTextEdit('The Lakeshore 121 Current Source is used to measure the critical temperature (Tc) and performed critical current (Ic) measurements of heavily damaged tapes. In the future, it could also serve to produce the Hall current of a magnetic field sensor.')
        self.vBoxLayoutLeft.addWidget(self.plainTextEditDeviceDescription)
        
        hBoxLayoutName = QHBoxLayout()
        self.labelName = QLabel('{: <40}'.format('Device:'))
        self.comboBoxName = QComboBox(self)
        self.comboBoxName.addItems(list(HARDWARE_PARAMETERS['devices'].keys()))
        self.pushButtonLoadManual = QPushButton('Open User Manual')
        
        hBoxLayoutName.addWidget(self.labelName)
        hBoxLayoutName.addWidget(self.comboBoxName)
        hBoxLayoutName.addStretch()
        hBoxLayoutName.addWidget(self.pushButtonLoadManual)
        self.vBoxLayoutLeft.addLayout(hBoxLayoutName)
        
        
        
        # Right panel widgets
        hBoxLayoutUSBPort = QHBoxLayout()
        self.labelUSBPort = QLabel('{: <40}'.format('USB Port:'))
        self.lineEditUSBPort = QLineEdit('/dev/ttyUSB0')
        hBoxLayoutUSBPort.addWidget(self.labelUSBPort)
        hBoxLayoutUSBPort.addStretch()
        hBoxLayoutUSBPort.addWidget(self.lineEditUSBPort)
        self.vBoxLayoutRight.addLayout(hBoxLayoutUSBPort)

        hBoxLayoutBaudRate = QHBoxLayout()
        self.labelBaudRate = QLabel('{: <40}'.format('Baud rate:'))
        self.lineEditBaudRate = QLineEdit('57600')
        hBoxLayoutBaudRate.addWidget(self.labelBaudRate)
        hBoxLayoutBaudRate.addStretch()
        hBoxLayoutBaudRate.addWidget(self.lineEditBaudRate)
        self.vBoxLayoutRight.addLayout(hBoxLayoutBaudRate)
        
        hBoxLayoutByteSize = QHBoxLayout()
        self.labelByteSize = QLabel('{: <40}'.format('Byte size:'))
        self.lineEditByteSize = QLineEdit('7')
        hBoxLayoutByteSize.addWidget(self.labelByteSize)
        hBoxLayoutByteSize.addStretch()
        hBoxLayoutByteSize.addWidget(self.lineEditByteSize)
        self.vBoxLayoutRight.addLayout(hBoxLayoutByteSize)

        hBoxLayoutParity = QHBoxLayout()
        self.labelParity = QLabel('{: <40}'.format('Parity:'))
        self.lineEditParity = QLineEdit('0')
        hBoxLayoutParity.addWidget(self.labelParity)
        hBoxLayoutParity.addStretch()
        hBoxLayoutParity.addWidget(self.lineEditParity)
        self.vBoxLayoutRight.addLayout(hBoxLayoutParity)

        hBoxLayoutStopBits = QHBoxLayout()
        self.labelStopBits = QLabel('{: <40}'.format('Stop bits:'))
        self.lineEditStopBits = QLineEdit('1')
        hBoxLayoutStopBits.addWidget(self.labelStopBits)
        hBoxLayoutStopBits.addStretch()
        hBoxLayoutStopBits.addWidget(self.lineEditStopBits)
        self.vBoxLayoutRight.addLayout(hBoxLayoutStopBits)

        hBoxLayoutTimeout = QHBoxLayout()
        self.labelTimeout = QLabel('{: <40}'.format('Timeout (s):'))
        self.lineEditTimeout = QLineEdit('1')
        hBoxLayoutTimeout.addWidget(self.labelTimeout)
        hBoxLayoutTimeout.addStretch()
        hBoxLayoutTimeout.addWidget(self.lineEditTimeout)
        self.vBoxLayoutRight.addLayout(hBoxLayoutTimeout)

        hBoxLayoutFlowControl = QHBoxLayout()
        self.labelFlowControl = QLabel('{: <40}'.format('Flow control (xonxoff):'))
        self.lineEditFlowControl = QLineEdit('false')
        hBoxLayoutFlowControl.addWidget(self.labelFlowControl)
        hBoxLayoutFlowControl.addStretch()
        hBoxLayoutFlowControl.addWidget(self.lineEditFlowControl)
        self.vBoxLayoutRight.addLayout(hBoxLayoutFlowControl)
        
        hBoxLayoutUSBPort = QHBoxLayout()
        self.labelUSBPort = QLabel('{: <40}'.format('USB Port:'))
        self.lineEditUSBPort = QLineEdit('/dev/ttyUSB0')
        hBoxLayoutUSBPort.addWidget(self.labelUSBPort)
        hBoxLayoutUSBPort.addStretch()
        hBoxLayoutUSBPort.addWidget(self.lineEditUSBPort)
        self.vBoxLayoutRight.addLayout(hBoxLayoutUSBPort)

        hBoxLayoutEnding = QHBoxLayout()
        self.labelEnding = QLabel('{: <40}'.format('Termination:'))
        self.lineEditEnding = QLineEdit('\\r\\n')
        hBoxLayoutEnding.addWidget(self.labelEnding)
        hBoxLayoutEnding.addStretch()
        hBoxLayoutEnding.addWidget(self.lineEditEnding)
        self.vBoxLayoutRight.addLayout(hBoxLayoutEnding)

        hBoxLayoutGreeting = QHBoxLayout()
        self.labelGreeting = QLabel('{: <40}'.format('Greeting:'))
        self.lineEditGreeting = QLineEdit('*IDN?')
        hBoxLayoutGreeting.addWidget(self.labelGreeting)
        hBoxLayoutGreeting.addStretch()
        hBoxLayoutGreeting.addWidget(self.lineEditGreeting)
        self.vBoxLayoutRight.addLayout(hBoxLayoutGreeting)

        hBoxLayoutResponse = QHBoxLayout()
        self.labelResponse = QLabel('{: <40}'.format('Greeting response:'))
        self.lineEditResponse = QLineEdit('LSCI,MODEL121')
        hBoxLayoutResponse.addWidget(self.labelResponse)
        hBoxLayoutResponse.addStretch()
        hBoxLayoutResponse.addWidget(self.lineEditResponse)
        self.vBoxLayoutRight.addLayout(hBoxLayoutResponse)
        
        hBoxLayoutETHPort = QHBoxLayout()
        self.labelETHPort = QLabel('{: <40}'.format('Ethernet Port:'))
        self.lineEditETHPort = QLineEdit('None')
        hBoxLayoutETHPort.addWidget(self.labelETHPort)
        hBoxLayoutETHPort.addStretch()
        hBoxLayoutETHPort.addWidget(self.lineEditETHPort)
        self.vBoxLayoutRight.addLayout(hBoxLayoutETHPort)

        self.pushButtonEditParameters = QPushButton('Edit Parameters')
        self.pushButtonTryConnection = QPushButton('Try Connection')
        
        self.pushButtonLoadManual.clicked.connect(lambda: self.openManual())

        self.hBoxLayoutButtons = QHBoxLayout()
        self.hBoxLayoutButtons.addWidget(self.pushButtonEditParameters)
        self.hBoxLayoutButtons.addWidget(self.pushButtonTryConnection)

        self.vBoxLayoutRight.addLayout(self.hBoxLayoutButtons)

        self.vBoxLayoutRight.addStretch()

        self.hBoxLayout.addLayout(self.vBoxLayoutLeft)
        self.hBoxLayout.addLayout(self.vBoxLayoutRight)
        self.vBoxLayoutTop.addLayout(self.hBoxLayout)
        self.setLayout(self.vBoxLayoutTop)
        
    def openManual(self):
        path_to_manual = HARDWARE_PARAMETERS['devices'][self.comboBoxName.currentText]['manual']
        subprocess.run(['xdg-open', path_to_manual], check=True)

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