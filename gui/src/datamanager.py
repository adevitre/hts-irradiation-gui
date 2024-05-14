from scipy.optimize import curve_fit
from scipy.interpolate import interp1d
from PyQt5.QtCore import pyqtSignal, QObject, QThreadPool, QMutex

from fittingFunctions import linear, powerLaw, inverseExponential, fitIV, fitTV
from task import Task

import time, datetime, sys, os, shutil, gc
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
sys.path.append('config')

from configure import update_json, load_json

class DataManager(QObject):
    
    log_signal = pyqtSignal(str, str)
    plot_signal = pyqtSignal(np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray, np.ndarray)
    
    def __init__(self, threadpool, parent=None):
        super(DataManager, self).__init__(parent)
        
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        
        self.tcData, self.pmData, self.paData = None, None, None
        self.threadpool = threadpool
        self.mutexTc, self.mutexPm, self.mutexPlots = QMutex(), QMutex(), QMutex()
        
        self.vc = 2e-7                    # 1 uV/cm2 * bridgeLength (0.2 cm)
        self.voltageNoiseThreshold = 7e-7 # This value is set above the typical noise of the system to make sure that the LogLog
                                          # fit only takes values from the exponential voltage rise
        self.storingData = False
        self.backupFlags = [False, False] # Indicates whether temperature, pressure time series should be backed up to text files.
        
        # create the save directory and subdirectories
        self.save_directory = self.preferences["temporary_savefolder"]+str(datetime.datetime.now()).replace(' ', '_').replace(':', '-').replace('.', '')
        if os.path.exists(self.save_directory):
            shutil.rmtree(self.save_directory)
        os.mkdir(self.save_directory)
        os.mkdir(self.save_directory+'/Ic')
        os.mkdir(self.save_directory+'/Tc')
        os.mkdir(self.save_directory+'/Vt')
        os.mkdir(self.save_directory+'/env')
        
        # create the logfile and fittedParameters file
        f = open(self.save_directory + '/fittedParameters.txt', 'w')
        f.close()
        f = open(self.save_directory + '/logfile.txt', 'w')
        f.close()
        
        # savefile names for environment data
        timestamp = str(datetime.datetime.now()).replace(' ', '_').replace(':', '-')
        self.savefileNames = [
            'temperature_{}.txt'.format(timestamp),
            'pressure_{}.txt'.format(timestamp)
        ]
        
    def __del__(self):
        self.saveEnvironmentData()
    
    def log_event(self, when, what, comment):
        log = '{:30s}\t{:15s}\t{:100s}'.format(when, what, comment)
        with open(self.save_directory + '/logfile.txt', 'a+') as f:
            f.write(log+'\n')
            f.close()
        
    def set_saveDirectory(self, newDirectory, folderName, sessionDescription):
        '''
            set_saveDirectory moves the information in tempFolderName to the save location and handles the case
            where the user restarts the GUI but wishes to append the data to an existing folder.
            
            savepath           - (str) Path where the save folder should be stored.
            folderName         - (str) User defined name to which a timestamp is appended making the save directory unique.
            sessionDescription - (str) User input commenting on the goals of the session
        '''
        
        if folderName in os.listdir(newDirectory):
            comment = 'Continued after GUI restart: {}'.format(sessionDescription)
        else:
            folderName = str(datetime.datetime.now()).replace(' ', '_')+'_'+folderName # timestamp makes savedirectory unique
            shutil.move(self.save_directory, newDirectory+'/'+folderName)
            comment = 'New session started: {}'.format(sessionDescription)
        
        self.save_directory = newDirectory+'/'+folderName
        self.log_signal.emit('SessionStart', comment)
    
    def startTime(self):
        self.t0 = time.time()
        
    def updatePmReadings(self, pressure):
        try:
            dt = datetime.datetime.now()
            data = {
                'time_s': time.time()-self.t0,
                'pressure_torr': pressure,
                'backedup': False
            }
            self.mutexPm.lock()
            if self.pmData is not None:
                self.pmData.loc[dt] = data
            else:
                self.pmData = pd.DataFrame(data, index=[dt])
        except Exception as e:
            print('Exception while updating pressure monitor readings: ', e)
        finally:
            self.mutexPm.unlock()
            
    def updateTcReadings(self, setpointT, sampleT, targetT, holderT, spareT, heatingPower):
        try:
            dt = datetime.datetime.now()
            data = {
                'time_s': time.time()-self.t0,
                'setpt_K': setpointT,
                'sampleT_K': sampleT,
                'targetT_K': targetT,
                'holderT_K': holderT,
                'spareT_K': spareT,
                'heaterPower_W': heatingPower,
                'backedup': False
            }
            self.mutexTc.lock()
            if self.tcData is not None:
                self.tcData.loc[dt] = data
            else:
                self.tcData = pd.DataFrame(data, index=[dt])
        except Exception as e:
            print('Exception while updating temperature controller readings: ', e)
        finally:
            self.mutexTc.unlock()
   
    def saveMeasurementToFile(self, datapoints, measurement='Ic', **kwargs):
        timestamp = kwargs['timestamp']
        with open(self.save_directory+'/'+measurement[0:2]+'/{}_'.format(measurement)+timestamp.replace(' ', '_').replace(':', '-').replace('.', '')+'_'+kwargs['tag']+'.txt', 'w') as f:
            if measurement == 'Ic':
                f.write('# Ic = {:4.2f} A, n = {:4.2f} , Tavg = {:4.2f} K, {}\n'.format(kwargs['ic'], kwargs['n'], kwargs['tavg'], kwargs['tag']))
                
            elif measurement == 'Tc':
                f.write('# Tc = {:4.2f} K, {}\n'.format(kwargs['tc'], kwargs['tag']))
            
            elif measurement == 'Vt':
                f.write('# Tavg = {:4.2f} K, {}\n'.format(kwargs['tavg'], kwargs['tag']))
                
            f.write('#{:30}  {:6}  {:20}  {:20}  {:6}  {:6}'.format('datetime', 't_s', 'iHTS_A', 'vHTS_V', 'tHTS_K', 'tTAR_K'))
            
            for datapoint in datapoints:
                f.write('\n{:<30}  {:6.2f}  {:20.8e}  {:20.8e}  {:6.4f}  {:6.4f}'.format(self.float2datetime(datapoint[0]), datapoint[1], datapoint[2], datapoint[3], datapoint[4], datapoint[5]))
            f.close()
        
        with open(self.save_directory+'/fittedParameters.txt', 'a') as f:
            if measurement == 'Ic':
                f.write('{:15} {:15} {:15} {:10.2f} {:10.4f} {:10.4f} {:>10}\n'.format(timestamp, 'Ic', kwargs['tag'], kwargs['ic'], kwargs['n'], kwargs['tavg'], '_'))

            elif measurement == 'Tc':
                f.write('{:15} {:15} {:15} {:10.4f} {:>10}\n'.format(timestamp, 'Tc', kwargs['tag'], kwargs['tc'], '1 mA'))
            f.close()
    
    def fitIcMeasurement(self, current, voltage, noiseThreshold=1e-7):
        return fitIV(current, voltage, vc=self.vc, vThreshold=noiseThreshold, fitType='logarithmic')
    
    def fitTcMeasurement(self, temperature, voltage, tag):
        return fitTV(temperature, voltage, tag, fitType='electric-field', vb=False)
    
    def updateCSCalibration(self, voltage, set_voltage, shuntR):
        popt, pcov = curve_fit(linear, set_voltage[voltage>0], voltage[voltage>0])
        a, b = popt[0], popt[1]
        
        data = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
        data["a"] = a
        data["b"] = b
        update_json(data=data, fname='hwparams.json', location=os.getcwd()+'/config')
        
        fig, ax = plt.subplots(figsize=(9.5, 5))
        ax.plot(set_voltage, voltage, color='k', marker='+', linestyle='None', label='raw data')
        ax.plot((voltage-b)/a, voltage, color='b', label='setV = {:4.2e} V + {:4.2e}'.format(a, b))
        ax.legend(fancybox=True, loc='upper left', fontsize=16)
        ax.set_ylabel('Measured voltage = '+r'I$_{DMM} \times R_{Shunt}$ [V]', fontsize=16)
        ax.set_xlabel('Set voltage [V]', fontsize=16)
        fig.show()
        plt.savefig(os.getcwd()+'/config/calibrations/100ACurrentSource/{}'.format(str(datetime.datetime.now()).replace(' ', '_').replace(':', '-').replace('.', '')))
         
        return a, b
     
    def updateEnvironmentPlots(self):
        self.mutexPlots.lock()
        self.mutexPm.lock()
        self.mutexTc.lock()
        try:
            cut = self.preferences['timeaxis_max']
            
            tcData = self.tcData.loc[self.tcData.index[-int(np.ceil(2*self.preferences['sampling_period_tc'])+cut):]].copy(deep=True)    
            pmData = self.pmData.loc[self.pmData.index[-int(np.ceil(2*self.preferences['sampling_period_pm'])+cut):]].copy(deep=True)    

            #tcData = self.tcData.last('{:5.0f}s'.format(np.ceil(2*self.preferences['sampling_period_tc']+cut))).copy(deep=True)    
            #pmData = self.pmData.last('{:5.0f}s'.format(np.ceil(2*self.preferences['sampling_period_pm']+cut))).copy(deep=True)
                                     
            self.plot_signal.emit(tcData.time_s.values, pmData.time_s.values, tcData.setpt_K.values, tcData.sampleT_K.values, tcData.targetT_K.values, tcData.holderT_K.values, tcData.spareT_K.values, pmData.pressure_torr.values, tcData.heaterPower_W.values)
        except AttributeError as e:
            print('DataManager:updateEnvironmentPlots returned: ', e)
            print(tcData)
        finally:
            self.mutexPm.unlock()
            self.mutexTc.unlock()
            self.mutexPlots.unlock()
    
    def getLatestValue(self, signal='Target Temperature'):
        '''
            getLatestValue returns the last measurement value of the specified signal.
            
            INPUTS
            -------------------------------------------------------------------------
            signal (str) - options: Target Temperature (default), Sample Temperature, qPid (power output of the PID controlled heater), CG (low vacuum gauge pressure).
            
            RETURNS
            -------------------------------------------------------------------------
            value (float) - last measured value of the requested signal.
        '''
        if signal == 'Target Temperature':
            value = self.tcData.targetT_K.iloc[-1]
        elif signal == 'Sample Temperature':
            value = self.tcData.sampleT_K.iloc[-1]
        elif signal == 'Holder Temperature':
            value = self.tcData.holderT_K.iloc[-1]
        elif signal == 'Spare Temperature':
            value = self.tcData.spareT_K.iloc[-1]
        elif signal == 'power':
            value = self.tcData.heaterPower_W.iloc[-1]
        elif signal == 'pressure':
            value = self.pmData.pressure_torr.iloc[-1]
        elif signal == 'Setpoint Temperature':
            value = self.tcData.setpt_K.iloc[-1]
        return value
    
    def saveEnvironmentData(self):
        try:
            self.mutexPlots.lock()
            self.mutexPm.lock()
            self.mutexTc.lock()
            fpath = self.save_directory+'/env/'
            for i, (df, fname, backup) in enumerate(zip([self.tcData, self.pmData], self.savefileNames, self.backupFlags)):
                if backup:
                    data = df.loc[df.backedup == False, df.columns != 'backedup']
                    
                    if fname not in os.listdir(fpath): # first save
                        self.savefileNames[i] = fname.split('_')[0]+'_{}.txt'.format(str(datetime.datetime.now()).replace(' ', '_').replace(':', '-'))
                        fname = self.savefileNames[i]
                        with open(fpath+fname, 'w') as f:
                            header = '{:<20}{:<20}'.format('date', 'timestamp')
                            for c in df.columns.tolist()[:-1]:
                                header += '{:<20}'.format(c)
                            f.write(header+'\n')
                            f.close()
                    data.to_csv(fpath+fname, index=True, header=False, mode='a', sep='\t')
                    
            self.tcData = self.tcData.assign(backedup=True)
            self.pmData = self.pmData.assign(backedup=True)
            
            comment = 'Temperature and heater power {}; pressure {}'.format(self.backupFlags[0], self.backupFlags[1])
        
        except Exception as e:
            print('Datamanager::saveEnvironmentData raised: ', str(e))
            comment = 'Save timetrace exception: '.format(str(e))
        finally:
            self.mutexPm.unlock()
            self.mutexTc.unlock()
            self.mutexPlots.unlock()
        
    def enableBackups(self, backupTemperatureTrace=True, backupPressureTrace=False):
        self.backupFlags = [backupTemperatureTrace, backupPressureTrace]
    
    def float2datetime(self, datetime_as_float):
        datetime_as_string = ''
        try:
            x = str(datetime_as_float)
            datetime_as_string = str(datetime.datetime(year=int(x[0:3]), month=int(x[4:6]), day=int(x[6:8]), hour=int(x[8:10]), minute=int(x[10:12]), second=int(x[12:14]), microsecond=int('{:0<6}'.format(x[15:])))).replace(' ', '_')
        except Exception as e:
            print('datamanager::float2datetime raised', e)
            print('Input value was {}'.format(datetime_as_float))
        return datetime_as_string