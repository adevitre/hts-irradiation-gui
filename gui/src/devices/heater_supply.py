from device import Device
import numpy as np
import re

'''
    A class for communications with Elektro-Automatik  EA-PS 9360-15 power supply.
    Alexis and David's code has been copied to allow communication with this new device. 
    @author Ben Clark, Alexis Devitre, David Fischer
    @lastModified 7/30/2025
'''

class HeaterSupply(Device):

    def __init__(self, wait_lock=950):
        # not sure yet what value to set for waitlock
        # write this code similar to CAEN because comm over ethernet (TCP/IP) via SCPI
        super().__init__('heater_supply', waitLock=wait_lock, serialDevice=False)

        # may need to add initializing commands here

    