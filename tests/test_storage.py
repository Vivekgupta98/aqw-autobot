"""Persistence tests use only disposable directories, never repository data."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from tests.support import offline_backend


# Independent expectations: do not derive these from storage.DEFAULT_CLASSES or
# use the tracked, user-customized data/classes.json as a fixture.
EXPECTED_DEFAULTS = {
    "ChronoShadowhunter": {
        "cooldowns": [0, 0.5, 5, 3, 1.5, 6],
        "combos": {
            "boss no heal": {"skills": [2, 4, 4, 4, 4, 4, 5], "repeat": 0},
            "boss low heal": {
                "skills": [2, 4, 4, 4, 4, 4, 5, 2, 3, 1, 1, 1, 1, 1, 2, 4, 4, 4, 4, 4, 5],
                "repeat": 0,
            },
        },
    },
    "ArchPaladin": {
        "cooldowns": [0, 2, 4, 10, 25, 25],
        "combos": {
            "farm no heal": {"skills": [1, 2], "repeat": 0},
            "farm heal": {"skills": [1, 2, 2, 2, 2, 2, 3], "repeat": 0},
        },
    },
    "Mage": {
        "cooldowns": [0, 2, 6, 6, 3, 20],
        "combos": {"farm": {"skills": [4, 1], "repeat": 0}},
    },
    "SwordMaster": {
        "cooldowns": [0, 2, 5, 25, 9, 10],
        "combos": {"farm": {"skills": [5, 2, 1, 2, 1], "repeat": 0}},
    },
    "NeChrono": {
        "cooldowns": [0, 2, 2, 4, 10, 2.5],
        "combos": {
            "solo farm": {"skills": [1, 2, 3, 5, 1, 2, 1, 2, 3, 4, 5], "repeat": 0},
        },
    },
}


class StorageTests(unittest.TestCase):
    def setUp(self):
        context = offline_backend("storage")
        modules, self.inputs = context.__enter__()
        self.addCleanup(context.__exit__, None, None, None)
        self.storage = modules.storage
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.data = Path(temporary.name) / "not-created-yet" / "data"
        self.classes_file = self.data / "classes.json"
        self.automations_file = self.data / "automations.json"
        patches = patch.multiple(
            self.storage,
            _DATA=str(self.data),
            CLASSES_FILE=str(self.classes_file),
            AUTOMATIONS_FILE=str(self.automations_file),
            # First-load returns a shallow copy. Isolate nested presets so a
            # test cannot accidentally mutate defaults used by another test.
            DEFAULT_CLASSES=deepcopy(self.storage.DEFAULT_CLASSES),
        )
        patches.start()
        self.addCleanup(patches.stop)

    def read_json(self, path):
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)

    def test_missing_classes_creates_directory_and_persists_all_defaults(self):
        self.assertFalse(self.data.exists())
        loaded = self.storage.load_classes()
        self.assertEqual(loaded, EXPECTED_DEFAULTS)
        self.assertEqual(self.read_json(self.classes_file), EXPECTED_DEFAULTS)
        self.assertEqual(self.storage.load_classes(), EXPECTED_DEFAULTS)
        self.assertFalse(self.automations_file.exists())

    def test_missing_automations_creates_directory_and_empty_store(self):
        self.assertFalse(self.data.exists())
        self.assertEqual(self.storage.load_automations(), {})
        self.assertEqual(self.read_json(self.automations_file), {})
        self.assertEqual(self.storage.load_automations(), {})
        self.assertFalse(self.classes_file.exists())

    def test_classes_round_trip_preserves_custom_names_and_combo_order(self):
        classes = {
            "Custom Mage / 雪": {
                "cooldowns": [0, 0.125, 2, 3.5, 4, 5],
                "combos": {
                    "boss phase 2": {"skills": [5, 2, 2, 1, 0], "repeat": 3},
                    "forever": {"skills": [4, 1], "repeat": 0},
                },
            },
            "Empty class": {"cooldowns": [0] * 6, "combos": {}},
        }
        self.storage.save_classes(classes)
        self.assertEqual(self.read_json(self.classes_file), classes)
        loaded = self.storage.load_classes()
        self.assertEqual(loaded, classes)
        loaded["Custom Mage / 雪"]["combos"]["boss phase 2"]["skills"].append(3)
        self.assertEqual(self.storage.load_classes(), classes)
        self.storage.save_classes(loaded)
        self.assertEqual(self.storage.load_classes(), loaded)

    def test_empty_classes_remain_empty_instead_of_regenerating_defaults(self):
        self.storage.save_classes({})
        self.assertEqual(self.read_json(self.classes_file), {})
        self.assertEqual(self.storage.load_classes(), {})

    def test_loading_defaults_does_not_save_later_in_memory_edits(self):
        loaded = self.storage.load_classes()
        loaded["Mage"]["combos"]["farm"]["skills"].append(5)
        self.assertEqual(self.storage.load_classes(), EXPECTED_DEFAULTS)
        self.assertEqual(self.read_json(self.classes_file), EXPECTED_DEFAULTS)

    def test_legacy_migration_preserves_fields_and_only_persists_on_save(self):
        legacy = {
            "Old class": {
                "cooldowns": [0, 1, 2.5, 3, 4, 5],
                "notes": "keep this extra field",
            },
            "Modern class": {
                "cooldowns": [0] * 6,
                "combos": {"custom": {"skills": [3, 1, 3], "repeat": 7}},
                "metadata": {"favorite": True},
            },
            "Already empty": {"cooldowns": [0] * 6, "combos": {}},
        }
        self.data.mkdir(parents=True)
        original = json.dumps(legacy, indent=4) + "\n"
        self.classes_file.write_text(original, encoding="utf-8")
        original_bytes = self.classes_file.read_bytes()
        expected = deepcopy(legacy)
        expected["Old class"]["combos"] = {}

        migrated = self.storage.load_classes()
        self.assertEqual(migrated, expected)
        self.assertEqual(self.classes_file.read_bytes(), original_bytes)
        self.storage.save_classes(migrated)
        self.assertEqual(self.read_json(self.classes_file), expected)
        self.assertEqual(self.storage.load_classes(), expected)

    def test_automations_round_trip_preserves_coordinates_delays_and_step_order(self):
        automations = {
            "Route / 雪": {
                "steps": [
                    {"x": 120, "y": 240, "delay": 0},
                    {"x": -10, "y": 15, "delay": 0.125},
                    {"x": 120, "y": 240, "delay": 1.75},
                ],
            },
            "Empty route": {"steps": []},
        }
        self.storage.save_automations(automations)
        self.assertEqual(self.read_json(self.automations_file), automations)
        loaded = self.storage.load_automations()
        self.assertEqual(loaded, automations)
        loaded["Route / 雪"]["steps"].reverse()
        self.assertEqual(self.storage.load_automations(), automations)
        self.storage.save_automations(loaded)
        self.assertEqual(self.storage.load_automations(), loaded)

    def test_empty_automations_overwrite_existing_store(self):
        self.storage.save_automations({"old": {"steps": []}})
        self.storage.save_automations({})
        self.assertEqual(self.read_json(self.automations_file), {})
        self.assertEqual(self.storage.load_automations(), {})

    def test_class_and_automation_stores_do_not_overwrite_each_other(self):
        self.storage.save_classes({"Custom": {"cooldowns": [0] * 6, "combos": {}}})
        classes_bytes = self.classes_file.read_bytes()
        self.storage.save_automations({"Custom": {"steps": []}})
        self.assertEqual(self.classes_file.read_bytes(), classes_bytes)
        automations_bytes = self.automations_file.read_bytes()
        self.storage.save_classes({})
        self.assertEqual(self.automations_file.read_bytes(), automations_bytes)
