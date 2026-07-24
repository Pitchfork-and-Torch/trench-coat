# Trench Coat plugins (API v1)

Drop `.py` files here or in `src/trenchcoat/plugins/examples/`.

Each plugin exposes `plugin` or `class Plugin` with:

```python
def register(registry):
    registry.add_obfuscator("name", factory)
    registry.add_hop_driver("name", factory)
    registry.add_hook("on_engage", fn)
```

Load:

```bash
trench plugins list
```

See `src/trenchcoat/plugins/examples/pad_obfuscator.py`.
