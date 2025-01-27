import os, sys, numpy, time, re, datetime, pyqtgraph
sys.path.append('../')
import hts_fitting as hts

from configure import load_json
from plottingArea import MeasurePlot

from spinbox_dialog import SpinboxDialog
from PyQt5.QtWidgets import QWidget, QPushButton, QComboBox, QLabel, QGridLayout, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QMessageBox, QInputDialog
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

HARDWARE_PARAMETERS = load_json(fname='hwparams.json', location=os.getcwd()+'/config')

'''
    Tab_AnalysisFluence is a submodule of the GUI containing GUI objects and functions
    needed to visualize the critical current or critical temperature as a function 
    of fluence at a given temperature.

    @author Alexis Devitre (devitre@mit.edu)
    @last-modified January 2025
'''
class Tab_AnalysisFluence(QWidget):
    
    def __init__(self, parent=None):
        
        super(Tab_AnalysisFluence, self).__init__(parent)
        self.parent = parent
        
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        
        gridLayout = QGridLayout(self)
        
        self.plottingArea = MeasurePlot(xLabel='Fluence [protons/m2]', yLabel='Critical current or Critical Temperature [A | K]')
        
        # Past measurements
        self.pushButtonAddToPlot = QPushButton(self)
        self.pushButtonAddToPlot.clicked.connect(lambda: self.overplot())
        self.pushButtonAddToPlot.setText('Add curves to plot...')
        self.QPushButton_clearIcPlot = QPushButton(self)
        self.QPushButton_clearIcPlot.setText('Clear plot')
        self.QPushButton_clearIcPlot.clicked.connect(lambda: self.clearPlot())
        verticalLayout = QVBoxLayout()
        verticalLayout.addWidget(self.pushButtonAddToPlot)
        verticalLayout.addWidget(self.QPushButton_clearIcPlot)
        verticalLayout.addStretch()
        gridLayout.addLayout(verticalLayout, 5, 9)
        gridLayout.addWidget(self.plottingArea, 0, 0, 8, 9)

    def overplot(self):
        filepaths = QFileDialog.getOpenFileNames(self, 'Select curves to process', self.parent.dm.save_directory+'/Ic')[0]
        data = hts.getIcT(filepaths)[2]
        for index, row in data.iterrows():
            print(row.fpath)
            fluence = re.search('[-+]?\d+(\.\d+)?[eE][-+]?\d+pm2', row.fpath)
            if fluence is not None:
                fluence = float(fluence.group(0)[:-3]) # remove the suffix pm2 and typecast to float
            else:
                dialog = SpinboxDialog()
                fluence = dialog.get_value() # returns -1 if the user is fed up with inputting the fluences manually and hits CANCEL
                del dialog
            if fluence != -1:
                random_color = (int(numpy.random.rand()*255), int(numpy.random.rand()*255), int(numpy.random.rand()*255))
                pen = pyqtgraph.mkPen(color=random_color, width=3, symbol='o', symbolSize=5)
                self.plottingArea.plotData([fluence], [row.ic], name='{}'.format(row.fpath.split('/')[-1]), pen=pen)

    def clearPlot(self):
        self.plottingArea.clear()