#!/bin/bash
# Launcher for UCI GUIs (En Croissant, Arena, Cute Chess).
# Runs engine.py from this folder, using .venv if it exists.
# GUIs (e.g. AppImage builds) may inject Python/library variables that break
# the engine's Python ("No module named 'encodings'"), so clear them first.
unset PYTHONHOME PYTHONPATH PYTHONSTARTUP PYTHONEXECUTABLE LD_LIBRARY_PATH LD_PRELOAD
cd "$(dirname "$0")" || exit 1
if [ -x ./.venv/bin/python ]; then
    exec ./.venv/bin/python -E engine.py
else
    exec python3 -E engine.py
fi
