import os, sys, numpy, time, re, datetime, pyqtgraph
sys.path.append('../')
import hts_fitting as hts

from configure import load_json
from plottingArea import MeasurePlot
from horizontalline import HorizontalLine
from hts_misc import fname_to_timestamp

from spinbox_dialog import SpinboxDialog
from PyQt5.QtWidgets import QWidget, QPushButton, QComboBox, QLabel, QSpacerItem, QGridLayout, QVBoxLayout, QDoubleSpinBox, QSpinBox, QFileDialog, QMessageBox, QInputDialog, QRadioButton, QButtonGroup
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt, pyqtSignal, QTimer

HARDWARE_PARAMETERS = load_json(fname='hwparams.json', location=os.getcwd()+'/config')

'''
    Tab_Analysis is a submodule of the GUI containing GUI objects and functions needed to visualize the critical current 
    or critical temperature as a function of several parameters such as time, flux, fluence, or temperature.

    @author Alexis Devitre (devitre@mit.edu)
    @last-modified January 2025
'''
class Tab_Analysis(QWidget):
    
    def __init__(self, parent=None):
        
        super(Tab_Analysis, self).__init__(parent)
        self.parent = parent
        
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')
        
        gridLayout = QGridLayout(self)
        
        self.plottingArea = MeasurePlot(xLabel='Fluence [protons/m2]', yLabel='Critical Current [A]')
        
        # Past measurements
        self.pushButtonAddToPlot = QPushButton(self)
        self.pushButtonAddToPlot.clicked.connect(lambda: self.overplot())
        self.pushButtonAddToPlot.setText('Add curves to plot...')
        self.QPushButton_clearIcPlot = QPushButton(self)
        self.QPushButton_clearIcPlot.setText('Clear plot')
        self.QPushButton_clearIcPlot.clicked.connect(lambda: self.clearPlot())

        self.qradiobutton_flux = QRadioButton('Beam current [nA]')
        self.qradiobutton_fluence = QRadioButton('Fluence [ion/m2]')
        self.qradiobutton_time = QRadioButton('Time [s]')
        self.qradiobutton_temperature = QRadioButton('Temperature [K]')

        self.qradiobutton_ic = QRadioButton('Critical Current [A]')
        self.qradiobutton_tc = QRadioButton('Critical Temperature [K]')
        
        self.qradiobutton_ic.clicked.connect(self.switchy)
        self.qradiobutton_tc.clicked.connect(self.switchy)

        self.qradiobutton_temperature.setChecked(True) # default selection is temperature
        self.qradiobutton_ic.setChecked(True) # default selection is Ic

        vertical_layout = QVBoxLayout()
        vertical_layout.addWidget(self.pushButtonAddToPlot)
        vertical_layout.addWidget(self.QPushButton_clearIcPlot)
        
        spacer = QSpacerItem(20, 40)#, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vertical_layout.addItem(spacer)

        vertical_layout.addWidget(HorizontalLine())
        self.button_group = QButtonGroup()
        for button in [self.qradiobutton_temperature, self.qradiobutton_time, self.qradiobutton_flux, self.qradiobutton_fluence]:
            button.clicked.connect(self.switchx)
            self.button_group.addButton(button)
            vertical_layout.addWidget(button)

        spacer = QSpacerItem(20, 40)#, QSizePolicy.Minimum, QSizePolicy.Expanding)
        vertical_layout.addItem(spacer)

        vertical_layout.addWidget(HorizontalLine())
        self.button_group = QButtonGroup()
        for button in [self.qradiobutton_ic, self.qradiobutton_tc]:
            self.button_group.addButton(button)
            vertical_layout.addWidget(button)
        vertical_layout.addStretch()

        gridLayout.addLayout(vertical_layout, 5, 9)
        gridLayout.addWidget(self.plottingArea, 0, 0, 8, 9)

    def overplot(self):
        if self.qradiobutton_ic.isChecked():
            filepaths = QFileDialog.getOpenFileNames(self, 'Select curves to process', self.parent.dm.save_directory+'/Ic')[0]
            data = hts.getIcT(filepaths)[2]
        else:
            filepaths = QFileDialog.getOpenFileNames(self, 'Select curves to process', self.parent.dm.save_directory+'/Tc')[0]
            #data = # FIT TC MEASUREMENTS hts.getIcT(filepaths)[2]
            
        for index, row in data.iterrows():
            if self.qradiobutton_ic.isChecked():
                y = row.ic
            else:
                y = row.tc

            x = 0
            if self.qradiobutton_fluence.isChecked():
                x = re.search('\d+(\.\d+)?[eE][-+]?\d+pm2', row.fpath)
                if x is not None:
                    x = float(x.group(0)[:-3])
                else:
                    dialog = SpinboxDialog()
                    x = dialog.get_value() # returns -1 if the user is fed up with inputting the fluences manually and hits CANCEL
                    del dialog
            elif self.qradiobutton_flux.isChecked():
                x = re.search('\d+nA', row.fpath)
                if x is not None:
                    x = float(x.group(0)[:-2])
                else:
                    dialog = SpinboxDialog()
                    x = dialog.get_value() # returns -1 if the user is fed up with inputting the fluences manually and hits CANCEL
                    del dialog
            elif self.qradiobutton_temperature.isChecked():
                x = row.temperature
            elif self.qradiobutton_time.isChecked():
                x = fname_to_timestamp(row.fpath)

            if x != -1:
                random_color = (int(numpy.random.rand()*255), int(numpy.random.rand()*255), int(numpy.random.rand()*255))
                pen = pyqtgraph.mkPen(color=random_color, width=3, symbol='o', symbolSize=5)
                self.plottingArea.plotData([x], [row.ic], name='{}'.format(row.fpath.split('/')[-1]), pen=pen)

    def clearPlot(self):
        self.plottingArea.clear()

    def switchy(self):
        self.clearPlot()
        if self.qradiobutton_ic.isChecked():
            self.qradiobutton_temperature.setEnabled(True)
            self.plottingArea.set_ylabel('Critical Current [A]')
        else:
            self.qradiobutton_temperature.setEnabled(False)
            self.plottingArea.set_ylabel('Critical Temperature [K]')

    def switchx(self):
        self.clearPlot()
        if self.qradiobutton_time.isChecked():
            self.plottingArea.set_xlabel('Time [s]')
        elif self.qradiobutton_fluence.isChecked():
            self.plottingArea.set_xlabel('Fluence [ions/m2]')
        elif self.qradiobutton_flux.isChecked():
            self.plottingArea.set_xlabel('Beam current [nA]')
        elif self.qradiobutton_temperature.isChecked():
            self.plottingArea.set_xlabel('Temperature [K]')
        