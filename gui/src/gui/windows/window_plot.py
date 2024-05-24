from PyQt5.QtWidgets import QVBoxLayout, QDesktopWidget, QMainWindow, QApplication, QPlainTextEdit, QPushButton, QWidget, QLabel, QMessageBox
from configure import load_json
from module_customWidgets import MplCanvas
import numpy as np

class PlotWindow(QWidget):
    
    def __init__(self, xlabel, ylabel, parent=None):
        super(PlotWindow, self).__init__(parent)
        
        self.setGeometry(100, 100, 500, 325)               # x, y, width, height
        verticalLayout = QVBoxLayout(self)
        
        self.plottingArea = MplCanvas()
        self.plottingArea = MplCanvas(nPlots=1, xlabel=xlabel, ylabels=[ylabel])
        verticalLayout.addWidget(self.plottingArea)
        
        #window setup
        self.setWindowTitle("100 A Current Source Calibration Complete!")
        resolution = QDesktopWidget().screenGeometry()
        self.move((resolution.width()-self.frameSize().width())/2, (resolution.height()-self.frameSize().height())/2)
    
    def plot(self, x, y, label):
        self.plottingArea.axes.plot(x, y, label)
        self.plottingArea.axes.set_xlim(0, np.max(x))
        self.plottingArea.axes.set_ylim(0, np.max(y))