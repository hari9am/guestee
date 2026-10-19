#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c 'import tkinter; import pystray; import mediapipe; import torch'
echo 'Setup complete. Run bash start.sh to start Gustee in the background.'