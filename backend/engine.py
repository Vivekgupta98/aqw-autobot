"""
backend/engine.py — Cooldown-aware AQW skill automation engine.
Runs in a background daemon thread; stop via AutomationRunner.stop().
"""
from __future__ import annotations

import time
import threading
import pyautogui

pyautogui.FAILSAFE = True  # Move mouse to screen corner to abort


class GameClassEngine:
    """
    Tracks per-skill cooldown state and fires keypresses via pyautogui.
    Skill indices 0–5 map to keys '0'–'5'. Index 0 is reserved / basic attack.
    """

    def __init__(self, cooldowns: list):
        assert len(cooldowns) == 6, "Must provide exactly 6 cooldown values (indices 0–5)."
        self.cooldown  = cooldowns
        self.last_left = [0.0] * 6

    def use_skill(self, index: int, stop_event: threading.Event, log) -> bool:
        """
        Press skill at `index`. Waits for cooldown if needed.
        Returns False if stop_event fires during the wait, True otherwise.
        """
        assert 0 <= index <= 5, "Skill index must be 0–5."

        remaining = self.last_left[index]
        if remaining > 0:
            log(f"  ⏳ Waiting {remaining:.1f}s for skill {index}…")
            deadline = time.time() + remaining
            while time.time() < deadline:
                if stop_event.is_set():
                    return False
                time.sleep(0.05)
            for i in range(6):
                self.last_left[i] = max(0.0, self.last_left[i] - remaining)

        pyautogui.press(str(index))
        log(f"  ▶ Skill {index} pressed  (cd: {self.cooldown[index]}s)")

        for i in range(6):
            if i == index:
                self.last_left[i] += self.cooldown[i]
            else:
                if self.last_left[i] == 0 and index != 1:
                    self.last_left[i] += min(1.0, self.cooldown[i])
        return True

    def reset(self):
        self.last_left = [0.0] * 6


class AutomationRunner:
    """High-level runner — executes a skill sequence in a background thread."""

    def __init__(self):
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None

    def is_running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(
        self,
        cooldowns: list,
        sequence: list,
        repeat: int,          # 0 = infinite
        initial_delay: float,
        log,
    ):
        if self.is_running():
            return
        self._stop_event.clear()

        def _run():
            log(f"⏱ Starting in {initial_delay:.1f}s… (switch to game window)")
            deadline = time.time() + initial_delay
            while time.time() < deadline:
                if self._stop_event.is_set():
                    log("🛑 Aborted during startup delay.")
                    return
                time.sleep(0.05)

            engine    = GameClassEngine(cooldowns)
            iteration = 0
            log("🟢 Automation running.")

            while True:
                if self._stop_event.is_set():
                    break
                iteration += 1
                label = "∞" if repeat == 0 else f"{iteration}/{repeat}"
                log(f"\n── Loop {label} ──")

                for idx in sequence:
                    if self._stop_event.is_set():
                        break
                    if not engine.use_skill(idx, self._stop_event, log):
                        break

                if repeat != 0 and iteration >= repeat:
                    log("✅ Sequence complete.")
                    break

            log("🔴 Automation stopped.")

        self._thread = threading.Thread(target=_run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
