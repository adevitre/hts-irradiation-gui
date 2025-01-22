import os, sys, numpy, time, re, datetime, pyqtgraph
sys.path.append('../')
import hts_fitting as hts

from configure import load_json
from plottingArea import MeasurePlot


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
        data = getIcT(filepaths)[2]
        for index, row in data.iterrows():
            pen = pyqtgraph.mkPen(color=(int(numpy.random.rand()*255), int(numpy.random.rand()*255), int(numpy.random.rand()*255)), width=3, symbol='+', symbolSize=5)
            self.plottingArea.plotData(row.sampleT, row.ic, name='{}'.format(row.fname), pen=pen)

    def clearPlot(self):
        self.plottingArea.clear()