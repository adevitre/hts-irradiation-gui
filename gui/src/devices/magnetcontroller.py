import numpy, re, time
from device import Device

'''
    A SerialDevice class for communications with an AMI430 magnet controller.
    @author Alexis Devitre (devitre@mit.edu)
    @lastModified November 2025
'''
class MagnetController(Device):
    
    def __init__(self, serialDevice=False, waitLock=350, vb=False):
        super().__init__('magnet_controller', waitLock=waitLock, serialDevice=serialDevice, vb=vb)
        if self.ser is not None:
            self.initialize()
    
    def initialize(self):
        #self.write('*rst') 
        #self.write('*cls')
        #self.write('CONFigure:FIELD:UNITS 1')           # set units to teslas
        #self.write('CONFigure:FIELD:TARGet 0')          # set the magnetic field to zero
        
        #self.coil_constant = self.read('COILconst?')    # get the coil constant to convert current into magnetic field

        # EDIT THOSE!!
        #self.write("CONFigure:RAMP:RATE:FIELD")
        #self.write('CONFigure:CURRent:LIMit ')
        
        time.sleep(.1)
                       
    def set_magnetic_field(self, setpoint):
        """
        set_magnetic_field sets the central magnetic field in the bore of the solenoid

        @input:
            setpoint (float) - magnetic field in teslas
        """
        try:
            if setpoint > 0:
                self.write("CONFigure:FIELD:TARGet {:3.3f}".format(setpoint))
            else:
                self.write("ZERO")
        except Exception as e:
            print('MagneticFieldController::set_magnetic_field raised: ', e)

    def read_setpoint_magnetic_field(self):
        setpoint = numpy.nan
        try:
            r = self.read("CURRent:MAGnet?")
            if re.fullmatch(self.settings["setp_pattern"], r) is not None:
                setpoint = float(r)
        except Exception as e:
            print('MagneticFieldController::read_setpoint_magnetic_field raised:', e)
            print('Return value: ', r)
        return setpoint

           
    def read_magnetic_field(self):
        central_field = numpy.nan
        try:
            r = self.read("CURRent:MAGnet?")
            if re.fullmatch(self.settings["setp_pattern"], r) is not None:
                central_field = float(r)
        except Exception as e:
            print('MagneticFieldController::read_magnetic_field raised:', e)
            print('Return value: ', r)
        return central_field