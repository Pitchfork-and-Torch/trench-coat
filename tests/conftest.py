"""Shared pytest fixtures."""

from __future__ import annotations

import pytest

from trenchcoat.engine.status_bus import release_owner


@pytest.fixture
def isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("TRENCH_COAT_CONFIG", str(tmp_path / "config.yaml"))
    monkeypatch.setattr("trenchcoat.config.loader.data_dir", lambda: tmp_path)
    monkeypatch.setattr("trenchcoat.engine.status_bus.data_dir", lambda: tmp_path)
    release_owner()
    yield tmp_path
    release_owner()
