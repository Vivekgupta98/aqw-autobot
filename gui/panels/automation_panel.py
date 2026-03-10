"""
gui/panels/automation_panel.py — Full tab for recording & replaying click automations.
Shows each recorded step and allows per-step editing.
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout,
    QLabel, QListWidget, QListWidgetItem, QPushButton,
    QDoubleSpinBox, QSpinBox, QTextEdit, QInputDialog,
    QMessageBox, QGroupBox, QSplitter,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal

import backend.storage as storage
from backend.click_recorder import ClickRecorder
from backend.click_player import ClickPlayer
from gui.dialogs.record_bar import RecordBar


class AutomationPanel(QWidget):
    _log_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._automations: dict = storage.load_automations()
        self._recorder = ClickRecorder()
        self._player = ClickPlayer()
        self._log_signal.connect(self._append_log)

        root = QVBoxLayout(self)
        root.setContentsMargins(12, 12, 12, 12)
        root.setSpacing(8)

        # ── Top area: splitter (automation list | step editor) ────────────────
        splitter = QSplitter(Qt.Horizontal)

        # -- Left: saved automations list --
        left = QWidget()
        left_lay = QVBoxLayout(left)
        left_lay.setContentsMargins(0, 0, 0, 0)
        left_lay.setSpacing(6)

        left_lay.addWidget(QLabel("<b>Saved Automations</b>"))
        self._list = QListWidget()
        self._list.setAlternatingRowColors(True)
        self._list.currentTextChanged.connect(self._on_automation_changed)
        left_lay.addWidget(self._list)

        crud_row = QHBoxLayout()
        rec_btn = QPushButton("🔴 Record New")
        rec_btn.clicked.connect(self._record_new)
        crud_row.addWidget(rec_btn)
        ren_btn = QPushButton("✏️ Rename")
        ren_btn.clicked.connect(self._rename_automation)
        crud_row.addWidget(ren_btn)
        del_btn = QPushButton("🗑 Delete")
        del_btn.clicked.connect(self._delete_automation)
        crud_row.addWidget(del_btn)
        left_lay.addLayout(crud_row)

        splitter.addWidget(left)

        # -- Right: step list + step editor --
        right = QWidget()
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(0, 0, 0, 0)
        right_lay.setSpacing(6)

        right_lay.addWidget(QLabel("<b>Steps</b>"))
        self._step_list = QListWidget()
        self._step_list.setAlternatingRowColors(True)
        self._step_list.currentRowChanged.connect(self._on_step_selected)
        right_lay.addWidget(self._step_list)

        step_btn_row = QHBoxLayout()
        self._del_step_btn = QPushButton("🗑 Remove Step")
        self._del_step_btn.clicked.connect(self._delete_step)
        self._del_step_btn.setEnabled(False)
        step_btn_row.addWidget(self._del_step_btn)
        self._move_up_btn = QPushButton("▲ Up")
        self._move_up_btn.clicked.connect(self._move_step_up)
        self._move_up_btn.setEnabled(False)
        step_btn_row.addWidget(self._move_up_btn)
        self._move_down_btn = QPushButton("▼ Down")
        self._move_down_btn.clicked.connect(self._move_step_down)
        self._move_down_btn.setEnabled(False)
        step_btn_row.addWidget(self._move_down_btn)
        right_lay.addLayout(step_btn_row)

        # Step editor group
        editor_box = QGroupBox("Edit Selected Step")
        editor_form = QFormLayout(editor_box)

        self._edit_x = QSpinBox()
        self._edit_x.setRange(0, 99999)
        editor_form.addRow("X:", self._edit_x)

        self._edit_y = QSpinBox()
        self._edit_y.setRange(0, 99999)
        editor_form.addRow("Y:", self._edit_y)

        self._edit_delay = QDoubleSpinBox()
        self._edit_delay.setRange(0, 600)
        self._edit_delay.setDecimals(2)
        self._edit_delay.setSingleStep(0.1)
        self._edit_delay.setSuffix(" s")
        editor_form.addRow("Delay before:", self._edit_delay)

        self._apply_btn = QPushButton("✅ Apply Changes")
        self._apply_btn.clicked.connect(self._apply_step_edit)
        self._apply_btn.setEnabled(False)
        editor_form.addRow(self._apply_btn)

        right_lay.addWidget(editor_box)
        splitter.addWidget(right)

        splitter.setSizes([220, 340])
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        root.addWidget(splitter, stretch=1)

        # ── Run controls ──────────────────────────────────────────────────────
        run_box = QGroupBox("Run")
        run_lay = QVBoxLayout(run_box)

        gap_row = QHBoxLayout()
        gap_row.addWidget(QLabel("Run Gap:"))
        self._gap_spin = QDoubleSpinBox()
        self._gap_spin.setRange(0, 600)
        self._gap_spin.setValue(5.0)
        self._gap_spin.setSuffix(" s")
        self._gap_spin.setDecimals(1)
        self._gap_spin.setSingleStep(0.5)
        gap_row.addWidget(self._gap_spin)
        gap_row.addStretch()
        run_lay.addLayout(gap_row)

        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("▶  START")
        self._start_btn.clicked.connect(self._start)
        self._stop_btn = QPushButton("⏹  STOP")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop)
        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        run_lay.addLayout(btn_row)

        self._status = QLabel("Status: IDLE")
        self._status.setAlignment(Qt.AlignCenter)
        run_lay.addWidget(self._status)

        root.addWidget(run_box)

        # ── Log ───────────────────────────────────────────────────────────────
        root.addWidget(QLabel("Log:"))
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        self._log.setMaximumHeight(140)
        root.addWidget(self._log)

        self._refresh_list()

    # ── Automation list ───────────────────────────────────────────────────────

    def _refresh_list(self):
        prev = self._list.currentItem()
        prev_text = prev.text() if prev else None
        self._list.clear()
        self._list.addItems(list(self._automations.keys()))
        if prev_text:
            items = self._list.findItems(prev_text, Qt.MatchExactly)
            if items:
                self._list.setCurrentItem(items[0])
        self._on_automation_changed(
            self._list.currentItem().text() if self._list.currentItem() else ""
        )

    def _on_automation_changed(self, name: str):
        self._step_list.clear()
        self._clear_editor()
        if name and name in self._automations:
            steps = self._automations[name]["steps"]
            for i, s in enumerate(steps):
                label = f"Step {i+1}:  ({s['x']}, {s['y']})  delay {s['delay']}s"
                self._step_list.addItem(label)

    # ── Step selection + editing ──────────────────────────────────────────────

    def _on_step_selected(self, row: int):
        name = self._list.currentItem().text() if self._list.currentItem() else ""
        valid = row >= 0 and name in self._automations
        self._del_step_btn.setEnabled(valid)
        self._move_up_btn.setEnabled(valid and row > 0)
        has_steps = name in self._automations and len(self._automations[name]["steps"]) > 0
        self._move_down_btn.setEnabled(
            valid and has_steps and row < len(self._automations[name]["steps"]) - 1
        )
        self._apply_btn.setEnabled(valid)

        if valid:
            step = self._automations[name]["steps"][row]
            self._edit_x.setValue(step["x"])
            self._edit_y.setValue(step["y"])
            self._edit_delay.setValue(step["delay"])
        else:
            self._clear_editor()

    def _clear_editor(self):
        self._edit_x.setValue(0)
        self._edit_y.setValue(0)
        self._edit_delay.setValue(0)
        self._del_step_btn.setEnabled(False)
        self._move_up_btn.setEnabled(False)
        self._move_down_btn.setEnabled(False)
        self._apply_btn.setEnabled(False)

    def _apply_step_edit(self):
        name = self._list.currentItem().text() if self._list.currentItem() else ""
        row = self._step_list.currentRow()
        if not name or row < 0:
            return
        step = self._automations[name]["steps"][row]
        step["x"] = self._edit_x.value()
        step["y"] = self._edit_y.value()
        step["delay"] = self._edit_delay.value()
        storage.save_automations(self._automations)
        # Update the step list label in-place
        label = f"Step {row+1}:  ({step['x']}, {step['y']})  delay {step['delay']}s"
        self._step_list.currentItem().setText(label)

    def _delete_step(self):
        name = self._list.currentItem().text() if self._list.currentItem() else ""
        row = self._step_list.currentRow()
        if not name or row < 0:
            return
        r = QMessageBox.question(self, "Delete Step", f"Remove step {row+1}?")
        if r == QMessageBox.Yes:
            del self._automations[name]["steps"][row]
            storage.save_automations(self._automations)
            self._on_automation_changed(name)

    def _move_step_up(self):
        name = self._list.currentItem().text() if self._list.currentItem() else ""
        row = self._step_list.currentRow()
        if not name or row <= 0:
            return
        steps = self._automations[name]["steps"]
        steps[row], steps[row - 1] = steps[row - 1], steps[row]
        storage.save_automations(self._automations)
        self._on_automation_changed(name)
        self._step_list.setCurrentRow(row - 1)

    def _move_step_down(self):
        name = self._list.currentItem().text() if self._list.currentItem() else ""
        row = self._step_list.currentRow()
        if not name or row < 0:
            return
        steps = self._automations[name]["steps"]
        if row >= len(steps) - 1:
            return
        steps[row], steps[row + 1] = steps[row + 1], steps[row]
        storage.save_automations(self._automations)
        self._on_automation_changed(name)
        self._step_list.setCurrentRow(row + 1)

    # ── Record ────────────────────────────────────────────────────────────────

    def _record_new(self):
        bar = RecordBar(self._recorder, parent=self)
        screen = self.screen().geometry() if self.screen() else None
        if screen:
            bar.move(screen.center().x() - bar.width() // 2, 30)
        bar.exec_()

        # Process result after dialog is fully closed (avoids reentrant modal)
        steps = bar.recorded_steps
        if not steps:
            if bar.result() == bar.Accepted:
                QMessageBox.information(self, "Recording", "No clicks were recorded.")
            return
        name, ok = QInputDialog.getText(self, "Save Automation", "Name:")
        if not ok or not name.strip():
            return
        name = name.strip()
        if name in self._automations:
            QMessageBox.warning(self, "Error", f"'{name}' already exists.")
            return
        self._automations[name] = {"steps": steps}
        storage.save_automations(self._automations)
        self._refresh_list()

    # ── Rename automation ─────────────────────────────────────────────────────

    def _rename_automation(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.information(self, "", "Select an automation first.")
            return
        old_name = item.text()
        new_name, ok = QInputDialog.getText(
            self, "Rename Automation", "New name:", text=old_name
        )
        if not ok or not new_name.strip():
            return
        new_name = new_name.strip()
        if new_name == old_name:
            return
        if new_name in self._automations:
            QMessageBox.warning(self, "Error", f"'{new_name}' already exists.")
            return
        self._automations[new_name] = self._automations.pop(old_name)
        storage.save_automations(self._automations)
        self._refresh_list()

    # ── Delete automation ─────────────────────────────────────────────────────

    def _delete_automation(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.information(self, "", "Select an automation first.")
            return
        name = item.text()
        r = QMessageBox.question(self, "Delete", f"Delete '{name}'?")
        if r == QMessageBox.Yes:
            del self._automations[name]
            storage.save_automations(self._automations)
            self._refresh_list()

    # ── Run / Stop ────────────────────────────────────────────────────────────

    def _write_log(self, msg: str):
        self._log_signal.emit(msg)

    def _append_log(self, msg: str):
        self._log.append(msg)

    def _start(self):
        item = self._list.currentItem()
        if not item:
            QMessageBox.warning(self, "Error", "Select an automation first.")
            return
        name = item.text()
        steps = self._automations[name]["steps"]
        if not steps:
            QMessageBox.warning(self, "Error", "Automation has no steps.")
            return

        self._log.clear()
        self._append_log(f"Automation: {name}  ({len(steps)} steps)")

        self._player.start(
            steps=steps,
            run_gap=self._gap_spin.value(),
            log=self._write_log,
        )
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status.setText("Status: RUNNING")

        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(300)
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start()

    def _stop(self):
        self._player.stop()
        if hasattr(self, "_poll_timer"):
            self._poll_timer.stop()
        self._set_idle()
        self._append_log("🛑 Stopped.")

    def _poll(self):
        if not self._player.is_running():
            self._poll_timer.stop()
            self._set_idle()

    def _set_idle(self):
        self._status.setText("Status: IDLE")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
