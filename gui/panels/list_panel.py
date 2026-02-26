"""
gui/panels/list_panel.py — PyQt5 list panel with QListWidget + Add/Edit/Delete buttons.
"""
from __future__ import annotations
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QListWidget, QPushButton,
)
from PyQt5.QtCore import Qt


class ListPanel(QWidget):
    def __init__(self, title: str, on_add, on_edit, on_delete, parent=None):
        super().__init__(parent)
        self._on_add    = on_add
        self._on_edit   = on_edit
        self._on_delete = on_delete

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)

        lbl = QLabel(f"<b>{title}</b>")
        lbl.setAlignment(Qt.AlignLeft)
        layout.addWidget(lbl)

        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        layout.addWidget(self._list)

        # Buttons
        btn_row = QHBoxLayout()
        btn_row.setSpacing(4)
        for label, slot in [("Add", self._on_add),
                             ("Edit", self._edit),
                             ("Delete", self._delete)]:
            btn = QPushButton(label)
            btn.clicked.connect(slot)
            btn_row.addWidget(btn)
        layout.addLayout(btn_row)

    # ── Public ────────────────────────────────────────────────────────────────

    def set_items(self, items: list[str]):
        self._list.clear()
        for item in items:
            self._list.addItem(item)

    def get_selected(self) -> str | None:
        item = self._list.currentItem()
        return item.text() if item else None

    # ── Internal ──────────────────────────────────────────────────────────────

    def _edit(self):   self._on_edit(self.get_selected())
    def _delete(self): self._on_delete(self.get_selected())
