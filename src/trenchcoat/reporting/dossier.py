"""Encrypted-ready session logging and HTML dossier export."""

from __future__ import annotations

import html
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path

from trenchcoat.config.loader import data_dir


@dataclass
class SessionEvent:
    ts: float
    kind: str
    message: str
    data: dict = field(default_factory=dict)


@dataclass
class SessionLog:
    session_id: str
    started_at: float
    events: list[SessionEvent] = field(default_factory=list)
    ended_at: float | None = None

    def add(self, kind: str, message: str, **data: object) -> None:
        self.events.append(
            SessionEvent(ts=time.time(), kind=kind, message=message, data=dict(data))
        )

    def close(self) -> None:
        self.ended_at = time.time()

    def save_json(self, path: Path | None = None) -> Path:
        out = path or (data_dir() / "sessions" / f"{self.session_id}.json")
        out.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "session_id": self.session_id,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "events": [asdict(e) for e in self.events],
        }
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return out

    def export_html(self, path: Path | None = None) -> Path:
        out = path or (data_dir() / "sessions" / f"{self.session_id}.html")
        out.parent.mkdir(parents=True, exist_ok=True)
        rows = []
        for e in self.events:
            rows.append(
                "<tr>"
                f"<td>{time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(e.ts))}</td>"
                f"<td class='kind'>{html.escape(e.kind)}</td>"
                f"<td>{html.escape(e.message)}</td>"
                "</tr>"
            )
        doc = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>CLASSIFIED DOSSIER — {html.escape(self.session_id)}</title>
<style>
  body {{ background:#0a0a0f; color:#c8facc; font-family: ui-monospace, Consolas, monospace;
         margin:0; padding:2rem; }}
  h1 {{ color:#00FF9F; text-shadow:0 0 12px #00FF9F88; letter-spacing:.12em; }}
  .stamp {{ color:#FF00AA; border:2px solid #FF00AA; display:inline-block;
            padding:.25rem .75rem; transform:rotate(-6deg); margin-bottom:1rem; }}
  table {{ width:100%; border-collapse:collapse; margin-top:1.5rem; }}
  th, td {{ border-bottom:1px solid #1f2a24; padding:.6rem .4rem; text-align:left; }}
  th {{ color:#FF00AA; }}
  .kind {{ color:#00FF9F; }}
  footer {{ margin-top:2rem; opacity:.6; font-size:.85rem; }}
</style>
</head>
<body>
  <div class="stamp">CLASSIFIED // LOCAL ONLY</div>
  <h1>TRENCH COAT DOSSIER</h1>
  <p>Session: <strong>{html.escape(self.session_id)}</strong></p>
  <p>Started: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(self.started_at))}</p>
  <table>
    <thead><tr><th>TIME</th><th>EVENT</th><th>NOTE</th></tr></thead>
    <tbody>
      {''.join(rows)}
    </tbody>
  </table>
  <footer>Encrypted storage optional via config.encrypt_logs — never leave dossiers on shared machines.</footer>
</body>
</html>
"""
        out.write_text(doc, encoding="utf-8")
        return out


def new_session() -> SessionLog:
    sid = time.strftime("%Y%m%d-%H%M%S")
    return SessionLog(session_id=sid, started_at=time.time())


def sessions_dir() -> Path:
    path = data_dir() / "sessions"
    path.mkdir(parents=True, exist_ok=True)
    return path


def list_sessions() -> list[dict]:
    """List saved session JSON dossiers (newest first)."""
    root = sessions_dir()
    items: list[dict] = []
    for path in sorted(root.glob("*.json"), reverse=True):
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            items.append(
                {
                    "session_id": data.get("session_id", path.stem),
                    "started_at": data.get("started_at"),
                    "ended_at": data.get("ended_at"),
                    "events": len(data.get("events") or []),
                    "path": str(path),
                    "html_path": str(path.with_suffix(".html"))
                    if path.with_suffix(".html").exists()
                    else None,
                }
            )
        except Exception:  # noqa: BLE001
            items.append({"session_id": path.stem, "path": str(path), "error": "unreadable"})
    return items


def load_session(session_id: str) -> dict | None:
    path = sessions_dir() / f"{session_id}.json"
    if not path.is_file():
        # allow bare stem lookup
        matches = list(sessions_dir().glob(f"{session_id}*.json"))
        if not matches:
            return None
        path = matches[0]
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None
