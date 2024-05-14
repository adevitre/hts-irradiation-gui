import usbtmc, numpy, re
import inspect
from PyQt5.QtCore import QMutex

class DMM6500:
    '''
    A class for serial communications with a Keithley Digital Multimeter 6500.
    This device uses usbtmc instead of the pyserial library and therefore does not inherit from SerialDevice.
    However, the class is implemented with similar functions.
    
    @author Alexis Devitre
    @lastModified 25/11/2022
    '''
    def __del__(self):
        print('DMM6500::__del__')
        
    def __init__(self, rshunt, waitLock=350):
        self.waitLock = waitLock
        self.rshunt = rshunt
        self.inUse = False
        self.mutex = QMutex()
        try:
            self.ser = usbtmc.Instrument(1510, 25856)
            print('DMM6500 connected!')
            
        except Exception as e:
            if str(e) == 'Device not found [init]':
                print('WARNING: DMM6500 not connected')
            elif str(e) == '[Errno 13] Access denied (insufficient permissions)':
                print('DMM6500 is not configured. The following line must be added to /etc/udev/rules.d/usbtmc.rules :\n SUBSYSTEMS=="usb", ACTION=="add", ATTRS{idVendor}=="05e6", ATTRS{idProduct}=="6$')
            else:
                print(e)
                
    def initialize(self):
        pass
        '''
        print('created')
        self.ser.ask('*RST?')
        print('Rst')
        self.ser.ask(':SENS:FUNC "VOLT:DC?"')
        print('VoltDc')
        self.ser.ask(':SENS:VOLT:RANG 10?')
        print('Range')
        self.ser.ask(':SENS:VOLT:INP AUTO')
        print('INP')
        self.ser.ask(':SENS:VOLT:NPLC 10')
        print('NPLC')
        self.ser.ask(':SENS:VOLT:AZER ON')
        print('AZER ON')
        self.ser.ask(':SENS:VOLT:AVER:TCON REP')
        print('TCONREP')
        self.ser.ask(':SENS:VOLT:AVER:COUN 100')
        print('COUN100')
        self.ser.ask(':SENS:VOLT:AVER:TCON REP')
        print('TCONREP')
        self.ser.ask(':SENS:VOLT:AVER ON')
        print('averON')
    '''
        
    '''
        Returns the status of the serial connection between hardware and software devices.
        
        @returns:
            connected (bool) - status of the serial connection between hardware and software.
    '''
    def isConnected(self):
        if self.ser == None:
            connected = False
        else:
            connected = True
        return connected
    
    '''
        Sends a command that does not expect a reply.
        @inputs:
            command (str) - the device specific serial communication command without ending characters.
    '''
    def write(self, command):
        self.ser.ask(command)
            
    '''
        Sends a command that expects a reply.
        @inputs:
            command (str) - the device specific serial communication command without ending characters.
        @returns:
            response (str) - the expected reply from the hardware device or an empty string.
    '''
    def read(self, command):
        return self.ser.ask(command)
    
    '''
        Requests a current measurement. The DMM6500 measures a voltage which
        is divided by resistance of the shunt resistor to give a current.
        
        @returns:
            current (float) - current in amps.
    '''
    def measure(self):
        r, current = '', numpy.nan
        if self.mutex.tryLock(self.waitLock):
            try:
                r = self.read(':READ?')
                if re.fullmatch("[-+]?[0-9]\\.[0-9]*E[-+][0-9][0-9]", r) is not None:
                    current = float(r)/self.rshunt
                else:
                    print('DMM6500::measure received string with incorrect format')
                    print('Value returned by :READ? is ', r, 'of type ', type(r))
            except Exception as e:
                print('DMM6500::measure raised: ', e)
                print('Value returned by :READ? is ', r, 'of type ', type(r))
                print(inspect.trace())
                print('\n\n\n', inspect.trace()[-1][3])
            finally:
                #pass
                self.mutex.unlock()
        return current
