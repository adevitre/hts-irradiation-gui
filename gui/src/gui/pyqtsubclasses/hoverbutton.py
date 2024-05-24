from PyQt5.QtWidgets import QPushButton
from PyQt5.QtGui import QIcon, QCursor
from PyQt5.QtCore import Qt, QSize, QEvent

'''
	Class QProgressLabel implements a dynamic label showing an ongoing process
	@author Alexis Devitre
	@lastModified 2023-08-12
'''

class HoverButton(QPushButton):
    def __init__(self, title, icon_path, icon_path_hover, parent=None):
        super(QPushButton, self).__init__()
        self.setText(title)
        self.defaultIcon = QIcon(icon_path)
        self.hoverIcon = QIcon(icon_path_hover)

        self.setIcon(self.defaultIcon)
        self.setIconSize(QSize(120, 120))
        self.setCursor(QCursor(Qt.PointingHandCursor))
        self.installEventFilter(self)

    def eventFilter(self, source, event):

        if event.type() == QEvent.HoverEnter:
            self.setIcon(self.hoverIcon)

        elif event.type() == QEvent.HoverLeave:
            self.setIcon(self.defaultIcon)

        return super().eventFilter(source, event)