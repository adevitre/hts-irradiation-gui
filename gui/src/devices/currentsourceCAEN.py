import numpy, time, re
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
        self.write("MON")
        self.write("MWG:35:0")
        self.write("SETFLOAT:F")
        self.write("UPMODE:NORMAL")
        self.write("LOOP:I")
        self.write("MOFF")
        
    '''
        Sets the current on the CAEN current source
        @inputs:
            current (float) - desired current
    '''
    def setCurrent(self, current=0.0000):
        try:
            if current < 0.001: # This is to prevent the current spike when opening the relay.
                self.write('MWI:{:4.4f}'.format(0))
                self.write('MOFF')
            else:
                self.write('MON')
                self.write('MWI:{:4.4f}'.format(current))
            time.sleep(0.004) # 2x required

        except Exception as e:
            print('CurrentSourceCAEN::setCurrent raised: ', e)
    
    def getCurrent(self):
        current = numpy.nan
        try:
            r = self.read('MRI')
            current = float(re.findall(r"[-+]?\d*\.\d+|\d+", r)[0])
            time.sleep(0.002)
        except Exception as e:
            print('CurrentSourceCAEN::getCurrent raised: ', e)
        return current