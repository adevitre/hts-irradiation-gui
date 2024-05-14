from PyQt5.QtWidgets import QLabel
from PyQt5.QtCore import QTimer

COLORS = {
    'r': 'red',
    'g': 'green',
    'k': 'black',
    'b': 'blue'
}

'''
	Class QProgressLabel implements a dynamic label showing an ongoing process
	@author Alexis Devitre
	@lastModified 2023-06-21
'''
class ProgressLabel(QLabel):
    
    def __init__(self, text, progress_char='.', color='k'):
        super(QLabel, self).__init__()
        self.text = text
        self.counter = 0
        
        self.setText(text)
        self.setStyleSheet('color: {}'.format(COLORS[color]))
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.updateLabel)
        
    def start(self, rate=500):
        self.timer.start(rate)
    
    def stop(self):
        self.timer.stop()
        self.text = ''
        
    def updateLabel(self):
        self.counter += 1
        self.setText(self.text+'.'*(self.counter%5))
