"""Keep package, pyproject, and CLI --version on the same stamp."""

from __future__ import annotations

import tomllib
from pathlib import Path

from click.testing import CliRunner

from trenchcoat import __codename__, __version__
from trenchcoat.cli import main

ROOT = Path(__file__).resolve().parents[1]


def test_pyproject_version_matches_package() -> None:
    data = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == __version__
    assert __version__ == "1.2.1"
    assert "CIRCUIT" in __codename__.upper()


def test_cli_version_option() -> None:
    result = CliRunner().invoke(main, ["--version"])
    assert result.exit_code == 0
    assert __version__ in result.output
    assert "trench" in result.output.lower()


def test_public_copy_stamps_match_package() -> None:
    landing = (ROOT / "landing" / "index.html").read_text(encoding="utf-8")
    assert f'"softwareVersion": "{__version__}"' in landing
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert __version__ in readme
    nexus = (ROOT / "gui" / "web" / "index.html").read_text(encoding="utf-8")
    assert __version__ in nexus
    llms = (ROOT / "landing" / "llms.txt").read_text(encoding="utf-8")
    assert __version__ in llms
