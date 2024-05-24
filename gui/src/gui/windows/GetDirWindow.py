import sys
from PyQt5.QtWidgets import QApplication, QWidget, QInputDialog, QLineEdit, QFileDialog
from PyQt5.QtGui import QIcon
#from ImageMagick import morgify

class launchWindow(QWidget):
    
    def __init__(self):
        super().__init__()
        self.title = 'PyQt5 file dialogs - pythonspot.com'
        self.left = 10
        self.top = 10
        self.width = 640
        self.height = 480
        self.path = ""
        self.initUI()
        
    def GetDir(self):
        options = QFileDialog.Options()
        # options |= QFileDialog.DontUseNativeDialog
        self.path = str(QFileDialog.getExistingDirectory(self,"/home/pi/Desktop"))
        
        
    
    def initUI(self):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        #mogrify *.png
        
        #self.GetDir()
        
        #self.show()
        

    
    

#if __name__ == '__main__':
#   app = QApplication(sys.argv)
#    ex = launchWindow()
#    sys.exit(app.exec_())

