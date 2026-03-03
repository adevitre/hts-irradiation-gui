import os, time

from PyQt5.QtCore import QObject, pyqtSignal
from configure import load_json

# from relays import Relays
from nanovoltmeter import NanoVoltmeter

# added, Ben Clark
from temperature_monitor import TemperatureMonitor
from heater_supply import HeaterSupply
from currentsourceCAEN import CurrentSourceCAEN
from currentsource100A import CurrentSource100A
from relay_controller import RelayController

# from dmm6500 import DMM6500
# from cs_tdk import CurrentSourceTDK
# from currentsource100mA import CurrentSource100mA
# from temperaturecontroller import TemperatureController
# from pressuremonitor import PressureMonitor
# from voltagesource import VoltageSource

# from magnetcontroller import MagnetController

TEMPERATURE_CONTROLLER = 'LakeShore 336 Temperature Controller'
MAGNET_CONTROLLER = 'American Magnetics Model 430'
CURRENT_SOURCE = 'LakeShore 121 Current Source'
POWER_SUPPLY = 'Keithley 2231-A-30-3 Power Supply'
NANOVOLTMETER = 'Keithley 2182A Nanovoltmeter'
MULTIMETER = 'Keithley DMM6500 Digital Multimeter'
PRESSURE_CONTROLLER = 'Instrutech FlexRax 4000 Vacuum Gauge Controller'

