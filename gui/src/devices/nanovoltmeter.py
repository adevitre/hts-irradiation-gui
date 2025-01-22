import numpy, re, time
from device import Device

'''
    A SerialDevice class for communications with a Keithley2182A nanovoltmeter.
    @author Alexis Devitre, David Fischer
    @lastModified 28/04/2022
'''
class NanoVoltmeter(Device):
    
    def __init__(self, waitLock=350):
        super().__init__('nanovoltmeter', waitLock=waitLock)
        self.display_text('Wazaaaaa! waaaaazaaaaaa... aaaah', delay=0.1)
        self.offset = 0.
        
        if self.ser is not None:
            self.initialize()
    
    def initialize(self):
        self.polarity = 1

        self.write('*rst') 
        self.write('*cls')                           # see p 207
        self.write(':init:cont off;:abor')           # abort the trigger loop if it was running 
        self.write(':sens:func \'volt:dc\'')         # measuring voltage
        self.write(':sens:chan 1')                   # sets the nvm to measure channel one
        self.write(':sens:volt:chan1:rang:auto on') 
        self.write(':sens:volt:chan2:rang:auto on')
        self.write(':syst:faz on')                   # makes the measurement twice with reversed polarity to improve accuracy
        self.write(':syst:azer on')
        self.write(':syst:lsyn off')                 # voltage on the powerline has 60Hz freq.
                                                     # This option delays measurement measure at the same phase of the AC voltage.
                                                     # linesync, only effective for for plc >= 1                         
        self.write(':outp off')                      # analog output off (at the back of the nvm)
        self.write(':sens:volt:chan1:dfil:stat on')  # turn off digital filter
        self.write(':sens:volt:chan2:dfil:stat on')
        self.write(':sens:volt:chan1:lpas:stat off') # turn off analog filter, otherwise 125msec slower
        self.write(':sens:volt:chan2:lpas:stat off')
        self.write(':sens:volt:nplc 1.0')           # set plc 1, 0.1, 0.01 (test different values); 0.01-60
        self.write(':disp:enab on')
        self.write(':form:elem read')                # format of the output
        self.write(':trig:del 0')                    # trigger delay until measurement
        self.write(':trig:sour imm')                 # as soon as init command start the measurement, as opposed to an external trigger
        self.write(':trig:coun inf')                 # number of cycles that are going to be executed
        self.write(':init')
        time.sleep(.1)
    
    def setPolarity(self, polarity=1):
        """
        Changes the sign of the measured voltage in case the use reverse biased the sample.

        @inputs:
        polarity (int) - Scaling factor for voltage 1 or -1
        """
        self.polarity = polarity
                        
    def setOffset(self):
        """
        setOffset averages 20 voltage measurements at zero current to determine the
        background offset which needs to be subtracted from measurements.
        
        @returns:
            voltage (float) - voltage in volts.
        """
        voltages, n = [], 20
        
        for k in range(n):
            try:
                v = self.measure(removeOffset=False)
                if v is not numpy.nan:
                    voltages.append(v)
            except Exception as e:
                print('Exception raised in setOffset:', e)
                print(type(voltages), voltages)

        if voltages is not []:
            voltages = numpy.array(voltages)*self.polarity
            std = numpy.nanstd(voltages)
            median = numpy.nanmedian(voltages)
            self.offset = numpy.nanmean(voltages[((median - std) < voltages) & (voltages < (median+std))]) # prevents abnormal offsets due to large fluctuations
        else:
            print('NanoVoltmeter::setOffset raised: all voltage measurements failed')
        return self.offset
    
    def measure(self, removeOffset=True, vb=True):    
        """
            Requests a voltage measurement from channel 1.
            The background offset is not removed.
            
            @returns:
                voltage (float)     - voltage in volts.
                removeOffset (bool) - returns raw voltage if False.
                vb (bool)           - display error messages for debugging purposes 
        """
        r, voltage = '', numpy.nan
        try:
            r = self.read(':sense:data:fresh?')
            if re.fullmatch(self.settings["fresh_pattern"], r) is not None:
                voltage = float(r)
                if removeOffset:
                    voltage -= self.offset
            else:
                if vb:
                    print('Nanovoltmeter::measure received string with incorrect format')
                    print('Value returned by :sense:data:fresh? is ', r)

        except Exception as e:
            if vb:
                print('Nanovoltmeter::measure returned ', e)
                print('Value returned by :sense:data:fresh? is ', r)

        return voltage*self.polarity
    
    def display_text(self, text, delay):
        """
        Displays a text on the physical display, scrolling left.
        
        @inputs:
            text (str) - text to be displayed, max 12 characters.
            delay (float) - time it takes to display the text.
        """
        self.write(':disp:text:stat on') # activate front panel display
        string2 = text+'            '
        if len(text) > 12:
            string1 = text+' '+text+'            '
        else:
            string1 = string2
               
        self.write(':disp:text:data "'+text[0:11]+'"') # display the first 12 characters for a short time 
        time.sleep(1.5)
        
        for i in range(len(text)): # start rolling the text
            if (i < 12):
                self.write(':disp:text:data "'+string1[i:(i+11)]+'"')
            else:
                self.write(':disp:text:data "'+string2[i:(i+11)]+'"')
            time.sleep(delay)
        
        self.write(':disp:text:stat off') # deactivate front panel display
