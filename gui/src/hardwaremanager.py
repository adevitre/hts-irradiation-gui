import os, time

from PyQt5.QtCore import QObject, pyqtSignal
from configure import load_json

from relays import Relays
from nanovoltmeter import NanoVoltmeter
from dmm6500 import DMM6500
from currentsourceCAEN import CurrentSourceCAEN
from cs_tdk import CurrentSourceTDK
from currentsource100A import CurrentSource100A
from currentsource100mA import CurrentSource100mA
from temperaturecontroller import TemperatureController
from pressuremonitor import PressureMonitor
from voltagesource import VoltageSource

TEMPERATURE_CONTROLLER = 'LakeShore 336 Temperature Controller'
CURRENT_SOURCE = 'LakeShore 121 Current Source'
POWER_SUPPLY = 'Keithley 2231-A-30-3 Power Supply'
NANOVOLTMETER = 'Keithley 2182A Nanovoltmeter'
MULTIMETER = 'Keithley DMM6500 Digital Multimeter'
PRESSURE_CONTROLLER = 'Instrutech FlexRax 4000 Vacuum Gauge Controller'
CURRENT_SOURCE_TDK = 'TDK Current Source GEN6-100'

class HardwareManager(QObject):
    
    log_signal = pyqtSignal(str, str)
    
    hardware_parameters = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
    
    def __init__(self, parent=None):
        self.tc, self.pm, self.nvm, self.dmm = None, None, None, None
        super(HardwareManager, self).__init__(parent)
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        
        self.vs = VoltageSource()
        self.csCAEN = CurrentSourceCAEN(serialDevice=False)
        self.csTDK = None #CurrentSourceTDK()
        self.cs100A = CurrentSource100A(self.hardware_parameters["a"], self.hardware_parameters["b"], self.hardware_parameters["shuntR"], self.vs, self.csCAEN, self.csTDK)
        self.cs100mA = CurrentSource100mA(int(self.preferences["sampling_period_tc"]*1000-50))
        self.relays = Relays()
        
        self.tc = TemperatureController(int(self.preferences["sampling_period_tc"]*1000-50), serialDevice=True)
        self.pm = PressureMonitor(int(self.preferences["sampling_period_pm"]*1000-50))
        self.nvm = NanoVoltmeter(int(self.preferences["sampling_period_nv"]*1000-50))
        self.dmm = DMM6500(self.hardware_parameters["shuntR"], int(self.preferences["sampling_period_nv"]*1000-50))
           
    def initializeHardware(self):
        self.relays.connectCurrentSource100mATo(device='hallSensor') # connect current source
        self.relays.connectSampleTo100A(connected=False)
        self.relays.measureSampleWith(device='nanovoltmeter')
        self.setVoltageOffset()
    
    def __del__(self):
        if self.tc is not None:
            self.tc.rampTemperature(rate=2., ramping=False)
            self.tc.__del__()
    
    def getPIDSensor(self):    
        return self.tc.getPIDSensor()
        
    def getGateValveState(self):
        return 1-self.relays.getGateValveState()
    
    def getCryocoolerState(self):
        return self.relays.getCryocoolerState()
    
    def getFaradayCupState(self):
        return self.relays.getFaradayCupState()
        
    def getPressureReading(self):
        pressure = self.pm.getPressure()
        if ((self.pm.igOn) & (pressure > 2.5e-3)) | ((not self.pm.igOn) & (pressure < 2.5e-3)):
            self.pm.testIgOn()                # adjust the flag if igOn and overpressure or igOff and low pressure
        return pressure
    
    def getTemperatureReading(self):
        sampleT, targetT, holderT, spareT = self.tc.getTemperatureReadings()
        heatingPower = self.tc.getHeatingPower()
        setpointT = self.tc.getSetpointTemperature()
        return setpointT, sampleT, targetT, holderT, spareT, heatingPower
    
    def getSampleTemperature(self):
        return self.tc.getSampleTemperature()
    
    def getTargetTemperature(self):
        return self.tc.getTargetTemperature()
    
    def getVoltageReading(self, removeOffset=True):
        return self.nvm.measure(removeOffset)
    
    def getCurrentReading(self, useDMM=True):
        if useDMM:
            current = self.dmm.measure()
        else:
            current = self.csCAEN.getCurrent()
        return current
    
    def getShuntResistance(self):
        return self.cs100A.shuntR
    
    def getSetpointTemperature(self):
        return self.tc.getSetpointTemperature()
    
    def getHeatingPower(self):
        return self.tc.getHeatingPower()

    def rampTemperature(self, rampTo, rampRate, ramping=False):
        self.tc.rampTemperature(rampRate, ramping)
        time.sleep(.1)
        self.tc.setSetpointTemperature(rampTo)
        time.sleep(.1)

    def setVoltageOffset(self):
        return self.nvm.setOffset()
    
    def setSmallCurrentPolarity(self, polarity=0):
        self.cs100mA.setPolarity(polarity)
        
    def setSmallCurrent(self, current=0):
        self.cs100mA.setCurrent(current)
    
    def setLargeCurrent(self, current=0, currentSource="HP6260B-120A", calib=True, vb=False):
        if vb: self.log_signal.emit('CurrentSet', 'Power supply {} set by user to {:4.2f} A'.format(currentSource, current))
        return self.cs100A.setCurrent(current, currentSource, calib, vb=vb)
    
    def enableParallelMode(self, enabled=False):
        self.cs100A.enableParallelMode(enabled=enabled)

    def setLargeCurrentCalibration(self, a, b):
        self.cs100A.updateCalibration(a, b)
    
    def setTemperature(self, temperature):
        self.setSetpointTemperature(temperature)
        time.sleep(0.1)
        self.setHeaterOutput(on=True)
        if temperature < self.tc.getTargetTemperature():
            self.setCooler(on=True)
        self.log_signal.emit('TempSet', '{:4.2f} K'.format(temperature))
        
    def setSetpointTemperature(self, temperature):
        self.tc.setSetpointTemperature(temperature)
        time.sleep(.1)
    
    def setPIDSensor(self, sensor='B'):
        self.tc.setPIDSensor(sensor=sensor)

    def setHeaterOutput(self, on=True):
        self.tc.setHeaterOutput(on)
        time.sleep(.1)
    
    def setCooler(self, on=True):
        self.relays.setCooler(on=on)
        if on:
            self.log_signal.emit('CoolingModeSet', '1')
        else:
            self.log_signal.emit('CoolingModeSet', '0')
            
    def connectCurrentSource100mATo(self, device='sample'):
        self.relays.connectCurrentSource100mATo(device) # connect current source
        time.sleep(1)
        self.cs100mA.enable(enabled=True)
        time.sleep(1)
        
    def connectSampleTo6A(self, connected=True):
        self.relays.connectSampleTo6A(connected)
    
    def connectSampleTo100A(self, connected=True):
        self.relays.connectSampleTo100A(connected)
    
    def enableCurrentSource100mA(self, enabled=True):
        self.cs100mA.enable(enabled)
        time.sleep(.1)
    
    def measureSampleWith(self, device='picoammeter'):
        '''
            Calls function from relays, which connects the picoammeter (during irradiation) or the nanovoltmeter (during measurements) to the sample
            
            INPUTS:
                device (str) 'picoammeter' or 'nanovoltmeter'
        '''
        self.relays.measureSampleWith(device)

    def insertFaradayCup(self, inserted=True, logEvent=True):
        '''
            Inserts or retracts the Faraday cup obn the beamline
            
            INPUTS:
                inserted (bool) - The faraday cup is inserted in the beam path (True), the Faraday cup is retracted to irradiate the sample (False)
        '''
        self.relays.insertFaradayCup(inserted)
        if logEvent:
            self.log_signal.emit('FaradayCup', 'Inserted = {}'.format(inserted))
    
    def switchHatLight(self, on=False):
        '''
            Switches the light inside the hat for collimator alignment.
            
            INPUTS:
                on (bool) - The light is ON if True, and OFF if False.
        '''
        self.relays.switchHatLight(on=on)
        if logEvent:
            if on:
                self.log_signal.emit('HatLight', 'Hat Light is ON.')
            else:
                self.log_signal.emit('HatLight', 'Hat Light is OFF.')
    
    def openGateValve(self, opened=True):
        self.relays.openGateValve(opened)
        self.log_signal.emit('GateValveToggle', 'Open = {}'.format(opened))

    def testSerialConnection(self, device):
        if device == self.hardware_parameters['devices']['temperature_controller']['name']:
            connected = self.tc.testConnection()
        elif device == self.hardware_parameters['devices']['current_source_tc']['name']:
            connected = self.cs100mA.testConnection()
        elif device == self.hardware_parameters['devices']['voltagesource']['name']:
            connected = self.vs.testConnection()
        elif device == self.hardware_parameters['devices']['nanovoltmeter']['name']:
            connected = self.nvm.testConnection()
        elif device == self.hardware_parameters['devices']['multimeter']['name']:
            connected = self.dmm.testConnection()
        elif device == self.hardware_parameters['devices']['pressure_monitor']['name']:
            connected = self.pm.testConnection()
        else:
            print('There is no implementation for testing the connection of this device')
            connected = False
        self.log_signal.emit('SerialStatus', '{}~{}'.format(device, connected))

    def setTargetLight(self, on=False):
        self.relays.setTargetLight(on=on)

    def setChamberLight(self, on=False):
        self.relays.setChamberLight(on=on)

    def setVoltageSign(self, sign):
        self.nvm.setPolarity(sign)
        self.log_signal.emit('VoltageSign', 'Voltage sign switched to {} by user. Ic, Tc and Vt measurements will be affected.')

    def resetQPS(self):
        self.relays.resetQPS()

    def reconnect_device(self, device_key):
        '''
            reconnect_device is called by a button in the help tab when the device registers as disconnected and the user wants to try to connect.

            INPUT
            --------
            device_key (str) - the unique identifier for a given device which allows the code to find all information related to this device in hwparams.json
        '''
        self.hardware_parameters = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
        if device_key == 'temperature_controller':
            if self.tc is not None: del self.tc
            self.tc = TemperatureController(int(self.preferences["sampling_period_tc"]*1000-50), serialDevice=True)
        elif device_key == 'current_source_tc':
            if self.cs100mA is not None: del self.cs100mA
            self.cs100mA = CurrentSource100mA(int(self.preferences["sampling_period_tc"]*1000-50))
        elif device_key == 'voltagesource':
            if self.vs is not None: del self.vs
            self.vs = VoltageSource()
        elif device_key == 'nanovoltmeter':
            if self.nvm is not None: del self.nvm
            self.nvm = NanoVoltmeter(int(self.preferences["sampling_period_nv"]*1000-50))
        elif device_key == 'multimeter':
            if self.dmm is not None: del self.dmm
            self.dmm = DMM6500(self.hardware_parameters["shuntR"], int(self.preferences["sampling_period_nv"]*1000-50))
        elif device_key == 'pressure_monitor':
            if self.pm is not None: del self.pm
            self.pm = PressureMonitor(int(self.preferences["sampling_period_pm"]*1000-50))
        else:
            print('There is no implementation for reconnecting this device')
            #self.csCAEN = CurrentSourceCAEN()
            #self.csTDK = None #CurrentSourceTDK()
            #self.cs100A = CurrentSource100A(self.hardware_parameters["a"], self.hardware_parameters["b"], self.hardware_parameters["shuntR"], self.vs, self.csCAEN, self.csTDK)
        
        success = self.testSerialConnection(device=self.hardware_parameters['devices'][device_key]['name'])

        if success:
            self.log_signal.emit('Reconect', 'Attempt to reconnect {} was successful'.format(self.hardware_parameters[devices][device_key]['name']))
        else:
            self.log_signal.emit('Reconect', 'Attempt to reconnect {} was unsuccessful'.format(self.hardware_parameters['devices'][device_key]['name']))

        
        