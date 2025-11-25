import sys
from pathlib import Path

BACKEND_ROOT = Path(__file__).resolve().parents[1]
BACKEND_PARENT = BACKEND_ROOT

if str(BACKEND_PARENT) not in sys.path:
    sys.path.insert(0, str(BACKEND_PARENT))
