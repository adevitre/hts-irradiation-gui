import os, numpy, time

from PyQt5.QtWidgets import QWidget, QCheckBox, QGridLayout, QVBoxLayout, QHBoxLayout, QLabel, QDoubleSpinBox, QPushButton, QApplication, QShortcut, QComboBox, QMessageBox, QRadioButton, QButtonGroup
from PyQt5.QtGui import QFont, QIcon, QKeySequence
from PyQt5.QtCore import pyqtSignal, Qt, QSize

from hoverbutton import HoverButton
from horizontalline import HorizontalLine
from configure import load_json

ID_SENSOR_A = 1
ID_SENSOR_B = 2
ID_SENSOR_C = 3
ID_SENSOR_D = 4

class LIFT1_Sidebar(QWidget):
    
    sensorset_signal = pyqtSignal(str) 
    cryoset_signal = pyqtSignal(bool)
    gateopen_signal = pyqtSignal(bool)
    warmup_signal = pyqtSignal()
    chamberlight_signal = pyqtSignal(bool)
    targetlight_signal = pyqtSignal(bool)
    settemp_signal = pyqtSignal(float)
    faradaycup_signal = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super(LIFT1_Sidebar, self).__init__(parent)
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets

        self.chamberLightOn = False
        self.targetLightOn = False
        self.faradayCupInserted = True
        self.cooling = False

        verticalLayoutSideBar = QVBoxLayout()
        verticalLayoutSideBar.insertSpacing(0, 25)
        verticalLayoutSideBar.setSpacing(25)
        
        # TpQ side info
        self.labelHeaterPower = QLabel(self)
        self.labelPressure = QLabel(self)
        self.labelSampleTemperature = QRadioButton(self)
        self.labelTargetTemperature = QRadioButton(self)
        self.labelHolderTemperature = QRadioButton(self)
        self.labelSpareTemperature = QRadioButton(self)
        self.labelShorcuts = QLabel(self)

        self.labelHeaterPower.setStyleSheet('color: black; font-size: 20px;')
        self.labelPressure.setStyleSheet('color: forestgreen; font-size: 20px;')

        self.labelSampleTemperature.setStyleSheet('QRadioButton {background-color: rgba(255, 255, 255, 0); color: blue; font-size: 20px}') # QRadioButton needs background color for foreground color to work
        self.labelTargetTemperature.setStyleSheet('QRadioButton {background-color: rgba(255, 255, 255, 0); color: red; font-size: 20px}')
        self.labelHolderTemperature.setStyleSheet('QRadioButton {background-color: rgba(255, 255, 255, 0); color: forestgreen; font-size: 20px}')
        self.labelSpareTemperature.setStyleSheet('QRadioButton {background-color: rgba(255, 255, 255, 0); color: purple; font-size: 20px}')
        self.labelShorcuts.setStyleSheet('color: black; font-size: 15px;')

        self.selectPIDSensorGroup = QButtonGroup()
        self.selectPIDSensorGroup.buttonClicked.connect(lambda: self.setPIDSensor())
        self.selectPIDSensorGroup.setExclusive(True)
        self.selectPIDSensorGroup.addButton(self.labelSampleTemperature)
        self.selectPIDSensorGroup.addButton(self.labelTargetTemperature)
        self.selectPIDSensorGroup.addButton(self.labelHolderTemperature)
        self.selectPIDSensorGroup.addButton(self.labelSpareTemperature)
        self.selectPIDSensorGroup.setId(self.labelSampleTemperature, ID_SENSOR_A)
        self.selectPIDSensorGroup.setId(self.labelTargetTemperature, ID_SENSOR_B)
        self.selectPIDSensorGroup.setId(self.labelHolderTemperature, ID_SENSOR_C)
        self.selectPIDSensorGroup.setId(self.labelSpareTemperature, ID_SENSOR_D)
        
        self.labelTargetTemperature.setChecked(True)

        spb_font = QFont()
        spb_font.setPointSize(22)
        spb_font.setBold(True)
        spb_font.setWeight(75)
        
        self.QDoubleSpinBox_setTemperature = QDoubleSpinBox(self)
        self.QDoubleSpinBox_setTemperature.setDecimals(2)
        self.QDoubleSpinBox_setTemperature.setRange(0, 320)
        self.QDoubleSpinBox_setTemperature.setButtonSymbols(QDoubleSpinBox.NoButtons)
        self.QDoubleSpinBox_setTemperature.setAlignment(Qt.AlignCenter)
        self.QDoubleSpinBox_setTemperature.setFont(spb_font)
        self.QDoubleSpinBox_setTemperature.setEnabled(False)

        self.pushButtonSetTemperature = QPushButton("Set temperature")
        self.pushButtonSetTemperature.clicked.connect(lambda: self.settemp_signal.emit(self.QDoubleSpinBox_setTemperature.value()))
        self.pushButtonSetTemperature.setStyleSheet(self.styles['QPushButton_simulation'])
        self.pushButtonSetTemperature.setShortcut('Ctrl+Return')
        self.pushButtonSetTemperature.setEnabled(False)
        self.pushButtonSetTemperature.setStyleSheet(self.styles['QPushButton_disable'])
        
        self.pushButtonFaradayCup = QPushButton()
        self.pushButtonFaradayCup.clicked.connect(self.pushButtonFaradayCup_clicked)
        self.pushButtonFaradayCup.setIcon(QIcon(os.getcwd()+'/images/BeamOff.png'))
        self.pushButtonFaradayCup.setStyleSheet(self.styles['QPushButton_icon'])
        self.pushButtonFaradayCup.setIconSize(QSize(100, 100))

        self.pushButtonCompressor = QPushButton()
        self.pushButtonCompressor.clicked.connect(self.pushButtonCompressor_clicked)
        self.pushButtonCompressor.setIcon(QIcon(os.getcwd()+'/images/notcooling.png'))
        self.pushButtonCompressor.setStyleSheet(self.styles['QPushButton_icon'])
        self.pushButtonCompressor.setIconSize(QSize(100, 100))

        self.pushButtonWarmup = HoverButton('', os.getcwd()+'/images/warmup-idle.png', os.getcwd()+'/images/warmup-hover.png')
        self.pushButtonWarmup.clicked.connect(self.warmup_signal.emit)
        self.pushButtonWarmup.setStyleSheet(self.styles['QPushButton_icon'])
        self.pushButtonWarmup.setIconSize(QSize(100, 100))
        self.pushButtonWarmup.setEnabled(False)
        
        self.pushButtonTargetLight = QPushButton()
        self.pushButtonTargetLight.clicked.connect(self.pushButtonTargetLight_clicked)
        self.pushButtonTargetLight.setIcon(QIcon(os.getcwd()+'/images/light-off.png'))
        self.pushButtonTargetLight.setStyleSheet(self.styles['QPushButton_icon'])
        self.pushButtonTargetLight.setIconSize(QSize(100, 100))
        self.pushButtonTargetLight.setEnabled(False)

        self.pushButtonChamberLight = QPushButton()
        self.pushButtonChamberLight.clicked.connect(self.pushButtonChamberLight_clicked)
        self.pushButtonChamberLight.setIcon(QIcon(os.getcwd()+'/images/light-off.png'))
        self.pushButtonChamberLight.setStyleSheet(self.styles['QPushButton_icon'])
        self.pushButtonChamberLight.setIconSize(QSize(100, 100))
        self.pushButtonChamberLight.setEnabled(False)

        self.comboBoxSetTurboValve = QComboBox(self)
        self.comboBoxSetTurboValve.addItems(["Turbo valve closed", "Turbo valve opened"])
        self.comboBoxSetTurboValve.activated.connect(self.comboBoxSetTurboValve_activated)
        self.comboBoxSetTurboValve.setEnabled(True)
        
        self.labelShorcuts.setText('Shortcut list\n\n{: <30}\t{: <30}\n{: <30}\t{: <30}\n{: <30}\t{: <30}\n{: <30}\t{: <30}'.format('Ctrl+L', 'Add a note to the log', 'Ctrl+N', 'Start New Session', 'Ctrl+C', 'Calibrate 100 A current source', 'Ctrl(+Shift)+Tab', 'Switch tabs'))

        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(self.QDoubleSpinBox_setTemperature)
        horizontalLayout.addWidget(self.pushButtonSetTemperature)
        verticalLayoutSideBar.addLayout(horizontalLayout)
        
        verticalLayoutSideBar.addWidget(HorizontalLine())
        verticalLayoutSideBar.addWidget(self.labelSampleTemperature)
        verticalLayoutSideBar.addWidget(self.labelHolderTemperature)
        verticalLayoutSideBar.addWidget(self.labelTargetTemperature)
        verticalLayoutSideBar.addWidget(self.labelSpareTemperature)
        
        verticalLayoutSideBar.addWidget(HorizontalLine())
        verticalLayoutSideBar.addWidget(self.labelHeaterPower)
        
        verticalLayoutSideBar.addWidget(HorizontalLine())
        verticalLayoutSideBar.addWidget(self.labelPressure)
        
        verticalLayoutSideBar.addWidget(HorizontalLine())
        horizontalLayout2 = QHBoxLayout()
        horizontalLayout2.addStretch()
        horizontalLayout2.addWidget(self.pushButtonFaradayCup)
        horizontalLayout2.addWidget(self.pushButtonCompressor)
        horizontalLayout2.addWidget(self.pushButtonWarmup)
        horizontalLayout2.addStretch()
        verticalLayoutSideBar.addLayout(horizontalLayout2)
        
        horizontalLayout3 = QHBoxLayout()
        horizontalLayout3.addStretch()
        horizontalLayout3.addWidget(self.pushButtonTargetLight)
        horizontalLayout3.addWidget(self.pushButtonChamberLight)
        horizontalLayout3.addWidget(self.comboBoxSetTurboValve)
        horizontalLayout3.addStretch()
        verticalLayoutSideBar.addLayout(horizontalLayout3)

        verticalLayoutSideBar.addStretch()
        verticalLayoutSideBar.addWidget(HorizontalLine())
        verticalLayoutSideBar.addWidget(self.labelShorcuts)
        
        self.setLayout(verticalLayoutSideBar)
        
        self.qShortcut_setTemperature = QShortcut(QKeySequence('Enter'), self)
        self.qShortcut_setTemperature.activated.connect(lambda: self.qShortcut_setTemperature_triggered())

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            if self.QDoubleSpinBox_setTemperature.hasFocus():
                self.settemp_signal.emit(self.QDoubleSpinBox_setTemperature.value())
                self.QDoubleSpinBox_setTemperature.clearFocus()

    def updateSetpointDisplay(self, value):
        if not self.QDoubleSpinBox_setTemperature.hasFocus():
            self.QDoubleSpinBox_setTemperature.setValue(value)       
    
    def qShortcut_setTemperature_triggered(self):
        self.QDoubleSpinBox_setTemperature.setFocus()
            
    def pushButtonFaradayCup_clicked(self):
        self.setControl(which='faradaycup', value=(not self.faradayCupInserted))
        self.faradaycup_signal.emit(self.faradayCupInserted)
        
    def pushButtonCompressor_clicked(self):
        if self.cooling:
            self.setControl(which='cryocooler', value=0)
        else:
            self.setControl(which='cryocooler', value=1)
        self.cryoset_signal.emit(self.cooling)

    def comboBoxSetTurboValve_activated(self):
        if self.comboBoxSetTurboValve.currentText() == 'Turbo valve opened':
            reply = QMessageBox.question(self, 'Open turbo pump to chamber?', 'Is the pressure low enough to open the turbo to the chamber?\nRecommended pressure < 150 mTorr.', QMessageBox.Yes | QMessageBox.Abort, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                self.gateopen_signal.emit(True)
            elif self.gvStateOpened:
                self.comboBoxSetTurboValve.setCurrentIndex(1)
            else:
                self.comboBoxSetTurboValve.setCurrentIndex(0)
        else:
            self.gateopen_signal.emit(False)
    
    def setPIDSensor(self):
        if self.selectPIDSensorGroup.checkedId() == ID_SENSOR_A:
            self.sensorset_signal.emit('A')
        elif self.selectPIDSensorGroup.checkedId() == ID_SENSOR_B:
            self.sensorset_signal.emit('B')
        elif self.selectPIDSensorGroup.checkedId() == ID_SENSOR_C:
            self.sensorset_signal.emit('C')
        elif self.selectPIDSensorGroup.checkedId() == ID_SENSOR_D:
            self.sensorset_signal.emit('D')

    def setControl(self, which, value):
        '''
            setControl is used by LIFT1_GUI to initialize the combo boxes in the environment tab
            
            INPUTS
            ------
            which - (str) cryocooler | turbovalve
            value - (int) index of the label corresponding to the state of the device  
        '''
        if which == 'cryocooler':
            if value == 0:
                self.cooling = False
                self.pushButtonCompressor.setIcon(QIcon(os.getcwd()+'/images/notcooling.png'))
            else:
                self.cooling = True
                self.pushButtonCompressor.setIcon(QIcon(os.getcwd()+'/images/cooling.png'))

        elif which == 'turbovalve':
            self.comboBoxSetTurboValve.setCurrentIndex(value)
            if value == 0:
                self.gvStateOpened = True
            else:
                self.gvStateOpened = False
        
        elif which == 'faradaycup':
            if value == 0: 
                self.faradayCupInserted = False # relay is 0 if cup is retracted
                self.pushButtonFaradayCup.setIcon(QIcon(os.getcwd()+'/images/BeamOn.png'))
            else: 
                self.faradayCupInserted = True # relay is 1 if cup is inserted
                self.pushButtonFaradayCup.setIcon(QIcon(os.getcwd()+'/images/BeamOff.png'))
        
        elif which == 'pidsensor':
            if value == ID_SENSOR_A:
                self.labelSampleTemperature.setChecked(True)
            elif value == ID_SENSOR_B:
                self.labelTargetTemperature.setChecked(True)
            elif value == ID_SENSOR_C:
                self.labelHolderTemperature.setChecked(True)
            elif value == ID_SENSOR_D:
                self.labelSpareTemperature.setChecked(True)
        
        elif which == 'chamberlight':
            if value == 0:
                self.chamberLightOn = False
                self.pushButtonChamberLight.setIcon(QIcon(os.getcwd()+'/images/light-off.png'))
            else:
                self.chamberLightOn = True
                self.pushButtonChamberLight.setIcon(QIcon(os.getcwd()+'/images/light-on.png'))

        elif which == 'targetlight':
            if value == 0:
                self.targetLightOn = False
                self.pushButtonTargetLight.setIcon(QIcon(os.getcwd()+'/images/light-off.png'))
            else:
                self.targetLightOn = True
                self.pushButtonTargetLight.setIcon(QIcon(os.getcwd()+'/images/light-on.png'))    

    def pushButtonChamberLight_clicked(self):
        if self.chamberLightOn:
            self.setControl(which='chamberlight', value=0)
        else:
            self.setControl(which='chamberlight', value=1)
        self.chamberlight_signal.emit(self.chamberLightOn)         

    def pushButtonTargetLight_clicked(self):
        if self.targetLightOn:
            self.setControl(which='targetlight', value=0)
        else:
            self.setControl(which='targetlight', value=1)
        self.targetlight_signal.emit(self.targetLightOn)

    def updateValues(self, values):
        if not self.QDoubleSpinBox_setTemperature.hasFocus():
            self.QDoubleSpinBox_setTemperature.setValue(values[0])
        self.labelSampleTemperature.setText('{: <30}{: >20.2f}{: >5}'.format('Sample temperature:', values[1], 'K'))
        self.labelTargetTemperature.setText('{: <30}\t{: >20.2f}{: >5}'.format('Target temperature:', values[2], 'K'))
        self.labelHolderTemperature.setText('{: <30}\t{: >20.2f}{: >5}'.format('Holder temperature:', values[3], 'K'))
        self.labelSpareTemperature.setText('{: <30}\t{: >20.2f}{: >5}'.format('Spare temperature:', values[4], 'K'))
        self.labelHeaterPower.setText('{: <30}\t{: >20.2f}{: >5}'.format('Heating power:', values[5], 'W'))
        self.labelPressure.setText('{: <30}\t{: >20.2e}\t{: >10}'.format('Pressure:', values[6], 'torr'))
        QApplication.processEvents()
        
    def enable(self, enabled=True):
        self.pushButtonSetTemperature.setStyleSheet(self.styles['QPushButton_simulation'])
        self.pushButtonSetTemperature.setEnabled(enabled)
        self.pushButtonChamberLight.setEnabled(enabled)
        self.pushButtonTargetLight.setEnabled(enabled)
        self.QDoubleSpinBox_setTemperature.setEnabled(enabled)
        self.pushButtonWarmup.setEnabled(True)