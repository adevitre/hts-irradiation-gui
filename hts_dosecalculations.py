import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle
from scipy import integrate, constants
MAX_BEAM_CURRENT = 300 # nA

def getMeasurementStartTime(fpaths, year='2024'):
    """
    getMeasurementStartTime returns the 

    Parameters:
    fpaths (str, array): paths to files with Ic/Tc measurement data (1st column must have format YYYY-MM-DD_HH:MM:SS.SSSSSS)
    year (str): This is to correct the year if needed, due to a bug that existed in our DATAQ.

    Returns:
    starttimes (datetime, array): Containing the datetime of the first point measured.
    """
    starttimes, endtimes = [], []
    for path in fpaths:
        df = pd.read_csv(path, usecols=[0], names=['date'], dtype={'date': 'str'}, delim_whitespace=True, skiprows=2)
        startdate = year+df['date'].iloc[0][4:]
        enddate = year+df['date'].iloc[-1][4:]
        starttimes.append(pd.to_datetime('-'.join(startdate.split('_'))))
        endtimes.append(pd.to_datetime('-'.join(enddate.split('_'))))
    return starttimes, endtimes

def loadBeamCurrent(ibpath, sname):
    """
    loadBeamCurrent reads an excel sheet containing the beam current.
    INPUTS
    ibpath (str) - absolute path to excel spreadsheet
    sname (str) - sheet name where columns 2 is relative time and column 3 is beam current in nA
    """
    data = pd.read_excel(io=ibpath, sheet_name=sname, usecols=[0, 1, 2], names=['time_datetime', 'time_s', 'ibeam_nA'])
    try:
        data['time_datetime'] = pd.to_datetime(data['time_datetime'])
    except Exception as e:
        print('dose::loadBeamCurrent raised: ', e)
        
    data['ibeam_nA'] *= 1e9
    return data

def plotBeamCurrent(data, fig=None, color='k'):
    if fig is None:
        fig, axdt = plt.subplots(figsize=(9, 4))
    else:
        axdt = fig.gca()
    
    axdt.plot(data.time_datetime, data.ibeam_nA, linestyle='None')
    lower, upper = data.time_datetime.min(), data.time_datetime.max()
    print(lower, upper)
    axdt.set_xlim(lower, upper)
    axdt.set_xlabel('Absolute Time [s]')
    
    axrt = axdt.twiny()
    
    axrt.plot(data.time_s, data.ibeam_nA, color=color, marker='+', markersize=2)
    axrt.set_xlim(data.time_s.min(), data.time_s.max())
    axrt.set_ylim(0, data.ibeam_nA.max())
    axrt.set_xlabel('Relative Time [s]')
    axrt.set_ylabel('Beam Current [nA]')
    
    fig.tight_layout()
    return fig, axrt, axdt

def plotBeamCurrentWithMeasurements(fpaths, ibpath, sname, fig=None):
    data = loadBeamCurrent(ibpath, sname=sname)
    if fig is None: fig, ax = plt.subplots(figsize=(9, 4))
    fig, axrt, axdt = plotBeamCurrent(data, fig=fig)
    starts, ends = getMeasurementStartTime(fpaths, year='2024')
    for t0, t1 in zip(starts, ends):
        axdt.axvline(t0, color='b', linestyle=':')
        axdt.axvspan(t0, t1, color='b', alpha=.1)
        axdt.axvline(t1, color='b', linestyle=':')
        
    return fig, axrt, axdt, data

def compute_fluence(time, current, d=0.003175):
    return integrate.trapz(current*1e-9/(np.pi*(d/2.)**2), time)/constants.elementary_charge

def compute_fluences(path_to_folder='', fname_tape='tape.txt', limits=[], offset=0, xymax=(0, 0), vb=True, window=None):
    
    t, i = read_beamCurrent(fname_tape=path_to_folder+fname_tape)
    fluence = []
    
    # Flux integration
    if limits == []:
        limits = [np.nanmax(i)]
    
    f = open(path_to_folder+'fluence_steps.txt', 'w+')
    f.write('{:<10}\t{:<10}\n'.format('Time_s', 'fluence_ppm2'))
    for tf in limits:
        fluence_step = compute_fluence(t[t < tf], i[t < tf])
        fluence.append(fluence_step)
        f.write('{:<10.2f}\t{:<10.4e}\n'.format(tf, fluence_step))
    f.close()
    
    if vb:
        plt.ioff()
        i /= 1e-9
        t = (t-offset)/60.
        
        if window is not None:
            t = moving_average(t, window)
            i = moving_average(i, window)
                
        for k, tf in enumerate(limits):
            tf = (tf-offset)/60.
            fig, ax = plt.subplots(figsize=(9, 4))
            ax.tick_params(axis='both', labelsize=18)
            ax.set_xlabel('Time [min]', fontsize=18)
            ax.set_ylabel('Beam current [nA]', fontsize=18)
            
            ax.plot(t, i)
            ax.fill_between(t[t < tf], i[t < tf], alpha=.2, label='Accumulated fluence = {:4.2e} protons/m$^2$'.format(fluence[k]))
            
            
            if (xymax[0] != 0) & (xymax[1] != 0):
                ax.set_xlim(0, xymax[0])
                ax.set_ylim(0, xymax[1])
            else:
                ax.set_xlim(0, np.nanmax(t))
                ax.set_ylim(0, np.nanmax(i))
                
            ax.legend(fancybox=True, loc='upper left', fontsize=16)
    
            fig.tight_layout()
            plt.savefig(path_to_folder+'upTo{:4.0f}min'.format(tf))
            plt.close(fig)
            
        plt.ion()
            
    return fluence


def fluence_estimation(i=20e-9, t=10, d=0.003):
    '''
        provides a total fluence for t minutes irradiation 
        at an average beam current i when the beam goes through
        a hole of diameter d
    '''
    return (60.*t)*i/(np.pi*constants.elementary_charge*(d/2.)**2)

def time_to_fluence_estimation(i, f, d=0.003):
    '''
        provides the time in minutes to reach fluence f at an average beam 
        current i when the beam goes through a hole of diameter d
    '''
    return f*(np.pi*constants.elementary_charge*(d/2.)**2)/(60.*i)