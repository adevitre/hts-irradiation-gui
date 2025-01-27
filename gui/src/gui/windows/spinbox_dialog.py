from PyQt5.QtWidgets import QDialog, QHBoxLayout, QVBoxLayout, QSpinBox, QDoubleSpinBox, QPushButton, QLabel

class SpinboxDialog(QDialog):
    def __init__(self, parent=None, title="Enter Value", min_value=0, max_value=100, default_value=50):
        super().__init__(parent)
        self.setWindowTitle(title)

        self.setFixedWidth(400)
        self.setFixedHeight(100)
        hlayout_line1 = QHBoxLayout()
        hlayout_line2 = QHBoxLayout()
        vlayout = QVBoxLayout()

        hlayout_line1.addWidget(QLabel("Fluence: "))

        self.spinbox_magnitude = QDoubleSpinBox()
        self.spinbox_magnitude.setMinimumWidth(80)
        self.spinbox_magnitude.setMaximumWidth(160)
        self.spinbox_magnitude.setMinimum(0.0)
        self.spinbox_magnitude.setMaximum(9.99)
        self.spinbox_magnitude.setValue(0.0)
        hlayout_line1.addWidget(self.spinbox_magnitude)

        hlayout_line1.addWidget(QLabel("E"))
        
        self.spinbox_exponent = QSpinBox()
        self.spinbox_exponent.setMinimumWidth(80)
        self.spinbox_exponent.setMaximumWidth(160)
        self.spinbox_exponent.setMinimum(15)
        self.spinbox_exponent.setMaximum(22)
        self.spinbox_exponent.setValue(19)
        hlayout_line1.addWidget(self.spinbox_exponent)

        hlayout_line1.addWidget(QLabel("protons/m2"))
        hlayout_line1.addStretch()
        ok_button = QPushButton("OK")
        ok_button.clicked.connect(self.accept)
        hlayout_line2.addWidget(ok_button)

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(self.reject)
        hlayout_line2.addWidget(cancel_button)
        
        vlayout.addLayout(hlayout_line1)
        vlayout.addLayout(hlayout_line2)

        self.setLayout(vlayout)

    def get_value(self):
        if self.exec_() == QDialog.Accepted:
            return float('{:4.2f}E{:2.0f}'.format(self.spinbox_magnitude.value(), self.spinbox_exponent.value()))
        else:
            return -1