"""
gui/dialogs/class_dialog.py — PyQt5 Add/Edit class dialog.
"""
from __future__ import annotations
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QHBoxLayout,
    QLabel, QLineEdit, QDoubleSpinBox, QPushButton, QMessageBox,
)


class ClassDialog(QDialog):
    def __init__(self, parent=None, title="Class", name="", cooldowns=None):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.result_data = None

        if cooldowns is None:
            cooldowns = [0.0, 2.0, 5.0, 10.0, 10.0, 15.0]

        layout = QVBoxLayout(self)

        form = QFormLayout()
        self._name = QLineEdit(name)
        form.addRow("Class Name:", self._name)

        form.addRow(QLabel("<small>Skill Cooldowns (seconds)</small>"))
        self._spins: list[QDoubleSpinBox] = []
        for i, cd in enumerate(cooldowns):
            sp = QDoubleSpinBox()
            sp.setRange(0, 300)
            sp.setDecimals(1)
            sp.setSingleStep(0.5)
            sp.setValue(cd)
            self._spins.append(sp)
            form.addRow(f"Skill {i}:", sp)
        layout.addLayout(form)

        btn_row = QHBoxLayout()
        save   = QPushButton("Save")
        cancel = QPushButton("Cancel")
        save.clicked.connect(self._save)
        cancel.clicked.connect(self.reject)
        btn_row.addStretch()
        btn_row.addWidget(save)
        btn_row.addWidget(cancel)
        layout.addLayout(btn_row)

    def _save(self):
        name = self._name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Name cannot be empty."); return
        self.result_data = (name, [sp.value() for sp in self._spins])
        self.accept()
