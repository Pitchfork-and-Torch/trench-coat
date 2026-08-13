"""Plugin API v1 — custom obfuscators and hop drivers (Phase 3)."""

from __future__ import annotations

import abc
import importlib.util
import logging
from pathlib import Path
from typing import Any, Callable

log = logging.getLogger("trenchcoat.plugins")

PLUGIN_API_VERSION = 1


class TrenchPlugin(abc.ABC):
    """Implement register() and set name/version."""

    name: str = "unnamed"
    version: str = "0.0.0"
    api_version: int = PLUGIN_API_VERSION

    @abc.abstractmethod
    def register(self, registry: "PluginRegistry") -> None:
        ...


class PluginRegistry:
    def __init__(self) -> None:
        self.obfuscators: dict[str, Callable[..., Any]] = {}
        self.hop_drivers: dict[str, Callable[..., Any]] = {}
        self.hooks: dict[str, list[Callable[..., Any]]] = {
            "on_engage": [],
            "on_disengage": [],
            "on_rotate": [],
        }

    def add_obfuscator(self, name: str, factory: Callable[..., Any]) -> None:
        self.obfuscators[name] = factory
        log.info("registered obfuscator plugin: %s", name)

    def add_hop_driver(self, name: str, factory: Callable[..., Any]) -> None:
        self.hop_drivers[name] = factory
        log.info("registered hop driver plugin: %s", name)

    def add_hook(self, event: str, fn: Callable[..., Any]) -> None:
        self.hooks.setdefault(event, []).append(fn)

    def list_plugins(self) -> dict[str, list[str]]:
        return {
            "obfuscators": sorted(self.obfuscators),
            "hop_drivers": sorted(self.hop_drivers),
            "hooks": sorted(self.hooks),
        }


def load_plugins_from_dir(directory: Path) -> PluginRegistry:
    registry = PluginRegistry()
    if not directory.exists():
        return registry
    for path in sorted(directory.glob("*.py")):
        if path.name.startswith("_"):
            continue
        mod_name = f"trenchcoat_plugin_{path.stem}"
        try:
            spec = importlib.util.spec_from_file_location(mod_name, path)
            if not spec or not spec.loader:
                continue
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            plugin = getattr(module, "plugin", None)
            if plugin is None and hasattr(module, "Plugin"):
                plugin = module.Plugin()
            if plugin and hasattr(plugin, "register"):
                plugin.register(registry)
        except Exception as exc:  # noqa: BLE001
            log.warning("failed to load plugin %s: %s", path, exc)
    return registry


def default_plugin_dir() -> Path:
    return Path(__file__).resolve().parent / "examples"

