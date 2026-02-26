"""
gui/dialogs/combo_dialog.py — PyQt5 Add/Edit combo dialog.
"""
from __future__ import annotations
from PyQt5.QtWidgets import (
    QDialog, QFormLayout, QVBoxLayout, QHBoxLayout,
    QLineEdit, QSpinBox, QPushButton, QMessageBox,
)


class ComboDialog(QDialog):
    def __init__(self, parent=None, title="Combo", name="", skills=None, repeat=0):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.result_data = None

        if skills is None:
            skills = [1, 2, 3]

        layout = QVBoxLayout(self)
        form   = QFormLayout()

        self._name = QLineEdit(name)
        form.addRow("Combo Name:", self._name)

        self._skills = QLineEdit(",".join(str(s) for s in skills))
        self._skills.setPlaceholderText("e.g. 1,2,3,1,2")
        form.addRow("Skills (0–5, comma):", self._skills)

        self._repeat = QSpinBox()
        self._repeat.setRange(0, 9999)
        self._repeat.setValue(repeat)
        self._repeat.setSpecialValueText("∞ (infinite)")
        form.addRow("Repeat (0 = ∞):", self._repeat)

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
        try:
            skills = [int(x.strip()) for x in self._skills.text().split(",") if x.strip()]
            if not skills: raise ValueError("empty")
            bad = [s for s in skills if not (0 <= s <= 5)]
            if bad: raise ValueError(f"out of range: {bad}")
        except ValueError as e:
            QMessageBox.warning(self, "Error", f"Invalid skill list: {e}"); return
        self.result_data = (name, skills, self._repeat.value())
        self.accept()
