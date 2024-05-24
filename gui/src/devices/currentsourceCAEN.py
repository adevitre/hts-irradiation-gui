import numpy, time, re
from serialdevice import SerialDevice
from device import Device
'''
    A CurrentSource class for communications with a CAEN FAST-PS-IK5-100-15 Current Source.
    @author Alexis Devitre, David Fischer
    @lastModified 28/03/2024
'''
class CurrentSourceCAEN(Device):
    
    def __init__(self, waitLock=950, serialDevice=True):
        super().__init__('current_source_caen', waitLock=waitLock, serialDevice=False)
        self.write("MRESET")
        self.read("MON")
        self.write("MWG:35:0")
        self.write("SETFLOAT:F")
        self.write("UPMODE:NORMAL")
        self.write("LOOP:I")
        
    '''
        Sets the current on the CAEN current source
        @inputs:
            current (float) - desired current
    '''
    def setCurrent(self, current=0.0000):
        try:
            self.write('MWI:{:4.4f}'.format(current))
        except Exception as e:
            print('CurrentSourceCAEN::setCurrent raised: ', e)