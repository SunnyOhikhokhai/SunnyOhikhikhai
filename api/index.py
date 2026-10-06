"""Vercel entry point: serves the NIMPA FastAPI backend as a Python function.

vercel.json routes /api/*, /uploads/* and /sitemap.xml here; everything else is
the built website (frontend/dist).
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402,F401
