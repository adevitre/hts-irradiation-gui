from configure import load_json
import os, re, serial, socket
from PyQt5.QtCore import QMutex

'''
    A generic class for reading data and sending commands with hardware devices.
    
    @author Alexis Devitre
    @lastModified 05/02/2024
'''
class Device:
    '''
        Establishes a connection between hardware and software devices.
        @inputs:
            device (str) - name of the device as it appears in the title of the file containing serial settings
    '''
    def __init__(self, device, waitLock, serialDevice=True):
        self.waitLock = waitLock
        self.ser, self.serialDevice = None, serialDevice
        self.mutex = QMutex()
        self.settings = load_json('hwparams.json', location=os.getcwd()+'/config')['devices'][device]

        if self.serialDevice:
            try:
                self.ser = serial.Serial(self.settings['port'], baudrate=self.settings['baudrate'], bytesize=self.settings['bytesize'], stopbits=self.settings['stopbits'], parity=self.settings['parity'], xonxoff=self.settings['xonxoff'], timeout=self.settings['timeout'])
                if not self.testConnection(vb=True):
                    self.ser.close()
                    self.ser = None
            except Exception as e:
                print('{} __init__() raised '.format(self.settings['name']), e)
                print('WARNING: port {} was not connected'.format(self.settings['port']))
        else:
            try:
                self.ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # TCP
                self.ser.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                self.ser.connect((self.settings['ip'], self.settings['ethernet_port']))
                self.closeSocket()
                if not self.testConnection(vb=True):
                    self.ser = None

            except Exception as e:
                print('{} __init__() raised '.format(self.settings['name']), e)
                print('WARNING: socket could not connect to {}'.format(self.settings['ip']))

    def __del__(self):
        self.disconnect()
            
    '''
        Safely terminates the serial connection between hardware and software devices.
    '''
    def disconnect(self):
        print('Deleted {}!'.format(self.settings['name']))
        if self.ser is not None:
            self.ser.close()
            self.ser = None
    
    def testConnection(self, vb=False):
        response = self.read(self.settings['greeting'])
        if (re.search(self.settings['response'], response)):
            self.connected = True
            if vb: 
                if self.serialDevice:
                    print(self.settings['port'] + ': {} connected!'.format(self.settings['name']))
                else:
                    print(self.settings['ip'] + ': {} connected!'.format(self.settings['name']))
        else:
            self.connected = False
            if vb:
                if self.serialDevice:
                    print('WARNING: {} is connected to a device which is not {}'.format(self.settings['port'], self.settings['name']))
                else:
                    print('WARNING: {} is connected to a device which is not {}'.format(self.settings['ip'], self.settings['name']))
                
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
                if self.serialDevice:
                    self.ser.write(bytes(command + self.settings['ending'],'utf-8'))
                else:
                    self.openSocket()
                    self.ser.sendall(bytes(command+self.settings['ending'], 'utf-8'))
                    self.closeSocket()
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
                    if self.serialDevice:
                        self.ser.write(bytes(command + self.settings['ending'],'utf-8'))
                        response = self.ser.readline().decode('utf-8').strip()
                    else:
                        self.openSocket()
                        self.ser.sendall((command+self.settings['ending']).encode())
                        response, listening = '', True
                        while listening:
                            response += self.ser.recv(128).decode()
                            if self.settings['ending'] in response:
                                response = response.strip()
                                listening = False
                        self.closeSocket()
            except Exception as e:
                print('While reading {} from {}, SerialDevice:read raised:'.format(command, self.settings['name']), e)
                response = ''
            finally:
                self.mutex.unlock()
                #pass
        else:
            print('{} not locking while attempting {}'.format(self.settings['name'], command))
        return response
    
    def openSocket(self):
        self.ser = socket.socket(socket.AF_INET, socket.SOCK_STREAM)     # TCP
        self.ser.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.ser.connect((self.settings['ip'], self.settings['ethernet_port']))
    
    def closeSocket(self):
        self.ser.close()