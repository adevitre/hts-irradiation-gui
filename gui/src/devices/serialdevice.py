from configure import load_json
import os, re, serial
from PyQt5.QtCore import QMutex

LATEST_CONFIG_LOCATION = '/home/htsirradiation/Documents/hts-irradiation-gui/config/' #os.getcwd()+'/config'

'''
    A generic class for serial communication (reading data and sending commands) with hardware devices.
    
    @author Alexis Devitre
    @lastModified 21/08/2021
'''
class SerialDevice:
    
    '''
        Establishes the serial connection between hardware and software devices.
        @inputs:
            device (str) - name of the device as it appears in the title of the file containing serial settings
    '''
    def __init__(self, device, waitLock):
        self.waitLock = waitLock
        self.ser = None
        self.mutex = QMutex()
        self.settings = load_json('hwparams.json', location=LATEST_CONFIG_LOCATION)['devices'][device]
        try:
            self.ser = serial.Serial(self.settings['port'], baudrate=self.settings['baudrate'], bytesize=self.settings['bytesize'], stopbits=self.settings['stopbits'], parity=self.settings['parity'], xonxoff=self.settings['xonxoff'], timeout=self.settings['timeout'])
            if not self.testSerialConnection(vb=True):
               self.ser.close()
               self.ser = None
        except Exception as e:
            print('{} __init__() raised '.format(self.settings['name']), e)
            print('WARNING: port {} was not connected'.format(self.settings['port']))

    def __del__(self):
        self.disconnect()
            
    '''
        Safely terminates the serial connection between hardware and software devices.
    '''
    def disconnect(self):
        print('Deleted {}!'.format(self.settings['name']))
        if self.ser is not None:
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            self.ser.close()
            self.ser = None
    
    def testSerialConnection(self, vb=False):
        if (re.search(self.settings['response'], self.read(self.settings['greeting']))):
            self.connected = True
            if vb: print(self.settings['port'] + ': {} connected!'.format(self.settings['name']))
        else:
            self.connected = False
            if vb: print('WARNING: port {} is connected to a device which is not {}'.format(self.settings['port'], self.settings['name']))
        return self.connected

    '''
        Sends a command that does not expect a reply.
        @inputs:
            command (str) - the device specific serial communication command without ending characters.
    '''
    def write(self, command):
        self.mutex.lock()
        try:
            if self.ser is not None:
                self.ser.write(bytes(command + self.settings['ending'],'utf-8'))
        except Exception as e:
            print("{} {}".format(self.settings['name'], e))
        finally:
            #pass
            self.mutex.unlock()

    '''
        Sends a command that expects a reply.
        @inputs:
            command (str) - the device specific serial communication command without ending characters.
        @returns:
            response (str) - the expected reply from the hardware device or an empty string.
    '''
    def read(self, command):
        response = ''
        if self.mutex.tryLock(self.waitLock):
            try:
                if self.ser is not None:
                    self.ser.write(bytes(command + self.settings['ending'],'utf-8'))
                    response = self.ser.readline().decode('utf-8').strip()
            except Exception as e:
                print('While reading {} from {}, SerialDevice:read raised:'.format(command, self.settings['name']), e)
                response = ''
            finally:
                #pass
                self.mutex.unlock()
        else:
            print('{} not locking while attempting {}'.format(self.settings['name'], command))
        return response
    
