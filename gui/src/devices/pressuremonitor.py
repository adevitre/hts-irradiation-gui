import numpy, re
from serialdevice import SerialDevice

'''
    A SerialDevice class for communications with a FlexRax4000 pressure monitor.
    
    @author Alexis Devitre, David Fischer
    @lastModified 21/08/2021
'''
class PressureMonitor(SerialDevice):
    
    def __init__(self, waitLock=2950):
        super().__init__('pressure_monitor', waitLock=waitLock)
        self.igOn=False
        if self.ser is not None:
            self.testIgOn()
    
    '''
        Tests if the IG was turned on by the FlexRax4000. The threshold for the FlexRax4000
        can be changed on the device and will only work if the IG3 is set to be controlled by CG1.
        
        @returns:
            self.igOn (bool) - current status of IG3
    '''
    def testIgOn(self):
        self.igOn = False
        try:
            r = self.read("#01IG4S")
            if re.fullmatch(self.settings["ig3s_pattern"], r) is not None:
                self.igOn = bool(float(r[4])) # the pattern is 0 or 1 preceeded by * and three whitespaces
            else:
                print('PressureMonitor::testIgOn received string with incorrect format')
                print('Value returned by #01IG4S is ', r)
        except Exception as e:
            print('PressureMonitor::testIgOn returned: ', e)
            print('Value returned by #01IG4S is ', r)
        return self.igOn
            
    '''
        Returns pressure readings (torr) from the high (IG3) or low (CG1) vacuum gauges
        of the FlexRax 4000 Pressure Monitor.
        
        @returns:
            pressure (float) - from either the low or high pressure gauges
    '''
    def getPressure(self):
        r, command, pressure = '', "#01RDCG1", numpy.nan
        try:
            if self.igOn:
                command = "#01RDIG4"
            r = self.read(command)
            if re.fullmatch(self.settings["RD_pattern"], r) is not None:
                pressure = float(r[3:]) # float value preceeded by * and three whitespaces
            else:
                print('PressureMonitor::getPressure received string with incorrect format')
                print('Value returned by {} is '.format(command), r)
                
        except Exception as e:
            print('PressureMonitor::getPressure returned: ', e)
            print('Value returned by {} is '.format(command), r)
        return pressure
    
