import re, os, sys, numpy, datetime
sys.path.append('/home/htsirradiation/Documents/hts-irradiation-gui/src/gui/pyqt_subclasses/')

from configure import load_json
from listwidget import ListWidget
from addIcStepWindow import AddIcStepWindow
from addTcStepWindow import AddTcStepWindow
from addTemperatureStepWindow import AddTemperatureStepWindow
from addWaitStepWindow import AddWaitStepWindow
from addRelayStepWindow import AddRelayStepWindow
from PyQt5.QtWidgets import QWidget, QLineEdit, QListWidgetItem, QProgressBar, QGridLayout, QHBoxLayout, QHeaderView, QAbstractItemView, QPushButton, QSpinBox, QDoubleSpinBox, QLabel, QInputDialog, QFileDialog, QMessageBox

from PyQt5.QtCore import Qt, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QIcon


class Tab_Sequences(QWidget):
    """
        Tab_Sequences is a submodule of the GUI containing GUI objects and functions
        needed to perform sequences of measurements and environmental condition control.

        @author Alexis Devitre (devitre@mit.edu)
        @last-modified July 2024
    """
    run_sequence_signal = pyqtSignal(list)
    log_signal = pyqtSignal(str, str)
    
    def __init__(self, parent=None):
        super(Tab_Sequences, self).__init__(parent)
        self.parent = parent
        
        self.styles = load_json(fname='styles.json', location=os.getcwd()+'/config')  # stylesheets for QtWidgets
        self.preferences = load_json(fname='preferences.json', location=os.getcwd()+'/config')

        gridLayout = QGridLayout(self)
        
        self.listWidget = ListWidget()
        self.listWidget.itemDoubleClicked.connect(self.editDoubleClickedItem)
        self.listWidget.setStyleSheet("background-color: #f0f0f0; border: 1px solid #f0f0f0;  outline: none;")

        self.pushButtonMoveUp = QPushButton()
        self.pushButtonMoveUp.clicked.connect(lambda: self.moveStep('up'))
        self.pushButtonMoveUp.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/up.png'))
        self.pushButtonMoveUp.setIconSize(QSize(100,100))

        self.pushButtonMoveDown = QPushButton()
        self.pushButtonMoveDown.clicked.connect(lambda: self.moveStep('down'))
        self.pushButtonMoveDown.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/down.png'))
        self.pushButtonMoveDown.setIconSize(QSize(100,100))

        self.pushButtonCopyStep = QPushButton()
        self.pushButtonCopyStep.clicked.connect(lambda: self.copyStep())
        self.pushButtonCopyStep.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/copy.png'))
        self.pushButtonCopyStep.setIconSize(QSize(100,100))

        self.pushButtonRemoveStep = QPushButton()
        self.pushButtonRemoveStep.clicked.connect(lambda: self.removeStep())
        self.pushButtonRemoveStep.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/delete.png'))
        self.pushButtonRemoveStep.setIconSize(QSize(100,100))
        
        self.labelStepStatus = QLabel('')
        self.progressStatus = QProgressBar()
        self.progressStatus.setMinimum(0)

        button_size = 120

        self.pushButtonIc = QPushButton()
        self.pushButtonIc.setFixedSize(button_size, button_size)
        self.pushButtonIc.clicked.connect(lambda: self.pushButtonIcPressed())
        self.pushButtonIc.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/ic.png'))
        self.pushButtonIc.setIconSize(QSize(100,100))

        self.pushButtonTc = QPushButton()
        self.pushButtonTc.setFixedSize(button_size, button_size)
        self.pushButtonTc.clicked.connect(lambda: self.pushButtonTcPressed())
        self.pushButtonTc.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/tc.png'))
        self.pushButtonTc.setIconSize(QSize(100,100))

        self.pushButtonWait = QPushButton()
        self.pushButtonWait.setFixedSize(button_size, button_size)
        self.pushButtonWait.clicked.connect(lambda: self.pushButtonWaitPressed())
        self.pushButtonWait.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/wait.png'))
        self.pushButtonWait.setIconSize(QSize(100,100))

        self.pushButtonSound = QPushButton()
        self.pushButtonSound.setFixedSize(button_size, button_size)
        self.pushButtonSound.clicked.connect(lambda: self.push_button_sound_pressed())
        self.pushButtonSound.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/sound.png'))
        self.pushButtonSound.setIconSize(QSize(100,100))

        self.pushButtonMagneticField = QPushButton()
        self.pushButtonMagneticField.setFixedSize(button_size, button_size)
        self.pushButtonMagneticField.clicked.connect(lambda: self.push_button_magnetic_field_pressed())
        self.pushButtonMagneticField.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/field.png'))
        self.pushButtonMagneticField.setIconSize(QSize(100,100))

        self.pushButtonLabel = QPushButton()
        self.pushButtonLabel.setFixedSize(button_size, button_size)
        self.pushButtonLabel.clicked.connect(lambda: self.pushButtonLabelPressed())
        self.pushButtonLabel.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/label.png'))
        self.pushButtonLabel.setIconSize(QSize(100,100))
        
        self.pushButtonRelays = QPushButton()
        self.pushButtonRelays.setFixedSize(button_size, button_size)
        self.pushButtonRelays.clicked.connect(lambda: self.pushButtonRelaysPressed())
        self.pushButtonRelays.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/relay.png'))
        self.pushButtonRelays.setIconSize(QSize(100, 100))

        self.pushButtonTemperature = QPushButton()
        self.pushButtonTemperature.setFixedSize(button_size, button_size)
        self.pushButtonTemperature.clicked.connect(lambda: self.pushButtonTemperaturePressed())
        self.pushButtonTemperature.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/temperature.png'))
        self.pushButtonTemperature.setIconSize(QSize(100, 100))

        self.pushButtonSave = QPushButton('Save Sequence...')
        self.pushButtonSave.clicked.connect(lambda: self.saveSequence())
        self.pushButtonSave.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/save.png'))
        self.pushButtonSave.setIconSize(QSize(100, 100))

        self.pushButtonLoad = QPushButton('Load sequence...')
        self.pushButtonLoad.clicked.connect(lambda: self.loadSequence())
        self.pushButtonLoad.setIcon(QIcon(os.getcwd()+'/images/sequence-icons/load.png'))
        self.pushButtonLoad.setIconSize(QSize(100, 100))

        self.pushButtonExecute = QPushButton("Run Sequence")
        self.pushButtonExecute.setStyleSheet(self.styles['QPushButton_disable'])
        self.pushButtonExecute.clicked.connect(lambda: self.runSequence())
        self.pushButtonExecute.setEnabled(False)
        
        gridLayout.addWidget(self.listWidget, 0, 2, 9, 9)
        gridLayout.addWidget(self.pushButtonLoad, 0, 0, 1, 2)
        gridLayout.setAlignment(self.pushButtonLoad, Qt.AlignCenter)
        gridLayout.addWidget(self.pushButtonSave, 1, 0, 1, 2)
        gridLayout.setAlignment(self.pushButtonSave, Qt.AlignCenter)

        gridLayout.addWidget(self.pushButtonTemperature, 2, 0, 1, 1)
        gridLayout.setAlignment(self.pushButtonTemperature, Qt.AlignCenter)
        gridLayout.addWidget(self.pushButtonMagneticField, 2, 1, 1, 1)
        gridLayout.setAlignment(self.pushButtonMagneticField, Qt.AlignCenter)

        gridLayout.addWidget(self.pushButtonRelays, 3, 0, 1, 1)
        gridLayout.setAlignment(self.pushButtonRelays, Qt.AlignCenter)
        gridLayout.addWidget(self.pushButtonWait, 3, 1, 1, 1)
        gridLayout.setAlignment(self.pushButtonWait, Qt.AlignCenter)

        gridLayout.addWidget(self.pushButtonIc, 4, 0, 1, 1)
        gridLayout.setAlignment(self.pushButtonIc, Qt.AlignCenter)
        gridLayout.addWidget(self.pushButtonTc, 4, 1, 1, 1)
        gridLayout.setAlignment(self.pushButtonTc, Qt.AlignCenter)

        gridLayout.addWidget(self.pushButtonLabel, 5, 0, 1, 1)
        gridLayout.setAlignment(self.pushButtonLabel, Qt.AlignCenter)
        gridLayout.addWidget(self.pushButtonSound, 5, 1, 1, 1)
        gridLayout.setAlignment(self.pushButtonSound, Qt.AlignCenter)

        gridLayout.addWidget(self.pushButtonMoveUp, 6, 0, 1, 1)
        gridLayout.setAlignment(self.pushButtonMoveUp, Qt.AlignCenter)
        gridLayout.addWidget(self.pushButtonCopyStep, 6, 1, 1, 1)
        gridLayout.setAlignment(self.pushButtonCopyStep, Qt.AlignCenter)

        gridLayout.addWidget(self.pushButtonMoveDown, 7, 0, 1, 1)
        gridLayout.setAlignment(self.pushButtonMoveDown, Qt.AlignCenter)
        gridLayout.addWidget(self.pushButtonRemoveStep, 7, 1, 1, 1)
        gridLayout.setAlignment(self.pushButtonRemoveStep, Qt.AlignCenter)

        gridLayout.addWidget(self.pushButtonExecute, 9, 0, 1, 2)
        gridLayout.setAlignment(self.pushButtonExecute, Qt.AlignCenter)
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
        self.prompt = AddWaitStepWindow()
        self.prompt.ok_signal.connect(self.addStep)
        self.prompt.show()

    def pushButtonRelaysPressed(self):
        self.prompt = AddRelayStepWindow()
        self.prompt.ok_signal.connect(self.addStep)
        self.prompt.show()
        
    def pushButtonTemperaturePressed(self):
        self.prompt = AddTemperatureStepWindow()
        self.prompt.ok_signal.connect(self.addStep)
        self.prompt.show()
    
    def push_button_magnetic_field_pressed(self):
        print('pressed field button')
        
    def push_button_sound_pressed(self):
        print('pressed sound button')
        
    def pushButtonLabelPressed(self):
        value, ok = QInputDialog.getText(self, 'Label', 'Specify common label to all subsequent measurements:')
        if ok: self.addStep('Label {}'.format(value))

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
        if filepath != '':
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
            self.run_sequence_signal.emit([])

    def stopSequence(self):
        self.enableSequenceEdits(enabled=True)
        self.labelStepStatus.setText('Status: Idle')
        self.pushButtonExecute.setStyleSheet(self.styles['QPushButton_idle'])
        self.pushButtonExecute.setText('Run Sequence')
        QMessageBox.information(self, 'Sequence Complete', 'Sequence completed!')

    def parseSequenceItems(self, items):
        sequence = []
        for item in items:
            if item[0] == '/':
                sequence.append('Subsequence : start')
                with open(item, 'r') as f:
                    steps = [l.strip() for l in f.readlines() if not l.isspace()]
                    for step in steps:
                        sequence.append(step)
                    f.close()
                sequence.append('Subsequence : stop')
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

    def updateStepStatus(self, status_text):
        self.labelStepStatus.setText(status_text.split('/')[0])

        if status_text.split()[0] == 'SequenceStarted':
            self.listWidget.setCurrentRow(0)
            
        elif status_text.split()[0] != 'SequenceComplete':
            try:
                progress = int(float(status_text.split('/')[1]))
                maximum = int(float(status_text.split('/')[2]))
                self.progressStatus.setValue(progress)
                self.progressStatus.setMaximum(maximum) # integers = re.findall(r'\d+', statusText)
            except Exception as e:
                print('Tab_Sequence::updateStepStatus raised ', type(e), e)

        if status_text[0] == '*':
            self.listWidget.setCurrentRow(self.listWidget.currentRow()+1)

    def enable(self, enabled=True):
        """
            enable is used to disable the gui elements while the sequence is running.

            @params
                enabled (bool): enable or disable the gui elements
        """
        self.enableSequenceEdits(enabled=True)
        self.pushButtonExecute.setEnabled(enabled)
        self.pushButtonExecute.setStyleSheet(self.styles['QPushButton_idle'])
    
    def showMessage(self, message):
        msgBox = QMessageBox()
        msgBox.setWindowTitle('Sequence in Progress')
        msgBox.setText('Ongoing sequence launched by: ' + message + '\nSequence started ' + str(datetime.datetime.now()))
        msgBox.setIcon(QMessageBox.Warning)
        msgBox.setWindowFlags(msgBox.windowFlags() | Qt.WindowStaysOnTopHint)
        msgBox.setStyleSheet("""QMessageBox {background-color: lightred; border: 2px solid darkred;}""")
        msgBox.exec()