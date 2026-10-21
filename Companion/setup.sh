#!/usr/bin/env bash
set -euo pipefail
cd -- "$(dirname -- "$0")"
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -c 'import tkinter; import pystray; import mediapipe; import torch'
echo 'Source setup complete. This is for local development from the repo.'
echo 'For normal use, install the packaged companion for your OS instead of running setup.sh manually.'
echo 'Then run bash start.sh if you are launching the companion from source.'