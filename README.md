# AQW Bot

A lightweight desktop automation tool for **Adventure Quest Worlds** (AQW). Define your game classes with skill cooldowns, build combat combos, and let the bot execute the rotation for you using simulated keypresses.

Built with **Python 3** + **PyQt5** (native macOS rendering) + **pyautogui** (key simulation).

---

## Screenshots

| Main Window | Add Class | Add Combo |
|---|---|---|
| ![Main Window](screenshots/main_window.png) | ![Add Class](screenshots/class_dialog.png) | ![Add Combo](screenshots/combo_dialog.png) |

> **Note:** Replace the placeholder images in `screenshots/` with your own screenshots.

---

## Features

- **Class Management** — Add / edit / delete game classes with 6 skill cooldowns each
- **Combo Builder** — Create named skill rotation sequences nested under each class
- **Cooldown Engine** — Accurate cooldown tracking with interruptible waits (50ms granularity)
- **Visual Countdown** — 3… 2… 1 countdown before automation starts (configurable delay)
- **Start / Stop** — Clean start and stop. Closing the window kills all threads instantly
- **Live Log** — Real-time activity log showing each keypress and cooldown wait
- **Persistent Data** — All classes and combos saved to `data/classes.json`
- **Failsafe** — Move mouse to any screen corner to abort (`pyautogui.FAILSAFE`)

---

## Quick Start

```bash
# Clone
git clone <your-repo-url> aq-tool
cd aq-tool

# Install dependencies
pip3 install -r requirements.txt

# Run
./run.sh
```

Or directly:

```bash
python3 run.py
```

---

## Project Structure

```
aq-tool/
├── run.py                  # Entry point (QApplication)
├── run.sh                  # Shell launcher (kills on exit)
├── requirements.txt        # PyQt5, pyautogui
├── data/
│   └── classes.json        # Persisted classes + combos
├── backend/
│   ├── engine.py           # Cooldown-aware automation runner (background thread)
│   └── storage.py          # JSON load/save with default presets
├── gui/
│   ├── app.py              # QMainWindow — single-panel layout, CRUD logic
│   ├── panels/
│   │   ├── list_panel.py   # Reusable QListWidget panel
│   │   └── run_panel.py    # Class/Combo selectors, countdown, log
│   └── dialogs/
│       ├── class_dialog.py # Add/Edit class (name + 6 cooldowns)
│       └── combo_dialog.py # Add/Edit combo (name + skill list + repeat)
└── screenshots/            # Your screenshots go here
```

---

## How It Works

1. **Select a Class** from the dropdown — cooldowns are shown below
2. **Select a Combo** — the skill rotation is previewed as `1 → 2 → 3 → 5 (∞)`
3. **Set Start Delay** — defaults to 3 seconds, giving you time to switch to the game window
4. **Click START** — a visual countdown runs, then the bot begins pressing number keys (1–5) in the defined sequence
5. **Click STOP** — immediately halts the automation mid-loop

The engine tracks per-skill cooldowns accurately. If a skill is still on cooldown, it waits the remaining time before pressing the key. All waits are interruptible — stopping is always instant.

---

## Default Classes

The app ships with 5 preloaded classes from the original automation script:

| Class | Cooldowns | Combos |
|---|---|---|
| ChronoShadowhunter | 0, 0.5, 5, 3, 1.5, 6 | boss no heal, boss low heal |
| ArchPaladin | 0, 2, 4, 10, 25, 25 | farm no heal, farm heal |
| Mage | 0, 2, 6, 6, 3, 20 | farm |
| SwordMaster | 0, 2, 5, 25, 9, 10 | farm |
| NeChrono | 0, 2, 2, 4, 10, 2.5 | solo farm |

Delete the `data/classes.json` file to regenerate defaults.

---

## Requirements

- macOS (tested on macOS 13+)
- Python 3.9+
- PyQt5 ≥ 5.15
- pyautogui ≥ 0.9.54

---

## License

MIT
