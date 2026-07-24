"""Example obfuscator plugin — payload padding (demo only, not crypto)."""

from __future__ import annotations

import os

from trenchcoat.plugins.base import PluginRegistry, TrenchPlugin


class PadObfuscator:
    """Prepend random pad bytes to illustrate plugin wiring (not for production crypto)."""

    def __init__(self, pad_size: int = 16) -> None:
        self.pad_size = pad_size

    def wrap(self, data: bytes) -> bytes:
        return os.urandom(self.pad_size) + data

    def unwrap(self, data: bytes) -> bytes:
        return data[self.pad_size :]


class Plugin(TrenchPlugin):
    name = "pad-obfuscator"
    version = "1.0.0"

    def register(self, registry: PluginRegistry) -> None:
        registry.add_obfuscator("pad", lambda **kw: PadObfuscator(**kw))
        registry.add_hook("on_engage", lambda **_: None)


plugin = Plugin()
