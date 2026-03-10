"""
backend/click_player.py — Replays recorded click automations via pyautogui.
Loops indefinitely with a configurable gap between runs.
"""
from __future__ import annotations

import time
import threading
import pyautogui

pyautogui.FAILSAFE = True  # Move mouse to screen corner to abort


class ClickPlayer:
    """Replays a list of click steps in a background thread."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self, steps: list[dict], run_gap: float, log):
        """
        Start replaying `steps` in a loop.

        Each step is {"x": int, "y": int, "delay": float}.
        After all steps, waits `run_gap` seconds, then loops again.
        """
        if self.is_running():
            return
        self._stop_event.clear()

        def _run():
            iteration = 0
            log("🟢 Click automation running.")

            while not self._stop_event.is_set():
                iteration += 1
                log(f"\n── Run {iteration} ──")

                for i, step in enumerate(steps, 1):
                    if self._stop_event.is_set():
                        break

                    # Wait the inter-click delay
                    delay = step["delay"]
                    if delay > 0:
                        log(f"  ⏳ Waiting {delay:.1f}s…")
                        deadline = time.time() + delay
                        while time.time() < deadline:
                            if self._stop_event.is_set():
                                break
                            time.sleep(0.05)
                        if self._stop_event.is_set():
                            break

                    # Perform the click
                    x, y = step["x"], step["y"]
                    pyautogui.click(x, y)
                    log(f"  ▶ Click {i}: ({x}, {y})")

                if self._stop_event.is_set():
                    break

                # Gap between full runs
                if run_gap > 0:
                    log(f"  ⏳ Run gap: waiting {run_gap:.1f}s…")
                    deadline = time.time() + run_gap
                    while time.time() < deadline:
                        if self._stop_event.is_set():
                            break
                        time.sleep(0.05)

            log("🔴 Click automation stopped.")

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
