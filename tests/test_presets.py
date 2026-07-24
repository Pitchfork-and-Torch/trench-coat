from trenchcoat.config.presets import get_preset, list_presets
from trenchcoat.config.models import AppConfig
from trenchcoat.config.loader import default_app_config


def test_all_presets_load():
    presets = list_presets()
    assert len(presets) >= 5
    names = {p.name for p in presets}
    assert "ghost" in names
    assert "paranoid" in names


def test_preset_copy_isolated():
    a = get_preset("ghost")
    b = get_preset("ghost")
    a.hops[0].host = "10.0.0.1"
    assert b.hops[0].host != "10.0.0.1"


def test_default_app_config():
    cfg = default_app_config()
    assert isinstance(cfg, AppConfig)
    assert cfg.active_chain == "casual-shadow"
    assert cfg.get_chain("casual-shadow") is not None


def test_chain_hop_unique_ids():
    chain = get_preset("whistleblower")
    ids = [h.id for h in chain.hops]
    assert len(ids) == len(set(ids))
