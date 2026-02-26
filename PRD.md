# AQW Automation Tool — Product Requirements Document

## Overview

A desktop GUI application written in Python that allows players of **Adventure Quest Worlds (AQW)** to manage game class skill rotations and control an automation bot — all without editing code.

---

## Goals

- Allow users to define custom AQW classes with per-skill cooldowns.
- Allow users to define and save named skill rotation sequences.
- Allow users to select a class + sequence and run the automation loop.
- Provide clear start/stop control with safety in mind.

---

## Tech Stack

| Layer | Choice |
|---|---|
| Language | Python 3.10+ |
| GUI Framework | `tkinter` (built-in) or `customtkinter` for modern styling |
| Automation | `pyautogui` |
| Persistence | JSON files (classes and sequences saved locally) |

---

## Features

### 1. Class Manager

Users can **create, edit, and delete** AQW classes.

**Fields per class:**
- `Class Name` — string label (e.g., `NeChrono`, `ArchPaladin`)
- `Skill Cooldowns` — 6 numeric inputs (one per skill slot, index 0–5)
  - Skill 0 is always the basic attack (cooldown = 0 or minimal)
  - Skills 1–5 are mapped to keyboard keys `1`–`5`

**Actions:**
- ➕ Add new class
- ✏️ Edit existing class
- 🗑️ Delete class
- All classes persisted to `classes.json`

---

### 2. Sequence Builder

Users can **create, edit, and delete** named skill rotation sequences.

**Fields per sequence:**
- `Sequence Name` — string label (e.g., `solo_farm`, `boss_no_heal`)
- `Skill Order` — ordered list of skill indices (e.g., `[1, 2, 3, 5, 1, 2]`)
  - Drag-and-drop reordering OR up/down arrows OR manual text entry
- `Repeat Count` — integer or `∞` (infinite loop)

**Actions:**
- ➕ Add new sequence
- ✏️ Edit existing sequence
- 🗑️ Delete sequence
- All sequences persisted to `sequences.json`

---

### 3. Run Panel (Main Control)

The primary panel the user interacts with during gameplay.

**Controls:**
- **Class Selector** — dropdown of saved classes
- **Sequence Selector** — dropdown of saved sequences (filtered or all)
- **Initial Delay** — numeric input (seconds to wait before starting, default: 3)
- **▶ Start Button** — begins the automation loop in a background thread
- **⏹ Stop Button** — gracefully stops the loop
- **Status Indicator** — shows `IDLE`, `RUNNING`, or `STOPPED`
- **Log / Activity Feed** — scrollable text area showing which skill was pressed and when

**Behavior:**
- Automation runs on a **background thread** so the GUI stays responsive.
- Pressing Stop sets a threading event that cleanly exits the loop.
- `pyautogui.FAILSAFE = True` is always enabled (move mouse to corner to abort).

---

### 4. Persistence

- `classes.json` — stores all user-defined classes and their cooldowns
- `sequences.json` — stores all user-defined sequences
- Both files are auto-created on first run with the built-in presets from `old.py` as defaults

**Default presets loaded on first run:**

| Class | Cooldowns |
|---|---|
| ChronoShadowhunter | `[0, 0.5, 5, 3, 1.5, 6]` |
| ArchPaladin | `[0, 2, 4, 10, 25, 25]` |
| Mage | `[0, 2, 6, 6, 3, 20]` |
| SwordMaster | `[0, 2, 5, 25, 9, 10]` |
| NeChrono | `[0, 2, 2, 4, 10, 2.5]` |

---

## UI Layout (Wireframe Description)

```
┌─────────────────────────────────────────────────────┐
│  AQW Automation Tool                         [─][□][×]│
├───────────────┬─────────────────────────────────────┤
│  Classes      │  Run Panel                           │
│  ──────────   │  ─────────                           │
│  [List of     │  Class:    [Dropdown ▼]              │
│   classes]    │  Sequence: [Dropdown ▼]              │
│               │  Delay:    [3] seconds               │
│  [+ Add]      │                                      │
│  [✏ Edit]     │       [▶ START]   [⏹ STOP]          │
│  [🗑 Delete]  │                                      │
│               │  Status: ● IDLE                      │
├───────────────┤  ────────────────────────────────── │
│  Sequences    │  Activity Log:                       │
│  ──────────   │  > Skill 1 pressed (cd: 2.0s)        │
│  [List of     │  > Skill 2 pressed (cd: 2.0s)        │
│   sequences]  │  > Waiting 1.3s for skill 3...       │
│               │                                      │
│  [+ Add]      │                                      │
│  [✏ Edit]     │                                      │
│  [🗑 Delete]  │                                      │
└───────────────┴─────────────────────────────────────┘
```

---

## Non-Functional Requirements

- **Safety**: `pyautogui.FAILSAFE` always on. Stop button always accessible.
- **Portability**: Works on macOS and Windows (primary targets for AQW players).
- **No external server**: Fully local, no network calls.
- **Single file or small package**: Easy to run with `python main.py`.

---

## Out of Scope (v1)

- Screen reading / OCR (health bar detection)
- Auto-targeting or pathfinding
- Multiple simultaneous class rotations
- Cloud sync of configs
