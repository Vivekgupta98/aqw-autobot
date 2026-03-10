"""
backend/click_recorder.py — Global mouse-click recorder using pynput.
Captures (x, y, delay_since_last_click) for each left-click.
"""
from __future__ import annotations

import time
import threading
from pynput import mouse


class ClickRecorder:
    """Records left-click positions and inter-click delays."""

    def __init__(self):
        self._steps: list[dict] = []
        self._last_time: float = 0.0
        self._listener: mouse.Listener | None = None
        self._lock = threading.Lock()

    def start(self):
        """Begin listening for mouse clicks."""
        self._steps = []
        self._last_time = time.time()
        self._listener = mouse.Listener(on_click=self._on_click)
        self._listener.start()

    def stop(self) -> list[dict]:
        """Stop listening and return recorded steps."""
        if self._listener is not None:
            self._listener.stop()
            self._listener = None
        with self._lock:
            return list(self._steps)

    @property
    def click_count(self) -> int:
        with self._lock:
            return len(self._steps)

    def _on_click(self, x: int, y: int, button, pressed: bool):
        # Only record left-button press (not release)
        if button != mouse.Button.left or not pressed:
            return
        now = time.time()
        delay = round(now - self._last_time, 3) if self._steps else 0.0
        self._last_time = now
        with self._lock:
            self._steps.append({"x": int(x), "y": int(y), "delay": delay})
