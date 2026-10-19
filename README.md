# Gustee

Control your apps with hand gestures. Train a local PyTorch model on your own hand signs, then launch apps and websites with a wave — all processing stays on your device.

## How it works

- **Web UI** — configure gestures, record training samples, monitor sessions, and view history
- **Desktop companion** — runs locally in the background, operates your camera and trained model, and launches approved apps

## Getting started

1. Download the Gustee companion from the Settings page
2. Follow the setup instructions for your OS (Windows / macOS / Linux)
3. Pair the companion using the key shown on first launch
4. Record ≥30 samples per gesture, train the model, then start a session

## Development

Requires Node.js 20+.

```sh
git clone <this-repository-url>
cd <repository-name>
npm install
npm run dev
```

## Built with

- TanStack Start + Router
- React 19
- TypeScript
- Tailwind CSS 4
- FastAPI + PyTorch (companion)
- MediaPipe (hand landmark detection)
