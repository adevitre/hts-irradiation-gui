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

from LIFT1_tab_Ic import LIFT1_tab_Ic
from LIFT1_tab_Tc import LIFT1_tab_Tc
from LIFT1_tab_Vt import LIFT1_tab_Vt
from LIFT1_tab_Environment import LIFT1_tab_Environment
from LIFT1_tab_Sequences import LIFT1_tab_Sequences

from LIFT1_tab_Logging import LIFT1_tab_Logging
from LIFT1_Sidebar import LIFT1_Sidebar

colorForestGreen = QColor(34, 139, 34)

class LIFT1_GUI(QMainWindow):
    
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
        
        super(LIFT1_GUI, self).__init__(parent)
        
        self.threadpool = QThreadPool()
        self.hardwareParameters = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')  # software preferences
        
        self.sessionStarted = False                              # if False, the GUI is in DEMO mode and data has not been acquired yet
        self.updatingPlots = False

        self.hm = HardwareManager()
        self.dm = DataManager(self.threadpool)
        self.tm = TaskManager(self.dm, self.hm, self.threadpool)
        

        # shortcuts
        self.qShortcut_launchNewSession = QShortcut(QKeySequence('Ctrl+N'), self)
        self.qShortcut_launchNewSession.activated.connect(lambda: self.launchNewSessionWindow())
        
        self.qShortcut_calibrate100ACurrentSource = QShortcut(QKeySequence('Ctrl+C'), self)
        self.qShortcut_calibrate100ACurrentSource.activated.connect(lambda: self.calibrate100ACurrentSource())
        
        self.qShortcut_displayManual = QShortcut(QKeySequence('Ctrl+H'), self)
        self.qShortcut_displayManual.activated.connect(lambda: self.showHelp())
        
        # main window
        resolution = QDesktopWidget().screenGeometry()
        width, height = resolution.width(), resolution.height()
        self.resize(int(7*width/8), int(7*height/8))

        self.gridLayout = QGridLayout()
        self.gridLayout.setColumnStretch(5, 9)
        self.myCentralWidget = QWidget()
        self.myCentralWidget.setLayout(self.gridLayout)
        self.setCentralWidget(self.myCentralWidget)
        
        # add tabs
        self.tabWidget = QTabWidget(self)
        self.tabWidget.setStyleSheet(self.styles['QTabWidget'])

        self.icTools = LIFT1_tab_Ic(parent=self)
        self.tcTools = LIFT1_tab_Tc(parent=self)
        self.vtTools = LIFT1_tab_Vt(parent=self)
        self.environmentTools = LIFT1_tab_Environment(usr_preferences=self.preferences, parent=self)
        self.loggingTools = LIFT1_tab_Logging(parent=self)
        self.sequencesTools = LIFT1_tab_Sequences(parent=self)
        
        self.tabWidget.addTab(self.environmentTools, "Signals")
        self.tabWidget.addTab(self.icTools, "Critical Current")
        self.tabWidget.addTab(self.tcTools, "Critical Temperature")
        self.tabWidget.addTab(self.vtTools, "Voltage steps")
        self.tabWidget.addTab(self.sequencesTools, "Sequences")
        self.tabWidget.addTab(self.loggingTools, "Troubleshooting")
        
        self.tabWidget.setCurrentIndex(0)
        
        self.sidebar = LIFT1_Sidebar()
        
        self.gridLayout.addWidget(self.tabWidget, 0, 0, 11, 11)
        self.gridLayout.addWidget(self.sidebar, 0, 11, 1, 7)
        
        # connect the signals
        self.hm.log_signal.connect(self.log_event)
        self.dm.log_signal.connect(self.log_event)
        self.dm.plot_signal.connect(self.updateSignalsPlots)
        self.tm.log_signal.connect(self.log_event)
        
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
        self.sequencesTools.run_sequence_signal.connect(self.runSequence)
        self.loggingTools.setvoltagesign_signal.connect(self.setVoltageSign)
        self.loggingTools.log_signal.connect(self.log_event)
        self.loggingTools.test_signal.connect(self.testSerialConnection)
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
        self.setWindowTitle("Proton irradiation of REBCO coated conductors at cryogenic temperatures")
        
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
    
    @pyqtSlot(float)
    def setCurrent(self, current):
        if current <= 5.9:
            self.hm.enableParallelMode(True)
            self.hm.connectSampleTo100A(connected=False)
            self.hm.connectSampleTo6A(connected=True)
            self.threadpool.start(Task(self.hm.setLargeCurrent, current, self.hardwareParameters['LABEL_CS006A'], vb=True))
        else:
            self.hm.enableParallelMode(False)
            self.hm.connectSampleTo6A(connected=False)
            self.hm.connectSampleTo100A(connected=True)
            self.threadpool.start(Task(self.hm.setLargeCurrent, current, self.hardwareParameters['LABEL_CS100A'], vb=True))

    @pyqtSlot(np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    def updateSignalsPlots(self, time_tc, time_pm, setpointT, sampleT, targetT, holderT, spareT, pressure, power):
        self.environmentTools.updatePlottingArea(time_tc, time_pm, sampleT, targetT, holderT, spareT, pressure, power)
        self.sidebar.updateValues(values=[setpointT[-1], sampleT[-1], targetT[-1], holderT[-1], spareT[-1], power[-1], pressure[-1]])
         
    def launchNewSessionWindow(self):
        self.NewSessionWindow = NewSessionWindow()
        self.NewSessionWindow.ok.connect(self.startSession)
        self.NewSessionWindow.show()

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
    
    @pyqtSlot(float, float, float, int, bool, str)
    def measureTc(self, rampStart, rampRate, stopT, transportCurrent, acquiring, tag):
        if not acquiring:
            print(transportCurrent, type(transportCurrent))
            self.threadpool.start(Task(self.tm.measureTc, startT=rampStart, rampRate=rampRate, stopT=stopT, transportCurrent=transportCurrent, tag=tag))
        else:
            self.tm.stopAcquiring()
    
    @pyqtSlot(float, bool, str)
    def measureVt(self, maxV, acquiringVt, tag):
        if not acquiringVt:
            self.threadpool.start(Task(self.tm.measureVt, maxV=maxV, tag=tag))
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
            self.loggingTools.addLogEntry(when, what, comment)
            self.dm.log_event(when, what, comment)
              
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
            
        elif (what == 'Ic'):
            params = comment.split()
            ic, n, tavg, tag = float(params[2]), float(params[6]), float(params[10]), params[-1]
            data, corrected_voltage = self.tm.pushLastMeasurement()
            self.dm.saveMeasurementToFile(data, measurement=what, ic=ic, n=n, tavg=tavg, tag=tag, timestamp=when)
            
            self.tm.datapoints = [] # needed to make sure data is not overplot with incorrect array
            self.icTools.nextMeasurement(tag=tag)
            
        elif (what == 'Tc'):
            tc, tag = float(comment.split()[2]), comment.split()[-1]
            data, _ = self.tm.pushLastMeasurement()
            self.dm.saveMeasurementToFile(data, measurement=what, tc=tc, tag=tag, timestamp=when)
            self.tcTools.resetGUI()

        elif (what == 'IcSequenceComplete'):
            self.icTools.setMeasurementCounter(1)
                
        elif(what == 'AnnealComplete'):
            values = comment.split()
            try:
                n_ic_measurements = int(values[10])
                anneal_temperature = values[3]
                anneal_time = values[6]
                tag = values[13]
            except Exception as e:
                anneal_temperature, anneal_time, tag = '', '', ''
                print('LIFT1_GUI::log_signal raised::AnnealComplete raised: ', e)
            print('{}: Anneal at {} K for {} s, and {} Ic measurements completed'.format(tag, anneal_temperature, anneal_time, n_ic_measurements))
            self.icTools.setMeasurementCounter(value=int(n_ic_measurements))
            self.icTools.nextMeasurement(tag)
            
        elif (what == 'Calibrated100ACS'):
            print('Current source 100A calibrated. Calibration values stored in /config')

        elif(what == 'SequenceUpdate'):
            self.sequencesTools.updateStepStatus(comment)
            
        elif(what == 'SequenceStopped'):
            self.sequencesTools.stopSequence()

        elif(what == 'SerialStatus'):
            device, status = comment.split('~')
            if status == 'True':
                self.loggingTools.displaySerialDeviceStatus(device, True)
            else:
                self.loggingTools.displaySerialDeviceStatus(device, False)
       
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

    @pyqtSlot(str, str, str, bool, bool, bool)
    def startSession(self, directory, folderName, expDescription, saveTData, savePData, ln2Measurements):
        if directory != '':
            self.setWindowTitle("REBCO Irradiation App (data saved in {})".format(directory+'/'+folderName))
            
            if folderName[:5] != '_temp':
                self.dm.set_saveDirectory(directory, folderName, expDescription)
            else:
                self.setWindowTitle("REBCO Irradiation App (data saved in {})".format(self.preferences['temporary_savefolder']))

            self.dm.vc = self.hardwareParameters['bridgeLength']*1e-1*1e-6 # vc = Ec*d = 1 uV/cm * bridge_length [mm] * 0.1 [cm/mm]
            self.icTools.enable(enabled=True)
            self.tcTools.enable(enabled=True)
            self.sidebar.enable(enabled=True)
            self.sequencesTools.enable(enabled=True)
            self.sidebar.enable(enabled=True)
            self.vtTools.enable(enabled=True)

            ln2Note = ''

            if ln2Measurements:
                self.tabWidget.removeTab(self.tabWidget.indexOf(self.tcTools))
                self.tabWidget.removeTab(self.tabWidget.indexOf(self.environmentTools))
                self.tabWidget.removeTab(self.tabWidget.indexOf(self.sequencesTools))
                ln2Note = 'LN2 '
                
            self.tm.startReadings(ln2Measurements)
            self.dm.enableBackups(backupTemperatureTrace=saveTData, backupPressureTrace=savePData)
            self.qShortcut_launchNewSession.activated.disconnect()
            self.qShortcut_launchNewSession.activated.connect(lambda: QMessageBox.warning(self, 'In session warning', 'To start a new session you must terminate this\nsession by closing the user interface. '))

            self.log_event('Startup', '{}Session started: {}'.format(ln2Note, expDescription))
            self.sessionStarted = True

    @pyqtSlot(bool)
    def toggleTargetLight(self, on):
        self.tm.setTargetLight(on=on)

    @pyqtSlot(bool)
    def toggleChamberLight(self, on):
        self.tm.setChamberLight(on=on)
    
    @pyqtSlot(int)
    def setVoltageSign(self, sign):
        self.hm.setVoltageSign(sign)