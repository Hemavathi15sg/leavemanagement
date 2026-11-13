import sys
from pathlib import Path

# Make the repo root importable (app.py, src.leave) when pytest runs from anywhere.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
