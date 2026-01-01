import numpy, time, re
from device import Device
'''
    A CurrentSource class for communications with a TDK-lambda GEN6-100 Current Source.
    @author Alexis Devitre
    @lastModified 10/07/2024
'''
class CurrentSourceTDK(Device):
    
    def __init__(self, waitLock=950, serialDevice=True, vb=False):
        super().__init__('current_source_tdk', waitLock=waitLock, serialDevice=serialDevice, vb=vb)
        #self.write("RST")
        self.write('ADR 6') # wake up the power supply
        time.sleep(.05)
        self.write("PV 6") # set voltage to maximum
        time.sleep(.05)
        self.write("OUT ON") # turn the output on
        time.sleep(.05)
        self.write("ADR 6")  # wake up the power supply after OUT
        time.sleep(.05)
        #print(self.read('ADR 6')) # wake up the power supply
        #print(self.read("PV 4"))  # set voltage to maximum
        #print(self.read("OUT 0")) # turn the output on
        #print(self.read("ADR 6"))  # wake up the power supply after OUT

        self.setCurrent(current=0)
        
    '''
        Sets the current on the TDK-lambda current source
        @inputs:
            current (float) - desired current
    '''
    def setCurrent(self, current=0.00):
        try:
            self.write('PC {:0>6.2f}'.format(current))
            time.sleep(.05) # we need a minimum delay of 50 ms between serial instructions or the current source doesn't respond correctly to serial commands
        except Exception as e:
            print('CurrentSourceTDK::setCurrent raised: ', e)