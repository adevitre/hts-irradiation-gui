import os, subprocess, numpy
from scipy import constants
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QWidget, QCheckBox, QLineEdit, QVBoxLayout, QHBoxLayout, QMessageBox, QPushButton, QComboBox, QLabel, QDoubleSpinBox
from PyQt5.QtCore import pyqtSignal, Qt

from horizontalline import HorizontalLine
from configure import load_json, update_json

"""
    Tab_Devices is a submodule of the GUI containing GUI objects and functions
    needed to monitor serial communication with the devices.

    @author Alexis Devitre (devitre@mit.edu)
    @last-modified January 2025
""" 

     
class Tab_Devices(QWidget):

    log_signal = pyqtSignal(str, str)
    test_signal = pyqtSignal(str)
    reset_signal = pyqtSignal()
    reconnect_signal = pyqtSignal(str)

    hardware_parameters = load_json(fname='hwparams.json', location=os.getcwd()+'/config')

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
        self.comboBoxName.addItems([self.hardware_parameters['devices'][key]['name'] for key in self.hardware_parameters['devices'].keys()])

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

        labelShortcutsTitle = QLabel('Irradiation calculator')
        labelShortcutsTitle.setStyleSheet(self.styles['QLabel_Subtitle'])
        self.vboxlayout_top.addStretch()
        self.vboxlayout_top.addWidget(labelShortcutsTitle)
        self.vboxlayout_top.addWidget(HorizontalLine())

        hboxlayout_calculator = QHBoxLayout()

        self.label_collimator = QLabel('Collimator diameter [mm]')
        self.label_flux = QLabel('Beam current [nA]')
        self.label_charge = QLabel('Ion charge')
        self.label_fluence = QLabel('Target fluence [10e19 ions/m2]')

        self.doublespinbox_collimator = QDoubleSpinBox()
        self.doublespinbox_collimator.setValue(3.175)
        
        self.doublespinbox_flux = QDoubleSpinBox()
        self.doublespinbox_flux.setValue(30.0)
        self.doublespinbox_flux.setMaximum(10000.0)

        self.doublespinbox_charge = QDoubleSpinBox()
        self.doublespinbox_charge.setValue(1)

        self.doublespinbox_fluence = QDoubleSpinBox()
        self.doublespinbox_fluence.setValue(5)
        
        self.checkbox_calculator = QCheckBox('Time (Fluence)')
        self.checkbox_calculator.setChecked(True)
        self.checkbox_calculator.clicked.connect(self.calculator_switched)

        self.label_answer = QLabel('')
        
        calculator_widgets = [self.label_collimator, self.doublespinbox_collimator, self.label_flux, self.doublespinbox_flux, self.label_charge, self.doublespinbox_charge, self.label_fluence, self.doublespinbox_fluence]
        calculator_decimals = [None, 3, None, 2, None, 0, None, 2]
        for widget, decimals in zip(calculator_widgets, calculator_decimals):
            hboxlayout_calculator.addWidget(widget)
            if type(widget) != type(QLabel('')):
                widget.valueChanged.connect(self.recalculate)
                widget.setDecimals(decimals)
        
        self.vboxlayout_top.addLayout(hboxlayout_calculator)
        self.vboxlayout_top.addWidget(self.label_answer)
        self.vboxlayout_top.addStretch()

        self.enableDeviceParameters(False)

    def openManual(self):
        path_to_manual = self.hardware_parameters['devices'][self.device_key]['manual']
        subprocess.run(['xdg-open', path_to_manual], check=True)

    def displayDeviceParameters(self):
        params = self.hardware_parameters['devices'][self.device_key]

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
        for key in list(self.hardware_parameters['devices'].keys()):
            if self.hardware_parameters['devices'][key]['name'] == self.comboBoxName.currentText():
                self.device_key = key
        self.displayDeviceParameters()

    def displaySerialDeviceStatus(self, device, connected):
        if connected:
            self.label_tryconnection.setText('{} connected!'.format(device))
        else:
            reply = QMessageBox.question(self, 'Reconnect device?', 'Would you like to try to reconnect this device?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.reconnect_signal.emit(self.device_key)
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
            reply = QMessageBox.question(self, 'Save new parameters?', 'Would you like to save the new parameters?', QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                data = load_json(fname='hwparams.json', location='config')
                data['devices'][self.device_key]['baudrate'] = int(self.lineEditBaudRate.text())
                data['devices'][self.device_key]['bytesize'] = int(self.lineEditByteSize.text())
                data['devices'][self.device_key]['ending'] = self.lineEditEnding.text()
                data['devices'][self.device_key]['ethernet_port'] = int(self.lineEditETHPort.text())
                data['devices'][self.device_key]['xonxoff'] = bool(self.lineEditFlowControl.text())
                data['devices'][self.device_key]['greeting'] = self.lineEditGreeting.text()
                data['devices'][self.device_key]['parity'] = self.lineEditParity.text()
                data['devices'][self.device_key]['response'] = self.lineEditResponse.text()
                data['devices'][self.device_key]['stopbits'] = int(self.lineEditStopBits.text())
                data['devices'][self.device_key]['timeout'] = int(self.lineEditTimeout.text())
                data['devices'][self.device_key]['port'] = self.lineEditUSBPort.text()
                update_json(data, fname='hwparams.json', location='config')
                self.hardware_parameters = load_json(fname='hwparams.json', location=os.getcwd()+'/config') # FUTURE FIX ADVISORY -- This should be a global variable. Although updating it won't ahve any effect in other contexts which use these data, it's not very elegant programming.
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

    def recalculate(self):
        flux = self.doublespinbox_flux.value()*1e-9
        area = constants.pi*(1e-3*self.doublespinbox_collimator.value()/2)**2
        charge = constants.elementary_charge*self.doublespinbox_charge.value()
    
        if self.checkbox_calculator.isChecked(): # User wants time from fluence
            target_fluence = self.doublespinbox_fluence.value()*1e19
            time = target_fluence*charge*area/flux
            hours = numpy.floor(time/3600)
            minutes = numpy.floor((time-3600*hours)/60)
            seconds = time-3600*hours-60*minutes
            result = 'Irradiate for {:>4.0f} hours {:>4.0f} minutes {:>4.0f} seconds'.format(hours, minutes, seconds)
        else:
            time = self.doublespinbox_fluence.value()
            fluence = time*flux/(charge*area)
            result = 'The fluence accumulated after {:<10.0f} seconds at {:<4.2f} nA is {:4.2e} ions/m2'.format(time, flux, fluence)

        self.label_answer.setText(result)

    def calculator_switched(self):
        if self.checkbox_calculator.isChecked(): # User wants time from fluence
            self.label_fluence.setText('Fluence [1e19 ions/m2]')
            self.doublespinbox_fluence.setValue(5)
            self.doublespinbox_fluence.setDecimals(2)
        else:
            self.label_fluence.setText('Time [s]')
            self.doublespinbox_fluence.setValue(1800)
            self.doublespinbox_fluence.setDecimals(0)
