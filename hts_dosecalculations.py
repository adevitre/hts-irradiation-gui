import pandas as pd
import matplotlib.pyplot as plt
from scipy import integrate, constants
MAX_BEAM_CURRENT = 300 # nA

'''
    loadBeamCurrent reads an excel sheet containing the beam current.
    INPUTS
    path (str) - absolute path to excel spreadsheet
    sname (str) - sheet name where columns 2 is relative time and column 3 is beam current in nA
'''
def loadBeamCurrent(fpath, sname):
    data = pd.read_excel(io=fpath, sheet_name=sname, usecols=[1, 2], names=['time_s', 'ibeam_nA'])
    data['ibeam_nA'] *= 1e9
    return data

def plotBeamCurrent(data, fig=None, color='k'):
    if fig is None:
        fig, ax = plt.subplots()
    else:
        ax = fig.gca()
    ax.plot(data.time_s, data.ibeam_nA, color=color, marker='+')
    ax.set_xlim(data.time_s.min(), data.time_s.max())
    ax.set_ylim(0, data.ibeam_nA.max())
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Beam Current [nA]')
    fig.tight_layout()
    return fig, ax

def read_beamCurrent(fname_tape='beam/tape.txt', fname_collimator='beam/collimator.txt', vb=False):
    tt, it = np.genfromtxt(fname_tape, delimiter=',', unpack=True, usecols=[1,2])
    
    if vb:
        fig, ax = plt.subplots(figsize=(9, 4))
        ax.tick_params(axis='both', labelsize=18)
        ax.set_xlabel('Time [min]', fontsize=18)
        ax.set_ylabel('Beam current [nA]', fontsize=18)
        ax.plot(tt, it*1e9, color='b', label='Beam current on sample')
        ax.set_xlim(np.nanmin(np.append(tt, tc)), np.nanmax(np.append(tt, tc)))
        ax.set_ylim(np.nanmin(np.append(it, ic))*1e9, MAX_BEAM_CURRENT)
        ax.legend(fancybox=True, loc='upper left', fontsize=16)
        
    return tt, it

def compute_fluence(time, current, d=0.003):
    return integrate.trapz(i/(np.pi*(d/2.)**2), t)/constants.elementary_charge

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