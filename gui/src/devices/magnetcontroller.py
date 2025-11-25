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
        #self.write('CONFigure:FIELD:UNITS 1')                  # set units to teslas
        #self.write('CONFigure:FIELD:TARGet 0')                 # set the magnetic field to zero
        
        self.coil_constant = float(self.read('COILconst?'))    # get the coil constant to convert current into magnetic field
        
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
            self.write("CONFigure:FIELD:TARGet {:3.3f}".format(setpoint))
            self.write("RAMP")
        except Exception as e:
            print('MagneticFieldController::set_magnetic_field raised: ', e)

    def get_setpoint_magnetic_field(self):
        setpoint = numpy.nan
        try:
            r = self.read("FIELD:TARGet?")
            print('The read setpoint command read: ', r)
            if re.fullmatch(self.settings["setp_pattern"], r) is not None:
                setpoint = float(r)
            print('The stripped value is: ', setpoint)
        except Exception as e:
            print('MagneticFieldController::read_setpoint_magnetic_field raised:', e)
            print('Return value: ', r)
        return setpoint

    def get_magnetic_field(self, vb=False):
        central_field = numpy.nan
        try:
            r = self.read("CURRent:MAGnet?")
            if vb: print('The read field command read: ', r)
            if re.fullmatch(self.settings["setp_pattern"], r) is not None:
                central_field = float(r)*self.coil_constant
            if vb: print('The stripped value is ', central_field)
        except Exception as e:
            print('EXCEPTION MagneticFieldController::read_magnetic_field raised:', e)
            print('Return value: ', r)
        return central_field
    
    def field_stable(self, vb=False):
        '''
            field_stable checks if the magnet status is 2, i.e., 'HOLDING at the target field/current'
            @input
                vb (bool) - toggle DEBUG printouts and features.
        '''
        stable = False
        try:
            r = int(self.read("STATE?"))
            if vb: print('DEBUG: Field stable command read ', r)
            if r == 2:
                stable = True
        except Exception as e:
            print('EXCEPTION: MagnetController::field_stable returned ', e)
        return stable