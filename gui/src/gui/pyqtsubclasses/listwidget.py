
from PyQt5.QtWidgets import QListWidget


'''
	Class ListWidget implements functions that are not directly available from the PyQt5 version of QListWidget
	@author Alexis Devitre
	@lastModified 2023-06-21
'''
class ListWidget(QListWidget):
    
    def __init__(self, parent=None):
        super(QListWidget, self).__init__(parent)
        self.parent = parent

    '''
    	Returns a list of string items in order of appearance
    	
    	RETURNS
        ---------
    	items (list, str) - all items in ListWidget in order of appearance 
    '''
    def getItems(self):
    	items = []
    	for i in range(self.count()):
    		items.append(self.item(i).text())
    		print(self.item(i).text())
    	return items