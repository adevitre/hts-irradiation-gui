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

        self.write("reset") # turns off all relays


    def __del__(self):
        self.write("reset") # turns off all relays


    def set_relay_states(self, channel):
        # channel: (int) the channel for the relay you want turned on

        active_channel = channel
        # assuming there are 4 channels in use (ch0 - ch3)
        # this gets all the channel numbers (integers) for the inactive channels
        # e.g. if channel is 1, it will return [2, 3, 0]
            # if channel is 0, returns [1, 2, 3]
        inactive_channels = [(channel+i)%4 for i in [1,2,3]]

        # turn the active channel on
        self.write("relay on " + str(active_channel))

        # turn the three other inactive channels off
        self.write("relay off " + str(inactive_channels[0]))
        self.write("relay off " + str(inactive_channels[1]))
        self.write("relay off " + str(inactive_channels[2]))
    
    def all_off(self):
        self.write("reset") # turns off all relays

    