# omniDriverTrainer

A Python port of the OmniDriver Trainer 3D perimeter driving and firing game.

This repository includes:
- `index.html` — the original Three.js browser game version
- `trainer.py` — an existing Ursina Python game version
- `driverTrainer.py` — a new Python port matching the browser game behavior
- `vehicle.glb` — the vehicle model used by the Python game

## Requirements

- Python 3.8+ or newer
- `ursina` package

## Install

```bash
pip install ursina
```

## Run

```bash
python driverTrainer.py
```

## Controls

- `W/A/S/D` — move the vehicle
- `J/L` — rotate the vehicle
- `I/K` — raise/lower the cannon
- `Space` — fire the cannon
- `Ctrl+1`, `Ctrl+2`, `Ctrl+3` — switch camera POV
- `R` — restart after game over

## Notes

The new `driverTrainer.py` file is designed to look and work similarly to the browser-based version while using the Ursina engine for Python.
