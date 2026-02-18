
from device import Device
import numpy as np
import re

'''
    A SerialDevice class for communications with a Lakeshore Model 218 Temperature Monitor.
    Alexis and David's code has been copied to allow communication with this new device. 
    @author Ben Clark, Alexis Devitre, David Fischer
    @lastModified 7/25/2025
'''

class TemperatureMonitor(Device):
    
    def __init__(self, wait_lock=950):
        # not sure yet what value to set for waitlock
        # serialDevice defaults to True
        super().__init__('temperature_monitor', waitLock=wait_lock) 


    def get_temperature_readings(self):
        '''
        Requests temperature readings (K) from Lakeshore Model 218 temperature monitor
        @returns:
            t1       float - temperature reading in Kelvin for channel 1
            t2      float - ... for channel 2
        '''
        t1 = np.nan
        try:
            r1 = self.read("KRDG? 1") # per manual, 0 is all inputs, 1-8 is single input 
            # if re.fullmatch(self.settings["krdg0_pattern"], r) is not None:
            if re.fullmatch(self.settings["krdga_pattern"], r1) is not None:
                # Alexis old version
                # d = [float(s) for s in r.split(',')]
                t1 = float(r1)
        except Exception as e:
            print('TemperatureMonitor::get_temperature_readings raised:', e)
            print('Value returned by KRDG? 1 is ', r1)

        # channel 2 
        t2 = np.nan
        try:
            r2 = self.read("KRDG? 2")
            if re.fullmatch(self.settings["krdga_pattern"], r2) is not None:
                t2 = float(r2)
        except Exception as e:
            print('TemperatureMonitor::get_temperature_readings raised:', e)
            print('Value returned by KRDG? 2 is ', r2)

            
        return t1, t2
