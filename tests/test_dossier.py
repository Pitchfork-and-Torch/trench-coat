from pathlib import Path

from trenchcoat.reporting.dossier import new_session


def test_session_export(tmp_path: Path):
    s = new_session()
    s.add("engage", "test")
    s.close()
    j = s.save_json(tmp_path / "s.json")
    h = s.export_html(tmp_path / "s.html")
    assert j.exists()
    assert "test" in h.read_text(encoding="utf-8")
    assert "CLASSIFIED" in h.read_text(encoding="utf-8")
