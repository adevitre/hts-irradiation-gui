import os, numpy
from configure import load_json
from progresslabel import ProgressLabel
from signalsplot import SignalsPlot

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtGui import QIcon

'''
    Tab_Signals is a submodule of the GUI containing GUI objects and functions
    needed to perform keep track of four temperature sensors, the heating power output,
    and the chamber pressure during experiments.

    @author Alexis Devitre (devitre@mit.edu)
    @last-modified July 2024
'''
class Tab_Signals(QWidget):
    
    def __init__(self, usr_preferences, parent=None):
        
        super(Tab_Signals, self).__init__(parent)
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')        # stylesheets for QtWidgets
        self.preferences = usr_preferences
        
        gridLayout = QGridLayout(self)
        
        self.plotref = None
        self.plottingArea = SignalsPlot(parent=None, xlabel='Time [s]', ylabels=['Temperature [K]', 'Heating power [W]', 'Pressure [torr]', 'Magnetic Field [T]'])
        
        # Temperature axis
        self.plottingArea.axes[0][0].set_yticks(numpy.arange(0, 400, 50))
        self.plottingArea.axes[0][0].set_ylim(0, 350)
        self.plottingArea.axes[0][0].set_xticks(numpy.arange(0, self.preferences['timeaxis_max']+self.preferences['timeaxis_step'], self.preferences['timeaxis_step']))
        self.plottingArea.axes[0][0].set_xlim(0, self.preferences['timeaxis_max'])
        
        # Heating power axis
        self.plottingArea.axes[0][1].set_yticks(numpy.arange(0, 600, 100))
        self.plottingArea.axes[0][1].set_ylim(0, 500)
        
        # Pressure axis
        self.plottingArea.axes[1][0].set_yscale('log')
        self.plottingArea.axes[1][0].set_yticks([1e-7, 1e-5, 1e-3, 1e-1, 1e1, 1e3, 1e5])
        self.plottingArea.axes[1][0].set_ylim(1e-7, 1e3)
        
        # Magnetic field axis
        self.plottingArea.axes[1][1].set_yticks(numpy.arange(0, 15, 3))
        self.plottingArea.axes[1][1].set_ylim(0, 16)
        
        plotWithToolbar = QWidget()
        plotLayout = QVBoxLayout()
        plotLayout.addWidget(NavigationToolbar(self.plottingArea, None))
        plotLayout.addWidget(self.plottingArea)
        plotWithToolbar.setLayout(plotLayout)
        
        gridLayout.addWidget(plotWithToolbar, 0, 0, 10, 10)
        
    def updatePlottingArea(self, time_tc, time_pm, time_mc, sampleT, targetT, holderT, spareT, pressure, power, field):
        
        if time_tc[-1] > self.preferences['timeaxis_max']:
            time_tc += self.preferences['timeaxis_max'] - time_tc[-1]
            
        if time_pm[-1] > self.preferences['timeaxis_max']:
            time_pm += self.preferences['timeaxis_max'] - time_pm[-1]
        
        if self.plotref is not None:
            self.plotref['Sample Temperature'].set_ydata(sampleT)
            self.plotref['Sample Temperature'].set_xdata(time_tc)
            self.plotref['Target Temperature'].set_ydata(targetT)
            self.plotref['Target Temperature'].set_xdata(time_tc)
            self.plotref['Holder Temperature'].set_ydata(holderT)
            self.plotref['Holder Temperature'].set_xdata(time_tc)
            self.plotref['Spare Temperature'].set_ydata(spareT)
            self.plotref['Spare Temperature'].set_xdata(time_tc)
            self.plotref['Power'].set_ydata(power)
            self.plotref['Power'].set_xdata(time_tc)
            self.plotref['Pressure'].set_ydata(pressure)
            self.plotref['Pressure'].set_xdata(time_pm)
            self.plotref['Magnetic Field'].set_ydata(field)
            self.plotref['Magnetic Field'].set_xdata(time_mc)
            
        else:
            self.plotref = {
                'Sample Temperature': self.plottingArea.axes[0][0].plot(time_tc, sampleT, color='b')[0],
                'Target Temperature': self.plottingArea.axes[0][0].plot(time_tc, targetT, color='r')[0],
                'Holder Temperature': self.plottingArea.axes[0][0].plot(time_tc, holderT, color='g')[0],
                'Spare Temperature': self.plottingArea.axes[0][0].plot(time_tc, spareT, color='purple')[0],
                'Power': self.plottingArea.axes[0][1].plot(time_tc, power, color='k')[0],
                'Pressure': self.plottingArea.axes[1][0].plot(time_pm, pressure, color='forestgreen')[0],
                'Magnetic Field': self.plottingArea.axes[1][1].plot(time_mc, field, color='magenta')[0]
            }
        #print(self.plotref, type(self.plotref), self.plotref['Sample Temperature'])
        try:
            self.plottingArea.draw()
        except Exception as e:
            print('Exception while plotting signals time traces: ', str(e))