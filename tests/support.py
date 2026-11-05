"""Isolated backend imports and bounded, synchronous offline test doubles."""

from contextlib import contextmanager
import importlib
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


def forbidden_input(*args, **kwargs):
    raise AssertionError("OS input and recording are forbidden in offline tests")


class FakeInputs:
    def __init__(self):
        self.presses = []
        self.pyautogui = ModuleType("pyautogui")
        self.pyautogui.press = self.presses.append
        for name in (
            "click", "doubleClick", "rightClick", "moveTo", "moveRel",
            "dragTo", "dragRel", "mouseDown", "mouseUp", "scroll",
            "keyDown", "keyUp", "hotkey", "write", "position", "screenshot",
        ):
            setattr(self.pyautogui, name, forbidden_input)
        self.mouse = ModuleType("pynput.mouse")
        # Fail at construction, before any listener can start.
        self.mouse.Listener = forbidden_input
        self.mouse.Button = SimpleNamespace(left=object(), right=object())
        self.pynput = ModuleType("pynput")
        self.pynput.__path__ = []
        self.pynput.mouse = self.mouse


@contextmanager
def offline_backend(*names):
    """Install input fakes BEFORE fresh backend imports; restore modules on exit.

    Removing the package as well as its submodules avoids modifying attributes
    on a previously imported backend package. No real input dependency is loaded,
    even if installed on the machine running these tests.
    """
    inputs = FakeInputs()
    with patch.dict(sys.modules, {
        "pyautogui": inputs.pyautogui,
        "pynput": inputs.pynput,
        "pynput.mouse": inputs.mouse,
    }):
        for name in list(sys.modules):
            if name == "backend" or name.startswith("backend."):
                del sys.modules[name]
        modules = {
            name: importlib.import_module("backend." + name) for name in names
        }
        yield SimpleNamespace(**modules), inputs


class FakeClock:
    """Advance integer microseconds only when the backend requests sleep."""

    def __init__(self):
        self.microseconds = 1_000_000_000
        self.sleeps = []
        self.reads = 0
        self.on_sleep = None

    def time(self):
        self.reads += 1
        if self.reads > 10_000:
            raise AssertionError("Clock polling exceeded offline test budget")
        return self.microseconds / 1_000_000

    def sleep(self, seconds):
        if not 0 < seconds <= 1:
            raise AssertionError("Unexpected wait: {!r}".format(seconds))
        if len(self.sleeps) >= 2_000:
            raise AssertionError("Waits exceeded offline test budget")
        self.sleeps.append(seconds)
        self.microseconds += round(seconds * 1_000_000)
        if self.on_sleep is not None:
            self.on_sleep()


class FakeEvent:
    """A single-threaded event with a guard against unbounded runner loops."""

    def __init__(self):
        self.flag = False
        self.checks = 0

    def set(self):
        self.flag = True

    def clear(self):
        self.flag = False

    def is_set(self):
        self.checks += 1
        if self.checks > 5_000:
            raise AssertionError("Cancellation checks exceeded offline test budget")
        return self.flag


class ManualThread:
    """start marks alive; the test explicitly runs the target synchronously."""

    def __init__(self, *, target, daemon):
        self.target = target
        self.daemon = daemon
        self.started = False
        self.alive = False

    def start(self):
        if self.started:
            raise AssertionError("Thread started twice")
        self.started = self.alive = True

    def is_alive(self):
        return self.alive

    def run_to_completion(self):
        if not self.alive:
            raise AssertionError("Thread must be started before running")
        try:
            self.target()
        finally:
            self.alive = False


class ManualThreads:
    def __init__(self):
        self.created = []

    def Thread(self, **kwargs):
        if len(self.created) >= 20:
            raise AssertionError("Thread creation exceeded offline test budget")
        thread = ManualThread(**kwargs)
        self.created.append(thread)
        return thread
