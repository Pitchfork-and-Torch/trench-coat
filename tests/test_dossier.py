from pathlib import Path

from trenchcoat.reporting.dossier import load_session, new_session


def test_session_export(tmp_path: Path):
    s = new_session()
    s.add("engage", "test")
    s.close()
    j = s.save_json(tmp_path / "s.json")
    h = s.export_html(tmp_path / "s.html")
    assert j.exists()
    assert "test" in h.read_text(encoding="utf-8")
    assert "CLASSIFIED" in h.read_text(encoding="utf-8")


def test_load_session_allowlist(tmp_path, monkeypatch):
    monkeypatch.setattr("trenchcoat.reporting.dossier.sessions_dir", lambda: tmp_path)
    (tmp_path / "ok_1.json").write_text('{"session_id": "ok_1"}', encoding="utf-8")
    (tmp_path / "ok_1-extra.json").write_text('{"session_id": "extra"}', encoding="utf-8")
    loaded = load_session("ok_1")
    assert loaded is not None
    assert loaded["session_id"] == "ok_1"
    assert load_session("ok") is None
    assert load_session("ok_1*") is None
    assert load_session("../ok_1") is None
    assert load_session("ok_1/../../etc") is None
    assert load_session("") is None
