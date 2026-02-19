from device import Device
# import numpy as np
# import re

'''
    A class for communications with 8 Channel Ethernet Solid State Relay Module
    product SKU: 8ETHSSR001 
    @author Ben Clark, Alexis Devitre, David Fischer
    @lastModified 2/19/2026
'''

class RelayController(Device):

    def __init__(self, wait_lock=950, serialDevice=True, vb=False):
        # not sure yet what value to set for waitlock
        # write this code similar to CAEN because comm over ethernet (TCP/IP) via Telnet
        super().__init__('relay_controller', waitLock=wait_lock, serialDevice=serialDevice, vb=vb)


    