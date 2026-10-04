#!/usr/bin/env python3
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from src.core import run
if __name__ == "__main__":
    raise SystemExit(run())
