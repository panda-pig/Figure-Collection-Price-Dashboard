from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

# Captured before any monkeypatching so the Postgres CI job can point the whole
# suite at a real server; without it each test gets its own SQLite file.
TARGET_DATABASE_URL = os.environ.get("DATABASE_URL")


def load_app(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, **env: str):
    """Import a fresh app module against a clean, freshly seeded database."""
    monkeypatch.delenv("VERCEL", raising=False)
    monkeypatch.delenv("FIGURE_DASHBOARD_TOKEN", raising=False)

    if TARGET_DATABASE_URL:
        monkeypatch.setenv("DATABASE_URL", TARGET_DATABASE_URL)
    else:
        monkeypatch.delenv("DATABASE_URL", raising=False)
        monkeypatch.setenv("FIGURE_DASHBOARD_DB", str(tmp_path / "test.db"))

    for key, value in env.items():
        monkeypatch.setenv(key, value)

    sys.modules.pop("app", None)
    module = importlib.import_module("app")
    # Start every test from the seed set, whichever backend is in play.
    module.init_database(seed=True, reset=True)
    module._schema_ready = True
    return module


@pytest.fixture
def app_module(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    return load_app(tmp_path, monkeypatch)


@pytest.fixture
def client(app_module):
    return app_module.app.test_client()
