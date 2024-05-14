import sys
import serial
import time

RELAYBOARD_ADDR_100A_SAMPLE = 0  # checked 14/03/2023
RELAYBOARD_ADDR_100mA_SAMPLE = 1 # checked 14/03/2023
RELAYBOARD_ADDR_6A_SAMPLE = 2    # not checked
RELAYBOARD_ADDR_TURBO_SCROLL = 3 # checked 14/03/2023
RELAYBOARD_ADDR_COLDHEAD = 10    # checked 14/03/2023
RELAYBOARD_ADDR_NVM_PICO = 12    # checked 14/03/2023
RELAYBOARD_ADDR_TARGETLIGHT = 13    # checked NOT
RELAYBOARD_ADDR_CHAMBERLIGHT = 14    # checked NOT
RELAYBOARD_ADDR_FARADAYCUP = 30

class Relays:
    
    def __init__(self):
        '''
            __init__ instantiates an object of class Relays
        '''
        self.ser = serial.Serial('/dev/ttyACM0', 19200, timeout=1)
        #for index in range(32): 
        
        self.measureSampleWith(device='nanovoltmeter')
        self.connectCurrentSource100mATo(device='hallSensor')
        self.connectSampleTo100A(connected=False)
    
    def __del__(self):
        '''
            __del__ destroys an object of class Relays ensuring that:
                - Sample is connected to nanovoltmeter
                - Sample is connected to 100A CS
                - Sample is disconnected from 100 mA CS
                - Serial connection to the relay board is closed.
        ''' 
        self.measureSampleWith(device='nanovoltmeter')
        self.connectCurrentSource100mATo(device='hallSensor')
        self.connectSampleTo100A(connected=False)
        self.ser.close()
    
    def setRelayState(self, index, state='on'):
        '''
            setRelayState switches the relay of specified index (0-31) to specified position (on/off).
            The original labeling of the relays is mapped to a numerical sequence from 0 toi 31.
            
            INPUTS
                * index (int) relay index from 0-31
                * state (str) 'on' or 'off'
        '''
        if (int(index) < 10):
            index = str(index)
        else:
            index = chr(55 + int(index))

        self.ser.write(bytes("relay {} {}\r".format(state, index), 'utf-8'))
    
    def getRelayState(self, index):
        '''
            getRelayState obtains the state ON/OFF of the relay with specified index (0-31).
            
            INPUTS
                * index (int) relay index from 0-31

            RETURNS
                * state (str) 0 if 'on' or 1 if 'off'
        '''
        if (int(index) < 10):
            index = str(index)
        else:
            index = chr(55 + int(index))

        self.ser.write(bytes('relay read {}\r'.format(index), 'utf-8'))
        r = str(self.ser.read(200).decode('utf-8').strip()).split('\n\r')[-2]
        
        if 'on' in r:
            state = 0
        elif 'off' in r:
            state = 1

        return state

    def openGateValve(self, opened=True):
        '''
            Opens and closes the gate valve shielding the turbo pump.
                        
            INPUTS
                * opened (bool) - state of the gate valve: Open (True, closes the relay 'on') Closed (False, opens the relay 'off')
        '''
        if opened:
            self.setRelayState(RELAYBOARD_ADDR_TURBO_SCROLL, state='on')
        else:            
            self.setRelayState(RELAYBOARD_ADDR_TURBO_SCROLL, state='off')
            
    def setCooler(self, on=True):
        '''
            Turns ON/OFF the compressor on the AL230 cryocooler
            
            INPUTS:
                on (bool) - Compressor and Motor OFF (True, opens the relay 'off'), Compressor and Motor ON  (1, closes the relay 'on')
        '''
        if on:
            self.setRelayState(RELAYBOARD_ADDR_COLDHEAD, state='off')
        else:            
            self.setRelayState(RELAYBOARD_ADDR_COLDHEAD, state='on')
    

    def insertFaradayCup(self, inserted=True):
        '''
            Inserts or retracts the Faraday cup obn the beamline
            
            INPUTS:
                inserted (bool) - The faraday cup is inserted in the beam path (True, opens the relay 'off'), the Faraday cup is retracted to irradiate the sample  (1, closes the relay 'on')
        '''
        if inserted:
            self.setRelayState(RELAYBOARD_ADDR_FARADAYCUP, state='off')
        else:            
            self.setRelayState(RELAYBOARD_ADDR_FARADAYCUP, state='on')


    def connectSampleTo100A(self, connected=True):
        '''
            Connects/Disconnects the 100A power supply (HP 6260B) to the sample
            
            INPUTS:
                connected (bool) Desired state of the connection opened (False) or closed (True)
        '''
        if connected:
            self.setRelayState(RELAYBOARD_ADDR_100A_SAMPLE, state='on')
        else:   
            self.setRelayState(RELAYBOARD_ADDR_100A_SAMPLE, state='off')
    
    def connectSampleTo6A(self, connected=False):
        '''
            Connects/Disconnects the 6A power supply (KEITHLEY 2231A-30-3) to the sample
            
            INPUTS:
                connected (bool) Desired state of the connection opened (False) or closed (True)
        '''
        if connected:
            self.setRelayState(RELAYBOARD_ADDR_6A_SAMPLE, state='on')
        else:
            self.setRelayState(RELAYBOARD_ADDR_6A_SAMPLE, state='off')

    def connectCurrentSource100mATo(self, device='sample'):
        '''
            Connects/Disconnects the 100mA current source to the sample or Hall sensor
            
            INPUTS:
                connected (bool) Desired state of the connection opened (False) or closed (True)
        '''
        if device == 'sample':
            self.setRelayState(RELAYBOARD_ADDR_100mA_SAMPLE, state='on')
        elif device == 'hallSensor':
            self.setRelayState(RELAYBOARD_ADDR_100mA_SAMPLE, state='off')
    
    def switchHatLight(self, on=False):
        '''
            Switches the light on/off inside the hat for collimator alignment.
            
            INPUTS:
                on (bool) Desired state of the light True (light on), False (light off).
        '''
        if on:
            self.setRelayState(RELAYBOARD_ADDR_HATLIGHT, state='on')
        else:
            self.setRelayState(RELAYBOARD_ADDR_HATLIGHT, state='off')

    def measureSampleWith(self, device='picoammeter'):
        '''
            Connects the picoammeter (during irradiation) or the nanovoltmeter (during measurements) to the sample
            
            INPUTS:
                device (str) 'picoammeter' or 'nanovoltameter'
        '''
        if device == 'picoammeter':
            self.setRelayState(RELAYBOARD_ADDR_NVM_PICO, state='on')
        elif device == 'nanovoltmeter':
            self.setRelayState(RELAYBOARD_ADDR_NVM_PICO, state='off')


    def getGateValveState(self):
        '''
            getGateValveState determines if the turbo valve is open
            
            RETURNS:
                state (bool) - 0 if Turbo pump is connected, 1 if Roughing pump is connected
        '''
        return self.getRelayState(RELAYBOARD_ADDR_TURBO_SCROLL)
    

    def getCryocoolerState(self):
        '''
            getCryocoolerState determines if the cryohead is cooling
            
            RETURNS:
                state (bool) - 0 if cryohead is cooling, 1 if it's not.
        '''
        return self.getRelayState(RELAYBOARD_ADDR_COLDHEAD)


    def getFaradayCupState(self):
        '''
            getFaradayCupState determines if Faraday cup is inserted
            
            RETURNS:
                state (bool) - 1 if Faraday Cup is retracted, 0 if it's inserted.
        '''
        return self.getRelayState(RELAYBOARD_ADDR_FARADAYCUP)
    
    def setTargetLight(self, on=False):
        if on:
            self.setRelayState(index=RELAYBOARD_ADDR_TARGETLIGHT, state='on')
        else:
            self.setRelayState(index=RELAYBOARD_ADDR_TARGETLIGHT, state='off')

    def setChamberLight(self, on=False):
        if on:
            self.setRelayState(index=RELAYBOARD_ADDR_CHAMBERLIGHT, state='on')
        else:
            self.setRelayState(index=RELAYBOARD_ADDR_CHAMBERLIGHT, state='off')