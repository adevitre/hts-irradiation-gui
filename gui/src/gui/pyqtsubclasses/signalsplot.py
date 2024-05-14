import numpy, matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout

'''
    Defines a class that holds the figure and axes of an MplWidget
'''
class SignalsPlot(FigureCanvasQTAgg):
    
    def __init__(self, nPlots=1, parent=None, xlabel='', ylabels=['']):
        self.fig, self.axes = matplotlib.pyplot.subplots(nPlots, 1, sharex=True, tight_layout=True)
        super(SignalsPlot, self).__init__(self.fig)
        self.xlabel, self.ylabels = xlabel, ylabels
        
        if nPlots > 1:
            for i, l in enumerate(self.ylabels):
                self.axes[i].set_xlabel(self.xlabel)
                self.axes[i].set_ylabel(l)
        else:
            self.axes.set_xlabel(self.xlabel)
            self.axes.set_ylabel(self.ylabels[0])
            
    def clear(self):
        '''
            Clears the plots
        '''
        self.axes.cla()
        if len(self.ylabels) > 1:
            for i, l in enumerate(self.ylabels):
                self.axes[i].set_xlabel(self.xlabel)
                self.axes[i].set_ylabel(l)
        else:
            self.axes.set_xlabel(self.xlabel)
            self.axes.set_ylabel(self.ylabels[0])
        self.canvas.draw()