import os, numpy
from configure import load_json
from progresslabel import ProgressLabel
from signalsplot import SignalsPlot

from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PyQt5.QtWidgets import QGridLayout, QVBoxLayout, QWidget
from PyQt5.QtCore import pyqtSignal, QSize
from PyQt5.QtGui import QIcon

class LIFT1_tab_Environment(QWidget):
    
    def __init__(self, usr_preferences, parent=None):
        
        super(LIFT1_tab_Environment, self).__init__(parent)
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')        # stylesheets for QtWidgets
        self.preferences = usr_preferences
        
        gridLayout = QGridLayout(self)
        
        self.plotref = None
        self.plottingArea = SignalsPlot(nPlots=3, xlabel='Time [s]', ylabels=['Temperature [K]', 'Heating power [W]', 'Pressure [torr]'])
        self.plottingArea.axes[2].set_yscale('log')
        self.plottingArea.axes[2].set_yticks([1e-7, 1e-5, 1e-3, 1e-1, 1e1, 1e3, 1e5])
        self.plottingArea.axes[2].set_ylim(1e-7, 1e3)
        self.plottingArea.axes[1].set_yticks(numpy.arange(0, 600, 100))
        self.plottingArea.axes[1].set_ylim(0, 500)
        self.plottingArea.axes[0].set_yticks(numpy.arange(0, 400, 50))
        self.plottingArea.axes[0].set_ylim(0, 350)
        self.plottingArea.axes[0].set_xticks(numpy.arange(0, self.preferences['timeaxis_max']+self.preferences['timeaxis_step'], self.preferences['timeaxis_step']))
        self.plottingArea.axes[0].set_xlim(0, self.preferences['timeaxis_max'])
        
        plotWithToolbar = QWidget()
        plotLayout = QVBoxLayout()
        plotLayout.addWidget(NavigationToolbar(self.plottingArea, None))
        plotLayout.addWidget(self.plottingArea)
        plotWithToolbar.setLayout(plotLayout)
        
        gridLayout.addWidget(plotWithToolbar, 0, 0, 10, 10)
        
    def updatePlottingArea(self, time_tc, time_pm, sampleT, targetT, holderT, spareT, pressure, power):
        
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
            
        else:
            self.plotref = {
                'Sample Temperature': self.plottingArea.axes[0].plot(time_tc, sampleT, color='b')[0],
                'Target Temperature': self.plottingArea.axes[0].plot(time_tc, targetT, color='r')[0],
                'Holder Temperature': self.plottingArea.axes[0].plot(time_tc, holderT, color='g')[0],
                'Spare Temperature': self.plottingArea.axes[0].plot(time_tc, spareT, color='purple')[0],
                'Power': self.plottingArea.axes[1].plot(time_tc, power, color='k')[0],
                'Pressure': self.plottingArea.axes[2].plot(time_pm, pressure, color='forestgreen')[0]
            }
            
        try:
            self.plottingArea.draw()
        except Exception as e:
            print('Exception while plotting signals time traces: ', str(e))