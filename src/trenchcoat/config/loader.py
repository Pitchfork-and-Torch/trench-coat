"""Load and persist Trench Coat configuration (YAML + encrypted optional)."""

from __future__ import annotations

import os
from pathlib import Path

import yaml
from platformdirs import user_config_dir, user_data_dir

from trenchcoat.config.models import AppConfig, ChainConfig
from trenchcoat.config.presets import get_preset, list_presets

APP_NAME = "trench-coat"
APP_AUTHOR = "trenchcoat"


def config_dir() -> Path:
    path = Path(user_config_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def data_dir() -> Path:
    path = Path(user_data_dir(APP_NAME, APP_AUTHOR))
    path.mkdir(parents=True, exist_ok=True)
    return path


def default_config_path() -> Path:
    override = os.environ.get("TRENCH_COAT_CONFIG")
    if override:
        return Path(override)
    return config_dir() / "config.yaml"


def default_app_config() -> AppConfig:
    chains = [p.model_copy(deep=True) for p in list_presets()]
    # Casual Shadow (Tor-only) is the safest default for first-run MVP
    return AppConfig(
        active_chain="casual-shadow",
        chains=chains,
        accepted_legal_notice=False,
        noir_mode=True,
    )


def load_config(path: Path | None = None) -> AppConfig:
    cfg_path = path or default_config_path()
    if not cfg_path.exists():
        cfg = default_app_config()
        save_config(cfg, cfg_path)
        return cfg
    raw = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
    return AppConfig.model_validate(raw)


def save_config(config: AppConfig, path: Path | None = None) -> Path:
    cfg_path = path or default_config_path()
    cfg_path.parent.mkdir(parents=True, exist_ok=True)
    data = config.model_dump(mode="json")
    cfg_path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return cfg_path


def ensure_chain(config: AppConfig, name: str) -> ChainConfig:
    chain = config.get_chain(name)
    if chain:
        return chain
    try:
        chain = get_preset(name)
    except KeyError as exc:
        raise ValueError(str(exc)) from exc
    config.chains.append(chain)
    return chain
