import numpy, time, os
from configure import load_json
from uldaq import get_daq_device_inventory, DaqDevice, InterfaceType, AOutFlag

hwparams = load_json(fname='hwparams.json', location=os.getcwd()+'/config')

class CurrentSource100A:
    '''
        CurrentSource100A controls the 100A power supply for critical current measurements
        Note: the circuit logic to connect/disconnect this power supply to the sample is in relays.py
    '''
    def __init__(self, a, b, shuntR, voltageSource, currentSourceCAEN, currentSourceTDK):
        self.shuntR = shuntR
        self.vs = voltageSource
        self.csCAEN = currentSourceCAEN
        self.csTDK = currentSourceTDK

        self.updateCalibration(a, b)

    def __del__(self):
        print('Current source 100 A disconnected and released')
        
    def setCurrent(self, current, currentSource=hwparams['LABEL_CS100A'], useCalibration=True, vb=False):
        '''
            setCurrent adjusts the control voltage on the pi to produce the desired current output.
            
            INPUTS
            ------------------------------------------
            current (float)       - desired setpoint in amps.
            currentSource (str)   - Choice of device HP6260B 120A, or 2231A-30-3 6A.
            useCalibration (bool) - use reasonable estimate if called by calibration function
            vb (bool)             - verbose enables printouts for debugging
            RETURNS
            ------------------------------------------
            control_voltage (float) - corresponding value of the control voltage.
        '''
        control_voltage = 0.
        
        if currentSource == hwparams['LABEL_CS006A']:
            self.vs.setCurrent(current)
        
        elif currentSource == hwparams['LABEL_CAEN']:
            self.csCAEN.setCurrent(current)
        
        elif currentSource == hwparams['LABEL_TDK']:
            self.csTDK.setCurrent(current)

        elif currentSource == hwparams['LABEL_CS100A']:
            if useCalibration:
                control_voltage = (current*self.shuntR-self.b)/self.a
                if vb:
                    print('calib {} {}'.format(self.a, self.b))
            else:           
                control_voltage = current*0.58/101.#2./45.692
            print(control_voltage, current)
            # Avoids negative currents or overcurrents set by calibration
            if (control_voltage < 0) | (control_voltage > .75):
                print('Bad calibration')
                if vb: print('Control voltage is out of range with value {}\nFor safety, control voltage was set to NaN.'.format(control_voltage))
                control_voltage = numpy.nan
            
            self.setControlVoltage(control_voltage)
            print(control_voltage, 'control voltage')
            time.sleep(.2) # stabilize the current

        return control_voltage
    
    def enableParallelMode(self, enabled=False):
        self.vs.enableParallelMode(enabled=enabled)

    def setControlVoltage(self, voltage):
        if (self.vs is not None) and (0 <= voltage) and (voltage <= .75):
            self.vs.setVoltage(channel=3, voltage=voltage)
        else:
            print('Request is out of range (0-5V)')
        
    def updateCalibration(self, a, b):
        self.a, self.b = a, b
        self.maxCurrent = 120 #(self.a*4.095+self.b)/self.shuntR