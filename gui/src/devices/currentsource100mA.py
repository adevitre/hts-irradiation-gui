import numpy, re, time
from device import Device

class CurrentSource100mA(Device):
    '''
        A SerialDevice class for communications with a LakeShore 121 current source.
        @author Alexis Devitre devitre@mit.edu, David Fischer dafisch@mit.edu
        @lastModified 2023/07/27
    '''

    def __init__(self, waitLock=950, vb=False):
        super().__init__('current_source_tc', waitLock=waitLock, vb=vb)

        if self.ser is not None:
            self.initialize()
    
    def initialize(self):
        self.write('DFLT')    # reset factory settings
        time.sleep(.4)
        self.write('RANGE13') #self.write('RANGE08')  # 1 mA, switch to RANGE13 for user defined current
        time.sleep(.4)
        self.write('IENBL 1') # closes the circuit and enables current to flow. An external relay was added because there was an issue having the live still connected to the load.
        time.sleep(.4)
        
    def setCurrent(self, value=0):
        '''
            Changes the value of the current output. The minimum current is 100 nA. Setting the current to zero sets it to 100 nA.
            
            @inputs:
                value (str) - setpoint for the current in amps (A)
        '''
        #self.write('IENBL 0') # disable the output before changing

        #if numpy.abs(value) <= 100e-9: # In case the current source is unhappy with out of range values
        #    set_value = 100e-9
        #else:
        #    set_value = value

        if value >= 0:
            command="SETI +{:3.0e}".format(numpy.abs(value)) # absolute value in case some asshole requests -0.0 -.-'
        else:
            command="SETI {:3.0e}".format(value) # negative floats come with a - sign
        self.write(command)
        time.sleep(.4) # takes < 300 ms for full-scale change in current (manual page 3)

        #if numpy.abs(value) >= 100e-6: # if we want to apply something greater than the minimum (100 nA) we must enable the output.
        #    self.write('IENBL 1')
    
    def setPolarity(self, polarity=0):
        '''
            Change the polarity of the current output.
            
            @inputs:
                polarity (int) - 0, 1
        '''
        self.write("IPOL {}".format(polarity))
        time.sleep(.6) # takes < 300 ms for full-scale change in current (manual page 3)
        
    def enable(self, enabled):
        '''
            Closes the circuit, enabling current to flow
            @inputs:
                enabled (bool) - the circuit should be closed allowing current to flow
        '''
        if enabled:
            self.write("IENBL 1")
        else:
            self.write("IENBL 0")
        time.sleep(.4)                   # takes < 300 ms for full-scale change in current (manual page 3)
            
    def isEnabled(self):
        return self.read("IENBL?")
