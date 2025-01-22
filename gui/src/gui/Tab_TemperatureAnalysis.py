import os, numpy, time, re, datetime, pyqtgraph

from configure import load_json
from progresslabel import ProgressLabel
from plottingArea import MeasurePlot
from fittingFunctions import powerLaw

from PyQt5.QtWidgets import QWidget, QPushButton, QComboBox, QLabel, QGridLayout, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QMessageBox, QInputDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

HARDWARE_PARAMETERS = load_json(fname='hwparams.json', location=os.getcwd()+'/config')

'''
    Tab_TemperatureAnalysis is a submodule of the GUI containing GUI objects and functions
    needed to visualize the critical current as a function of temperature at a given fluence.

    @author Alexis Devitre (devitre@mit.edu)
    @last-modified December 2024
'''
class Tab_TemperatureAnalysis(QWidget):
    
    def __init__(self, parent=None):
        
        super(Tab_TemperatureAnalysis, self).__init__(parent)
        self.parent = parent
        
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        
        gridLayout = QGridLayout(self)
        
        self.plottingArea = MeasurePlot(xLabel='Temperature [K]', yLabel='Critical current [A]', title='Critical current vs Temperature')
        
        # Past measurements
        self.pushButtonAddToPlot = QPushButton(self)
        self.pushButtonAddToPlot.clicked.connect(lambda: self.overplot())
        self.pushButtonAddToPlot.setText('Add curves to plot...')
        
        self.QPushButton_clearIcPlot = QPushButton(self)
        self.QPushButton_clearIcPlot.setText('Clear plot')
        self.QPushButton_clearIcPlot.clicked.connect(lambda: self.clearPlot())
        
        verticalLayout = QVBoxLayout()
        verticalLayout.addStretch()
        verticalLayout.addWidget(self.pushButtonAddToPlot)
        verticalLayout.addWidget(self.QPushButton_clearIcPlot)

        gridLayout.addLayout(verticalLayout, 5, 0)
        gridLayout.addWidget(self.plottingArea, 0, 1, 9, 9)

    def overplot(self):
        '''
        
        '''
        filepaths = QFileDialog.getOpenFileNames(self, 'Select IV curves to process', self.parent.dm.save_directory+'/Ic')[0]
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
        self.plottingArea.clear()