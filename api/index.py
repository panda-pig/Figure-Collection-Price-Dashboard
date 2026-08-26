"""Vercel entry point.

The `app` import is the WSGI handle Vercel serves; it must stay re-exported
even though nothing in this module references it.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app import app  # noqa: E402,F401

__all__ = ["app"]
