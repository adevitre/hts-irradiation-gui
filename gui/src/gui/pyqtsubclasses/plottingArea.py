import numpy as np

from pyqtgraph import PlotWidget, mkPen, InfiniteLine, TextItem
from PyQt5.QtWidgets import QWidget
from fittingFunctions import linear, powerLaw
'''
    MeasurePlot implements a plotting area for real time data display including navigation tools
'''
class MeasurePlot(PlotWidget):
    
    def __init__(self, xLabel='', yLabel='', title='', parent=None):
        super(MeasurePlot, self).__init__(parent)

        label_style = {"color": "#000000", "font-size": "14pt"}
        self.setLabel("bottom", xLabel, **label_style)
        self.setLabel("left", yLabel, **label_style)
        self.setTitle(title)
        self.setBackground('w')
        self.getAxis('left').setTextPen('k')
        self.getAxis('bottom').setTextPen('k')
        self.getAxis('left').setPen('k')
        self.getAxis('bottom').setPen('k')
        self.showGrid(x=True, y=True, alpha=0.1)
        
        # autoranging
        self.enableAutoRange(axis='y')
        self.enableAutoRange(axis='x')
        self.setAutoVisible(y=True)
        
        self.addLegend()

        self.lines = []
        self.activeLine = None
        
    def updateActiveLine(self, x, y):
        self.activeLine.setData(x, y)
        
    def addCurve(self, **kwargs):
        self.activeLine = self.plot([], [], **kwargs)
        self.lines = np.append(self.lines, self.activeLine)

    def plotData(self, x, y, **kwargs):
        newLine = self.scatterPlot(x, y, **kwargs)
        self.lines = np.append(self.lines, newLine)

    def plotFit(self, xvalues, fitParameters, pen):
        x = np.linspace(np.min(xvalues), np.max(xvalues), num=10000)
        y = powerLaw(x, fitParameters[0], fitParameters[1])*1e6
        self.plot(x, y, pen=pen)

    def plotInfiniteLine(self, pos, angle, label, **kwargs):
        newLine = InfiniteLine(pos=pos, angle=angle, movable=False, pen=mkPen('g', width=4))
        text = TextItem(label)#, anchor=(pos[0]+0.1, pos[1]+0.1))
        self.addItem(newLine, ignoreBounds=True)
        self.addItem(text)
        text.setPos(pos[0]+0.001, pos[1]+0.001)
        self.setXRange(0, 1)
        self.setYRange(-1, 1)


    def clear(self):
        '''
            Clears the plots
        '''
        self.clear()
        del self.lines
        self.lines = []

