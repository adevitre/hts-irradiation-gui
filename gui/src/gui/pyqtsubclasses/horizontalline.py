from PyQt5.QtWidgets import QFrame

'''
	HorizontalLine implements a line used to separate contexts within a vertical layout
	@author Alexis Devitre
	@lastModified 2023-06-21
'''
class HorizontalLine(QFrame):
    def __init__(self, parent=None):
        super(HorizontalLine, self).__init__()
        self.setFrameShape(QFrame.HLine)
        self.setFrameShadow(QFrame.Sunken)
