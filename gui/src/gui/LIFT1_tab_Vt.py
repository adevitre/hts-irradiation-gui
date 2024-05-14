import os, numpy, time, re, datetime, pyqtgraph

from configure import load_json

from plottingArea import MeasurePlot
from listwidget import ListWidget
from progresslabel import ProgressLabel
from fittingFunctions import powerLaw

from PyQt5.QtWidgets import QWidget, QPushButton, QLabel, QGridLayout, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QMessageBox, QInputDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import pyqtSignal, Qt, QTimer

class LIFT1_tab_Vt(QWidget):
    
    setcurrent_signal = pyqtSignal(float)
    measure_signal = pyqtSignal(float, bool, str)
    updatePlot_signal = pyqtSignal()
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        
        super(LIFT1_tab_Vt, self).__init__(parent)
        self.parent = parent
        
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        
        self.acquiring = False
        self.lastLabel = ''
        gridLayout = QGridLayout(self)

        self.QtimerUpdatePlot = QTimer()
        self.QtimerUpdatePlot.setInterval(100)
        self.QtimerUpdatePlot.timeout.connect(lambda: self.updatePlot_signal.emit())
        self.plottingArea = MeasurePlot(xLabel='Time [s]', yLabel='Voltage [uV]', title='Voltage vs Time')
        
        self.QLabel_stepSize = QLabel(self)
        self.QLabel_threshold = QLabel(self)
        self.QLabel_stepSize.setText('Current [A]')
        self.QLabel_threshold.setText('Voltage limit [uV]')
        
        self.QDoubleSpinBox_current = QDoubleSpinBox(self)
        self.QDoubleSpinBox_current.setRange(0., 100.)
        self.QDoubleSpinBox_current.setValue(0.0)
        self.QDoubleSpinBox_current.setDecimals(3)
        self.QDoubleSpinBox_current.setSingleStep(.002)
        self.QDoubleSpinBox_current.valueChanged.connect(lambda: self.setcurrent_signal.emit(self.QDoubleSpinBox_current.value()))
        self.QDoubleSpinBox_current.setSingleStep(.1)
        self.QDoubleSpinBox_current.setEnabled(True)
        
        self.QDoubleSpinBox_threshold = QDoubleSpinBox(self)
        self.QDoubleSpinBox_threshold.setRange(0, self.preferences["tv_voltageThreshold"])
        self.QDoubleSpinBox_threshold.setValue(20)
        self.QDoubleSpinBox_threshold.setSingleStep(.5)
        self.QDoubleSpinBox_threshold.setEnabled(False)
        
        self.QLabel_measureConfirm = ProgressLabel('acquiring')
        self.QLabel_measureConfirm.setText('')
        
        # Past measurements
        self.pushButtonAddToPlot = QPushButton(self)
        self.pushButtonAddToPlot.clicked.connect(lambda: self.overplot())
        self.pushButtonAddToPlot.setText('Add curves to plot...')
        
        self.QPushButton_clearPlot = QPushButton(self)
        self.QPushButton_clearPlot.setText('Clear plot')
        self.QPushButton_clearPlot.clicked.connect(lambda: self.clearPlot())
        
        self.QPushButton_measure = QPushButton(self)
        self.QPushButton_measure.setStyleSheet(self.styles['QPushButton_disable'])
        self.QPushButton_measure.setText('Measure')
        self.QPushButton_measure.clicked.connect(lambda: self.simulate())
        self.QPushButton_measure.setEnabled(False)
        
        verticalLayout = QVBoxLayout()
        verticalLayout.addStretch()
        verticalLayout.addWidget(self.QLabel_stepSize)
        verticalLayout.addWidget(self.QDoubleSpinBox_current)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QLabel_threshold)
        verticalLayout.addWidget(self.QDoubleSpinBox_threshold)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.pushButtonAddToPlot)
        verticalLayout.addWidget(self.QPushButton_clearPlot)
        verticalLayout.addWidget(QLabel(" "))
        verticalLayout.addWidget(self.QPushButton_measure)
        verticalLayout.addWidget(self.QLabel_measureConfirm)

        #gridLayout.addWidget(self.listWidget)
        gridLayout.addLayout(verticalLayout, 5, 0)
        gridLayout.addWidget(self.plottingArea, 0, 1, 9, 9)

    def measure(self, tag=None):
        if (not self.acquiring):
            ok = True
            if tag is None:
                tag, ok = QInputDialog.getText(self, 'Voltage vs Time measurement', 'Briefly describe this measurement', text=self.lastLabel)
            if ok:
                if re.match('^[a-zA-Z0-9_-]+$', tag) is not None:
                    self.acquiring, self.lastLabel = True, tag
                    self.QPushButton_measure.setStyleSheet(self.styles['QPushButton_acquiring'])
                    self.QPushButton_measure.setText('Stop')
                    self.QDoubleSpinBox_current.setEnabled(True)
                    self.QLabel_measureConfirm.start()
                    self.plottingArea.addCurve(name=tag, color=(numpy.random.rand(), numpy.random.rand(), numpy.random.rand()))
                    self.QtimerUpdatePlot.start()
                    self.measure_signal.emit(self.QDoubleSpinBox_threshold.value()*1e-6, False, tag)
                else:
                    QMessageBox.warning(self, 'Warning: invalid tag \"{}\"'.format(tag), 'Use only alphanumeric characters.')
        else:
            self.QDoubleSpinBox_current.setEnabled(False)
            self.measure_signal.emit(self.QDoubleSpinBox_threshold.value()*1e-6, True, 'stop')
            self.resetGUI()
    
    def overplot(self):
        filepaths = QFileDialog.getOpenFileNames(self, 'Select Vt curves to add to plotting area', self.parent.dm.save_directory+'/Vt')[0]

        for path in filepaths:
            try:
                t, v, temp, tag = [], [], 1.,'fail' 
                t, v = numpy.genfromtxt((line  for line  in open(path, 'rb') if line[0] != '#'), usecols=[1, 3], unpack=True, skip_header=1)
                with open(path) as f:
                    fit_parameters = f.readline().split()
                    temp, tag = float(fit_parameters[-3]), fit_parameters[-1]
                    f.close()

                pen = pyqtgraph.mkPen(color=(int(numpy.random.rand()*255), int(numpy.random.rand()*255), int(numpy.random.rand()*255)))
                self.plottingArea.plotData(t-t[0], v*1e6, name='T = {:4.2f} {}'.format(temp, tag), pen=pen)
            except ValueError as e:
                QMessageBox.warning(self, 'File does not contain an Vt Measurement', 'Did you forget your ADHD medication today? ')
                print(e)
            except Exception as e:
                print(e)

    def clearPlot(self):
        if not self.acquiring:
            self.plottingArea.clear()
        else:
            QMessageBox.warning(self, 'Warning: Clear plot', 'You cannot clear the plot during a measurement.')

    def updateActiveLine(self, time, voltage):
        self.plottingArea.updateActiveLine(time-time[0], voltage*1e6)

    def resetGUI(self):
        self.acquiring = False
        self.QLabel_measureConfirm.stop()
        self.QLabel_measureConfirm.setText('')
        self.QPushButton_measure.setStyleSheet(self.styles['QPushButton_idle'])
        self.QPushButton_measure.setText('Measure')
        self.acquiring = False
        self.QtimerUpdatePlot.stop()
        self.QDoubleSpinBox_current.setValue(0.0)
        self.QDoubleSpinBox_current.setEnabled(True)

    def enable(self, enabled=True):
        self.QPushButton_measure.setEnabled(enabled)
        self.QDoubleSpinBox_threshold.setEnabled(enabled)
        self.QPushButton_measure.setStyleSheet(self.styles['QPushButton_idle'])
        self.QPushButton_measure.clicked.disconnect()
        self.QPushButton_measure.clicked.connect(lambda: self.measure())
