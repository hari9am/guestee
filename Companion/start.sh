#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [ ! -x .venv/bin/python ]; then
  echo 'Run bash setup.sh first (requires Python 3.11 and Tk).'
  exit 1
fi
mkdir -p logs
nohup .venv/bin/python app.py >> logs/companion.log 2>&1 < /dev/null &
echo 'Gustee is starting. Look for its consent dialog and system-tray icon.'
echo 'If no icon appears, check logs/companion.log.'
