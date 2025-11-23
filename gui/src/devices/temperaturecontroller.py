import numpy, time, re
from device import Device
'''
    A SerialDevice class for communications with a Lakeshore 336 temperature controller.
    @author Alexis Devitre, David Fischer
    @lastModified 21/08/2021
'''
class TemperatureController(Device):
    
    def __init__(self, waitLock=950, serialDevice=True, vb=False):
        super().__init__('temperature_controller', waitLock=waitLock, serialDevice=serialDevice, vb=vb)
        self.write('TLIMIT B,320')
        self.rampTemperature(rate=3, ramping=False)
        self.setHeaterOutput(on=True)
        
    '''
        Requests temperature readings (K) from channel a, b, c and d from the
        Lakeshore 336 Temperature Controller.
        @returns:
            temperatures (float, array) - temperature reading on each channel in kelvin
    '''
    def getTemperatureReadings(self):
        d = [numpy.nan, numpy.nan, numpy.nan, numpy.nan]
        try:
            r = self.read("KRDG? 0") # 
            if re.fullmatch(self.settings["krdg0_pattern"], r) is not None:
                d = [float(s) for s in r.split(',')]
        except Exception as e:
            print('TemperatureController::getTemperatureReadings raised:', e)
            print('Value returned by KRDG? 0 is ', r)
        return tuple(d)
    
    '''
        Requests one temperature reading (K) from channel a (sample).
        @returns:
            temperature (float) - temperature reading from channel a in kelvin
    '''
    def getSampleTemperature(self):
        temperature = numpy.nan
        try:
            r = self.read("KRDG? a")
            if re.fullmatch(self.settings["krdga_pattern"], r) is not None:
                temperature = float(r)
        except Exception as e:
            print('TemperatureController::getSampleTemperature raised:', e)
            print('Value returned by KRDG? a is ', r)
        return temperature
    
    '''
        Requests one temperature reading (K) from channel b (sample).
        @returns:
            temperature (float) - temperature reading from channel a in kelvin
    '''
    def getTargetTemperature(self):
        temperature = numpy.nan
        try:
            r = self.read("KRDG? b")
            if re.fullmatch(self.settings["krdga_pattern"], r) is not None:
                temperature = float(r)
        except Exception as e:
            print('TemperatureController::getTargetTemperature raised:', e)
            print('Value returned by KRDG? b is ', r)
        return temperature
    
    '''
        Requests one reading of the current level of the PID heater.
        @returns:
            power (float) - percentage of the maximum heating power of the PID controlled heater (50W).
    '''
    def getHeatingPower(self):
        power = numpy.nan
        try:
            r = self.read('AOUT? 3') # heaterVoltagePercent
            if re.fullmatch(self.settings["aout_pattern"], r) is not None:
                power = (120.*float(r)/100.)**2/36 # R_eff = 36 Ohm, V_lim = 120 V
        except Exception as e:
            print('TemperatureController::getHeatingPower raised:', e)
            print('Value returned by AOUT? 3 is ', r)
        return power
    
    '''
        Requests one reading of the setpoint temperature.
        @returns:
            setpoint (float) - setpoint temperature in kelvin.
    '''
    def getSetpointTemperature(self):
        setpoint = numpy.nan
        try:
            r = self.read("SETP? 3")
            if re.fullmatch(self.settings["setp_pattern"], r) is not None:
                setpoint = float(r)
        except Exception as e:
            print('TemperatureController::getSetpointTemperature raised:', e)
            print('Value returned by SETP? 3 is ', r)
        return setpoint
    
    '''
        Changes the setpoint temperature.
        @inputs:
            setpoint (float) - setpoint temperature in kelvin.
    '''
    def setSetpointTemperature(self, setpoint):
        try:
            self.write("SETP 3, {:3.3f}".format(setpoint))
        except Exception as e:
            print('TemperatureController::setSetpointTemperature raised: ', e)
    
    def getPIDSensor(self):
        sensor = None
        try:
            r = self.read("OUTMODE? 3")
            sensor = int(r.split(',')[1])
        except Exception as e:
            print('TemperatureController::getOutmode raised: ', e)
        return sensor

    def setPIDSensor(self, sensor):
        try:
            if sensor == 'A':
                self.write("OUTMODE 3,1,1,0")
                print('Sensor A')
            elif sensor == 'B':
                self.write("OUTMODE 3,1,2,0")
                print('Sensor B')
            elif sensor == 'C':
                self.write("OUTMODE 3,1,3,0")
                print('Sensor C')
            elif sensor == 'D':
                self.write("OUTMODE 3,1,4,0")
                print('Sensor D')
            else:
                print('Invalid sensor name')    
            
        except Exception as e:
            print('TemperatureController::setOutmode raised: ', e)

    '''
        Changes the heating output 3 status
        @inputs:
            on (int) - True (1) False (0)
    '''
    def setHeaterOutput(self, on=True):
        try:
            if on:
                self.write('RANGE 3,{}'.format(1))
            else:
                self.write('RANGE 3,{}'.format(0))
        except Exception as e:
            print('TemperatureController::setHeaterOutput raised: ', e)
    
    def rampTemperature(self, rate, ramping=True):
        try:
            if ramping:
                self.write("RAMP 3,1,{:3.4f}".format(rate))
            else:
                self.write("RAMP 3,0,{:3.4f}".format(rate))
        except Exception as e:
            print('TemperatureController::rampTemperature raised: ', e)
    
    def isRamping(self):
        try:
            ramping = False
            r = self.read("RAMPST? 3")
            if (r is not None) and (r == 1):
                ramping = True
        except Exception as e:
            print('TemperatureController::isRamping raised: ', e)
        return ramping