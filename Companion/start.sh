#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
if [ -x ./Gustee/Gustee ]; then
  mkdir -p logs
  nohup ./Gustee/Gustee >> logs/companion.log 2>&1 < /dev/null &
  echo 'Gustee is starting in the background from the packaged app build.'
  echo 'Open https://gestuee.netlify.app to pair or train gestures.'
  exit 0
fi
if [ ! -x .venv/bin/python ]; then
  echo 'This is a source-only launch helper. Run bash setup.sh first (requires Python 3.11 and Tk).'
  exit 1
fi
mkdir -p logs
nohup .venv/bin/python app.py >> logs/companion.log 2>&1 < /dev/null &
echo 'Gustee is starting from source. Look for its consent dialog and system-tray icon.'
echo 'If no icon appears, check logs/companion.log.'
