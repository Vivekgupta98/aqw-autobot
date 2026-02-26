#!/usr/bin/env bash
# run.sh — Launch the AQW Automation Tool.
# Usage: ./run.sh
#
# The script changes to its own directory so relative imports work correctly,
# then starts the app. Closing the app window kills the process entirely
# (handled by os._exit(0) in gui/app.py).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "Starting AQW Automation Tool…"
python3 run.py
