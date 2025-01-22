import numpy, re, time
from device import Device

'''
    A SerialDevice class for communications with a LakeShore 121 current source.
    @author Alexis Devitre devitre@mit.edu, David Fischer dafisch@mit.edu
    @lastModified 2023/07/27
'''
class CurrentSource100mA(Device):
    
    def __init__(self, waitLock=950):
        super().__init__('current_source_tc', waitLock=waitLock)

        if self.ser is not None:
            self.initialize()
    
    def initialize(self):
        self.write('DFLT')    # reset factory settings
        time.sleep(.4)
        self.write('RANGE13') #self.write('RANGE08')  # 1 mA, switch to RANGE13 for user defined current
        time.sleep(.4)
        self.write('IENBL 1') # closes the circuit and enables current to flow. An external relay was added because there was an issue having the live still connected to the load.
    '''
        Change the value of the current output.
        The minimum current is 100 nA. Setting the current to zero sets it to 100 nA.
        
        @inputs:
            value (str) - -001, +001, -100, +100 mA
    '''
    def setCurrent(self, value=0):
        value *= 1e-3
        if value > 0:
            command="SETI +{:3.0e}".format(value)
        else:
            command="SETI {:3.0e}".format(value)
        self.write(command)
        time.sleep(.6) # takes < 300 ms for full-scale change in current (manual page 3)

    '''
    Change the polarity of the current output.
    
    @inputs:
        polarity (int) - 0, 1
    '''
    def setPolarity(self, polarity=0):
        self.write("IPOL {}".format(polarity))
        time.sleep(.6) # takes < 300 ms for full-scale change in current (manual page 3)
        
    '''
        Closes the circuit and enables current to flow
        
        @inputs:
            enabled (bool) - the circuit should be closed allowing current to flow
    '''
    def enable(self, enabled):
        if enabled:
            self.write("IENBL 1")
        else:
            self.write("IENBL 0")
        time.sleep(.4)                   # takes < 300 ms for full-scale change in current (manual page 3)
            
    def isEnabled(self):
        return self.read("IENBL?")