# added, Ben Clark
TEMPERATURE_MONITOR = 'LakeShore 218 Temperature Monitor'
HEATER_SUPPLY = 'Elektro-Automatik  EA-PS 9360-15 heater supply'

        
class HardwareManager(QObject):
    
    log_signal = pyqtSignal(str, str)
    
    hardware_parameters = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
    
    def __init__(self, parent=None, vb=False):
        self.tc, self.pm, self.nvm, self.dmm = None, None, None, None
        # # added, Ben Clark, set these to None in order to test PID with separate script
        # self.tm218 = None
        # self.hs = None

        super(HardwareManager, self).__init__(parent)
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        
        # self.vs = VoltageSource(vb=vb)
        self.vs = None
        self.csCAEN = CurrentSourceCAEN(serialDevice=False, vb=vb)
        self.csTDK = None
        self.cs100A = CurrentSource100A(self.hardware_parameters["a"], self.hardware_parameters["b"], self.hardware_parameters["shuntR"], self.vs, self.csCAEN, self.csTDK, vb=vb)
        # self.cs100mA = CurrentSource100mA(int(self.preferences["sampling_period_tc"]*1000-50), vb=vb)
        # self.relays = Relays()
        
        # self.tc = TemperatureController(int(self.preferences["sampling_period_tc"]*1000-50), serialDevice=True, vb=vb)
        # self.mc = MagnetController(serialDevice=False, vb=vb)
        # self.pm = PressureMonitor(int(self.preferences["sampling_period_pm"]*1000-50), vb=vb)
        self.nvm = NanoVoltmeter(int(self.preferences["sampling_period_nv"]*1000-50), vb=vb)
        # self.dmm = DMM6500(self.hardware_parameters["shuntR"], int(self.preferences["sampling_period_nv"]*1000-50), vb=vb)
        
        # added, Ben Clark
        self.tm218 = TemperatureMonitor()
        self.hs = HeaterSupply()
        self.rc = RelayController(serialDevice=False, vb=vb)

    def initializeHardware(self):
        # self.relays.connectCurrentSource100mATo(device='hallSensor') # connect current source
        # self.relays.connectSampleTo100A(connected=False)
        # self.relays.measureSampleWith(device='nanovoltmeter')
        self.setVoltageOffset()
    
    def __del__(self):
        if self.tc is not None:
            self.tc.rampTemperature(rate=2., ramping=False)
            self.tc.__del__()

        if self.rc is not None:
            self.rc.__del__()
    
    def getPIDSensor(self):    
        return self.tc.getPIDSensor()
        
    def getGateValveState(self):
        return 1-self.relays.getGateValveState()
    
    def getCryocoolerState(self):
        return self.relays.getCryocoolerState()
    
    def getFaradayCupState(self):
        return self.relays.getFaradayCupState()
        
    def getPressureReading(self):
        # commented out, Ben Clark
        # pressure = self.pm.getPressure()
        # if ((self.pm.igOn) & (pressure > 2.5e-3)) | ((not self.pm.igOn) & (pressure < 2.5e-3)):
        #     self.pm.testIgOn()                # adjust the flag if igOn and overpressure or igOff and low pressure
        # return pressure

        # modified version, Ben Clark
        pressure = 0 # temporary
        return pressure
    
    def getMagneticFieldReading(self):
        return self.mc.get_magnetic_field()
    
    def get_setpoint_magnetic_field_reading(self):
        return self.mc.get_setpoint_magnetic_field()
    
    def field_stable(self):
        return self.mc.field_stable()
    
    def getTemperatureReading(self):
        # comment out this function, added return statement -Ben Clark
        # sampleT, targetT, holderT, spareT = self.tc.getTemperatureReadings()
        # heatingPower = self.tc.getHeatingPower()
        # setpointT = self.tc.getSetpointTemperature()
        # return setpointT, sampleT, targetT, holderT, spareT, heatingPower

        # modified version, Ben Clark
        sampleT, holderT = self.tm218.get_temperature_readings()
        return sampleT, holderT

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
    
    def update_temperature_input_configuration(self, configuration):
        self.tc.set_input_configuration(self.hardware_parameters['calibrations'][configuration])

    def enableParallelMode(self, enabled=False):
        # commented out, Ben Clark
        # self.cs100A.enableParallelMode(enabled=enabled)
        return
    
    def setLargeCurrentCalibration(self, a, b):
        # commented out, Ben Clark
        # self.cs100A.updateCalibration(a, b)
        return

    def set_magnetic_field(self, magnetic_field):
        # self.mc.set_magnetic_field(magnetic_field)
        # self.log_signal.emit('MagSet', 'AMI Magnet field set to {:4.2f} T'.format(magnetic_field))
        return

    def setTemperature(self, temperature):
        self.setSetpointTemperature(temperature)
        time.sleep(0.1)
        self.setHeaterOutput(on=True)
        if temperature < self.tc.getTargetTemperature():
            self.setCooler(on=True)
        self.log_signal.emit('TempSet', 'Target temperature set to {:4.2f} K'.format(temperature))
        
    def setSetpointTemperature(self, temperature):
        self.tc.setSetpointTemperature(temperature)
        time.sleep(.1)
    
    def setPIDSensor(self, sensor='B'):
        # commented out, Ben Clark
        # self.tc.setPIDSensor(sensor=sensor)
        return

    def setHeaterOutput(self, on=True):
        self.tc.setHeaterOutput(on)
        time.sleep(.1)
    
    def setCooler(self, on=True):
        #  commented  out, Ben Clark
        # self.relays.setCooler(on=on)
        # if on:
        #     self.log_signal.emit('CoolingModeSet', '1')
        # else:
        #     self.log_signal.emit('CoolingModeSet', '0')
        return
            
    def connectCurrentSource100mATo(self, device='sample'):
        # commented out, Ben Clark
        # self.relays.connectCurrentSource100mATo(device) # connect current source
        # time.sleep(1)
        # self.cs100mA.enable(enabled=True)
        # time.sleep(1)
        return
    
    def connectSampleTo6A(self, connected=True):
        # commented out, Ben Clark
        # self.relays.connectSampleTo6A(connected)
        return
    
    def connectSampleTo100A(self, connected=True):
        # commented out, Ben Clark
        # self.relays.connectSampleTo100A(connected)
        return
    
    def set_channel(self, channel):
        # set_channel connects the relay corresponding to the sample you want to measure
        self.rc.set_relay_states(channel)
    
    def disconnect_relays(self):
        self.rc.all_off()

    def enableCurrentSource100mA(self, enabled=True):
        # commented out, Ben Clark
        # self.cs100mA.enable(enabled)
        # time.sleep(.1)
        return
    
    def measureSampleWith(self, device='picoammeter'):
        # commented out, Ben Clark
        # '''
        #     Calls function from relays, which connects the picoammeter (during irradiation) or the nanovoltmeter (during measurements) to the sample
            
        #     INPUTS:
        #         device (str) 'picoammeter' or 'nanovoltmeter'
        # '''
        # self.relays.measureSampleWith(device)
        return

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
        elif device == self.hardware_parameters['devices']['magnet_controller']['name']:
            connected = self.mc.testConnection()
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
        # commented out, Ben Clark
        # self.relays.setTargetLight(on=on)
        return

    def setChamberLight(self, on=False):
        # commented out, Ben Clark
        # self.relays.setChamberLight(on=on)
        return

    def setVoltageSign(self, sign):
        self.nvm.setPolarity(sign)
        self.log_signal.emit('VoltageSign', 'Voltage sign switched to {} by user. Ic, Tc and Vt measurements will be affected.')

    def resetQPS(self):
        # commented out, Ben Clark
        # self.relays.resetQPS()
        # new version
        self.rc.reset_qps()

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
        elif device_key == 'magnet_controller':
            if self.mc is not None: del self.mc
            self.mc = MagnetController()
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

        
        