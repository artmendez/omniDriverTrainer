# omniDriverTrainer

A Python port of the OmniDriver Trainer 3D perimeter driving and firing game.

This repository includes:
- `index.html` — the original Three.js browser game version
- `vehicle.glb` — the vehicle model used by the Python game

## Requirements

- Python 3.8+ or newer

## Install

- Extract the files into a folder.

## Run

- Open a terminal window at the folder's location.
- run a local web-server with `python -m http.server 8000` (loading external files will be blocked by the browser. The script needs to load the vehicle 3D model from a glbt file.)
- Open http://localhost:8000 to run the program. Fullscreen mode is advisable.


## Controls

- `W/A/S/D` — move the vehicle
- `J/L` — rotate the vehicle
- `I/K` — raise/lower the cannon
- `Space` — fire the cannon
- `Ctrl+1`, `Ctrl+2`, `Ctrl+3` — switch camera POV
- `R` — restart after game over

## Notes

- Much to be done... yes.
- The intention is to help potential drivers unlearn traditional driving control and train the brain for omnidirectional driving.