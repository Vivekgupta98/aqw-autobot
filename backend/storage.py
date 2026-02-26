"""
backend/storage.py — JSON persistence for AQW Automation Tool.
Single file: data/classes.json — each class has cooldowns + nested combos.
"""

import json
import os

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_DATA = os.path.join(_ROOT, "data")
CLASSES_FILE = os.path.join(_DATA, "classes.json")

# ── Default presets (from old.py) ─────────────────────────────────────────────

DEFAULT_CLASSES = {
    "ChronoShadowhunter": {
        "cooldowns": [0, 0.5, 5, 3, 1.5, 6],
        "combos": {
            "boss no heal":  {"skills": [2, 4, 4, 4, 4, 4, 5], "repeat": 0},
            "boss low heal": {"skills": [2, 4, 4, 4, 4, 4, 5, 2, 3, 1, 1, 1, 1, 1, 2, 4, 4, 4, 4, 4, 5], "repeat": 0},
        },
    },
    "ArchPaladin": {
        "cooldowns": [0, 2, 4, 10, 25, 25],
        "combos": {
            "farm no heal":  {"skills": [1, 2], "repeat": 0},
            "farm heal":     {"skills": [1, 2, 2, 2, 2, 2, 3], "repeat": 0},
        },
    },
    "Mage": {
        "cooldowns": [0, 2, 6, 6, 3, 20],
        "combos": {
            "farm": {"skills": [4, 1], "repeat": 0},
        },
    },
    "SwordMaster": {
        "cooldowns": [0, 2, 5, 25, 9, 10],
        "combos": {
            "farm": {"skills": [5, 2, 1, 2, 1], "repeat": 0},
        },
    },
    "NeChrono": {
        "cooldowns": [0, 2, 2, 4, 10, 2.5],
        "combos": {
            "solo farm": {"skills": [1, 2, 3, 5, 1, 2, 1, 2, 3, 4, 5], "repeat": 0},
        },
    },
}


def _ensure_data_dir():
    os.makedirs(_DATA, exist_ok=True)


def load_classes() -> dict:
    """Return {name: {"cooldowns": [...], "combos": {cname: {...}, ...}}}."""
    _ensure_data_dir()
    if not os.path.exists(CLASSES_FILE):
        save_classes(DEFAULT_CLASSES)
        return dict(DEFAULT_CLASSES)
    with open(CLASSES_FILE, "r") as f:
        data = json.load(f)
    # Ensure every class has a combos dict (migration safety)
    for cls in data.values():
        cls.setdefault("combos", {})
    return data


def save_classes(classes: dict) -> None:
    _ensure_data_dir()
    with open(CLASSES_FILE, "w") as f:
        json.dump(classes, f, indent=2)
