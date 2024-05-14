import re, os, sys, numpy, datetime
sys.path.append('/home/htsirradiation/Documents/hts-irradiation-gui/src/gui/pyqt_subclasses/')

from configure import load_json
from listwidget import ListWidget
from addIcStepWindow import AddIcStepWindow
from addTcStepWindow import AddTcStepWindow
from addTemperatureStepWindow import AddTemperatureStepWindow
from PyQt5.QtWidgets import QWidget, QLineEdit, QListWidgetItem, QProgressBar, QGridLayout, QHBoxLayout, QHeaderView, QAbstractItemView, QPushButton, QSpinBox, QDoubleSpinBox, QLabel, QInputDialog, QFileDialog, QMessageBox

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QIcon


class LIFT1_tab_Sequences(QWidget):
    
    run_sequence_signal = pyqtSignal(list)
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super(LIFT1_tab_Sequences, self).__init__(parent)
        self.parent = parent
        
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')

        gridLayout = QGridLayout(self)
        
        self.listWidget = ListWidget()
        self.listWidget.itemDoubleClicked.connect(self.editDoubleClickedItem)
        self.listWidget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #f0f0f0;  outline: none;")
        self.pushButtonMoveUp = QPushButton("\u25B2")
        self.pushButtonMoveUp.clicked.connect(lambda: self.moveStep('up'))
        self.pushButtonMoveUp.setFixedSize(30, 30)
        self.pushButtonMoveDown = QPushButton("\u25BC")
        self.pushButtonMoveDown.clicked.connect(lambda: self.moveStep('down'))
        self.pushButtonMoveDown.setFixedSize(30, 30)
        self.pushButtonCopyStep = QPushButton("+")
        self.pushButtonCopyStep.clicked.connect(lambda: self.copyStep())
        self.pushButtonCopyStep.setFixedSize(30, 30)
        self.pushButtonRemoveStep = QPushButton("x")
        self.pushButtonRemoveStep.clicked.connect(lambda: self.removeStep())
        self.pushButtonRemoveStep.setFixedSize(30, 30)
        self.pushButtonRemoveStep.setIconSize(QSize(50, 50))
        
        horizontalLayout = QHBoxLayout()
        horizontalLayout.addWidget(self.pushButtonMoveUp)
        horizontalLayout.addWidget(self.pushButtonMoveDown)
        horizontalLayout.addWidget(self.pushButtonCopyStep)
        horizontalLayout.addWidget(self.pushButtonRemoveStep)

        self.labelStepStatus = QLabel('')
        self.progressStatus = QProgressBar()
        self.progressStatus.setMinimum(0)

        self.pushButtonIc = QPushButton()
        self.pushButtonIc.setFixedSize(150, 150)
        self.pushButtonIc.clicked.connect(lambda: self.pushButtonIcPressed())
        self.pushButtonIc.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/ic.png'))
        self.pushButtonIc.setIconSize(QSize(100,100))

        self.pushButtonTc = QPushButton()
        self.pushButtonTc.setFixedSize(150, 150)
        self.pushButtonTc.clicked.connect(lambda: self.pushButtonTcPressed())
        self.pushButtonTc.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/tc.png'))
        self.pushButtonTc.setIconSize(QSize(100,100))

        self.pushButtonWait = QPushButton()
        self.pushButtonWait.setFixedSize(150, 150)
        self.pushButtonWait.clicked.connect(lambda: self.pushButtonWaitPressed())
        self.pushButtonWait.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/wait.png'))
        self.pushButtonWait.setIconSize(QSize(150,150))

        self.pushButtonTemperature = QPushButton()
        self.pushButtonTemperature.setFixedSize(150, 150)
        self.pushButtonTemperature.clicked.connect(lambda: self.pushButtonTemperaturePressed())
        self.pushButtonTemperature.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/setTemp.png'))
        self.pushButtonTemperature.setIconSize(QSize(150, 150))

        self.pushButtonSave = QPushButton('Save Sequence...')
        self.pushButtonSave.clicked.connect(lambda: self.saveSequence())
        self.pushButtonSave.setFixedSize(150, 30)

        self.pushButtonLoad = QPushButton('Load sequence...')
        self.pushButtonLoad.clicked.connect(lambda: self.loadSequence())
        self.pushButtonLoad.setFixedSize(150, 30)

        self.pushButtonExecute = QPushButton("Run Sequence")
        self.pushButtonExecute.setStyleSheet(self.styles['QPushButton_disable'])
        self.pushButtonExecute.clicked.connect(lambda: self.runSequence())
        self.pushButtonExecute.setEnabled(False)
        
        gridLayout.addWidget(self.listWidget, 0, 1, 9, 10)
        gridLayout.addWidget(self.pushButtonLoad, 0, 0)
        gridLayout.addWidget(self.pushButtonSave, 1, 0)
        gridLayout.addWidget(self.pushButtonWait, 2, 0)
        gridLayout.addWidget(self.pushButtonTemperature, 3, 0)
        gridLayout.addWidget(self.pushButtonIc, 4, 0)
        gridLayout.addWidget(self.pushButtonTc, 5, 0)
        gridLayout.addLayout(horizontalLayout, 6, 0)
        gridLayout.addWidget(self.pushButtonExecute, 9, 0)
        gridLayout.addWidget(self.labelStepStatus, 9, 1, 1, 4)
        gridLayout.addWidget(self.progressStatus, 9, 5, 1, 6)

    def editDoubleClickedItem(self):
        item = self.listWidget.currentItem()
        row = self.listWidget.currentRow()
        line_edit = QLineEdit(item.text(), self.listWidget)
        line_edit.editingFinished.connect(lambda: self.finishEditing(line_edit, row))
        self.listWidget.setItemWidget(item, line_edit)
        line_edit.setFocus()

    def finishEditing(self, line_edit, row):
        self.listWidget.takeItem(row)
        self.listWidget.insertItem(row, QListWidgetItem(line_edit.text()))

    def addStep(self, step):
        if self.listWidget.count() > 0:
            self.listWidget.insertItem(self.listWidget.currentRow()+1, step)
        else:
            self.listWidget.addItem(step)
        self.listWidget.setCurrentRow(self.listWidget.currentRow()+1)

    def pushButtonIcPressed(self):
        self.prompt = AddIcStepWindow()
        self.prompt.ok_signal.connect(self.addStep)
        self.prompt.show()

    def pushButtonTcPressed(self):
        self.prompt = AddTcStepWindow()
        self.prompt.ok_signal.connect(self.addStep)
        self.prompt.show()

    def pushButtonWaitPressed(self):
        value, ok = QInputDialog.getInt(self, 'Wait', 'Specify wait time in seconds', value=600, min=1, max=436800, step=600)
        if ok:
            self.addStep('Wait {} seconds'.format(value))

    def pushButtonTemperaturePressed(self):
        self.prompt = AddTemperatureStepWindow()
        self.prompt.ok_signal.connect(self.addStep)
        self.prompt.show()
    
    def removeStep(self):
        self.listWidget.takeItem(self.listWidget.currentRow())
    
    def moveStep(self, move='up'):
        currentRow = self.listWidget.currentRow()
        currentItem = None
        
        if (move == 'up') and (currentRow != 0):
            currentItem = self.listWidget.takeItem(currentRow)
            currentRow -= 1
        elif (move == 'down') and (currentRow != self.listWidget.count()-1):
            currentItem = self.listWidget.takeItem(currentRow)
            currentRow += 1
        
        if currentItem is not None:
            self.listWidget.insertItem(currentRow, currentItem)
        self.listWidget.setCurrentRow(currentRow)

    def copyStep(self):
        currentRow = self.listWidget.currentRow()
        currentItem = self.listWidget.currentItem()
        print(currentItem)
        if currentItem is not None:
            itemCopy = currentItem.clone()
            if itemCopy is not None:
                self.listWidget.insertItem(currentRow+1, itemCopy)
            self.listWidget.setCurrentRow(currentRow+1)

    def saveSequence(self):
        filepath, _ = QFileDialog.getSaveFileName(self, 'Save Sequence', '', 'seq (*.seq)')
        if filepath != '':
            if filepath.find('.seq') == -1:
                filepath += '.seq'
            steps = self.listWidget.getItems()
            if len(steps) != 0:
                with open(filepath, 'w') as f:
                    for step in steps:
                        f.write(step+'\n')
                    f.close()
            else:
                QMessageBox.warning(self, 'Warning', 'Sequence is empty!')
                
    def loadSequence(self):
        filepath = QFileDialog.getOpenFileName(self, 'Load sequence', self.preferences['path_sequences'], 'seq(*.seq)')[0]
        self.listWidget.addItem(filepath)

    def runSequence(self):
        if self.pushButtonExecute.text() == 'Run Sequence':
            totalSteps = self.listWidget.count()
            if totalSteps > 0:
                self.pushButtonExecute.setStyleSheet(self.styles['QPushButton_acquiring'])
                self.pushButtonExecute.setText('Stop')
                self.run_sequence_signal.emit(self.parseSequenceItems(self.listWidget.getItems()))
                self.log_signal.emit('SequenceStart', 'Sequence {} started by user.'.format('SequenceName'))
                self.enableSequenceEdits(enabled=False)
            else:
                QMessageBox.warning(self, 'Warning', 'Sequence is empty!')
        else:
            self.stopSequence()
            self.log_signal.emit('SequenceStop', 'Sequence {} stopped by user.'.format('SequenceName'))
    
    def stopSequence(self):
        self.enableSequenceEdits(enabled=True)
        self.labelStepStatus.setText('Status: Idle')
        self.pushButtonExecute.setStyleSheet(self.styles['QPushButton_idle'])
        self.pushButtonExecute.setText('Run Sequence')
        self.run_sequence_signal.emit([])
        QMessageBox.information(self, 'Sequence Complete', 'Sequence completed!')

    def parseSequenceItems(self, items):
        sequence = []
        for item in items:
            if item[0] == '/':
                with open(item, 'r') as f:
                    steps = [l.strip() for l in f.readlines() if not l.isspace()]
                    for step in steps:
                        sequence.append(step)
                    f.close()
            else:
                sequence.append(item)
        return sequence

    def enableSequenceEdits(self, enabled=True):
        self.listWidget.setEnabled(enabled)
        self.pushButtonTemperature.setEnabled(enabled)
        self.pushButtonIc.setEnabled(enabled)
        self.pushButtonTc.setEnabled(enabled)
        self.pushButtonWait.setEnabled(enabled)
        self.pushButtonLoad.setEnabled(enabled)
        self.pushButtonSave.setEnabled(enabled)
        self.pushButtonMoveUp.setEnabled(enabled)
        self.pushButtonMoveDown.setEnabled(enabled)
        self.pushButtonRemoveStep.setEnabled(enabled)
        self.pushButtonCopyStep.setEnabled(enabled)

    def updateStepStatus(self, statusText):
        self.labelStepStatus.setText(statusText)

        if statusText.split()[0] == 'Started':
            self.listWidget.setCurrentRow(int(statusText.split()[2])-1)

        elif statusText.split()[0] != 'SequenceComplete':
            integers = re.findall(r'\d+', statusText)
            if len(integers) == 2:
                currentIndex, maxIndex = int(integers[0]), int(integers[1])
                self.progressStatus.setMaximum(maxIndex)
                self.progressStatus.setValue(currentIndex)

    def enable(self, enabled=True):
        self.enableSequenceEdits(enabled=True)
        self.pushButtonExecute.setEnabled(enabled)
        self.pushButtonExecute.setStyleSheet(self.styles['QPushButton_idle'])