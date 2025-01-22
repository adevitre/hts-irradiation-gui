'''
    The beamspot.py library implements functions that can evaluate the temperature of the beamspot 
    in hts ion-irradiation experiments.
'''
import hts_fitting as hts

import pandas as pd
import numpy as np
import hts_fitfunctions as ff
import matplotlib.pyplot as plt
from ipywidgets import IntProgress, IntText
from scipy.optimize import curve_fit, brentq

def getEmpiricalTcDegradation(x, a=0.69975365, b=0.75392883, c=0.13455914, d=0.01259732):
    '''
        This function is an empirical fit to Tc degradation as a function of Tc degradation
        It is used to interpolate Tc degradation values. The default values were obtained 
        without ffj20 points, which do not follow this empirical law very well.
    '''
    return a*np.sqrt(c*x+d)+b

def invertIcT(icnorm, popt, T0=20):
    '''
        invertIcT finds the optimal parameters for T(Icnorm) given the optimal parameters
        of a third order polynomial fit to Icnorm(T), where Icnorm = Ic/Ic0.
        
        icnorm (float)      - Ic/Ic0 or degradation level correcponding to the measured points
        popt (float, array) - Optimumal parameters for Ic(T)
        T0 (float)          - Temperature of the highest Ic.  
    '''
    def f(x):
        return popt[0]*(x-T0)**3 + popt[1]*(x-T0)**2 + popt[2]*(x-T0) + 1 - icnorm
    return brentq(f, 19, 90) # Alexis changed 19 for 20 on 23/10/2024


def getCorrectedSuppression(icon, icoff, ic0, 
                            poptp=[-1.91142195e-07,  1.45788152e-04, -2.38487357e-02], 
                            poptd=[-4.62920679e-06,  7.73025030e-04, -4.75032687e-02], 
                            Tcp=88.49, Tcd=68.62868916,
                            poptIcTc=[0.69975365, 0.75392883, 0.13455914, 0.01259732]):
    '''
        getCorrectedSuppression assumes that Ic suppression is thermal and interpolates between Ic(T) pristine 
        and Ic(T) degraded to find Ic(T) damaged, using Ic degradation as an interpolation variable.
        
        INPUTS
        --------------
        icon (float)  - critical current measured during irradiation
        icoff (float) - critical current measured before irradiation
        ic0 (float)   - critical current measured for the pristine sample
        
        poptp (array, float)    - optimized parameters for Ic(T) when tape is in (p)ristine condition
        poptd (array, float)    - optimized parameters for Ic(T) when tape is at maximum (d)egradation
        Tcp (float)             - value of critical temperature when tape is in pristine condition
        Tcd (float)             - values of critical temperature when tape is at maximum degradation
        poptIcTc (array, float) - optimized parameters for empirical law that produces Tc/Tc0 from Ic/Ic0
        
        RETURNS
        --------------
        icOnNoDamage (float)        - critical current we would measure for the pristine tape
        suppressionNoDamage (float) - critical current suppression we would measured for the pristine tape
        Ton (float)                 - temperature corresponding to suppressionNoDamage
    '''
        
    Td, Tp = invertIcT(icon/icoff, poptd), invertIcT(icon/icoff, poptp)
    desiredTcDegradation, damagedTcDegradation = getEmpiricalTcDegradation(icoff/ic0, *poptIcTc), Tcd/Tcp
    Ton = Td + (Tp - Td)*(desiredTcDegradation-damagedTcDegradation)/(1-damagedTcDegradation)
    
    icOnNoDamage = ic0*ff.cubic2(Ton, *poptp)
    suppressionNoDamage = 1-ff.cubic2(Ton, *poptp)
    
    return suppressionNoDamage, icOnNoDamage, Ton


# Call this version if you need to predict an entire curve to verify the procedure
v_getCorrectedSuppression = np.vectorize(getCorrectedSuppression)

def getBeamPower(master, ibpath, vb=False):
    '''
        getBeamPower calculates beam power for several beam on events based on user stipulated 
        time intervals and terminal potential.
        
    '''
    names = [
        'tapeid',     # tape sample name
        'sname',      # sheet name in spreadsheet with beam current data
        't0Beam',     # start time of interval for beam current evaluation
        't1Beam',     # stop time of interval for beam current evaluation
        't0Offset',   # start time of interval for beam current offset evaluation
        't1Offset'    # stop time of interval for beam current offset evaluation
    ]
    
    df = pd.read_excel(master, usecols=[0, 3, 4, 5, 6, 7], names=names, skiprows=1)
    
    # Progress bar
    if vb:
        pb = IntProgress(min=0, max=df.count().values[0])
        display(pb)

    means, stds, offsetmeans, offsetstds = [], [], [], []

    for i, row in df.iterrows():
        if vb: pb.value += 1
        data = pd.read_excel(ibpath+row['tapeid']+'.xlsx', sheet_name=row['sname'], usecols=[1, 2], names=['time', 'ibeam'])

        cut = data[(row['t0Beam'] < data.time) & (data.time < row['t1Beam']) & (2e-10 < data.ibeam) & (data.ibeam != 0.0e0)]
        means.append(cut['ibeam'].mean()*1e9)
        stds.append(cut['ibeam'].std()*1e9)

        cut = data[(row['t0Offset'] < data.time) & (data.time < row['t1Offset']) & (data.ibeam != 0.0e0)]
        offsetmeans.append(cut['ibeam'].mean()*1e9)
        offsetstds.append(cut['ibeam'].std()*1e9)

    data = {'mean': np.array(means), 'std': np.array(stds), 'omean': np.array(offsetmeans)}
    
    print(data)
    
    with pd.ExcelWriter(master, engine='openpyxl', if_sheet_exists='replace', mode='a') as writer:
        pd.DataFrame(data).to_excel(writer, index=False, sheet_name='output-ibeam', header=False)
        
        
        
