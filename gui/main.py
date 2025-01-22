import sys, os, shutil

sys.path.append(os.getcwd())
sys.path.append(os.getcwd()+'/config')
sys.path.append(os.getcwd()+'/src')
sys.path.append(os.getcwd()+'/src/devices')
sys.path.append(os.getcwd()+'/src/gui')
sys.path.append(os.getcwd()+'/src/gui/windows')
sys.path.append(os.getcwd()+'/src/gui/pyqtsubclasses')

def eliminateTempFiles(directory):
	for d in [directory+'/'+d for d in os.listdir(directory) if (os.path.isdir(directory+'/'+d) and (d != '.git'))]:
		if d.find('__pycache__') >= 0:
			shutil.rmtree(d)
		else:
			eliminateTempFiles(d)

from configure import configure_ports
from guimanager import GUIManager
from PyQt5.QtWidgets import QApplication, QSplashScreen
from PyQt5 import QtGui, QtCore

#configure_ports()

ui = None
app = QApplication(sys.argv)    # create the app (event loop)
ui = GUIManager()                # create the GUI
ui.show()                       # show the GUI
app.exec_()			     		# start the event loop
eliminateTempFiles(os.getcwd()) # Remove python cache files
sys.exit()                      # End program