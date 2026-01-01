import numpy, matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout


class SignalsPlot(FigureCanvasQTAgg):
    '''
    
    MplWidget with multiple figures and axes in a column. This is used for the self updating plots of the "Signals" tab,
    which displays the temperatures, chamber pressure and heater power.
    @last-update November 2025
    @author Alexis Devitre (devitre@mit.edu)
    
    '''
    def __init__(self, parent=None, xlabel='', ylabels=['']):
        self.fig, self.axes = matplotlib.pyplot.subplots(2, 2, sharex=True, tight_layout=True)
        super(SignalsPlot, self).__init__(self.fig)
        self.xlabel, self.ylabels = xlabel, ylabels
        
        self.reset_axes_labels()

    def reset_axes_labels(self):
        '''
            When clearing the plot this function resets axes titles
        '''
        self.axes[0][0].set_ylabel(self.ylabels[0])
        self.axes[0][1].set_ylabel(self.ylabels[1])
        self.axes[1][0].set_ylabel(self.ylabels[2])
        self.axes[1][1].set_ylabel(self.ylabels[3])
        self.axes[1][0].set_xlabel(self.xlabel)
        self.axes[1][1].set_xlabel(self.xlabel)

    def clear(self):
        '''
            Clears the plots
        '''
        self.axes.cla()
        self.reset_axes_labels()
        self.canvas.draw()