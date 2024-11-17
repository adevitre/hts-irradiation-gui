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

HARDWARE_PARAMETERS = load_json(fname='hwparams.json', location=os.getcwd()+'/config')

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
        
        if not self.ln2Measurements:
            self.tcTimer.start(int(self.preferences['sampling_period_tc']*1000))
            self.pmTimer.start(int(self.preferences['sampling_period_pm']*1000))
            self.plotTimer.start(1000)
            self.dataBackupTimer.start(int(self.preferences['saverate']*1000)) # TQp data backup, user specified in seconds
        else:
            self.dm.updateEnvironmentPlots()
    
    def stopReadings(self):
        if not self.ln2Measurements:
            self.tcTimer.stop()
            self.pmTimer.stop()
            self.plotTimer.stop()
            self.dataBackupTimer.stop()


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
    
    def connectFourPointProbe(self, connected=True, current_source=HARDWARE_PARAMETERS['LABEL_LS121']):
        """
            connectFourPointProbe connects or disconnects the transport measurement system for Ic, Tc, and Vt measurements.
            It also resets the Quench Protection System (QPS) everytime the measurement starts.

            @params
                connected (bool): indicates if the fourpoint probe should be connected or disconnected.
                current_source (str): indicates which current source should be connected.
        """
        if connected:
            self.hm.measureSampleWith(device='nanovoltmeter')
        #else:
        #    self.hm.measureSampleWith(device='picoammeter') #
  
        if current_source == HARDWARE_PARAMETERS['LABEL_CS006A']:
            self.hm.setLargeCurrent(0.000, currentSource=current_source)
            self.useDMM, self.maxI = True, 5.9 # The 2231A-30-3 gets stuck at 5.9 A (max rating 6A)
            self.hm.enableParallelMode(enabled=connected)
            self.hm.connectSampleTo100A(connected=not connected)
            self.hm.connectSampleTo6A(connected=connected)

        elif current_source == HARDWARE_PARAMETERS['LABEL_CS100A']:
            self.useDMM, self.maxI = True, 120
            self.hm.setLargeCurrent(0.000, currentSource=current_source)
            self.hm.enableParallelMode(enabled=not connected)
            self.hm.connectSampleTo6A(connected=not connected)
            self.hm.connectSampleTo100A(connected=connected)

        elif current_source == HARDWARE_PARAMETERS['LABEL_CAEN']:
            self.useDMM, self.maxI = True, 100
            self.hm.setLargeCurrent(0.000, currentSource=current_source)
            self.hm.connectSampleTo6A(connected=not connected)
            self.hm.connectSampleTo100A(connected=connected)

        elif current_source == HARDWARE_PARAMETERS['LABEL_TDK']:
            self.useDMM, self.maxI = True, 100
            self.hm.connectSampleTo6A(connected=not connected)
            self.hm.connectSampleTo100A(connected=connected)

        elif current_source == HARDWARE_PARAMETERS['LABEL_LS121']:
            self.useDMM = True
            self.hm.setSmallCurrent(0.000)
            if connected:
                self.hm.connectCurrentSource100mATo('sample')
            else:
                self.hm.connectCurrentSource100mATo(device='hallSensor')
        
        if connected:
            self.resetQPS() # this might need to be at the end...Seems likely! Alexis Devitre 2024.09.16
    
    def measureTc(self, startT, rampRate, stopT, transportCurrent, tag):
        """
        MeasureTc ramps the temperature at a fixed rate, while measuring voltage at fixed transport current. 
        The setpoint is set past stopT accounting for a possible temperature difference between the PID 
        sensor (CX-CH) and the sensor on sample (CX-T).
        
        @params
            startT (float): Start temperature in K.
            stopT (float): Stop temperature in K.
            transportCurrent (float): magnitude of the current through the sample 100 nA to 100 mA
            tag (str): a descriptive file name
        """
        tc, self.datapoints, self.acquiring = numpy.nan, [], True

        self.connectFourPointProbe(connected=True, current_source=HARDWARE_PARAMETERS['LABEL_LS121'])
        
        sampleT, targetT = self.dm.getLatestValue('Sample Temperature'), self.dm.getLatestValue('Target Temperature')
        self.stabilizeTemperature(setTemperature=startT, rampRate=9, stabilizationMargin=self.preferences['TcStabilizationMargin'], stabilizationTime=60, vb=True)
        
        if self.acquiring:
            if stopT > startT:
                self.hm.rampTemperature(95, rampRate, ramping=True)
            else:
                self.hm.rampTemperature(10, rampRate, ramping=True)
        try:
            while (self.acquiring & (numpy.abs(sampleT - stopT) > 0.3)):
                sampleT, targetT, spareT, holderT = self.dm.getLatestValue('Sample Temperature'), self.dm.getLatestValue('Target Temperature'), self.dm.getLatestValue('Spare Temperature'), self.dm.getLatestValue('Holder Temperature')
                
                self.hm.setSmallCurrent(transportCurrent)
                vpos = self.hm.getVoltageReading(removeOffset=False)
                
                self.hm.setSmallCurrent(-1*transportCurrent)
                vneg = self.hm.getVoltageReading(removeOffset=False)
                vavg = (vpos-vneg)/2.
                
                self.datapoints.append([float(datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')), time.time()-self.dm.t0, self.hm.getCurrentReading(useDMM=True), vavg, sampleT, targetT, vpos, vneg, holderT, spareT])
                if self.sequenceRunning:
                    self.log_signal.emit('SequenceUpdate', 'Measuring Tc (T = {:3.2f} v+ = {:3.3e} v- = {:3.3e} vavg = {:3.3e}) /{}/{}'.format(sampleT, vpos, vneg, vavg, numpy.abs(stopT-startT)-numpy.abs(sampleT-stopT), numpy.abs(stopT-startT)))
                else:
                    print('T = {:3.2f} v+ = {:3.5e} v- = {:3.5e} vavg = {:3.5e}'.format(sampleT, vpos, vneg, vavg))
            
            self.hm.rampTemperature(stopT, 1., ramping=False)
            
            self.connectFourPointProbe(connected=False, current_source=HARDWARE_PARAMETERS['LABEL_LS121'])

            if ((self.datapoints is not []) & self.acquiring):
                tData = numpy.transpose(self.datapoints)  # 3 is voltage, 4 is sample temperature
                tc, _ = self.dm.fitTcMeasurement(tData[3], tData[4], tag)
                
        except Exception as e:
            print('Taskmanager::measureTc raised:', e)

        finally:
            self.hm.setSmallCurrent(0)
            if self.acquiring: # not acquiring means the user wants to stop, so the measurement is likely incomplete and not worth saving or displaying
                self.acquiring = False
            else:
                self.log_signal.emit('Note', 'Tc sequence canceled by user')
                print('Tc sequence cancelled by user.')

            tData = numpy.transpose(self.datapoints)
            self.log_signal.emit('Tc', 'Tc = {:4.2f} K, {}'.format(tc, tag))


    def measureIc(self, rampStart=0, iStep=0.1, maxV=1e-5, currentSource=HARDWARE_PARAMETERS['LABEL_CS100A'], tag='Pristine', vb=True):
        '''
            Performs Ic measurement. Requests fitting and data output from datamanager object,
            then plotting and logging from LIFT1_GUI object.
            
            INPUTS            ---------
            rampStart - (float) Starting value of current ramp
            iStep     - (float) Current ramp step in amps
            maxV      - (float) Voltage at which the current ramp is terminated
            tag       - (string) Data file label
            vb        - (bool) Verbose enables printouts for debugging
        '''
        self.connectFourPointProbe(connected=True, current_source=currentSource)
        
        try:
            self.datapoints, self.acquiring = [], True
            v, iRequest, control_voltage = 0, 0, 0
            self.hm.setVoltageOffset() # needs to come after acquiring is set to True to avoid conflicts
            
            if rampStart > 10: # Ramp the power in steps slowly to avoid "tail lifting" in IV curve due to induction
                while (self.acquiring) and (iRequest < rampStart) and (control_voltage is not numpy.nan) and (abs(v) < maxV):
                    control_voltage = self.hm.setLargeCurrent(iRequest, currentSource=currentSource, vb=vb)
                    v = self.hm.getVoltageReading()
                    iRequest += 0.2*rampStart
            
            v, i, iRequest = 0, 0.0, rampStart
            while(self.acquiring and (abs(v) < maxV) and (iRequest < self.maxI) and (control_voltage != numpy.nan)):
                
                control_voltage = self.hm.setLargeCurrent(iRequest, currentSource=currentSource, vb=vb)
                sampleT, targetT, holderT, spareT = self.dm.getLatestValue('Sample Temperature'), self.dm.getLatestValue('Target Temperature'), self.dm.getLatestValue('Holder Temperature'), self.dm.getLatestValue('Spare Temperature')
                v = self.hm.getVoltageReading()
                i = self.hm.getCurrentReading(useDMM=self.useDMM)
                self.datapoints.append([float(datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')), time.time()-self.dm.t0, i, v, sampleT, targetT, holderT, spareT])
                iRequest += iStep
                if self.sequenceRunning:
                    pass # In the future we will add sequence updates
                else:
                    print('i = {:<4.3f}A, v = {:<4.3e}V, v_control={:<4.3e}, next_request={:<4.3e}'.format(i, v, control_voltage, iRequest))
            
            if self.datapoints: # [] is False
                data = numpy.transpose(self.datapoints)
                tavg = data[4][-1]
                ic, n, self.corrected_voltage = self.dm.fitIcMeasurement(data[2], data[3])
                self.dm.saveMeasurementToFile(self.datapoints, measurement='Ic', ic=ic, n=n, tavg=tavg, tag=tag, timestamp=str(datetime.datetime.now()))

                if self.acquiring: # not acquiring means the user wants to stop, so the measurement is likely incomplete and not worth saving or displaying
                    self.log_signal.emit('Ic', 'Ic = {:4.2f} A, n = {:4.2f} , Tavg = {:4.2f} K, {}'.format(ic, n, tavg, tag))
                    self.acquiring = False
                else:
                    self.log_signal.emit('Note', 'Ic sequence canceled by user')
        except Exception as e: # Usually IndexError or TypeError
            ic, n, tavg = numpy.nan, numpy.nan, numpy.nan
            print('TaskManager::measureIc raised: ', e)
            
        finally:
            self.connectFourPointProbe(connected=False, current_source=currentSource)
            self.datapoints = [] # datapoints must be erased to avoid showing the previous measurement at the start of the next.
            if not self.sequenceRunning: # in case the measurement was requested by the GUI not by a sequence.
                self.log_signal.emit('nextIV', tag)

    def measureVt(self, maxV=1e-5, tag='Pristine', current_source=HARDWARE_PARAMETERS['LABEL_CS100A']):
        '''
            Performs voltage vs time measurement.
            
            @params
            tStep (float): Sampling period in seconds
            maxV (float): Voltage at which the current ramp is terminated
            tag (string) Data file label
        '''
        self.connectFourPointProbe(connected=True, current_source=current_source)

        try:
            if maxV == 0.:
                maxV = numpy.inf

            self.datapoints, self.acquiring, v = [], True, 0
            self.hm.setVoltageOffset() # needs to come after acquiring is set to True to avoid conflicts
            
            while(self.acquiring and (abs(v) < maxV)):
                t, v, i, sampleT, targetT, holderT, spareT = time.time()-self.dm.t0, self.hm.getVoltageReading(removeOffset=True), self.hm.getCurrentReading(useDMM=self.useDMM), self.dm.getLatestValue('Sample Temperature'), self.dm.getLatestValue('Target Temperature'), self.dm.getLatestValue('Holder Temperature'), self.dm.getLatestValue('Spare Temperature')
                self.datapoints.append([float(datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')), t, i, v, sampleT, targetT, holderT, spareT])
            
            tData = numpy.transpose(self.datapoints)
            tmax = tData[4][-1]
            
        except Exception as e:
            tmax, self.acquiring = numpy.nan, False
            print('TaskManager::measureVt raised: ', e)
            
        finally:
            self.connectFourPointProbe(connected=False, current_source=current_source)
            self.log_signal.emit('Vt', 'TransportCurrent = {:4.2f}, Tavg = {:4.2f} K, {}'.format(i, tmax, tag))
            
    def stopAcquiring(self):
        """
            stopAcquiring allows the user to stop a measurement in progress. 
            The 'acquiring' attribute is switched to False, which breaks the measurement loop.
        """
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
            pidSensor = self.hm.getPIDSensor()
            
            while (self.acquiring | self.annealing | self.sequenceRunning) and (counter > 0):
                inputAT, inputBT, inputCT, inputDT = self.dm.getLatestTemperatureReading()
                pidSensorT = [inputAT, inputBT, inputCT, inputDT][pidSensor-1] # A = 1, B = 2, C = 3, D = 4
                if numpy.abs(setTemperature - pidSensorT) < stabilizationMargin:
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
            commonLabel = ''
            while self.sequenceRunning and (i < len(sequence)):
                params = sequence[i].split()
                action = params[0]

                if action == 'MeasureIc':
                    nic, waitBetweenIVs = int(params[8]), int(params[14])
                    for n in range(nic):
                        self.measureIc(currentSource=params[-1], rampStart=float(params[18]), iStep=float(params[21]), maxV=float(params[25])*1e-6, tag=commonLabel+'_'+params[4], vb=True)
                        if self.sequenceRunning:
                            self.log_signal.emit('SequenceUpdate', 'Ic measurement /{}/{}'.format(n+1, nic))
                            time.sleep(waitBetweenIVs) # there must be a delay to write the data to file
                        else:
                            self.log_signal.emit('SequenceUpdate', 'Ic measurements stopped by user /{}/{}'.format(n+1, nic))
                            break
                    if self.sequenceRunning:
                        self.log_signal.emit('SequenceUpdate', 'Ic measurements completed! /{}/{}'.format(n+1, nic))
                    
                elif action == 'MeasureTc':
                    self.log_signal.emit('SequenceUpdate', 'Tc measurement started /{}/{}'.format(0, 100))
                    self.measureTc(startT=float(params[8]), rampRate=float(params[15]), stopT=float(params[12]), transportCurrent=int(params[19]), tag=commonLabel+'_'+params[4])
                    if self.sequenceRunning:
                        self.log_signal.emit('SequenceUpdate', 'Tc measurement complete! /{}/{}'.format(100, 100))
                    else:
                        self.log_signal.emit('SequenceUpdate', 'Tc measurement stopped by user! /{}/{}'.format(100, 100))
                    
                elif action == 'SetTemperature':
                    self.log_signal.emit('SequenceUpdate', 'Set Temperature /{}/{}'.format(0, 100))
                    self.stabilizeTemperature(setTemperature=float(params[4]), rampRate=float(params[16]), stabilizationTime=int(params[12]), stabilizationMargin=float(params[8]), vb=False)
                    deltaT = 0
                    pidSensor = self.hm.getPIDSensor()
                    deltaT = []
                    for j in range(30):
                        inputAT, inputBT, inputCT, inputDT = self.dm.getLatestTemperatureReading()
                        pidSensorT = [inputAT, inputBT, inputCT, inputDT][pidSensor-1] # A = 1, B = 2, C = 3, D = 4
                        deltaT.append(inputAT-pidSensorT)
                        if self.sequenceRunning:
                            time.sleep(1)
                        else:
                            break
                    if self.sequenceRunning:
                        self.stabilizeTemperature(setTemperature=pidSensorT-numpy.nanmean(deltaT), rampRate=0, stabilizationTime=int(params[12])/2, stabilizationMargin=float(params[8]), vb=False)

                elif action == 'Wait':
                    waitTime = int(params[1])
                    for t in range(waitTime+1):
                        time.sleep(1)
                        if self.sequenceRunning:
                            self.log_signal.emit('SequenceUpdate', 'Seconds elapsed {} of {} /{}/{}'.format(t, waitTime, t, waitTime))
                        else:
                            self.log_signal.emit('SequenceUpdate', 'Wait canceled by user. Seconds elapsed /{}/{}'.format(t, waitTime))
                            break

                elif action == 'Label':
                    commonLabel = params[1]

                elif action == 'Warmup':
                    self.warmup()
                    self.log_signal.emit('SequenceUpdate', 'Warming up the system /{}/{}'.format(self.dm.getLatestValue('Target Temperature'), int(self.warmupTemperature)))
                            
                    while (self.dm.getLatestValue('Target Temperature') < self.warmupTemperature):
                        if self.sequenceRunning:
                            time.sleep(1)
                        else:
                            break
                else:
                    self.log_signal.emit('InvalidStep', 'Step {} in Sequence {} is not a valid action.'.format(i, 'SequenceName'))
                
                i += 1
                self.log_signal.emit('SequenceUpdate', '*'+action+'(Complete) /0/100')

        except Exception as e:
            self.log_signal.emit('Exception', 'Exception while running sequence {} step {}:\n{}/0/0'.format('SequenceName', i, e))
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
            current.append(self.hm.getCurrentReading(useDMM=True))
            set_current += currentstep
            print('iShunt = {:4.3f}\t setV = {:4.3f}'.format(current[-1], set_voltage[-1]))
        
        self.hm.setLargeCurrent(0)
        self.hm.connectSampleTo100A(connected=False)
        self.hm.measureSampleWith(device='picoammeter')
        
        print(current, set_voltage)
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
    
    def resetQPS(self):
        self.hm.resetQPS()
        self.log_signal.emit('QPS', 'QPS reset by user')