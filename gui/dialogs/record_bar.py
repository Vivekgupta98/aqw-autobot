"""
gui/dialogs/record_bar.py — Small always-on-top floating bar shown during click recording.
Displays live click count and a Stop button.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QDialog, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, QTimer


class RecordBar(QDialog):
    """Frameless, always-on-top recording indicator.

    After exec_(), read `self.recorded_steps` for the result (list[dict] or None).
    """

    def __init__(self, recorder, parent=None):
        super().__init__(parent)
        self._recorder = recorder
        self.recorded_steps: list[dict] | None = None

        self.setWindowTitle("Recording")
        self.setWindowFlags(
            Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool
        )
        self.setFixedSize(260, 50)
        self.setStyleSheet(
            "background: #222; color: #eee; border-radius: 8px; font-size: 13px;"
        )

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 6, 12, 6)

        self._dot = QLabel("🔴")
        layout.addWidget(self._dot)

        self._label = QLabel("Recording…  0 clicks")
        self._label.setStyleSheet("color: #ff6b6b; font-weight: bold;")
        layout.addWidget(self._label, stretch=1)

        stop_btn = QPushButton("⏹ Stop")
        stop_btn.setFixedWidth(70)
        stop_btn.setStyleSheet(
            "background: #c0392b; color: white; border: none; "
            "border-radius: 4px; padding: 4px 8px; font-weight: bold;"
        )
        stop_btn.clicked.connect(self._stop)
        layout.addWidget(stop_btn)

        # Poll click count every 200ms
        self._poll = QTimer(self)
        self._poll.setInterval(200)
        self._poll.timeout.connect(self._update)

    def showEvent(self, event):
        super().showEvent(event)
        self._recorder.start()
        self._poll.start()

    def _update(self):
        n = self._recorder.click_count
        self._label.setText(f"Recording…  {n} click{'s' if n != 1 else ''}")

    def _stop(self):
        self._poll.stop()
        self.recorded_steps = self._recorder.stop()
        self.accept()
