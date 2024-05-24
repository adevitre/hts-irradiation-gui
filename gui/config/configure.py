from serial.tools.list_ports import comports
from serial.tools import list_ports
import os
import re, subprocess, time, serial
import numpy as np
import json

def configure_ports(vb=True, config_directory='config'):
    '''
        configure_ports iterates through all occupied serial ports and identifies which device is connected to which port
        this information is then stored in config/configuration.json
    '''

    t0 = time.time()
    
    hwparams = load_json(fname='hwparams.json', location=config_directory)
    devices = hwparams["devices"]

    configuration = {}
    for device in list(devices.keys()):
        configuration[device] = None

    for comport in comports():
        port = comport[0]
        print('\n', port, '\n')

        for device in ['pressure_monitor', 'nanovoltmeter', 'current_source_tc', 'temperature_controller']: # list(devices.keys()): #

            if configuration[device] is None:
            
                it_worked = configure_device(devices[device], port, vb=True) # at this point we have validated that the device is connected to the port
                if it_worked:
                    if vb: print('{} connected to {}'.format(device, port))
                    configuration[device] = port
                    devices[device]['port'] = port
                    #update_json(devices, fname='hwparams.json', location=config_directory)
                    break
            
    if vb: print('\n\nConfigured in {:4.2f} seconds'.format(time.time()-t0))

    for device in list(devices.keys()):
        print(devices[device]['name'], devices[device]['port'])
    time.sleep(.2)


def configure_device(device, usb_port='/dev/ttyUSB0', vb=False):
    '''
        configure_device tries to connect a device through a serial port based on the serial communication parameters
        stored in config/devicename.json
        
        INPUTS
        -----------------------------------
        device (dict) - a dictionary containing the information needed to establish a serial communication with the device
        usb_port (str) - port to which the device should be connected; e.g. /dev/ttyUSB0
    '''
    ser, success = None, False
    try:
        if vb:
            print('Trying to open port of device '+ str(device['name']))
        ser = serial.Serial(usb_port, baudrate=device['baudrate'], bytesize=device['bytesize'], stopbits=device['stopbits'], parity=device['parity'], xonxoff=device['xonxoff'], timeout=1, exclusive=True)
        ser.write(bytes(device['greeting']+device['ending'],'utf-8'))
        r = ser.read(100).decode('utf-8', errors='backslashreplace').strip()
        
        print(r)

        if re.search(device['response'], r):
            success = True

    except Exception as e:
        print(e)
            
    return success


def update_json(data, fname='preferences.json', location='config'):
    '''
    store a dictionary in json file

    Parameters
    ----------
    
    data       - (dic) dictionary with data to be stored
    filename   - (str) name of the file
    location   - (str) parent directory (in case you keep the file elsewhere)
    '''
    with open(location+'/{}'.format(fname), 'w') as f:
        json.dump(data, f, indent=2, sort_keys=True)


def load_json(fname='preferences.json', location='config'):
    '''
    read reads a json file as a dictionary

    Parameters
    ----------
    fname    - (str) name of the file
    location - (str) parent directory (in case you keep the file elsewhere)

    Returns
    ---------- 
    (dic) dictionary with data
    '''
    try:
        if location is not None:
            path_to_json = location+'/{}'.format(fname)
        else:
            path_to_json = fname
        with open(path_to_json) as f:
            dictionary = json.load(f)
    except IOError:
        raise IOError('{} not found in {}.'.format(fname, location))
        dictionary = {}
    except ValueError:
        raise ValueError("{} is corrupted.".format(fname))
        dictionary = {}
        
    return dictionary