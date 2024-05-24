import os, time

from PyQt5.QtCore import QObject, pyqtSignal
from configure import load_json

from relays import Relays
from nanovoltmeter import NanoVoltmeter
from dmm6500 import DMM6500
from currentsourceCAEN import CurrentSourceCAEN
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

LABEL_CAEN = 'CAEN'
LABEL_CS100A = 'HP6260B-120A'
LABEL_CS006A = '2231A-30-3-6A'

class HardwareManager(QObject):
    
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        self.tc, self.pm, self.nvm, self.dmm = None, None, None, None
        super(HardwareManager, self).__init__(parent)
        hardwareParameters = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        
        self.vs = VoltageSource()
        self.csCAEN = CurrentSourceCAEN()
        self.cs100A = CurrentSource100A(hardwareParameters["a"], hardwareParameters["b"], hardwareParameters["shuntR"], self.vs, self.csCAEN)
        self.cs100mA = CurrentSource100mA(int(self.preferences["sampling_period_tc"]*1000-50))
        self.relays = Relays()
        
        self.tc = TemperatureController(int(self.preferences["sampling_period_tc"]*1000-50), serialDevice=False)
        self.pm = PressureMonitor(int(self.preferences["sampling_period_pm"]*1000-50))
        self.nvm = NanoVoltmeter(int(self.preferences["sampling_period_nv"]*1000-50))
        self.dmm = DMM6500(hardwareParameters["shuntR"], int(self.preferences["sampling_period_nv"]*1000-50))
           
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
    
    def getCurrentReading(self):
        current = self.dmm.measure()
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
        
    def setSmallCurrent(self, current=-1):
        self.cs100mA.setCurrent(current)
    
    def setLargeCurrent(self, current=0, currentSource=LABEL_CS100A, calib=True, vb=False):
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
        self.cs100mA.enable(enabled=True)
    
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
                device (str) 'picoammeter' or 'nanovoltameter'
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

    def testSerialConnection(self, device=TEMPERATURE_CONTROLLER):
        if device == TEMPERATURE_CONTROLLER:
            connected = self.tc.testSerialConnection()
        elif device == CURRENT_SOURCE:
            connected = self.cs100mA.testSerialConnection()
            if not connected:
                print('fuser -k {}'.format(self.cs100mA.settings['port']))
            #connected = self.cs100mA.testSerialConnection()

        elif device == POWER_SUPPLY:
            connected = self.vs.testSerialConnection()
        elif device == NANOVOLTMETER:
            connected = self.nvm.testSerialConnection()
        elif device == MULTIMETER:
            connected = self.dmm.testSerialConnection()
        elif device == PRESSURE_CONTROLLER:
            connected = self.pm.testSerialConnection()
        self.log_signal.emit('SerialStatus', '{}~{}'.format(device, connected))

    def setTargetLight(self, on=False):
        self.relays.setTargetLight(on=on)

    def setChamberLight(self, on=False):
        self.relays.setChamberLight(on=on)

    def setVoltageSign(self, sign):
        self.nvm.setPolarity(sign)
        self.log_signal.emit('VoltageSign', 'Voltage sign switched to {} by user. Ic, Tc and Vt measurements will be affected.')