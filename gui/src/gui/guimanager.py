import time, datetime, os
import numpy as np

# emails
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart

from PyQt5.QtWidgets import QAction, QWidget, QShortcut, QGridLayout, QMainWindow, QMessageBox, QInputDialog, QTabWidget, QDesktopWidget

from PyQt5.QtGui import QColor, QKeySequence
from PyQt5.QtCore import pyqtSlot, QThreadPool

from configure import load_json
from window_newSession import NewSessionWindow

from hardwaremanager import HardwareManager
from taskmanager import TaskManager
from datamanager import DataManager
from task import Task

from Tab_VoltageCurrent import Tab_VoltageCurrent
from Tab_VoltageTemperature import Tab_VoltageTemperature
from Tab_VoltageTime import Tab_VoltageTime
from Tab_Analysis import Tab_Analysis
from Tab_Signals import Tab_Signals
from Tab_Sequences import Tab_Sequences
from Tab_Login import Tab_Login

from Tab_Logbook import Tab_Logbook
from Tab_Devices import Tab_Devices
from sidebar import Sidebar

colorForestGreen = QColor(34, 139, 34)

class GUIManager(QMainWindow):
    
    def closeEvent(self, event):
        reply = QMessageBox.question(self, 'Window Close', 'Are you sure you want to close the window?',
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            event.accept()
            self.dm.log_event('Shutdown', 'Session terminated', 'Normal')
            self.dm.__del__()
            self.hm.__del__()
            print('Program ended by user')
        else:
            event.ignore()
    
    def __init__(self, parent=None):
        
        super(GUIManager, self).__init__(parent)
        
        self.threadpool = QThreadPool()
        self.hardware_parameters = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')  # software preferences
        
        self.sessionStarted = False  # if False, the GUI is in DEMO mode and data has not been acquired yet
        self.updatingPlots = False

        self.hm = HardwareManager()
        self.dm = DataManager(self.threadpool)
        self.tm = TaskManager(self.dm, self.hm, self.threadpool)
        
        self.qShortcut_calibrate100ACurrentSource = QShortcut(QKeySequence('Ctrl+C'), self)
        self.qShortcut_calibrate100ACurrentSource.activated.connect(lambda: self.calibrate100ACurrentSource())
        
        self.qShortcut_displayManual = QShortcut(QKeySequence('Ctrl+H'), self)
        self.qShortcut_displayManual.activated.connect(lambda: self.showHelp())
        
        # main window
        resolution = QDesktopWidget().screenGeometry()
        width, height = resolution.width(), resolution.height()
        self.resize(width, height) #int(7*width/8), int(7*height/8))

        self.gridLayout = QGridLayout()
        self.gridLayout.setColumnStretch(5, 9)
        self.myCentralWidget = QWidget()
        self.myCentralWidget.setLayout(self.gridLayout)
        self.setCentralWidget(self.myCentralWidget)
        
        # Setup the tabs used to control different aspects of the experiment.
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setStyleSheet(self.styles['QTabWidget'])

        # tabs in a tab for mission control
        self.missionControl = QTabWidget(self.tabWidget)
        self.missionControl.setStyleSheet(self.styles['QTabWidgetVertical'])
        self.missionControl.setTabPosition(QTabWidget.West)

        self.loginTools = Tab_Login(parent=self)
        self.logbookTools = Tab_Logbook(parent=self)
        self.environmentTools = Tab_Signals(usr_preferences=self.preferences, parent=self)
        self.deviceTools = Tab_Devices(parent=self)
        
        self.missionControl.addTab(self.environmentTools, 'Signals')
        self.missionControl.addTab(self.logbookTools, "Logbook")
        self.missionControl.addTab(self.loginTools, 'Session')
        self.missionControl.setCurrentIndex(2)

        # tabs in a tab for measurements
        self.measurementTools = QTabWidget(self.tabWidget)
        self.measurementTools.setStyleSheet(self.styles['QTabWidgetVertical'])
        self.measurementTools.setTabPosition(QTabWidget.West)

        self.icTools = Tab_VoltageCurrent(parent=self)
        self.tcTools = Tab_VoltageTemperature(parent=self)
        self.vtTools = Tab_VoltageTime(parent=self)

        self.measurementTools.addTab(self.icTools, "Voltage/Current")
        self.measurementTools.addTab(self.tcTools, "Voltage/Temperature")
        self.measurementTools.addTab(self.vtTools, "Voltage/Time")

        # tabs in a tab for data analysis
        self.analysis_tools = Tab_Analysis(parent=self)

        # add vertical tab widgets to horizontal master tab widget
        self.sequencesTools = Tab_Sequences(parent=self)
        self.tabWidget.addTab(self.missionControl, 'Mission Control')
        self.tabWidget.addTab(self.measurementTools, "Measurements")
        self.tabWidget.addTab(self.sequencesTools, "Sequences")
        self.tabWidget.addTab(self.analysis_tools, "Analysis")
        self.tabWidget.addTab(self.deviceTools, "Help")
        self.tabWidget.setCurrentIndex(0)
        
        self.sidebar = Sidebar()
        
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 11, 11)
        self.gridLayout.addWidget(self.sidebar, 0, 11, 1, 7)
        
        # connect the signals
        self.hm.log_signal.connect(self.log_event)
        self.dm.log_signal.connect(self.log_event)
        self.dm.plot_signal.connect(self.updateSignalsPlots)
        self.tm.log_signal.connect(self.log_event)

        self.loginTools.signal_newsession.connect(self.startSession)
        self.loginTools.signal_stopsession.connect(self.stopSession)
        self.loginTools.setvoltagesign_signal.connect(self.setVoltageSign)
        
        self.icTools.measure_signal.connect(self.measureIc)
        self.icTools.updatePlot_signal.connect(self.updateIcPlot)
        self.icTools.log_signal.connect(self.log_event)
        self.tcTools.measure_signal.connect(self.measureTc)
        self.tcTools.updatePlot_signal.connect(self.updateTcPlot)
        self.vtTools.setcurrent_signal.connect(self.setCurrent)
        self.vtTools.measure_signal.connect(self.measureVt)
        self.vtTools.log_signal.connect(self.log_event)
        self.vtTools.updatePlot_signal.connect(self.updateVtPlot)

        self.sidebar.sensorset_signal.connect(self.setPIDSensor)
        self.sidebar.gateopen_signal.connect(self.setGateValves)
        self.sidebar.cryoset_signal.connect(self.setCoolingMode)
        self.sidebar.warmup_signal.connect(self.warmup)
        self.sidebar.targetlight_signal.connect(self.toggleTargetLight)
        self.sidebar.chamberlight_signal.connect(self.toggleChamberLight)
        self.sidebar.reset_signal.connect(self.resetQPS)

        self.sequencesTools.run_sequence_signal.connect(self.runSequence)
        
        self.logbookTools.log_signal.connect(self.log_event)
        
        self.deviceTools.test_signal.connect(self.testSerialConnection)
        self.deviceTools.reconnect_signal.connect(self.reconnect_device)

        self.sidebar.settemp_signal.connect(self.setTemperature)
        self.sidebar.faradaycup_signal.connect(self.insertFaradayCup)
        
        self.tabSwitchAction = QAction()
        self.tabSwitchAction.triggered.connect(self.switchTab)
        self.tabSwitchAction.setShortcut("Ctrl+\t")
        
        self.tabSwitchBackAction = QAction()
        self.tabSwitchBackAction.triggered.connect(self.switchBackTab)
        self.tabSwitchBackAction.setShortcut("Ctrl+Shift+\t")
        
        self.hm.initializeHardware()
        self.initializeControls()
        self.move(int((width-self.frameSize().width())/4), int((height-self.frameSize().height())/4))
        
        self.setWindowTitle(' ')
        
    def initializeControls(self):
        self.sidebar.setControl(which='pidsensor', value=self.hm.getPIDSensor())
        self.sidebar.setControl(which='cryocooler', value=self.hm.getCryocoolerState())
        self.sidebar.setControl(which='turbovalve', value=self.hm.getGateValveState())
        self.sidebar.setControl(which='faradaycup', value=self.hm.getFaradayCupState())
        setpointT, sampleT, targetT, holderT, spareT, heatingPower = self.hm.getTemperatureReading()
        self.sidebar.updateValues(values=[setpointT, sampleT, targetT, holderT, spareT, heatingPower, 0, 0, 0])
        
    def switchTab(self):
        self.tabWidget.setCurrentIndex((self.tabWidget.currentIndex()+1)%self.tabWidget.count())
        
    def switchBackTab(self):
        self.tabWidget.setCurrentIndex((self.tabWidget.currentIndex()+-1)%self.tabWidget.count())

    @pyqtSlot(bool)
    def setCoolingMode(self, desired_state):
        '''
            setCoolingMode turns the compressor ON/OFF depending on user input in comboBoxCryocooler
            Note: It is also possible to stop the motor without stopping the compressor to prevent vibrations during an Ic measurement
            desired_state (bool) - True if the desired_state is to cool, false if the desired_state is not-to-cool.
        '''
        self.hm.setCooler(on=desired_state) # Motor and Compressor OFF
    
    @pyqtSlot(bool)
    def setGateValves(self, opened):
        '''
            setGateValves opens/closes the gate valve connecting the chamber and the turbo pump depending on the truth value of opened 
        '''
        self.threadpool.start(Task(self.hm.openGateValve, opened))

        if opened:
            self.sidebar.setControl(which='turbovalve', value=1)
        else:
            self.sidebar.setControl(which='turbovalve', value=0)
        
    @pyqtSlot(float)
    def setTemperature(self, temperature):
        self.threadpool.start(Task(self.hm.setTemperature, temperature))
    
    @pyqtSlot(float, str)
    def setCurrent(self, current, current_source):
        if current_source == self.hardware_parameters['LABEL_CS006A']:
            self.hm.enableParallelMode(True)
            self.hm.connectSampleTo100A(connected=False)
            self.hm.connectSampleTo6A(connected=True)
            self.threadpool.start(Task(self.hm.setLargeCurrent, current, self.hardware_parameters['LABEL_CS006A'], vb=True))

        elif current_source == self.hardware_parameters['LABEL_CS100A']:
            self.hm.enableParallelMode(False)
            self.hm.connectSampleTo6A(connected=False)
            self.hm.connectSampleTo100A(connected=True)
            self.threadpool.start(Task(self.hm.setLargeCurrent, current, self.hardware_parameters['LABEL_CS100A'], vb=True))
            
        elif current_source == self.hardware_parameters['LABEL_CAEN']:
            self.hm.enableParallelMode(False)
            self.hm.connectSampleTo6A(connected=False)
            self.hm.connectSampleTo100A(connected=True)
            self.threadpool.start(Task(self.hm.setLargeCurrent, current, self.hardware_parameters['LABEL_CAEN'], vb=True))
        
        elif current_source == self.hardware_parameters['LABEL_TDK']:
            self.hm.enableParallelMode(False)
            self.hm.connectSampleTo6A(connected=False)
            self.hm.connectSampleTo100A(connected=True)
            self.threadpool.start(Task(self.hm.setLargeCurrent, current, self.hardware_parameters['LABEL_TDK'], vb=True))
        
    @pyqtSlot(np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    def updateSignalsPlots(self, time_tc, time_pm, setpointT, sampleT, targetT, holderT, spareT, pressure, power):
        self.environmentTools.updatePlottingArea(time_tc, time_pm, sampleT, targetT, holderT, spareT, pressure, power)
        self.sidebar.updateValues(values=[setpointT[-1], sampleT[-1], targetT[-1], holderT[-1], spareT[-1], power[-1], pressure[-1]])
         
    def showHelp(self):
        with open('docs/README.txt') as f:
            QMessageBox.information(self, 'Help', f.read(-1))
    
    def calibrate100ACurrentSource(self):
        value, ok = QInputDialog.getInt(self, '100 A current source calibration', 'The calibration will be run in steps of 0.1 A at a rate of 0.5 A/s.\nPlease input the upper current limit:', value=20, max=100, min=10, step=5)
        if ok:
            self.threadpool.start(Task(self.tm.calibrate100ACurrentSource, currentRangeUpperLimit=value))

    def launch_preferencesWindow(self):
        self.preferencesWindow = PreferencesWindow(self.preferences)
        self.preferencesWindow.ok.connect(self.modifyPreferences)
        self.preferencesWindow.show()
    
    @pyqtSlot(bool)
    def insertFaradayCup(self, inserted, logEvent=True):
        self.hm.insertFaradayCup(inserted=inserted, logEvent=logEvent)
     
    @pyqtSlot(float, float, float, str, bool, str)
    def measureIc(self, rampStart, iStep, maxV, currentSource, acquiring, tag):
        if not acquiring:
            self.threadpool.start(Task(self.tm.measureIc, rampStart=rampStart, iStep=iStep, maxV=maxV, currentSource=currentSource, tag=tag))
        else:
            self.tm.stopAcquiring()
    
    @pyqtSlot(float, float, float, float, bool, str)
    def measureTc(self, rampStart, rampRate, stopT, transportCurrent, acquiring, tag):
        if not acquiring:
            self.threadpool.start(Task(self.tm.measureTc, startT=rampStart, rampRate=rampRate, stopT=stopT, transportCurrent=transportCurrent, tag=tag))
        else:
            self.tm.stopAcquiring()
    
    @pyqtSlot(float, str, bool, bool, str)
    def measureVt(self, maxV, current_source, hall_measurement, acquiringVt, tag):
        if not acquiringVt:
            self.threadpool.start(Task(self.tm.measureVt, maxV=maxV, current_source=current_source, hall_measurement=hall_measurement, tag=tag))
        else:
            self.tm.stopAcquiring()
    
    @pyqtSlot()
    def updateIcPlot(self):
        if self.tm.datapoints != []:
            data = np.transpose(self.tm.datapoints)
            self.threadpool.start(Task(self.icTools.updateActiveLine, current=data[2], voltage=data[3]))
    
    @pyqtSlot()
    def updateTcPlot(self):
        if self.tm.datapoints != []:
            data = np.transpose(self.tm.datapoints)
            self.threadpool.start(Task(self.tcTools.updateActiveLine, temperature=data[4], voltage=data[3]))
    
    @pyqtSlot()
    def updateVtPlot(self):
        if self.tm.datapoints != []:
            data = np.transpose(self.tm.datapoints)
            self.threadpool.start(Task(self.vtTools.updateActiveLine, time=data[1], voltage=data[3]))

    @pyqtSlot(str)
    def setPIDSensor(self, sensor):
        self.hm.setPIDSensor(sensor=sensor)
        self.log_event('SensorSet', 'PID control is now referenced to sensor {}'.format(sensor))

    @pyqtSlot(str, str)
    def log_event(self, what='', comment='', logEvent=True):
        
        when = str(datetime.datetime.now())    
        if logEvent:
            self.logbookTools.addLogEntry(when, what, comment.split('/')[0]) # everything after '/' is ignored for logging purposes (this allows passing parameters silently, e.g. UpdateSequence)
            self.dm.log_event(when, what, comment.split('/')[0])
              
        if what == 'TempSet':
            self.sidebar.updateSetpointDisplay(float(comment[:-2]))
            
        elif what == 'CoolingModeSet':
            self.sidebar.setControl(which='cryocooler', value=int(comment))
        
        elif what == 'Vt':
            params = comment.split()
            tavg, tag = float(params[-3]), params[-1]
            data, _ = self.tm.pushLastMeasurement()
            if data != []:
                self.dm.saveMeasurementToFile(data, measurement=what, tavg=tavg, tag=tag, timestamp=when)
            self.vtTools.resetGUI()
            
        elif (what == 'nextIV'):
            self.threadpool.start(Task(self.icTools.nextMeasurement, comment))
            
        elif (what == 'Tc'):
            tc, tag = float(comment.split()[2]), comment.split()[-1]
            data, _ = self.tm.pushLastMeasurement()
            self.dm.saveMeasurementToFile(data, measurement=what, tc=tc, tag=tag, timestamp=when)
            self.tcTools.resetGUI()

        elif (what == 'IcSequenceComplete'):
            self.icTools.setMeasurementCounter(1)
                   
        elif (what == 'Calibrated100ACS'):
            print('Current source 100A calibrated. Calibration values stored in /config')

        elif (what == 'SequenceStarted'):
            self.sequencesTools.updateStepStatus(what)
            
        elif(what == 'SequenceUpdate'):
            self.sequencesTools.updateStepStatus(comment)
            
        elif(what == 'SequenceStopped'):
            self.sequencesTools.stopSequence()

        elif(what == 'SerialStatus'):
            device, status = comment.split('~')
            if status == 'True':
                self.deviceTools.displaySerialDeviceStatus(device, True)
            else:
                self.deviceTools.displaySerialDeviceStatus(device, False)
       
    @pyqtSlot(str)
    def testSerialConnection(self, device):
        '''
            testSerialConnection evaluates the status of serial connection to specified device

            INPUTS
            ------
            device (str) - name of device to test
        '''
        self.threadpool.start(Task(self.hm.testSerialConnection, device))

    @pyqtSlot()
    def resetQPS(self):
        '''
            resetQPS resets the Quench Protection System (Quenchbox) after a fault
        '''
        self.threadpool.start(Task(self.tm.resetQPS))

    @pyqtSlot()
    def warmup(self):
        reply = QMessageBox.question(self, 'Warmup', 'Are you sure you want to warm up the system to room temperature?', QMessageBox.Yes | QMessageBox.Abort, QMessageBox.Yes)

        if reply == QMessageBox.Yes:
            self.setGateValves(opened=False)
            self.threadpool.start(Task(self.tm.warmup))
            print('Warmup initiated!')
    

    @pyqtSlot(list)
    def runSequence(self, sequence):
        if sequence != []:
            self.threadpool.start(Task(self.tm.runSequence, sequence=sequence))
        else:
            self.tm.sequenceRunning = False
            self.tm.stopAcquiring()

    def enableGUI(self, enabled=True):
        self.icTools.enable(enabled)
        self.tcTools.enable(enabled)
        self.sidebar.enable(enabled)
        self.sequencesTools.enable(enabled)
        self.sidebar.enable(enabled)
        self.vtTools.enable(enabled)

    @pyqtSlot(str, str, bool, bool, bool)
    def startSession(self, directory, folderName, saveTData, savePData, ln2Measurements):
        if directory != '':
            self.setWindowTitle("REBCO Irradiation App (data saved in {})".format(directory+'/'+folderName))
            
            if folderName[:5] != '_temp':
                self.dm.set_saveDirectory(directory, folderName)
                self.icTools.sessionTag = folderName.split('_')[-1]+'-'
                self.tcTools.sessionTag = folderName.split('_')[-1]+'-'
                self.vtTools.sessionTag = folderName.split('_')[-1]+'-'
            else:
                self.setWindowTitle("REBCO Irradiation App (data saved in {})".format(self.preferences['temporary_savefolder']))
                self.icTools.sessionTag = ''
                self.tcTools.sessionTag = ''
                self.vtTools.sessionTag = ''

            self.dm.vc = self.hardware_parameters['bridgeLength']*1e-1*1e-6 # vc = Ec*d = 1 uV/cm * bridge_length [mm] * 0.1 [cm/mm]
            self.enableGUI(True)

            ln2Note = ''
            if ln2Measurements:
                self.tabWidget.removeTab(self.tabWidget.indexOf(self.tcTools))
                self.tabWidget.removeTab(self.tabWidget.indexOf(self.environmentTools))
                self.tabWidget.removeTab(self.tabWidget.indexOf(self.sequencesTools))
                ln2Note = 'LN2 '
                
            self.tm.startReadings(ln2Measurements)
            self.dm.enableBackups(backupTemperatureTrace=saveTData, backupPressureTrace=savePData)
            
            self.log_event('Startup', '{}Session started'.format(ln2Note))
            self.sessionStarted = True
    
    @pyqtSlot()
    def stopSession(self):
        print('Session stop not yet operational')
        self.sessionStarted = False

    @pyqtSlot(bool)
    def toggleTargetLight(self, on):
        self.tm.setTargetLight(on=on)

    @pyqtSlot(bool)
    def toggleChamberLight(self, on):
        self.tm.setChamberLight(on=on)
    
    @pyqtSlot(int)
    def setVoltageSign(self, sign):
        self.hm.setVoltageSign(sign)
    
    @pyqtSlot(str)
    def reconnect_device(self, device_key):
        self.hardware_parameters = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
        self.hm.reconnect_device(device_key)
        