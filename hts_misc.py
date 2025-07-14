import numpy as np
import pandas as pd
import os, re
import hts_fitfunctions as ff
from scipy.optimize import brentq


def renameFiles(path, pattern, rpattern):
    for f in [f for f in os.listdir(path) if pattern in f]:
        os.rename(path + f, path + re.sub(pattern, rpattern, f))
        
def binAverage(xbins, xdata, ydata):
    yavgs, ystds, yfiltered, xfiltered = [], [], np.array([]), np.array([])
    for (minb, maxb) in zip(xbins[:-1], xbins[1:]):
        cut = (minb < xdata) & (xdata < maxb)
        yavg, ystd = np.nanmean(ydata[cut]), np.nanstd(ydata[cut])
        yavgs.append(yavg)
        ystds.append(ystd)
        stdfilter = (yavg-ystd <= ydata[cut])&(ydata[cut] <= yavg+ystd)
        yfiltered = np.append(yfiltered, ydata[cut][stdfilter])
        xfiltered = np.append(xfiltered, xdata[cut][stdfilter])
    return xbins[:-1]+(xbins[1]-xbins[0])/2., np.array(yavgs), np.array(ystds), xfiltered, yfiltered

def moving_average(x, w):
    return np.convolve(x, np.ones(w), 'valid') / w

def timestamp_to_seconds(timestamp):
    hh, mm, ss = timestamp[11:].split('-')
    return float(hh)*3600+float(mm)*60+float(ss)/1e6
    
def fname_to_timestamp(fname):
    y, m, d = [int(n) for n in fname.split('_')[1].split('-')]
    hh, mm, us = fname.split('_')[2].split('-')
    hh, mm, ss, us = int(hh), int(mm), int(us[:2]), int(us[2:])
    return pd.Timestamp(year=y, month=m, day=d, hour=hh, minute=mm, second=ss, microsecond=us)

def time_between_measurements(fname1, fname2):
    ts1 = fname_to_timestamp(fname1)
    ts2 = fname_to_timestamp(fname2)
    return abs(ts1 - ts2)

def readEnvironmentFile(fpath):
    return pd.read_csv(fpath, delim_whitespace=True, parse_dates={'datetime' : [0, 1]}, date_format={'date':'%d/%m/%y', 'timestamp':'%H:%M:%S.%f'})

def concatenateEnvironmentFiles(fpaths, vb=False):
    i, deltaT = 0, 0
    data = readEnvironmentFile(fpaths[0])

    for fpath in fpaths[1:]:
        nextdata = readEnvironmentFile(fpath)
        deltaT = (nextdata.iloc[0].datetime-data.iloc[-1].datetime).total_seconds()
        nextdata['time_s'] += data.time_s.values[-1] + deltaT
        missing_times = np.arange(data.time_s.values[-1], nextdata.time_s.values[0], data.time_s[-20:].diff().mean())

        data = pd.concat([data, pd.DataFrame({'time_s': missing_times}), nextdata], ignore_index=True)
        data = data.sort_values('time_s').interpolate(method='linear').reset_index(drop=True)
    
    if vb:
        fig, ax = plt.subplots(figsize=(9, 4))
        if 'temperature' in fpaths[0]:
            ax.plot(data.time_s, data.targetT_K, color='r')
            ax.plot(data.time_s, data.sampleT_K, color='b')
            ax.set_ylim(0, 300)
            ax.set_xlim(0, data.time_s.max())
        else:
            ax.semilogy(data.time_s, data.pressure_torr, color='g')
            ax.set_ylim(1e-8, 1e3)
            ax.set_xlim(0, data.time_s.max())
    return data

######################### Beam-on experiments #########################

def invertIcT(icnorm, popt, T0=20.):
    '''
        invertIcT finds the optimal parameters for T(Icnorm) given the optimal parameters
        of a third order polynomial fit to Icnorm(T), where Icnorm = Ic/Ic0.
        
        icnorm (float)      - Ic/Ic0 or degradation level correcponding to the measured points
        popt (float, array) - Optimumal parameters for Ic(T)
        T0 (float)          - Temperature of the highest Ic.  
    '''
    def f(x):
        return popt[0]*(x-T0)**3 + popt[1]*(x-T0)**2 + popt[2]*(x-T0) + 1 - icnorm
    return brentq(f, 19, 90)

def getCorrectedSuppression37(icon, icoff, ic0, poptp=[-3.88998965e-07,  1.66203890e-04, -2.43896814e-02], poptd=[-4.67823165e-06,  5.38287476e-04, -3.67295261e-02]):
    Tdamaged, degradation =  np.array([]), icoff/ic0
    Td, Tp = invertIcT(icon/icoff, poptd), invertIcT(icon/icoff, poptp)
    Ton = Td + (Tp - Td)*(degradation-0.18657000907933957)/(1-0.18657000907933957)
    return 1-ff.cubic2(Ton, *poptp), ic0*ff.cubic2(Ton, *poptp), Ton

def getCorrectedSuppression29(icon, icoff, ic0, poptp=[2.36162190e-07, 9.85656675e-05, -2.24987554e-02], poptd=[-2.11990545e-06, 3.58520738e-04, -3.32828593e-02]):
    Tdamaged, degradation =  np.array([]), icoff/ic0
    Td, Tp = invertIcT(icon/icoff, poptd), invertIcT(icon/icoff, poptp)
    Ton = Td + (Tp - Td)*(degradation-0.18592005711978735)/(1-0.18592005711978735)
    return 1-ff.cubic2(Ton, *poptp), ic0*ff.cubic2(Ton, *poptp), Ton

def getCorrectedSuppression28(icon, icoff, ic0, poptp=[ 2.36162190e-07, 9.85656675e-05, -2.24987554e-02], poptd=[-1.27385146e-06, 4.06420746e-04, -3.71872166e-02]):
    Tdamaged, degradation =  np.array([]), icoff/ic0
    Td, Tp = invertIcT(icon/icoff, poptd), invertIcT(icon/icoff, poptp)
    Ton = Td + (Tp - Td)*(degradation-0.12106582898)/(1-0.12106582898)
    return 1-ff.cubic2(Ton, *poptp), ic0*ff.cubic2(Ton, *poptp), Ton


v_getCorrectedSuppression37 = np.vectorize(getCorrectedSuppression37)
v_getCorrectedSuppression29 = np.vectorize(getCorrectedSuppression29)
v_getCorrectedSuppression28= np.vectorize(getCorrectedSuppression28)
