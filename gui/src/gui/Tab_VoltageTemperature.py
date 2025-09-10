import os, re, numpy, time, pyqtgraph

from configure import load_json
from progresslabel import ProgressLabel
from plottingArea import MeasurePlot
from listwidget import ListWidget

from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QGridLayout, QVBoxLayout, QSpinBox, QDoubleSpinBox, QFileDialog, QInputDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, QTimer

"""
    Tab_VoltageTemperature is a submodule of the GUI containing GUI objects and functions
    needed to perform measurements of voltage at fixed transport current as a function of 
    temperature, i.e., critical temperature measurements (Tc).

    @author Alexis Devitre (devitre@mit.edu)
    @last-modified July 2024
"""
class Tab_VoltageTemperature(QWidget):
    
    measure_signal = pyqtSignal(float, float, float, float, bool, str)
    updatePlot_signal = pyqtSignal()
    
    def __init__(self, parent=None):
        super(Tab_VoltageTemperature, self).__init__(parent)
        self.parent = parent

        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.acquiring = False
        self.sessionTag, self.lastLabel = '', ''
        gridLayout = QGridLayout(self)
        
        self.QtimerUpdatePlot = QTimer()
        self.QtimerUpdatePlot.setInterval(1000)
        self.QtimerUpdatePlot.timeout.connect(lambda: self.updatePlot_signal.emit())
        self.plottingArea = MeasurePlot(xLabel='Temperature [K]', yLabel='Voltage [uV]', title='Voltage vs Sample temperature')
            
        self.QLabel_rampStart = QLabel(self)
        self.QLabel_rampStart.setText('Ramp start [K]')
        self.QSpinBox_rampStart = QSpinBox(self)
        self.QSpinBox_rampStart.setRange(20, 305)
        self.QSpinBox_rampStart.setValue(60)
        self.QSpinBox_rampStart.setSingleStep(5)
        self.QSpinBox_rampStart.setEnabled(False)
        
        self.QLabel_rampStop = QLabel(self)
        self.QLabel_rampStop.setText(r'Ramp stop [K]')
        self.QSpinBox_rampStop = QSpinBox(self)
        self.QSpinBox_rampStop.setRange(20, 310)
        self.QSpinBox_rampStop.setValue(95)
        self.QSpinBox_rampStop.setEnabled(False)
        
        self.QLabel_rampRate = QLabel(self)
        self.QLabel_rampRate.setText('Ramp rate [K/min]')
        self.QSpinBox_rampRate = QDoubleSpinBox(self)
        self.QSpinBox_rampRate.setRange(0.01, 5)
        self.QSpinBox_rampRate.setValue(0.5)
        self.QSpinBox_rampRate.setSingleStep(.1)
        self.QSpinBox_rampRate.setEnabled(False)
        
        self.QLabel_measureTcConfirm = ProgressLabel('acquiring')
        self.QLabel_measureTcConfirm.setText('')
        
        self.QLabel_transportCurrent = QLabel(self)
        self.QLabel_transportCurrent.setText('Transport Current [mA]')
        self.QSpinBox_transportCurrent = QDoubleSpinBox(self)
        self.QSpinBox_transportCurrent.setRange(0.0001, 100)
        self.QSpinBox_transportCurrent.setValue(1.0000)
        self.QSpinBox_transportCurrent.setSingleStep(0.1)
        self.QSpinBox_transportCurrent.setEnabled(False)

        # Past measurements
        self.pushButtonAddToPlot = QPushButton(self)
        self.pushButtonAddToPlot.clicked.connect(lambda: self.overplot())
        self.pushButtonAddToPlot.setText('Add curves to plot...')
        
        self.QPushButton_clearTcPlot = QPushButton(self)
        self.QPushButton_clearTcPlot.clicked.connect(lambda: self.clearPlot())
        self.QPushButton_clearTcPlot.setText('Clear plot')
        
        self.QPushButton_measureTc = QPushButton(self)
        self.QPushButton_measureTc.setStyleSheet(self.styles['QPushButton_disable'])
        self.QPushButton_measureTc.setText('Measure')
        self.QPushButton_measureTc.clicked.connect(lambda: self.measureTc())
        self.QPushButton_measureTc.setEnabled(False)
        
        #self.listWidget = ListWidget()

        verticalLayout = QVBoxLayout()
        verticalLayout.addStretch()
        verticalLayout.addWidget(self.QLabel_transportCurrent)
        verticalLayout.addWidget(self.QSpinBox_transportCurrent)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QLabel_rampStart)
        verticalLayout.addWidget(self.QSpinBox_rampStart)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QLabel_rampRate)
        verticalLayout.addWidget(self.QSpinBox_rampRate)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QLabel_rampStop)
        verticalLayout.addWidget(self.QSpinBox_rampStop)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.pushButtonAddToPlot)
        verticalLayout.addWidget(self.QPushButton_clearTcPlot)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QPushButton_measureTc)
        verticalLayout.addWidget(self.QLabel_measureTcConfirm)

        #gridLayout.addWidget(self.listWidget)
        gridLayout.addLayout(verticalLayout, 5, 0)
        gridLayout.addWidget(self.plottingArea, 0, 1, 9, 9)
    
    def measureTc(self):
        if (not self.acquiring):
            tag, ok = QInputDialog.getText(self, 'Critical Temperature measurement', 'Briefly describe this measurement', text=self.lastLabel)
            if ok:
                if re.match('^[a-zA-Z0-9_-]+$', tag):
                    self.lastLabel = tag
                    tag = self.sessionTag + tag # done afterwards to avoid accumulating sessionTag in lastLabel
                    self.QPushButton_measureTc.setStyleSheet(self.styles['QPushButton_acquiring'])
                    self.QPushButton_measureTc.setText('Stop')
                    self.QLabel_measureTcConfirm.start()
                    
                    # add a new curve that will be updated during the measurement
                    self.enableDataAcquisition(tag=tag, enabled=True)

                    self.measure_signal.emit(self.QSpinBox_rampStart.value(), self.QSpinBox_rampRate.value(), self.QSpinBox_rampStop.value(), 1e-3*self.QSpinBox_transportCurrent.value(), False, tag)
                    self.acquiring = True
                else:
                    QMessageBox.warning(self, 'Warning: invalid tag', 'Use only alphanumeric characters.')    
        else:
            self.measure_signal.emit(self.QSpinBox_rampStart.value(), self.QSpinBox_rampRate.value(), self.QSpinBox_rampStop.value(), 0, True, 'stop')
            self.enableDataAcquisition(enabled=False)
            self.resetGUI()
           
    def overplot(self):
        filepaths = QFileDialog.getOpenFileNames(self, 'Select TV curves to add to plotting area', self.parent.dm.save_directory+'/Tc')[0]
        for path in filepaths:
            try:
                t, v, tc, tag = numpy.nan, numpy.nan, numpy.nan, ''
                v, t = numpy.genfromtxt((line  for line  in open(path, 'rb') if line[0] != '#'), usecols=[3, 4], unpack=True)
                
                if v[numpy.argmax(numpy.abs(v))] < 0:
                    v *= -1 # fix for data where sample was reverse biased.

                with open(path) as f:
                    header_values = f.readline().split(',')
                    tc, tag = header_values[0].split(' ')[-2], header_values[1]
                    f.close()
            except Exception as e:
                print('LIFT1_tab_Tc::overplot raised ', e)
                print('Legacy file has no fit parameters. Refitting...')
                tc = self.parent.dm.fitTcMeasurement(t, v, tag='legacy')
                tag = 'legacy'
            finally:
                pen = pyqtgraph.mkPen(color=(int(numpy.random.rand()*255), int(numpy.random.rand()*255), int(numpy.random.rand()*255)))
                self.plottingArea.plotData(t, v*1e6, name='I = 1 mA {}'.format(tag), pen=pen)

    def clearPlot(self):
        if not self.acquiring:
            self.plottingArea.clear()
        else:
            QMessageBox.warning(self, 'Warning: Clear plot', 'You cannot clear the plot during a measurement.')
            
    def updateActiveLine(self, temperature, voltage):
        self.plottingArea.updateActiveLine(temperature, voltage*1e6)

    def resetGUI(self):
        self.QLabel_measureTcConfirm.stop()
        self.QPushButton_measureTc.setStyleSheet(self.styles['QPushButton_idle'])
        self.QPushButton_measureTc.setText('Measure')
        self.QtimerUpdatePlot.stop()
        self.acquiring = False

    def enableDataAcquisition(self, tag='', enabled=True):
        if enabled:
            self.QPushButton_measureTc.setStyleSheet(self.styles['QPushButton_acquiring'])
            self.QPushButton_measureTc.setText('Stop')
            self.plottingArea.addCurve(name=tag, color=(numpy.random.rand(), numpy.random.rand(), numpy.random.rand()))
            self.QtimerUpdatePlot.start()
        else:
            self.QPushButton_measureTc.setStyleSheet(self.styles['QPushButton_idle'])
            self.QPushButton_measureTc.setText('Measure')
            if self.QtimerUpdatePlot is not None:
                self.QtimerUpdatePlot.stop()
                
    def enable(self, enabled=True):
        self.QSpinBox_transportCurrent.setEnabled(enabled)
        self.QSpinBox_rampRate.setEnabled(enabled)
        self.QSpinBox_rampStart.setEnabled(enabled)
        self.QSpinBox_rampStop.setEnabled(enabled)
        self.QPushButton_measureTc.setEnabled(enabled)
        self.QPushButton_measureTc.setStyleSheet(self.styles['QPushButton_idle'])
        self.QPushButton_measureTc.setText('Measure')
        self.QPushButton_measureTc.clicked.disconnect()
        self.QPushButton_measureTc.clicked.connect(lambda: self.measureTc())