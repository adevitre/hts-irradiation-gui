import os, time, datetime, numpy


from configure import load_json
from scipy import integrate, constants

from PyQt5.QtCore import pyqtSignal, QObject, QThreadPool, QTimer, QMutex

from task import Task

'''
    Performs all high-level functions of the HTS irradiation setup at the Vault
    * Measurement of the critical current, Ic
    * Measurement of the critical temperature, Tc
    * Annealing sequence
    * Temperature control
    * Vacuum connections for roughing and turbo pumps
    
    @author Alexis Devitre devitre@mit.edu, David Fischer dafisch@mit.edu
    @lastModified 06/04/2023 Alexis Devitre
'''

LABEL_CAEN = 'CAEN'
LABEL_CS100A = 'HP6260B-120A'
LABEL_CS006A = '2231A-30-3-6A'

class TaskManager(QObject):
    
    log_signal = pyqtSignal(str, str)
    plotSignal = pyqtSignal(float, float, str)

    def __init__(self, dataManager, hardwareManager, threadpool, parent=None):
        super(TaskManager, self).__init__(parent)
        
        self.threadpool = threadpool
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        self.corrected_voltage = 0
        self.warmupTemperature = 300.
        self.dm = dataManager
        self.hm = hardwareManager
        
        self.datapoints = []
        self.acquiring = False
        self.annealing = False
        self.sequenceRunning = False
        
        # timers
        self.nvTimer, self.tcTimer, self.pmTimer, self.plotTimer, self.dataBackupTimer  = QTimer(), QTimer(), QTimer(), QTimer(), QTimer()
        self.nvTimer.timeout.connect(lambda: self.threadpool.start(Task(self.updateNvReadings)))
        self.tcTimer.timeout.connect(lambda: self.threadpool.start(Task(self.updateTcReadings)))
        self.pmTimer.timeout.connect(lambda: self.threadpool.start(Task(self.updatePmReadings)))
        self.plotTimer.timeout.connect(lambda: self.threadpool.start(Task(self.dm.updateEnvironmentPlots)))
        self.dataBackupTimer.timeout.connect(lambda: self.threadpool.start(Task(self.dm.saveEnvironmentData)))
    
    def startReadings(self, ln2Measurements=False):
        self.dm.startTime()
        self.ln2Measurements = ln2Measurements
        self.updateTcReadings() # Necessary: otherwise the dataframes are None and plot update fails.
        self.updatePmReadings()
        
        if not ln2Measurements:
            self.tcTimer.start(int(self.preferences['sampling_period_tc']*1000))
            self.pmTimer.start(int(self.preferences['sampling_period_pm']*1000))
            
            self.plotTimer.start(1000)
            self.dataBackupTimer.start(int(self.preferences['saverate']*1000)) # TQp data backup, user specified in seconds
        else:
            self.dm.updateEnvironmentPlots()
        
    def updateTcReadings(self):
        if not self.ln2Measurements:
            setpointT, sampleT, targetT, holderT, spareT, heatingPower = self.hm.getTemperatureReading()
        else:
            setpointT, sampleT, targetT, holderT, spareT, heatingPower = 77.3, 77.3, 0, 0, 0, 0.
        self.dm.updateTcReadings(setpointT, sampleT, targetT, holderT, spareT, heatingPower)
        
    def updatePmReadings(self, ln2Measurements=False):
        if not self.ln2Measurements:
            pressure = self.hm.getPressureReading()
        else:
            pressure = 760.
        self.dm.updatePmReadings(pressure)
    

    def measureTc(self, startT, rampRate, stopT, transportCurrent, tag):
        
        self.datapoints, self.acquiring = [], True

        self.hm.connectCurrentSource100mATo('sample')
        self.hm.measureSampleWith(device='nanovoltmeter')
        
        sampleT = self.dm.getLatestValue('Sample Temperature')
        targetT = self.dm.getLatestValue('Target Temperature')
        self.stabilizeTemperature(setTemperature=startT, rampRate=9, stabilizationMargin=self.preferences['TcStabilizationMargin'], stabilizationTime=60, vb=True)
        
        # turn off cryohead, start the ramp
        if self.acquiring:
            if stopT > startT:
                self.hm.rampTemperature(100, rampRate, ramping=True)
            else:
                self.hm.rampTemperature(10, rampRate, ramping=True)
        try:
            tc = numpy.nan
            while (self.acquiring & (numpy.abs(sampleT - stopT) > 0.3)):
                sampleT = self.dm.getLatestValue('Sample Temperature')
                targetT = self.dm.getLatestValue('Target Temperature')
                
                self.hm.setSmallCurrentPolarity(polarity=0)
                vpos = self.hm.getVoltageReading(removeOffset=False)
                
                self.hm.setSmallCurrentPolarity(polarity=1)
                vneg = self.hm.getVoltageReading(removeOffset=False)
                vavg = (vpos-vneg)/2.
                
                self.datapoints.append([float(datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')), time.time()-self.dm.t0, self.hm.getCurrentReading(), vavg, sampleT, targetT, vpos, vneg])
                print('T = {:3.2f} v+ = {:3.5e} v- = {:3.5e} vavg = {:3.5e}'.format(sampleT, vpos, vneg, vavg))
            
            self.hm.rampTemperature(stopT, 1., ramping=False)
            self.hm.connectCurrentSource100mATo(device='hallSensor') # connect current source
            
            tc = numpy.nan
            if ((self.datapoints is not []) & self.acquiring):
                tData = numpy.transpose(self.datapoints)  # 3 is voltage, 4 is sample temperature
                tc, _ = self.dm.fitTcMeasurement(tData[3], tData[4], tag)
                
        except Exception as e:
            print('Taskmanager::measureTc raised:', e)
        
        finally:
            if self.acquiring: # not acquiring means the user wants to stop, so the measurement is likely incomplete and not worth saving or displaying
                self.acquiring = False
            else:
                self.log_signal.emit('Note', 'Tc sequence canceled by user')
                print('Tc sequence cancelled by user.')

            tData = numpy.transpose(self.datapoints)
            self.log_signal.emit('Tc', 'Tc = {:4.2f} K, {}'.format(tc, tag))

    def measureIc(self, rampStart=0, iStep=0.1, maxV=1e-5, currentSource=LABEL_CS100A, tag='Pristine', vb=True):
        '''
            Performs Jc measurement. Requests fitting and data output from datamanager object,
            then plotting and logging from LIFT1_GUI object.
            
            INPUTS            ---------
            rampStart - (float) Starting value of current ramp
            iStep     - (float) Current ramp step in amps
            maxV      - (float) Voltage at which the current ramp is terminated
            tag       - (string) Data file label
            vb        - (bool) Verbose enables printouts for debugging
        '''
        self.hm.measureSampleWith(device='nanovoltmeter')
        self.hm.setLargeCurrent(0, vb=vb)
        
        if currentSource == LABEL_CS006A:
            self.hm.enableParallelMode(enabled=True)
            self.hm.connectSampleTo100A(connected=False)
            self.hm.connectSampleTo6A(connected=True)
            maxI = 5.9 # The 2231A-30-3 gets stuck at 5.9 A (max rating 6A)
        elif currentSource == LABEL_CS100A:
            self.hm.enableParallelMode(enabled=False)
            self.hm.connectSampleTo6A(connected=False)
            self.hm.connectSampleTo100A(connected=True)
            maxI = 120
        elif currentSource == LABEL_CAEN:
            self.hm.enableParallelMode(enabled=False)
            self.hm.connectSampleTo6A(connected=False)
            self.hm.connectSampleTo100A(connected=True)
            maxI = 100

        try:
            self.datapoints, self.acquiring = [], True
            v, iRequest, control_voltage = 0, 0, 0
            self.hm.setVoltageOffset() # needs to come after acquiring is set to True to avoid conflicts
            
            if rampStart > 10: # Ramp the power in steps slowly to avoid "tail lifting" in IV curve due to induction
                while (self.acquiring) and (iRequest < rampStart) and (control_voltage is not numpy.nan) and (abs(v) < maxV):
                    control_voltage = self.hm.setLargeCurrent(iRequest)
                    v = self.hm.getVoltageReading()
                    iRequest += 2
                    time.sleep(.5)
            
            v, i, iRequest = 0, 0.0, rampStart
            while(self.acquiring and (abs(v) < maxV) and (iRequest < maxI) and (control_voltage != numpy.nan)):
                
                control_voltage = self.hm.setLargeCurrent(iRequest, currentSource=currentSource, vb=vb)
                sampleT, targetT = self.dm.getLatestValue('Sample Temperature'), self.dm.getLatestValue('Target Temperature')
                i, v = self.hm.getCurrentReading(), self.hm.getVoltageReading()
                self.datapoints.append([float(datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')), time.time()-self.dm.t0, i, v, sampleT, targetT])
                iRequest += iStep
                print('i = {:<4.3f}A, v = {:<4.3e}V, v_control={:<4.3e}, next_request={:<4.3e}'.format(i, v, control_voltage, iRequest))
            
        except Exception as e: # Usually IndexError or TypeError
            ic, n, tavg = numpy.nan, numpy.nan, numpy.nan
            print('TaskManager::measureIc raised: ', e)
            
        finally:
            self.hm.setLargeCurrent(0.0000, currentSource=currentSource, vb=vb)
            if currentSource == LABEL_CS006A:
                self.hm.enableParallelMode(enabled=False)
                self.hm.connectSampleTo6A(connected=False)    
            elif currentSource == LABEL_CS100A:
                self.hm.connectSampleTo100A(connected=False)
            elif currentSource == LABEL_CAEN:
                self.hm.connectSampleTo100A(connected=False)
            
            if self.acquiring: # not acquiring means the user wants to stop, so the measurement is likely incomplete and not worth saving or displaying
                self.acquiring = False
            else:
                self.log_signal.emit('Note', 'Ic sequence canceled by user')
                print('Ic sequence cancelled by user.')
            tData = numpy.transpose(self.datapoints)
            ic, n, self.corrected_voltage = self.dm.fitIcMeasurement(tData[2], tData[3])
            tavg = tData[4][-1]
            self.log_signal.emit('Ic', 'Ic = {:4.2f} A, n = {:4.2f} , Tavg = {:4.2f} K, {}'.format(ic, n, tavg, tag))
    
    def measureVt(self, current=0.0, maxV=1e-5, tag='Pristine'):
        '''
            Performs voltage vs time measurement.
            
            INPUTS
            ---------
            tStep     - (float) Sampling period in seconds
            maxV      - (float) Voltage at which the current ramp is terminated
            tag       - (string) Data file label
        '''
        self.hm.setLargeCurrent(0, currentSource=LABEL_CS100A)
        self.hm.setLargeCurrent(0, currentSource=LABEL_CS006A)
        self.hm.connectSampleTo100A(connected=True)
        self.hm.measureSampleWith(device='nanovoltmeter')

        try:
            if maxV == 0.:
                maxV = numpy.inf

            self.datapoints, self.acquiring, v = [], True, 0
            self.hm.setVoltageOffset() # needs to come after acquiring is set to True to avoid conflicts
            
            while(self.acquiring and (abs(v) < maxV)):
                t, v, i, sampleT, targetT = time.time()-self.dm.t0, self.hm.getVoltageReading(), self.hm.getCurrentReading(), self.dm.getLatestValue('Sample Temperature'), self.dm.getLatestValue('Target Temperature')
                self.datapoints.append([float(datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')), t, i, v, sampleT, targetT])
            
            tData = numpy.transpose(self.datapoints)
            tmax = tData[4][-1]
            
        except Exception as e:
            tmax, self.acquiring = numpy.nan, False
            print('TaskManager::measureVt raised: ', e)
            
        finally:
            self.hm.setLargeCurrent(0, currentSource=LABEL_CS100A)
            self.hm.setLargeCurrent(0, currentSource=LABEL_CS006A)
            self.hm.connectSampleTo100A(connected=False)
            self.log_signal.emit('Vt', 'TransportCurrent = {:4.2f}, Tavg = {:4.2f} K, {}'.format(i, tmax, tag))
            
    def stopAcquiring(self):
        self.acquiring = False
        
    def pushLastMeasurement(self):
        return self.datapoints, self.corrected_voltage
    
    def runCurrent(self, current, logEvent=False):
        if current == 0.:
            self.hm.connectSampleTo100A(connected=False)  
        else:
            self.hm.connectSampleTo100A(connected=True)
        self.hm.setLargeCurrent(0)
        offset = self.hm.setVoltageOffset()
        self.hm.setLargeCurrent(current)
        if logEvent:
            self.log_signal.emit('CurrentSet', 'HTS Current {:4.2f} A, Voltage Offset = {:4.4e}'.format(current, offset))
    
    def warmup(self):
        '''
            warmup returns target temperature to 300 K
        '''
        self.hm.setCooler(on=False)
        self.hm.setTemperature(self.warmupTemperature)
        self.log_signal.emit('Warming up to {:4.1f}'.format(self.warmupTemperature), 'Started!')
    
    def stabilizeTemperature(self, setTemperature, rampRate=9., stabilizationTime=60, stabilizationMargin=.1, vb=False):
        if rampRate > 0:
            self.hm.rampTemperature(setTemperature, rampRate, ramping=True)
        else:
            self.hm.setTemperature(setTemperature)
        
        if stabilizationTime > 0:
            counter = stabilizationTime
            while (self.acquiring | self.annealing | self.sequenceRunning) and (counter > 0):
                if numpy.abs(setTemperature - self.dm.getLatestValue('Target Temperature')) < stabilizationMargin:
                    counter -= 1
                    if vb:
                        print('Stabilizing temperature. Remaining time: {:4.0f} s.'.format(counter))
                else:
                    counter = stabilizationTime
                time.sleep(1.)    
        
        if rampRate > 0:
            self.hm.rampTemperature(setTemperature, rampRate, ramping=False)
    
    def runSequence(self, sequence):
        try:
            self.sequenceRunning, i = True, 0
            self.log_signal.emit('SequenceStarted', 'Sequence started by user.')
            while self.sequenceRunning and (i < len(sequence)):
                params = sequence[i].split()
                action = params[0]

                if action == 'MeasureIc':
                    nic = int(params[8])
                    for n in range(nic):
                        self.measureIc(currentSource=params[-1], rampStart=float(params[12]), iStep=float(params[15]), maxV=float(params[19])*1e-6, tag=params[4], vb=True)
                        self.log_signal.emit('SequenceUpdate', 'Ic measurement # {} / {}'.format(n+1, nic))
                    self.log_signal.emit('SequenceUpdate', 'Ic measurements completed! # {} / {}'.format(n+1, nic))
                    
                elif action == 'MeasureTc':
                    self.log_signal.emit('SequenceUpdate', 'Tc measurement in progress # {} / {}'.format(0, 100))
                    self.measureTc(startT=float(params[8]), rampRate=float(params[15]), stopT=float(params[12]), transportCurrent=int(params[19]), tag=params[4])
                    self.log_signal.emit('SequenceUpdate', 'Tc measurement complete! # {} / {}'.format(100, 100))
                    
                elif action == 'SetTemperature':
                    self.stabilizeTemperature(setTemperature=float(params[4]), rampRate=float(params[16]), stabilizationTime=int(params[12]), stabilizationMargin=float(params[8]), vb=False)
                    deltaT = []
                    for j in range(30):
                        _, sampleT, targetT, _, _, _ = self.hm.getTemperatureReading()
                        deltaT.append(sampleT-targetT)
                        time.sleep(1)
                    self.stabilizeTemperature(setTemperature=targetT-numpy.nanmean(deltaT), rampRate=0, stabilizationTime=int(params[12])/2, stabilizationMargin=float(params[8]), vb=False)
                    
                elif action == 'Wait':
                    waitTime = int(params[1])
                    for t in range(waitTime):
                        time.sleep(1)
                        self.log_signal.emit('SequenceUpdate', '{} seconds remain. Waiting for {} seconds.'.format(t, waitTime))
                
                elif action == 'Warmup':
                    print('ask for warmup')
                    self.warmup()
                    print('warmup granted')

                    currentTemperature = self.dm.getLatestValue('Target Temperature')
                    print(currentTemperature, self.warmupTemperature)
                    print('entering loop 1 ')
                    while (currentTemperature < self.warmupTemperature) :
                        self.log_signal.emit('SequenceUpdate', '{} K. Warming up to {} K.'.format(int(currentTemperature), int(self.warmupTemperature)))
                        currentTemperature = self.dm.getLatestValue('Target Temperature')
                        print(currentTemperature, self.warmupTemperature)
                        time.sleep(1)
                    print('entering loop 2')
                    deltaT, npoints = [], 30
                    for j in range(npoints):
                        _, sampleT, targetT, _, _, _ = self.hm.getTemperatureReading()
                        deltaT.append(sampleT-targetT)
                        self.log_signal.emit('SequenceUpdate', '{} / {} points.'.format(j, npoints))
                        time.sleep(1)
                    print('exit loop 2 and offset temperature setpoint')    
                    self.hm.setSetpointTemperature(targetT-numpy.nanmean(deltaT))

                else:
                    self.log_signal.emit('InvalidStep', 'Step {} in Sequence {} is not a valid action.'.format(i, 'SequenceName'))
                i += 1
        
        except Exception as e:
            self.log_signal.emit('Exception', 'Exception while running sequence {} step {}:\n{}'.format('SequenceName', i, e))
            print(e)

        finally:
            if self.sequenceRunning:
                self.sequenceRunning = False
                self.log_signal.emit('SequenceStopped', 'Stopped : Sequence completed sucessfully!')
            else:
                self.log_signal.emit('SequenceStopped', 'Stopped : Sequence stopped by user.')


    def calibrate100ACurrentSource(self, currentRangeUpperLimit):
        shuntR = self.hm.getShuntResistance()

        self.hm.measureSampleWith(device='nanovoltmeter')
        self.hm.connectSampleTo100A(connected=True)

        set_current, currentstep = 0., 0.5  # amps
        set_voltage, current = [], []

        while (set_current < currentRangeUpperLimit):
            control_voltage = self.hm.setLargeCurrent(set_current, calib=False)
            if control_voltage is numpy.nan:
                control_voltage = 0.
            set_voltage.append(control_voltage)
            current.append(self.hm.getCurrentReading())
            set_current += currentstep
            print('iShunt = {:4.3f}\t setV = {:4.3f}'.format(current[-1], set_voltage[-1]))
        
        self.hm.setLargeCurrent(0)
        self.hm.connectSampleTo100A(connected=False)
        self.hm.measureSampleWith(device='picoammeter')
        
        voltage, set_voltage = numpy.array(current)*shuntR, numpy.array(set_voltage)
        a, b = self.dm.updateCSCalibration(voltage, set_voltage, shuntR)
        self.hm.setLargeCurrentCalibration(a, b)
        
        self.log_signal.emit('Calibrated100ACS', 'a = {:4.4f}, b = {:4.4f}'.format(a, b))

    def setTargetLight(self, on):
        self.hm.setTargetLight(on)
        self.log_signal.emit('TargetLight', 'on = {}'.format(str(on)))

    def setChamberLight(self, on):
        self.hm.setChamberLight(on)
        self.log_signal.emit('ChamberLight', 'on = {}'.format(str(on)))
        