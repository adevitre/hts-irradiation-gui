import numpy, matplotlib
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
matplotlib.use('Qt5Agg')

from PyQt5 import QtCore, QtGui
from PyQt5.QtWidgets import QWidget, QVBoxLayout

'''
    MeasurePlot implements a plotting area for real time data display including navigation tools
'''
class MeasurePlot(QWidget):
    
    def __init__(self, xLabel, yLabel, parent=None):
        self.canvas = MplCanvas(nPlots=1, parent=self)
        self.plotref = None
        self.xLabel = xLabel
        self.yLabel = yLabel
        self.activeLine = None

        layout = QVBoxLayout()
        layout.addWidget(NavigationToolbar(self.canvas, None))
        layout.addWidget(self.canvas)
        
        super(MeasurePlot, self).__init__()
        self.setLayout(layout)
        
        self.canvas.axes.set_ylabel(self.yLabel)
        self.canvas.axes.set_xlabel(self.xLabel)
        #self.canvas.axes.autoscale(enable=True, axis='both', tight=True)
        self.canvas.fig.tight_layout()
    
    def updateActiveLine(self, x, y):
        #newx, newy = numpy.append(self.activeLine.get_xdata(), x), numpy.append(self.activeLine.get_ydata(), y)
        self.activeLine.set_data(x, y)
        self.canvas.draw()
        #self.canvas.fig.canvas.draw_idle()
        self.canvas.fig.canvas.flush_events()
        #matplotlib.pyplot.pause(0.001)

    def newLine(self):
        self.activeLine = self.canvas.axes.plot([], [])[-1]

    def display(self, x, y, **kwargs):
        self.canvas.axes.plot(x, y, **kwargs)[0]
        self.canvas.axes.legend(fancybox=True, loc='upper left', fontsize=10)
        self.canvas.draw()
        
    def clear(self):
        '''
            Clears the plots
        '''
        self.canvas.axes.cla()
        self.canvas.axes.set_xlabel(self.xLabel)
        self.canvas.axes.set_ylabel(self.yLabel)
        self.canvas.draw()

'''
    Defines a class that holds the figure and axes of an MplWidget
'''
class MplCanvas(FigureCanvasQTAgg):
    
    def __init__(self, nPlots=1, parent=None, xlabel='', ylabels=['']):
        self.fig, self.axes = matplotlib.pyplot.subplots(nPlots, 1, sharex=True, tight_layout=True)
        super(MplCanvas, self).__init__(self.fig)
        self.xlabel, self.ylabels = xlabel, ylabels
        
        self.axes.autoscale()
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