def getBeamOnTemperature(master, ictpath):
    
    cols = [0, 15, 16, 17, 18]
    names = [
        'tapeid',  # tape sample name
        'f0',      # filename of iv pristine
        'foff',    # filename of iv during beam exposure
        'fon',     # filename of iv before beam exposure
        'icT',     # path to the Ic(T) calibration
    ]

    df = pd.read_excel(master, usecols=cols, names=names, skiprows=1)
    
    # Progress bar
    pb = IntProgress(min=0, max=df.count().values[0])
    display(pb)

    ic0, n0, icon, non, icoff, noff = [], [], [], [], [], []
    ic0err, n0err, icofferr, nofferr, iconerr, nonerr = [], [], [], [], [], []
    tHTS0, tTAR0, tHTSon, tTARon, tHTSoff, tTARoff = [], [], [], [], [], []
    tHTS0err, tTAR0err, tHTSonerr, tTARonerr, tHTSofferr, tTARofferr = [], [], [], [], [], []
    icCorrected, tCorrected = [], []

    for i, row in df.iterrows():

        for file in ['f0', 'fon', 'foff', 'icT']:

            ic, n, tHTS, tTAR = np.nan, np.nan, np.nan, np.nan
            icerr, nerr, tHTSerr, tTARerr = np.nan, np.nan, np.nan, np.nan
            icNoDegradation, tNoDegradation = np.nan, np.nan

            try:
                if file != 'icT':
                    fpath = '../data/Ic/{}/{}'.format(row.tapeid, row[file])
                    ic, n, _, _, _, pcov = hts.fitIcMeasurement(fpath, fformat='mit', function='linear', vMax=20e-6, vb=False)
                    icerr, nerr = np.sqrt(pcov[0][0]), np.sqrt(pcov[1][1])
                    data = hts.readIV(fpath)
                    tHTS, tTAR = np.nanmean(data.sampleT[0][-10:]), np.nanmean(data.targetT[1][-10:])
                    tHTSerr, tTARerr = np.nanstd(data.sampleT[0][-10:]), np.nanstd(data.targetT[1][-10:])
                else:
                    _, icOnNoDeg, tNoDeg = hts.getCorrectedSuppression(icon=icon[-1], icoff=icoff[-1], ic0=ic0[-1])
                    
            except ValueError as ve:
                print(ve, i+3, row.tapeid, row[file])
                tHTS = np.nan

            except TypeError as te:
                print(te)

            if file == 'f0':
                ic0.append(ic)
                ic0err.append(icerr)
                n0.append(n)
                n0err.append(nerr)
                tHTS0.append(tHTS)
                tHTS0err.append(tHTSerr)
                tTAR0.append(tTAR)
                tTAR0err.append(tTARerr)

            elif file == 'foff':
                icoff.append(ic)
                icofferr.append(icerr)
                noff.append(n)
                nofferr.append(nerr)
                tHTSoff.append(tHTS)
                tHTSofferr.append(tHTSerr)
                tTARoff.append(tTAR)
                tTARofferr.append(tTARerr)

            elif file == 'fon':
                icon.append(ic)
                iconerr.append(icerr)
                non.append(n)
                nonerr.append(nerr)
                tHTSon.append(tHTS)
                tHTSonerr.append(tHTSerr)
                tTARon.append(tTAR)
                tTARonerr.append(tTARerr)

            elif file == 'icT':
                icCorrected.append(float(icOnNoDeg))
                tCorrected.append(float(tNoDeg))

            pb.value += 1

    data = {
        'ic0': ic0, 
        'ic0err': ic0err,
        'n0': n0, 
        'n0err': n0err,

        'icoff': icoff, 
        'icofferr': icofferr,
        'noff': noff, 
        'nofferr': nofferr, 

        'icon': icon, 
        'iconerr': iconerr, 
        'non': non, 
        'nonerrr': nonerr, 

        'iceq': iceq, 
        'iceqerr': iceqerr, 
        'neq': neq, 
        'neqerr': neqerr,

        'tHTS0': tHTS0, 
        'tHTS0err': tHTS0err,
        'tTAR0': tTAR0, 
        'tTAR0err': tTAR0err, 

        'tHTSoff': tHTSoff, 
        'tHTSofferr': tHTSofferr,
        'tTARoff': tTARoff, 
        'tTARofferr': tTARofferr,

        'tHTSon': tHTSon, 
        'tHTSonerr': tHTSonerr,
        'tTARon': tTARon, 
        'tTARonerr': tTARonerr,  

        'icOn0': icCorrected,
        'tREBCO': tCorrected,
    }
    print(data)
    #with pd.ExcelWriter(dfs.master, engine='openpyxl',if_sheet_exists='replace', mode='a') as writer:
    #    pd.DataFrame(data).to_excel(writer, sheet_name='output-icnt', index=False, header=False)
