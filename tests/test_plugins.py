from trenchcoat.plugins.base import default_plugin_dir, load_plugins_from_dir


def test_load_example_plugins():
    reg = load_plugins_from_dir(default_plugin_dir())
    assert "pad" in reg.obfuscators
    pad = reg.obfuscators["pad"](pad_size=4)
    wrapped = pad.wrap(b"hi")
    assert len(wrapped) == 6
    assert pad.unwrap(wrapped) == b"hi"
