import os, numpy, time, re, datetime, pyqtgraph

from configure import load_json
from progresslabel import ProgressLabel
from plottingArea import MeasurePlot
from fittingFunctions import powerLaw

from PyQt5.QtWidgets import QWidget, QPushButton, QComboBox, QLabel, QGridLayout,QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QMessageBox, QInputDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

LABEL_CAEN = 'CAEN'
LABEL_CS100A = 'HP6260B-120A'
LABEL_CS006A = '2231A-30-3-6A'

class LIFT1_tab_Ic(QWidget):
    
    measure_signal = pyqtSignal(float, float, float, str, bool, str)
    updatePlot_signal = pyqtSignal()
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        
        super(LIFT1_tab_Ic, self).__init__(parent)
        self.parent = parent
        
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        self.hardwareParameters = load_json(fname='hwparams.json', location=os.getcwd()+'/config')
        
        self.acquiring = False
        self.lastLabel = ''
        gridLayout = QGridLayout(self)
        
        self.QtimerUpdatePlot = QTimer()
        self.QtimerUpdatePlot.setInterval(100)
        self.QtimerUpdatePlot.timeout.connect(lambda: self.updatePlot_signal.emit())

        self.plottingArea = MeasurePlot(xLabel='Current [A]', yLabel='Voltage [uV]', title='Voltage vs Transport current')
        self.plottingArea.plotInfiniteLine(pos=(0, self.hardwareParameters['bridgeLength']*0.1), angle=180, label='Vc') # marks the position of Vc
        
        self.QLabel_rampStart = QLabel(self)
        self.QLabel_stepSize = QLabel(self)
        self.QLabel_threshold = QLabel(self)
        self.QLabel_currentSource = QLabel(self)
        self.QLabel_nMeasurements = QLabel(self)
        self.QLabel_waitTime = QLabel(self)
        self.QLabel_rampStart.setText('Ramp start [A]')
        self.QLabel_stepSize.setText('Step size [A]')
        self.QLabel_threshold.setText('Voltage limit [uV]')
        self.QLabel_nMeasurements.setText('Repeat measurement')
        self.QLabel_waitTime.setText('Wait before next IV [s]')
        self.QLabel_currentSource.setText('Select current source')

        spb_font = QFont()
        spb_font.setPointSize(22)
        spb_font.setBold(True)
        spb_font.setWeight(75)
        
        self.comboBoxSelectCurrentSource = QComboBox(self)
        self.comboBoxSelectCurrentSource.addItems([LABEL_CAEN, LABEL_CS006A, LABEL_CS100A]) # WARNING: Changing these labels will affect the functionality of Ic measurements!
        self.comboBoxSelectCurrentSource.activated.connect(self.comboBoxSelectCurrentSource_activated)
        self.comboBoxSelectCurrentSource.setEnabled(True)

        self.QSpinBox_nMeasurements = QSpinBox(self)
        self.QSpinBox_nMeasurements.setRange(0, 20)
        self.QSpinBox_nMeasurements.setValue(1)
        self.QSpinBox_nMeasurements.setSingleStep(1)
        self.QSpinBox_nMeasurements.setFont(spb_font)
        self.QSpinBox_nMeasurements.setAlignment(Qt.AlignCenter)
        self.QSpinBox_nMeasurements.setEnabled(False)
        
        self.QSpinBox_rampStart = QSpinBox(self)
        self.QSpinBox_rampStart.setRange(0, 100)
        self.QSpinBox_rampStart.setValue(0)
        self.QSpinBox_rampStart.setSingleStep(10)
        self.QSpinBox_rampStart.setEnabled(False)

        self.QSpinBox_waitTime = QSpinBox(self)
        self.QSpinBox_waitTime.setRange(0, 600)
        self.QSpinBox_waitTime.setValue(self.preferences["waitBetweenSuccessiveIV"])
        self.QSpinBox_waitTime.setSingleStep(5)
        self.QSpinBox_waitTime.setEnabled(False)

        self.QDoubleSpinBox_stepSize = QDoubleSpinBox(self)
        self.QDoubleSpinBox_stepSize.setRange(0.001, 5.000)
        self.QDoubleSpinBox_stepSize.setValue(0.001)
        self.QDoubleSpinBox_stepSize.setDecimals(3)
        self.QDoubleSpinBox_stepSize.setSingleStep(0.001)
        self.QDoubleSpinBox_stepSize.setEnabled(False)

        self.QDoubleSpinBox_threshold = QDoubleSpinBox(self)
        # changed multiplier to 500 for quenchbox testing, Ben Clark, 5/10/24 
        self.QDoubleSpinBox_threshold.setRange(0.1, self.preferences["iv_voltageThreshold"]*500) 
        self.QDoubleSpinBox_threshold.setValue(self.preferences["iv_voltageThreshold"])
        self.QDoubleSpinBox_threshold.setSingleStep(.5)
        self.QDoubleSpinBox_threshold.setEnabled(False)

        self.labelMeasureIc = QLabel('')
        
        # Past measurements
        self.pushButtonAddToPlot = QPushButton(self)
        self.pushButtonAddToPlot.clicked.connect(lambda: self.overplot())
        self.pushButtonAddToPlot.setText('Add curves to plot...')
        
        self.QPushButton_clearIcPlot = QPushButton(self)
        self.QPushButton_clearIcPlot.setText('Clear plot')
        self.QPushButton_clearIcPlot.clicked.connect(lambda: self.clearPlot())
        
        self.QPushButton_measureIc = QPushButton(self)
        self.QPushButton_measureIc.setStyleSheet(self.styles['QPushButton_disable'])
        self.QPushButton_measureIc.setText('Measure')
        self.QPushButton_measureIc.clicked.connect(lambda: self.measureIc())
        self.QPushButton_measureIc.setEnabled(False)

        verticalLayout = QVBoxLayout()
        verticalLayout.addStretch()
        verticalLayout.addWidget(self.QLabel_currentSource)
        verticalLayout.addWidget(self.comboBoxSelectCurrentSource)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QLabel_nMeasurements)
        verticalLayout.addWidget(self.QSpinBox_nMeasurements)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QLabel_waitTime)
        verticalLayout.addWidget(self.QSpinBox_waitTime)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QLabel_rampStart)
        verticalLayout.addWidget(self.QSpinBox_rampStart)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QLabel_stepSize)
        verticalLayout.addWidget(self.QDoubleSpinBox_stepSize)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QLabel_threshold)
        verticalLayout.addWidget(self.QDoubleSpinBox_threshold)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.pushButtonAddToPlot)
        verticalLayout.addWidget(self.QPushButton_clearIcPlot)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QPushButton_measureIc)
        verticalLayout.addWidget(self.labelMeasureIc)

        gridLayout.addLayout(verticalLayout, 5, 0)
        gridLayout.addWidget(self.plottingArea, 0, 1, 9, 9)

    def measureIc(self, tag=None):

        if (not self.acquiring):
            tag, ok = QInputDialog.getText(self, 'Critical currrent measurement', 'Briefly describe this measurement', text=self.lastLabel)
            if ok:
                if re.match('^[a-zA-Z0-9_-]+$', tag) is not None:
                    self.lastLabel = tag
                    self.enableDataAcquisition(enabled=True, tag=tag)
                    self.measure_signal.emit(self.QSpinBox_rampStart.value(), self.QDoubleSpinBox_stepSize.value(), self.QDoubleSpinBox_threshold.value()*1e-6, self.comboBoxSelectCurrentSource.currentText(), False, tag)
                else:
                    QMessageBox.warning(self, 'Warning: invalid tag \"{}\"'.format(tag), 'Use only alphanumeric characters.')
        else:
            self.measure_signal.emit(self.QSpinBox_rampStart.value(), self.QDoubleSpinBox_stepSize.value(), self.QDoubleSpinBox_threshold.value()*1e-6, self.comboBoxSelectCurrentSource.currentText(), True, 'stop')
            self.enableDataAcquisition(enabled=False)
    
    def comboBoxSelectCurrentSource_activated(self):
        if self.comboBoxSelectCurrentSource.currentText() == LABEL_CS100A:
            self.QDoubleSpinBox_stepSize.setValue(0.3)
            self.QDoubleSpinBox_stepSize.setDecimals(1)
            self.QDoubleSpinBox_stepSize.setSingleStep(0.1)
            self.QDoubleSpinBox_stepSize.setRange(0.3, 3.0)
            
        elif self.comboBoxSelectCurrentSource.currentText() == LABEL_CS006A:
            self.QDoubleSpinBox_stepSize.setDecimals(3)
            self.QDoubleSpinBox_stepSize.setSingleStep(0.001)
            self.QDoubleSpinBox_stepSize.setRange(0.001, 0.500)
            self.QDoubleSpinBox_stepSize.setValue(0.20)

    def overplot(self):
        filepaths = QFileDialog.getOpenFileNames(self, 'Select IV curves to add to plotting area', self.parent.dm.save_directory+'/Ic')[0]
        for path in filepaths:
            try:
                i, v, ic, n, temp, tag = [], [], 1., 1., 1.,'fail' 
                i, v = numpy.genfromtxt((line  for line  in open(path, 'rb') if line[0] != '#'), usecols=[2, 3], unpack=True)
                if v[numpy.argmax(numpy.abs(v))] < 0:
                    v *= -1 # fix for data where sample was reverse biased.
                with open(path) as f:
                    fit_parameters = f.readline().split()
                    ic, n, temp, tag = float(fit_parameters[3]), float(fit_parameters[7]), float(fit_parameters[-3]), fit_parameters[-1]
                    f.close()
                    
            except ValueError as e:
                QMessageBox.warning(self, 'File does not contain an Ic Measurement', 'Did you forget your ADHD medication today? ', e)

            except UnboundLocalError as e:
                print('Crappy file!', e)

            except Exception as e:
                ic, n, tag = self.parent.dm.fitIcMeasurement(i, v), 'legacy'

            finally:
                pen = pyqtgraph.mkPen(color=(int(numpy.random.rand()*255), int(numpy.random.rand()*255), int(numpy.random.rand()*255)), width=3, symbol='+', symbolSize=5)
                self.plottingArea.plotData(i, v*1e6, name='T = {:4.2f} {}'.format(temp, tag), pen=pen)
                
                fitParameters = [ic, n]
                if numpy.isfinite(fitParameters).all():
                    self.plottingArea.plotFit(xvalues=i, fitParameters=fitParameters, pen=pen)
        
    def clearPlot(self):
        if not self.acquiring:
            self.plottingArea.clear()
            self.plottingArea.plotInfiniteLine(pos=(0, self.hardwareParameters['bridgeLength']*0.1), angle=180, label='Vc')
        else:
            QMessageBox.warning(self, 'Warning: Clear plot', 'You cannot clear the plot during a measurement.')


    def nextMeasurement(self, tag):
        self.QSpinBox_nMeasurements.setValue(self.QSpinBox_nMeasurements.value()-1) 
        if self.QSpinBox_nMeasurements.value() > 0:
            for i in range(self.QSpinBox_waitTime.value()): 
                self.labelMeasureIc.setText('Next IV in {:4.0f} s'.format(self.QSpinBox_waitTime.value()-i))
                time.sleep(1.)
            self.measure_signal.emit(self.QSpinBox_rampStart.value(), self.QDoubleSpinBox_stepSize.value(), self.QDoubleSpinBox_threshold.value()*1e-6, self.comboBoxSelectCurrentSource.currentText(), False, tag)
        else:
            self.enableDataAcquisition(False)
            self.labelMeasureIc.setText('Data saved in file')
            self.log_signal.emit('IcSequenceComplete', '')

    def setMeasurementCounter(self, value):
        self.QSpinBox_nMeasurements.setValue(value)
    
    def updateActiveLine(self, current, voltage):
        self.plottingArea.updateActiveLine(current, voltage*1e6)


    def enableDataAcquisition(self, tag='', enabled=False):
        self.acquiring = enabled
        if enabled:
            self.QPushButton_measureIc.setStyleSheet(self.styles['QPushButton_acquiring'])
            self.QPushButton_measureIc.setText('Stop')
            self.plottingArea.addCurve(name=tag, color=(numpy.random.rand(), numpy.random.rand(), numpy.random.rand()), width=3)
            self.QtimerUpdatePlot.start()
        else:
            self.QPushButton_measureIc.setStyleSheet(self.styles['QPushButton_idle'])
            self.QPushButton_measureIc.setText('Measure')
            self.QtimerUpdatePlot.stop()

    def enable(self, enabled=True):
        self.QPushButton_measureIc.setEnabled(enabled)
        self.QSpinBox_nMeasurements.setEnabled(enabled)
        self.QSpinBox_rampStart.setEnabled(enabled)
        self.QDoubleSpinBox_stepSize.setEnabled(enabled)
        self.QSpinBox_waitTime.setEnabled(enabled)
        self.QDoubleSpinBox_threshold.setEnabled(enabled)
        self.QPushButton_measureIc.setStyleSheet(self.styles['QPushButton_idle'])
