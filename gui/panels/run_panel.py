"""
gui/panels/run_panel.py — PyQt5 single-panel layout.
Class dropdown (+ CRUD + cooldown preview)
→ Combo dropdown (+ CRUD + skill preview)
→ Delay, Start/Stop, Log.
"""
from __future__ import annotations
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QHBoxLayout,
    QLabel, QComboBox, QSpinBox, QPushButton, QTextEdit, QMessageBox,
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal


class RunPanel(QWidget):
    _log_signal = pyqtSignal(str)

    def __init__(self, get_classes, runner,
                 on_add_class, on_edit_class, on_delete_class,
                 on_add_combo, on_edit_combo, on_delete_combo,
                 parent=None):
        super().__init__(parent)
        self._get_classes     = get_classes
        self._runner          = runner
        self._on_add_class    = on_add_class
        self._on_edit_class   = on_edit_class
        self._on_delete_class = on_delete_class
        self._on_add_combo    = on_add_combo
        self._on_edit_combo   = on_edit_combo
        self._on_delete_combo = on_delete_combo
        self._countdown_val   = 0
        self._cancelled       = False
        self._timer           = QTimer(self)
        self._timer.setSingleShot(False)
        self._timer.setInterval(1000)
        self._timer.timeout.connect(self._tick)
        self._log_signal.connect(self._append_log)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(6)

        layout.addWidget(QLabel("<b>AQW Bot</b>"))

        # ── Form ──────────────────────────────────────────────────────────────
        form = QFormLayout()
        form.setSpacing(6)

        # Class selector + CRUD
        class_row = QHBoxLayout()
        self._class_cb = QComboBox()
        self._class_cb.setMinimumWidth(180)
        self._class_cb.currentTextChanged.connect(self._on_class_changed)
        class_row.addWidget(self._class_cb, stretch=1)
        for label, slot in [("Add", self._add_class),
                             ("Edit", self._edit_class),
                             ("Del", self._del_class)]:
            btn = QPushButton(label)
            btn.setFixedWidth(56)
            btn.clicked.connect(slot)
            class_row.addWidget(btn)
        form.addRow("Class:", class_row)

        # Cooldown preview
        self._cd_preview = QLabel("")
        self._cd_preview.setWordWrap(False)
        self._cd_preview.setStyleSheet("color: #888; font-size: 12px; padding: 2px 0;")
        form.addRow("", self._cd_preview)

        # Combo selector + CRUD
        combo_row = QHBoxLayout()
        self._combo_cb = QComboBox()
        self._combo_cb.setMinimumWidth(180)
        self._combo_cb.currentTextChanged.connect(self._on_combo_changed)
        combo_row.addWidget(self._combo_cb, stretch=1)
        for label, slot in [("Add", self._add_combo),
                             ("Edit", self._edit_combo),
                             ("Del", self._del_combo)]:
            btn = QPushButton(label)
            btn.setFixedWidth(56)
            btn.clicked.connect(slot)
            combo_row.addWidget(btn)
        form.addRow("Combo:", combo_row)

        # Skill preview
        self._skill_preview = QLabel("")
        self._skill_preview.setWordWrap(False)
        self._skill_preview.setStyleSheet("color: #888; font-size: 12px; padding: 2px 0;")
        form.addRow("", self._skill_preview)

        # Delay
        self._delay_spin = QSpinBox()
        self._delay_spin.setRange(1, 60)
        self._delay_spin.setValue(3)
        self._delay_spin.setSuffix(" s")
        form.addRow("Start Delay:", self._delay_spin)

        layout.addLayout(form)

        # ── Start / Stop ──────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        self._start_btn = QPushButton("▶  START")
        self._start_btn.clicked.connect(self._start)
        self._stop_btn  = QPushButton("⏹  STOP")
        self._stop_btn.setEnabled(False)
        self._stop_btn.clicked.connect(self._stop)
        btn_row.addWidget(self._start_btn)
        btn_row.addWidget(self._stop_btn)
        layout.addLayout(btn_row)

        # ── Status ────────────────────────────────────────────────────────────
        self._status_lbl = QLabel("Status: IDLE")
        self._status_lbl.setAlignment(Qt.AlignCenter)
        layout.addWidget(self._status_lbl)

        # ── Log ───────────────────────────────────────────────────────────────
        layout.addWidget(QLabel("Log:"))
        self._log = QTextEdit()
        self._log.setReadOnly(True)
        layout.addWidget(self._log, stretch=1)

    # ── Public refresh ────────────────────────────────────────────────────────

    def refresh(self):
        prev = self._class_cb.currentText()
        self._class_cb.blockSignals(True)
        self._class_cb.clear()
        self._class_cb.addItems(list(self._get_classes().keys()))
        if prev:
            idx = self._class_cb.findText(prev)
            if idx >= 0:
                self._class_cb.setCurrentIndex(idx)
        self._class_cb.blockSignals(False)
        self._on_class_changed(self._class_cb.currentText())

    # ── Class change → update previews + combos ───────────────────────────────

    def _on_class_changed(self, cls_name: str):
        classes = self._get_classes()
        # Cooldown preview
        if cls_name in classes:
            cds = classes[cls_name]["cooldowns"]
            parts = [f"S{i}={cd}s" for i, cd in enumerate(cds)]
            self._cd_preview.setText("  ".join(parts))
        else:
            self._cd_preview.setText("")
        # Populate combos
        self._combo_cb.blockSignals(True)
        self._combo_cb.clear()
        if cls_name and cls_name in classes:
            combos = classes[cls_name].get("combos", {})
            self._combo_cb.addItems(list(combos.keys()))
        self._combo_cb.blockSignals(False)
        self._on_combo_changed(self._combo_cb.currentText())

    def _on_combo_changed(self, combo_name: str):
        cls_name = self._class_cb.currentText()
        classes  = self._get_classes()
        if cls_name in classes:
            combo = classes[cls_name].get("combos", {}).get(combo_name)
            if combo:
                arr = " → ".join(str(s) for s in combo["skills"])
                rep = "∞" if combo["repeat"] == 0 else f"{combo['repeat']}×"
                self._skill_preview.setText(f"{arr}   ({rep})")
                return
        self._skill_preview.setText("")

    # ── Class CRUD (delegates to app) ─────────────────────────────────────────

    def _add_class(self):  self._on_add_class()
    def _edit_class(self):
        cls = self._class_cb.currentText()
        if cls: self._on_edit_class(cls)
        else: QMessageBox.information(self, "", "Select a class first.")
    def _del_class(self):
        cls = self._class_cb.currentText()
        if cls: self._on_delete_class(cls)
        else: QMessageBox.information(self, "", "Select a class first.")

    # ── Combo CRUD (delegates to app) ─────────────────────────────────────────

    def _add_combo(self):
        cls = self._class_cb.currentText()
        if cls: self._on_add_combo(cls)
        else: QMessageBox.information(self, "", "Select a class first.")
    def _edit_combo(self):
        cls   = self._class_cb.currentText()
        combo = self._combo_cb.currentText()
        if cls and combo: self._on_edit_combo(cls, combo)
        elif cls: QMessageBox.information(self, "", "Select a combo first.")
    def _del_combo(self):
        cls   = self._class_cb.currentText()
        combo = self._combo_cb.currentText()
        if cls and combo: self._on_delete_combo(cls, combo)
        elif cls: QMessageBox.information(self, "", "Select a combo first.")

    # ── Logging ───────────────────────────────────────────────────────────────

    def _write_log(self, msg: str):
        self._log_signal.emit(msg)

    def _append_log(self, msg: str):
        self._log.append(msg)

    # ── Countdown + run ───────────────────────────────────────────────────────

    def _start(self):
        cls_name   = self._class_cb.currentText()
        combo_name = self._combo_cb.currentText()
        classes    = self._get_classes()

        if cls_name not in classes:
            QMessageBox.warning(self, "Error", "Select a class."); return
        combos = classes[cls_name].get("combos", {})
        if combo_name not in combos:
            QMessageBox.warning(self, "Error", "Select a combo."); return

        self._pending = dict(
            cooldowns     = classes[cls_name]["cooldowns"],
            sequence      = combos[combo_name]["skills"],
            repeat        = combos[combo_name]["repeat"],
            initial_delay = 0,
            log           = self._write_log,
        )

        self._log.clear()
        self._append_log(f"Class: {cls_name}  |  Combo: {combo_name}")

        self._cancelled = False
        self._countdown_val = self._delay_spin.value()
        self._start_btn.setEnabled(False)
        self._stop_btn.setEnabled(True)
        self._status_lbl.setText(f"Starting in {self._countdown_val}…")
        self._append_log(f"⏳ {self._countdown_val}…")
        self._timer.start()

    def _tick(self):
        if self._cancelled:
            self._timer.stop(); return
        self._countdown_val -= 1
        if self._countdown_val > 0:
            self._status_lbl.setText(f"Starting in {self._countdown_val}…")
            self._append_log(f"⏳ {self._countdown_val}…")
        else:
            self._timer.stop()
            self._launch()

    def _launch(self):
        self._status_lbl.setText("Status: RUNNING")
        self._runner.start(**self._pending)
        self._poll_timer = QTimer(self)
        self._poll_timer.setInterval(300)
        self._poll_timer.timeout.connect(self._poll)
        self._poll_timer.start()

    def _stop(self):
        self._cancelled = True
        self._timer.stop()
        self._runner.stop()
        if hasattr(self, "_poll_timer"):
            self._poll_timer.stop()
        self._set_idle()
        self._append_log("🛑 Stopped.")

    def _poll(self):
        if not self._runner.is_running():
            self._poll_timer.stop()
            self._set_idle()

    def _set_idle(self):
        self._status_lbl.setText("Status: IDLE")
        self._start_btn.setEnabled(True)
        self._stop_btn.setEnabled(False)
