'''

    A library to quickly check measurements of the Critical Current (Ic) and Critical Temperature (Tc) of REBCO coated conductors.
    @author Alexis Devitre (devitre@mit.edu)
    @modified 2025/01/21
    
'''

import numpy as np
import matplotlib.pyplot as plt
import hts_fitting as hts
import hts_fitfunctions as ff
import ipywidgets as widgets

def showcaseIVs(fpaths, fformat='mit', style='loglog', vMax=20e-6, bounds=None, titles=None, vb=False):
    fig, ax = plt.subplots(figsize=(9, 4))
    def on_spinbox_value_change(change, ax):
        try:
            ax.clear()
            f = fpaths[spinbox.value]
            if titles is None:
                ax.set_title(f.split('/')[-1], fontsize=12)
            else:
                ax.set_title(titles[spinbox.value], fontsize=12)
            data = hts.readIV(f, fformat=fformat)
            if style == 'loglog':
                ic, n, current, voltage, chisq, pcov = hts.fitIcMeasurement(f, function='linear', vMax=vMax)
                ax.loglog(data.current, 1e6*data.voltage, color='lightgray', marker='+', label='raw data')
                ax.loglog(current, 1e6*voltage, color='k', marker='+', label='corrected voltage')
                xsmooth = np.linspace(np.min(current), np.max(current), 10000)
                cut = voltage > .2e-6
                ax.loglog(current[cut], 1e6*voltage[cut], color='b', marker='+')
                ax.loglog(xsmooth, 1e6*ff.powerLaw(xsmooth, ic, n), linewidth=3, alpha=.2, color='b', label=r'loglog fit: Ic = {:4.2f}, n = {:4.2f}'.format(ic, n))
                ax.set_ylim(1e-2, 1e2)
            else:
                ic, n, current, voltage, chisq, pcov = hts.fitIcMeasurement(f, function='powerLaw', vMax=vMax)
                ax.plot(data.current, 1e6*data.voltage, color='lightgray', marker='+', label='raw data')
                ax.plot(current, 1e6*voltage, color='k', marker='+', label='corrected voltage')
                xsmooth = np.linspace(np.min(current), np.max(current), 10000)
                ax.plot(current, 1e6*voltage, color='b', marker='+')
                ax.plot(xsmooth, 1e6*ff.powerLaw(xsmooth, ic, n), linewidth=3, alpha=.2, color='b', label=r'powerLaw fit: Ic = {:4.2f}, n = {:4.2f}'.format(ic, n))
                ax.set_ylim(-.5, 3)
            xmax = np.ceil(np.max(data.current)) + (5-np.ceil(np.max(data.current))%5)
            ax.set_xlim(0.001, xmax)
            ax.axhline(0.2, color='k', linestyle=':', label=r'$\mathrm{E_c}$ = 1 uV/cm')
            ax.legend() 
            ax.set_xlabel('Current [A]')
            ax.set_ylabel('Voltage [uV]')
            fig.tight_layout()
            
            if bounds is not None:
                ax.set_xlim(bounds[0], bounds[1])
        except Exception as e:
            if vb: print(e)
    spinbox = widgets.IntText(description="IV#:", min=0, max=len(fpaths), value=1)
    spinbox.observe(lambda change: on_spinbox_value_change(change, ax), names='value')
    display(spinbox)
    spinbox.value = 0
    
    
def showcaseTVs(fpaths, wsz=1, vb=False):
    fig, ax = plt.subplots(figsize=(9, 4))
    def on_spinbox_value_change(change, ax):
        try:
            ax.clear()
            f = fpaths[spinbox.value]
            ax.set_title(f.split('/')[-1], fontsize=14)
            data = hts.readTV(f)
            ax.plot(data.sampleT, 1e6*data.rolling(wsz).mean().voltage, color='k', marker='+', label='raw data')
            ax.axhline(0.2)
            ax.legend()
            ax.set_xlim(60, 90)
            ax.set_ylim(-1, np.ceil(np.max(1e6*data.voltage)))
        except Exception as e:
            if vb: print(e)
    spinbox = widgets.IntText(description="TV#:", min=0, max=len(fpaths), value=1)
    spinbox.observe(lambda change: on_spinbox_value_change(change, ax), names='value')
    display(spinbox)
    spinbox.value = 0