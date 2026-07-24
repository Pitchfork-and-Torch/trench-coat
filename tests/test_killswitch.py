"""Phase 6 Iron Collar — hard kill-switch safety paths (no admin required)."""

from __future__ import annotations

from pathlib import Path

from trenchcoat.engine.killswitch import RULE_PREFIX, KillSwitch


def test_soft_arm_messages():
    st = KillSwitch(strict=False).arm(allow_uid_ports=[1080])
    assert st.active is True
    assert any("Soft kill-switch" in m for m in st.messages)
    assert st.hard_enabled is False


def test_hard_dry_run_writes_undo(tmp_path: Path):
    st = KillSwitch(strict=True).arm_hard(
        [1080, 9050], confirm=False, dry_run=True, undo_dir=tmp_path / "ks"
    )
    assert st.hard_enabled is False
    assert st.undo_script is not None
    undo = Path(st.undo_script)
    assert undo.exists()
    text = undo.read_text(encoding="utf-8")
    assert RULE_PREFIX in text or "trenchcoat" in text.lower() or "Undo" in text or "undo" in text
    assert any("Dry-run" in m for m in st.messages)


def test_hard_requires_confirm(tmp_path: Path):
    st = KillSwitch().arm_hard([1080], confirm=False, dry_run=False, undo_dir=tmp_path)
    assert st.hard_enabled is False
    assert any("NOT applied" in m or "confirm" in m.lower() for m in st.messages)


def test_emit_hard_bundle(tmp_path: Path):
    paths = KillSwitch().emit_hard_bundle(tmp_path, allow_ports=[1080])
    names = {p.name for p in paths}
    assert "windows-hard-killswitch.ps1" in names
    assert "windows-hard-killswitch-undo.ps1" in names
    assert "linux-hard-killswitch.nft" in names
    assert "macos-hard-killswitch.pf" in names
    win = (tmp_path / "windows-hard-killswitch.ps1").read_text(encoding="utf-8")
    assert RULE_PREFIX in win
    assert "1080" in win
    nft = (tmp_path / "linux-hard-killswitch.nft").read_text(encoding="utf-8")
    assert "trenchcoat_hard" in nft
