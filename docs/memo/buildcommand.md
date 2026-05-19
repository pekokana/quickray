# Quickray ⚡

Fast Spotlight-like launcher for Windows.

## Run command
uv run quickray


## Build command
uv run pyinstaller --noconsole --onedir src/quickray/main.py --name quickray

uv run pyinstaller ^
  --noconsole ^
  --onedir ^
  --noupx ^
  --name quickray ^
  src/quickray/main.py

uv run pyinstaller ^
  --noconsole ^
  --onedir ^
  --noupx ^
  --collect-all PyQt6 ^
  --add-data "src/quickray/icon.png;quickray" ^
  --name quickray ^
  src/quickray/main.py



## icon build command
uv run python tools/build_icon.py
