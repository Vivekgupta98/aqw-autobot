"""
gui/app.py — PyQt5 main window. Two-tab layout:
  Tab 1: Keyboard Automation (skill-bot RunPanel)
  Tab 2: Mouse Click Automation (AutomationPanel)
"""
from __future__ import annotations
import os

from PyQt5.QtWidgets import QMainWindow, QMessageBox, QTabWidget

import backend.storage as storage
from backend.engine import AutomationRunner
from gui.panels.run_panel import RunPanel
from gui.panels.automation_panel import AutomationPanel
from gui.dialogs.class_dialog import ClassDialog
from gui.dialogs.combo_dialog import ComboDialog


class App(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AQW Bot")
        self.setMinimumSize(540, 520)
        self.resize(600, 640)

        self._classes = storage.load_classes()
        self._runner  = AutomationRunner()

        # ── Tab widget ────────────────────────────────────────────────────────
        self._tabs = QTabWidget()
        self._tabs.setDocumentMode(True)

        # Tab 1 — Keyboard Automation
        self._panel = RunPanel(
            get_classes     = lambda: self._classes,
            runner          = self._runner,
            on_add_class    = self._add_class,
            on_edit_class   = self._edit_class,
            on_delete_class = self._del_class,
            on_add_combo    = self._add_combo,
            on_edit_combo   = self._edit_combo,
            on_delete_combo = self._del_combo,
        )
        self._tabs.addTab(self._panel, "⌨️  Move Combos")

        # Tab 2 — Mouse Click Automation
        self._auto_panel = AutomationPanel()
        self._tabs.addTab(self._auto_panel, "🖱  Mouse Click Automation")

        self.setCentralWidget(self._tabs)
        self._panel.refresh()

    def closeEvent(self, event):
        self._runner.stop()
        event.accept()
        os._exit(0)

    # ── Class CRUD ────────────────────────────────────────────────────────────

    def _add_class(self):
        dlg = ClassDialog(self, title="Add Class")
        if dlg.exec_() and dlg.result_data:
            name, cds = dlg.result_data
            if name in self._classes:
                QMessageBox.warning(self, "Error", f"'{name}' already exists."); return
            self._classes[name] = {"cooldowns": cds, "combos": {}}
            storage.save_classes(self._classes)
            self._panel.refresh()

    def _edit_class(self, name: str):
        dlg = ClassDialog(self, title="Edit Class", name=name,
                          cooldowns=self._classes[name]["cooldowns"])
        if dlg.exec_() and dlg.result_data:
            new_name, cds = dlg.result_data
            if new_name != name:
                self._classes[new_name] = self._classes.pop(name)
            self._classes[new_name]["cooldowns"] = cds
            storage.save_classes(self._classes)
            self._panel.refresh()

    def _del_class(self, name: str):
        r = QMessageBox.question(self, "Delete", f"Delete '{name}' and all its combos?")
        if r == QMessageBox.Yes:
            del self._classes[name]
            storage.save_classes(self._classes)
            self._panel.refresh()

    # ── Combo CRUD ────────────────────────────────────────────────────────────

    def _add_combo(self, cls_name: str):
        dlg = ComboDialog(self, title=f"Add Combo — {cls_name}")
        if dlg.exec_() and dlg.result_data:
            name, skills, repeat = dlg.result_data
            combos = self._classes[cls_name].setdefault("combos", {})
            if name in combos:
                QMessageBox.warning(self, "Error", f"'{name}' already exists."); return
            combos[name] = {"skills": skills, "repeat": repeat}
            storage.save_classes(self._classes)
            self._panel.refresh()

    def _edit_combo(self, cls_name: str, combo_name: str):
        data = self._classes[cls_name]["combos"][combo_name]
        dlg  = ComboDialog(self, title=f"Edit Combo — {cls_name}",
                           name=combo_name, skills=data["skills"], repeat=data["repeat"])
        if dlg.exec_() and dlg.result_data:
            new_name, skills, repeat = dlg.result_data
            combos = self._classes[cls_name]["combos"]
            if new_name != combo_name:
                del combos[combo_name]
            combos[new_name] = {"skills": skills, "repeat": repeat}
            storage.save_classes(self._classes)
            self._panel.refresh()

    def _del_combo(self, cls_name: str, combo_name: str):
        r = QMessageBox.question(self, "Delete", f"Delete combo '{combo_name}'?")
        if r == QMessageBox.Yes:
            del self._classes[cls_name]["combos"][combo_name]
            storage.save_classes(self._classes)
            self._panel.refresh()
