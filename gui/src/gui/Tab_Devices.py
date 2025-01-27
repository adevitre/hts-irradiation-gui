import os, subprocess
from PyQt5.QtGui import QKeySequence, QPixmap
from PyQt5.QtWidgets import QWidget, QCheckBox, QLineEdit, QVBoxLayout, QPlainTextEdit, QHBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QInputDialog, QShortcut, QPushButton, QComboBox, QLabel
from PyQt5.QtCore import pyqtSignal, Qt

from horizontalline import HorizontalLine
from configure import load_json

"""
    Tab_Devices is a submodule of the GUI containing GUI objects and functions
    needed to monitor serial communication with the devices.

    @author Alexis Devitre (devitre@mit.edu)
    @last-modified January 2025
""" 

HARDWARE_PARAMETERS = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
     
class Tab_Devices(QWidget):

    log_signal = pyqtSignal(str, str)
    test_signal = pyqtSignal(str)
    reset_signal = pyqtSignal()

    def __init__(self, parent=None):
        super(Tab_Devices, self).__init__(parent)
        self.parent = parent
        
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QWidgets
        
        self.vboxlayout_top = QVBoxLayout()
        self.vboxlayout_device_parameters = QVBoxLayout()
        hboxlayout_device_parameters = QHBoxLayout()
        hboxlayout_device_functions = QHBoxLayout()

        self.labelDeviceManuals = QLabel('Device Parameters and Manuals')
        self.labelDeviceManualsDescription = QLabel('Use this menu to adjust the serial and ethernet communication parameters of peripheral devices, and to conveniently access their user manuals.')
        self.labelDeviceManuals.setStyleSheet(self.styles['QLabel_Subtitle'])

        self.vboxlayout_top.addWidget(self.labelDeviceManuals)
        self.vboxlayout_top.addWidget(self.labelDeviceManualsDescription)
        self.vboxlayout_top.addWidget(HorizontalLine())
        
        self.device_image = QLabel(self)
        self.comboBoxName = QComboBox(self)
        self.comboBoxName.addItems([HARDWARE_PARAMETERS['devices'][key]['name'] for key in HARDWARE_PARAMETERS['devices'].keys()])

        self.pushButtonLoadManual = QPushButton('Open User Manual')
        self.pushButtonEditParameters = QPushButton('Edit Parameters')
        self.pushButtonTryConnection = QPushButton('Try Connection')
        self.label_tryconnection = QLabel('')

        hboxlayout_device_functions.addWidget(self.comboBoxName)
        hboxlayout_device_functions.addWidget(self.pushButtonLoadManual)
        hboxlayout_device_functions.addWidget(self.pushButtonTryConnection)
        hboxlayout_device_functions.addWidget(self.label_tryconnection)
        hboxlayout_device_functions.addStretch()
        hboxlayout_device_functions.addWidget(self.pushButtonEditParameters)

        hboxlayout_device_parameters.addStretch()
        hboxlayout_device_parameters.addWidget(self.device_image)
        hboxlayout_device_parameters.addStretch()
        
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
            hboxlayout = QHBoxLayout()  
            lineEdit.setMaximumWidth(400)
            lineEdit.setMinimumWidth(300)
            lineEdit.setAlignment(Qt.AlignRight)
            hboxlayout.addWidget(QLabel('{: <40}'.format(lineEditLabel)))
            hboxlayout.addStretch()
            hboxlayout.addWidget(lineEdit)
            self.vboxlayout_device_parameters.addLayout(hboxlayout)
            
        self.vboxlayout_device_parameters.addStretch()
        hboxlayout_device_parameters.addLayout(self.vboxlayout_device_parameters)

        self.vboxlayout_top.addLayout(hboxlayout_device_functions)
        self.vboxlayout_top.addLayout(hboxlayout_device_parameters)
        self.vboxlayout_top.addStretch()

        self.setLayout(self.vboxlayout_top)

        self.comboBoxName.currentTextChanged.connect(self.comboBoxName_selection_changed)
        self.comboBoxName.setCurrentIndex(0)
        self.pushButtonLoadManual.clicked.connect(lambda: self.openManual())
        self.pushButtonEditParameters.clicked.connect(lambda: self.editDeviceParameters())
        self.pushButtonTryConnection.clicked.connect(lambda: self.test_signal.emit(self.comboBoxName.currentText()))

        self.comboBoxName.setCurrentIndex(1) #Trigger this function once to set the device parameters according to the combobox

        labelShortcutsTitle = QLabel('List of shortcuts')
        labelShortcutsTitle.setStyleSheet(self.styles['QLabel_Subtitle'])
        labelShortcuts = QLabel('{: <30}\t{: <30}\n{: <30}\t{: <30}\n{: <30}\t{: <30}'.format('Ctrl+L', 'Add a note to the log', 'Ctrl+C', 'Calibrate 100 A current source', 'Ctrl(+Shift)+Tab', 'Switch tabs'))
        self.vboxlayout_top.addStretch()
        self.vboxlayout_top.addWidget(labelShortcutsTitle)
        self.vboxlayout_top.addWidget(HorizontalLine())
        self.vboxlayout_top.addWidget(labelShortcuts)
        self.vboxlayout_top.addStretch()

        self.enableDeviceParameters(False)

    def openManual(self):
        path_to_manual = HARDWARE_PARAMETERS['devices'][self.device_key]['manual']
        subprocess.run(['xdg-open', path_to_manual], check=True)

    def displayDeviceParameters(self):
        params = HARDWARE_PARAMETERS['devices'][self.device_key]

        # load the device parameters
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

        # load the device image
        device_pixmap = QPixmap(os.getcwd()+str(params['image']))
        self.device_image.setPixmap(device_pixmap)
        self.device_image.setMaximumHeight(300)
        self.device_image.setMaximumWidth(600)
        self.device_image.setScaledContents(True)

    def comboBoxName_selection_changed(self):
        for key in list(HARDWARE_PARAMETERS['devices'].keys()):
            if HARDWARE_PARAMETERS['devices'][key]['name'] == self.comboBoxName.currentText():
                self.device_key = key
        self.displayDeviceParameters()

    def displaySerialDeviceStatus(self, device, connected):
        if connected:
            self.label_tryconnection.setText('{} connected!'.format(device))
        else:
            self.label_tryconnection.setText('{} not connected!'.format(device))

    def checkBoxSetVoltageSign_clicked(self):
        if self.checkboxSetVoltageSign.isChecked():
            self.setvoltagesign_signal.emit(-1)
        else:
            self.setvoltagesign_signal.emit(1)
    
    def editDeviceParameters(self):
        if self.pushButtonEditParameters.text() == 'Edit Parameters':
            self.enableDeviceParameters(True)
            self.pushButtonEditParameters.setEnabled(True)
            self.pushButtonEditParameters.setText('Save/Cancel')
        else:
            self.enableDeviceParameters(False)
            self.pushButtonEditParameters.setEnabled(True)
            self.pushButtonEditParameters.setText('Edit Parameters')
    
    def enableDeviceParameters(self, enabled):
        self.lineEditUSBPort.setEnabled(enabled)
        self.lineEditBaudRate.setEnabled(enabled)
        self.lineEditByteSize.setEnabled(enabled)
        self.lineEditParity.setEnabled(enabled)
        self.lineEditStopBits.setEnabled(enabled)
        self.lineEditTimeout.setEnabled(enabled)
        self.lineEditFlowControl.setEnabled(enabled)
        self.lineEditEnding.setEnabled(enabled)
        self.lineEditGreeting.setEnabled(enabled)
        self.lineEditResponse.setEnabled(enabled)
        self.lineEditETHPort.setEnabled(enabled)