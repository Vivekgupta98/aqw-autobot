"""Verify input isolation without opening the GUI or starting a recorder."""

import sys
from types import ModuleType
import unittest
from unittest.mock import patch

from tests.support import offline_backend


class OfflineImportTests(unittest.TestCase):
    def test_backend_imports_use_fakes_and_cannot_send_mouse_input_or_listen(self):
        previous = set(sys.modules)
        with offline_backend("storage", "engine", "click_player", "click_recorder") as (modules, inputs):
            self.assertIs(modules.engine.pyautogui, inputs.pyautogui)
            self.assertIs(modules.click_player.pyautogui, inputs.pyautogui)
            self.assertIs(modules.click_recorder.mouse, inputs.mouse)
            self.assertIs(sys.modules["pynput"], inputs.pynput)
            self.assertTrue(inputs.pyautogui.FAILSAFE)
            self.assertEqual(inputs.presses, [])
            for name in ("click", "moveTo", "moveRel", "mouseDown", "mouseUp"):
                with self.subTest(action=name), self.assertRaises(AssertionError):
                    getattr(inputs.pyautogui, name)(0, 0)
            with self.assertRaises(AssertionError):
                inputs.mouse.Listener(on_click=lambda *args: None)
            newly_loaded = set(sys.modules) - previous
            self.assertFalse(any(
                name == "gui" or name.startswith("gui.") or name == "run"
                or name == "PyQt5" or name.startswith("PyQt5.")
                for name in newly_loaded
            ))

    def test_import_context_restores_preexisting_modules_even_on_failure(self):
        names = ("backend", "backend.engine", "pyautogui", "pynput", "pynput.mouse")
        originals = {name: ModuleType(name) for name in names}
        with patch.dict(sys.modules, originals):
            with self.assertRaisesRegex(RuntimeError, "intentional"):
                with offline_backend("engine") as (modules, inputs):
                    self.assertIsNot(modules.engine, originals["backend.engine"])
                    self.assertIs(modules.engine.pyautogui, inputs.pyautogui)
                    raise RuntimeError("intentional")
            for name, original in originals.items():
                self.assertIs(sys.modules[name], original)
