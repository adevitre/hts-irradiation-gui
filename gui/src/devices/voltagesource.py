import numpy, re, time
from serialdevice import SerialDevice

'''
    A SerialDevice class for communications with a Keithley 2231A-30-3 Triple-Channel DC Power Supply.
    @author Alexis Devitre, Ben Clark
    @lastModified 15/06/2023
'''
class VoltageSource(SerialDevice):
    
    def __init__(self, waitLock=350):
        super().__init__('voltagesource', waitLock=waitLock)
        
        if self.ser is not None:
            self.initialize()
    
    def initialize(self):
        self.write('SYST:REM')
        self.write('*rst')
        self.write('*cls')
        self.write('APPLY CH1,0.0')
        self.write('APPLY CH2,0.0')
        self.write('APPLY CH3,0.0')
        self.write('CHAN:OUTP ON')
        self.enableParallelMode(enabled=False)
        time.sleep(.1)

    '''
        Applies voltage to the desired channel
        
        @returns:
            channel (int) - 1, 2, or 3
            voltage (float) - voltage in volts.
    '''
    def setVoltage(self, channel, voltage):
        try:
            self.write('APPLY CH{},{:4.3f}'.format(channel, voltage))
            self.write('CHAN:OUTP ON')
            time.sleep(0.15)
        except Exception as e:
            print('Exception raised in setVoltage:', e)
            print('Channel {}; Voltage {:4.3f}'.format(channel, voltage))

    '''
        Applies current from combined channels 1 and 2 connected in parallel
        
        @returns:
            channel (int) - 1 and 2
            current (float) - current in amperes.
    '''
    def setCurrent(self, current):
        try:
            self.write('APPLY CH1,10,{:4.3f}'.format(current))
            self.write('CHAN:OUTP ON')
            time.sleep(0.15)
        except Exception as e:
            print('Exception raised in setCurrent:', e)
            print('Channel {}; Current {:4.3f}'.format(1, current))

    def enableParallelMode(self, enabled=False):
        if enabled:
            self.write('INSTRUMENT:COMBINE:PARALLEL')
        else:
            self.write('INSTRUMENT:COMBINE:OFF')