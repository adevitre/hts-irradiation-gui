import numpy as np
from scipy.optimize import curve_fit

'''
    Fitting functions for transport current measurements
    
    @author Alexis Devitre, Raphael Unterrainer, David Fischer
    @lastModified 31/04/2022
'''

def powerLaw(i, ic, n, vc=2e-7):
    return vc*(i/ic)**n

def linear(x, a, b):
    return a*x+b

def inverseExponential(temperature, a, b, t50):
    return a*temperature*(1-1/(np.exp(b*(temperature-t50))+1))

def fitTV(temperature, voltage, tag='', vc=0.2, fitType='inverse-exponential', vb=False):
    '''
        fitTV fits the TV data to a 3-parameter inverse exponential
        
        INPUTS
        ----------------------------------------------------------
        temperature (float, list) - measured temperatures
        voltage (float, list) - Measured voltages (must be same length as temperature)
        fitType (str) - "electric-field" or "inverse-exponential"

        RETURNS
        ----------------------------------------------------------
        tc_lossless (float) - value of the temperature below which the current is considered to be carried without resistance (Ec = 1 uV/cm)
        tc_superconducting (float) - value of the temperature below which cooper pairs form
    '''
    try:
        if fitType == 'electric-field':
            tc_lossfree = np.interp([vc], voltage, temperature)
            tc_superconducting = temperature[np.argmin(np.abs(voltage-9*vc))]
            tc_lossfree = 0 # fix later
        else:
            print('Not implemented')
            tc_lossfree, tc_superconducting = np.nan, np.nan

    except Exception as e:
        print('fittingFunctions::fitTV returned: ', e)
        tc_lossfree, tc_superconducting = np.nan, np.nan
        
    return tc_lossfree, tc_superconducting
    
def fitIV(current, voltage, vc=.2e-6, fitType='logarithmic', vThreshold=1e-7, vb=False): #vThreshold = 1e-7 is the minimum we have achieved
    '''
        fitIcMeasurement fits the IV data to a 2-parameter power law
        
        INPUTS
        ----------------------------------------------------------
        current (float, list) - measured currents
        voltage (float, list) - Measured voltages (must be same length as current)
        vc (float)            - Voltage corresponding to the conventional electric field criterion (Ec=1uV/cm). Change with bridge length.
        fitType (str)         - Indicates the fitting function to be used: linear in loglog-space or exponential in linear-space
        vThreshold (float)    - Expected voltage-noise level, used to remove the background.
        vb (bool)             - Verbose is true if the user wants printouts for dubugging purposes.

        RETURNS
        ----------------------------------------------------------
        ic - Fitted value of the critical current
        n  - Fitted value of the exponent
    '''
    try:
        #print('\n\nCurrent:\n\n')
        #print(current)
        #print('\n\nVoltage:\n\n')
        #print(voltage)
        # first remove the high-voltage points (>40uV, arbitrary) that can lead to an innacurate fit
        current = current[voltage <= 4e-5]
        voltage = voltage[voltage <= 4e-5]
        
        valid = ~(np.isnan(current) | np.isnan(voltage))
        popt, pcov = curve_fit(linear, np.log(np.abs(current[valid][-2:])), np.log(np.abs(voltage[valid][-2:])))
        n, ic = popt[0], vc**(1./popt[0])/np.exp(popt[1]/popt[0])

        if vb: print('First estimate of Ic is {:4.3e} A, n is {:4.3f}. The last two points are [{:4.3e}, {:4.3e}] and [{:4.3e}, {:4.3e}]'.format(ic, n, current[valid][-2], voltage[valid][-2], current[valid][-1], voltage[valid][-1]))
        
        popt, pcov = curve_fit(powerLaw, current[valid], voltage[valid])
        
        iThreshold, newThreshold, tolerance = ic*(vThreshold/vc)**(1/n), 1e6, 0.01
        
        counter = 1
        while((counter < 5) and (np.abs(iThreshold-newThreshold) > tolerance)):
            #print('iThreshold {:4.4e}'.format(iThreshold))
            #print('counter = {} ic = {:4.4e}, n = {:4.4e}'.format(str(counter), ic, n))
            iThreshold = newThreshold
            voltage = removeBackground(current, voltage, ic, n, vThreshold, vc)
            popt, pcov = curve_fit(powerLaw, current, voltage, p0=[ic, n])
            ic, n = popt[0], popt[1]
            newThreshold = ic*(vThreshold/vc)**(1/n)
            counter+=1
        
        if vb: print('afterLoop', iThreshold, newThreshold)
        
        if fitType == 'powerLaw':
            popt, pcov = curve_fit(powerLaw, current, voltage, p0=[ic, n])
            ic, n = popt[0], popt[1]
        else:
            log_current = np.log(current[voltage > vc])
            log_voltage = np.log(voltage[voltage > vc])
            
            valid = ~(np.isnan(log_current) | np.isnan(log_voltage))
            popt, pcov = curve_fit(linear, log_current[valid], log_voltage[valid])
            
            n, ic = popt[0], vc**(1./popt[0]) / np.exp(popt[1]/popt[0])
            
        if ((ic < 0) | (n < 1)):
                ic = n = np.nan 
        if vb: print(ic, n)
        
    except Exception as e: # Usually TypeError, IndexError
        print('fittingFuntions:fitIV returned: ', e)
        ic, n = np.nan, np.nan
        
    return ic, n, voltage
    
def removeBackground(current, voltage, ic, n, noiseThreshold, vc, vb=False):
    if vb: print(ic, noiseThreshold, vc,n)

    iThreshold = ic*(noiseThreshold/vc)**(1./n)
    cut = (current < iThreshold)
    popt, pcov = curve_fit(linear, current[cut], voltage[cut])
    background = linear(current, *popt)
    
    if vb: print('\n\nBackground:\n\n', background)
    
    return voltage - background
    
    
        