"""Local control API + WebSocket status for the GUI (Command Nexus)."""

from __future__ import annotations

import asyncio
import subprocess
import sys
from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from trenchcoat import LEGAL_NOTICE, __version__
from trenchcoat.config.loader import ensure_chain, load_config, save_config
from trenchcoat.config.presets import list_presets
from trenchcoat.engine.router import CloakEngine


class ActivateBody(BaseModel):
    name: str = Field(..., description="Chain or preset name")


class CloakUpBody(BaseModel):
    chain: str | None = None
    wait_tor: float = 0.0
    accept_legal: bool = False


def create_app(engine_holder: dict[str, Any] | None = None) -> FastAPI:
    holder: dict[str, Any] = engine_holder if engine_holder is not None else {"engine": None}
    app = FastAPI(title="Trench Coat Control", version=__version__)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:8765",
            "http://localhost:8765",
            "http://127.0.0.1:8742",
            "http://localhost:8742",
            "null",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    async def health() -> dict[str, Any]:
        return {"ok": True, "version": __version__, "legal": LEGAL_NOTICE}

    @app.get("/api/status")
    async def status() -> dict[str, Any]:
        from trenchcoat.engine.status_bus import read_status
        from trenchcoat.engine.tor_detect import detect_tor, port_open

        engine: CloakEngine | None = holder.get("engine")
        if engine:
            return engine.status.to_dict()
        # Cross-process: trench up writes runtime_status.json
        bus = read_status(max_age_seconds=120.0)
        if bus and bus.get("running"):
            bus.setdefault("version", __version__)
            bus["source"] = "status_bus"
            return bus
        # Live probe fallback
        cfg = load_config()
        entry_up = port_open(cfg.listen_host, cfg.listen_port)
        tor = detect_tor()
        return {
            "running": entry_up,
            "version": __version__,
            "chain_name": cfg.active_chain,
            "listen": f"{cfg.listen_host}:{cfg.listen_port}" if entry_up else None,
            "proxy_chain": [tor.as_url()] if tor else [],
            # Probe fallback cannot know soft/hard KS state — do not lie.
            "kill_switch_active": False,
            "fail_closed_tripped": False,
            "refuse_direct": True,
            "source": "probe",
            "messages": (
                ["Cloak entry detected (live probe)."]
                if entry_up
                else ["No cloak process status yet — run trench up."]
            ),
        }

    @app.get("/api/presets")
    async def presets() -> list[dict[str, Any]]:
        return [
            {
                "name": p.name,
                "profile": p.profile.value,
                "description": p.description,
                "hops": len(p.hops),
                "tags": p.tags,
            }
            for p in list_presets()
        ]

    @app.get("/api/config")
    async def config_summary() -> dict[str, Any]:
        cfg = load_config()
        return {
            "active_chain": cfg.active_chain,
            "listen": f"{cfg.listen_host}:{cfg.listen_port}",
            "noir_mode": cfg.noir_mode,
            "chains": [c.name for c in cfg.chains],
            "accepted_legal_notice": cfg.accepted_legal_notice,
        }

    @app.get("/api/tor")
    async def tor_status() -> dict[str, Any]:
        from trenchcoat.engine.tor_detect import detect_tor

        ep = detect_tor()
        if not ep:
            return {"available": False}
        return {
            "available": True,
            "host": ep.host,
            "port": ep.port,
            "url": ep.as_url(),
            "label": ep.label(),
        }

    @app.get("/api/split")
    async def split_rules() -> dict[str, Any]:
        from trenchcoat.engine.split_tunnel import SplitTunnelEngine

        cfg = load_config()
        chain = cfg.get_chain()
        eng = SplitTunnelEngine(chain.split_tunnel if chain else [])
        return {"rules": eng.summarize()}

    @app.get("/api/plugins")
    async def plugins() -> dict[str, Any]:
        from trenchcoat.plugins.base import default_plugin_dir, load_plugins_from_dir

        reg = load_plugins_from_dir(default_plugin_dir())
        root = Path(__file__).resolve().parents[3] / "plugins"
        reg2 = load_plugins_from_dir(root)
        reg.obfuscators.update(reg2.obfuscators)
        return reg.list_plugins()

    @app.get("/api/identity")
    async def identity(via: str = "auto") -> dict[str, Any]:
        """Egress identity. via=auto|cloak|direct|hop"""
        from trenchcoat.engine.identity import check_identity
        from trenchcoat.engine.tor_detect import detect_tor, port_open

        cfg = load_config()
        proxies: list[str] | None = None
        if via != "direct":
            if via in ("auto", "cloak") and port_open(cfg.listen_host, cfg.listen_port):
                proxies = [f"socks5://{cfg.listen_host}:{cfg.listen_port}"]
            else:
                engine: CloakEngine | None = holder.get("engine")
                if engine:
                    proxies = engine.builder.proxy_urls() or None
                if not proxies:
                    ep = detect_tor()
                    if ep:
                        proxies = [ep.as_url()]
        report = await check_identity(proxies)
        return report.to_dict()

    @app.get("/api/doctor")
    async def doctor(identity: bool = False) -> dict[str, Any]:
        from trenchcoat.engine.self_test import run_self_test

        report = await run_self_test(include_identity=identity)
        return report.to_dict()

    @app.post("/api/legal/accept")
    async def legal_accept() -> dict[str, Any]:
        cfg = load_config()
        cfg.accepted_legal_notice = True
        save_config(cfg)
        return {"ok": True, "accepted_legal_notice": True}

    @app.post("/api/chain/activate")
    async def chain_activate(body: ActivateBody) -> dict[str, Any]:
        cfg = load_config()
        try:
            ensure_chain(cfg, body.name)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        cfg.active_chain = body.name
        save_config(cfg)
        return {"ok": True, "active_chain": body.name}

    @app.post("/api/tor/newnym")
    async def tor_newnym() -> dict[str, Any]:
        from trenchcoat.engine.tor_control import signal_newnym

        cfg = load_config()
        chain = cfg.get_chain()
        ctrl = 9051
        if chain:
            for hop in chain.hops:
                if hop.type.value == "tor":
                    ctrl = int(hop.options.get("control_port", 9051))
                    break
        ok, msg = await signal_newnym(port=ctrl)
        return {"ok": ok, "message": msg, "control_port": ctrl}

    @app.get("/api/sessions")
    async def sessions() -> dict[str, Any]:
        from trenchcoat.reporting.dossier import list_sessions

        return {"sessions": list_sessions()}

    @app.get("/api/sessions/{session_id}")
    async def session_detail(session_id: str) -> dict[str, Any]:
        from trenchcoat.reporting.dossier import load_session

        data = load_session(session_id)
        if not data:
            raise HTTPException(status_code=404, detail="Session not found")
        return data

    @app.post("/api/cloak/up")
    async def cloak_up(body: CloakUpBody) -> dict[str, Any]:
        """Engage cloak via subprocess (CLI owns data plane — avoids dual engines)."""
        cfg = load_config()
        if body.accept_legal:
            cfg.accepted_legal_notice = True
            save_config(cfg)
        if not cfg.accepted_legal_notice:
            raise HTTPException(
                status_code=403,
                detail="Legal notice not accepted. POST /api/legal/accept or pass accept_legal.",
            )
        chain = body.chain or cfg.active_chain
        cmd = [
            sys.executable,
            "-m",
            "trenchcoat",
            "up",
            "--accept-legal",
            "--wait-tor",
            str(body.wait_tor or 0),
        ]
        if chain:
            cmd.extend(["--chain", chain])
        # Non-blocking start in background so API returns; operator uses status bus.
        try:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=str(exc)) from exc
        return {
            "ok": True,
            "mode": "subprocess",
            "pid": proc.pid,
            "chain": chain,
            "message": "Cloak engage requested. Watch /api/status or status bus.",
        }

    @app.post("/api/cloak/down")
    async def cloak_down() -> dict[str, Any]:
        """Best-effort: if in-process engine, stop it; else advise operator."""
        engine: CloakEngine | None = holder.get("engine")
        if engine and engine.status.running:
            st = await engine.stop()
            holder["engine"] = None
            return {"ok": True, "mode": "in_process", "messages": st.messages}
        return {
            "ok": True,
            "mode": "hint",
            "message": "No in-process engine. Stop the trench up process (Ctrl+C) in its terminal.",
        }

    @app.websocket("/ws/status")
    async def ws_status(ws: WebSocket) -> None:
        await ws.accept()
        try:
            while True:
                # Reuse HTTP status resolver (in-process engine OR status bus OR probe)
                payload = await status()
                await ws.send_json(payload)
                await asyncio.sleep(1.0)
        except WebSocketDisconnect:
            return

    # Serve Command Nexus UI (prefer dist, fall back to source tree)
    repo_gui = Path(__file__).resolve().parents[3] / "gui" / "web"
    gui_dist = repo_gui / "dist"
    gui_root = gui_dist if gui_dist.exists() else repo_gui
    if gui_root.exists():
        # Mount assets under /src and / for static files; SPA index at /
        app.mount("/src", StaticFiles(directory=str(gui_root / "src")), name="gui-src")
        if (gui_root / "public").exists():
            app.mount("/public", StaticFiles(directory=str(gui_root / "public")), name="gui-public")

        @app.get("/")
        async def index() -> FileResponse:
            return FileResponse(gui_root / "index.html")

    return app
