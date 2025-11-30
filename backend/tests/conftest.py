import sys
import pathlib

# Ensure backend package is importable when running tests from repo root or backend/
ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))
