#!/bin/bash
# Launcher for UCI GUIs (En Croissant, Arena, Cute Chess).
# Runs engine.py from this folder, using .venv if it exists.
cd "$(dirname "$0")" || exit 1
if [ -x ./.venv/bin/python ]; then
    exec ./.venv/bin/python engine.py
else
    exec python3 engine.py
fi
