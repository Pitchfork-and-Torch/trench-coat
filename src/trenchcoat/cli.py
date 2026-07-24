"""Trench Coat CLI — the coat's first button is always a terminal."""

from __future__ import annotations

import asyncio
import logging
import sys
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from trenchcoat import LEGAL_NOTICE, __codename__, __version__
from trenchcoat.config.loader import (
    default_config_path,
    ensure_chain,
    load_config,
    save_config,
)
from trenchcoat.config.presets import list_presets
from trenchcoat.engine.router import CloakEngine
from trenchcoat.noir.narration import say
from trenchcoat.reporting.dossier import new_session

console = Console()


BANNER = r"""
[bold #00FF9F]
████████╗██████╗ ███████╗███╗   ██╗ ██████╗██╗  ██╗
╚══██╔══╝██╔══██╗██╔════╝████╗  ██║██╔════╝██║  ██║
   ██║   ██████╔╝█████╗  ██╔██╗ ██║██║     ███████║
   ██║   ██╔══██╗██╔══╝  ██║╚██╗██║██║     ██╔══██║
   ██║   ██║  ██║███████╗██║ ╚████║╚██████╗██║  ██║
   ╚═╝   ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝ ╚═════╝╚═╝  ╚═╝
[/][bold #FF00AA]  ██████╗ ██████╗  █████╗ ████████╗[/]
[bold #FF00AA] ██╔════╝██╔═══██╗██╔══██╗╚══██╔══╝[/]
[bold #FF00AA] ██║     ██║   ██║███████║   ██║   [/]
[bold #FF00AA] ██║     ██║   ██║██╔══██║   ██║   [/]
[bold #FF00AA] ╚██████╗╚██████╔╝██║  ██║   ██║   [/]
[bold #FF00AA]  ╚═════╝ ╚═════╝ ╚═╝  ╚═╝   ╚═╝   [/]
[dim]  digital invisibility cloak  ·  {version}  ·  {codename}[/]
[bold #9B59B6]  THE SHADOWS ARE YOUR ALLY[/]
"""


def _setup_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )


def _print_banner(noir: bool = True) -> None:
    console.print(BANNER.format(version=__version__, codename=__codename__))
    if noir:
        console.print(Panel(say("boot"), border_style="#00FF9F", title="NOIR"))


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(__version__, prog_name="trench")
@click.option("--verbose", "-v", is_flag=True, help="Debug logging.")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Trench Coat — multi-hop privacy cloak (legal use only)."""
    ctx.ensure_object(dict)
    _setup_logging("DEBUG" if verbose else "INFO")
    ctx.obj["verbose"] = verbose


@main.command("legal")
def legal_cmd() -> None:
    """Show the legal notice. Read it. Mean it."""
    console.print(Panel(LEGAL_NOTICE, title="LEGAL", border_style="#FF00AA"))
    console.print(say("legal"))


@main.command("banner")
def banner_cmd() -> None:
    """Print the neon banner."""
    _print_banner(True)


@main.group("chain")
def chain_group() -> None:
    """Build, inspect, and run multi-hop chains."""


@chain_group.command("list")
def chain_list() -> None:
    """List configured chains and built-in profiles."""
    cfg = load_config()
    table = Table(title="Configured Chains", border_style="#00FF9F")
    table.add_column("Name", style="#00FF9F")
    table.add_column("Profile", style="#FF00AA")
    table.add_column("Hops")
    table.add_column("Active")
    for c in cfg.chains:
        table.add_row(
            c.name,
            c.profile.value,
            str(len(c.hops)),
            "★" if c.name == cfg.active_chain else "",
        )
    console.print(table)
    console.print("\n[bold]Built-in presets:[/]")
    for p in list_presets():
        console.print(f"  [cyan]{p.name}[/] — {p.description}")


@chain_group.command("show")
@click.argument("name", required=False)
def chain_show(name: Optional[str]) -> None:
    """Show hop layout for a chain."""
    cfg = load_config()
    chain = cfg.get_chain(name)
    if not chain:
        console.print(f"[red]Chain not found: {name or cfg.active_chain}[/]")
        sys.exit(1)
    table = Table(title=f"Chain: {chain.name}", border_style="#9B59B6")
    table.add_column("#")
    table.add_column("ID", style="#00FF9F")
    table.add_column("Type", style="#FF00AA")
    table.add_column("Endpoint")
    table.add_column("Enabled")
    table.add_column("Label")
    for i, h in enumerate(chain.hops, 1):
        table.add_row(
            str(i),
            h.id,
            h.type.value,
            h.endpoint(),
            "yes" if h.enabled else "no",
            h.label or "",
        )
    console.print(table)
    console.print(f"Policy: kill_switch={chain.policy.kill_switch} "
                  f"rotation={chain.policy.rotation_minutes}m "
                  f"min_hops={chain.policy.min_hops}")


@chain_group.command("new")
@click.option("--hops", "hop_count", default=3, show_default=True, help="Desired hop count hint.")
@click.option(
    "--profile",
    type=click.Choice(
        ["ghost", "journalist", "whistleblower", "casual-shadow", "paranoid"],
        case_sensitive=False,
    ),
    default="paranoid",
    show_default=True,
)
@click.option("--name", default=None, help="Chain name (default: profile name).")
@click.option("--activate/--no-activate", default=True, help="Set as active chain.")
def chain_new(hop_count: int, profile: str, name: Optional[str], activate: bool) -> None:
    """Create a chain from a profile preset.

    Example: trench chain new --hops 5 --profile paranoid
    """
    cfg = load_config()
    chain = ensure_chain(cfg, profile)
    if name and name != chain.name:
        chain = chain.model_copy(deep=True)
        chain.name = name
        # replace or append
        cfg.chains = [c for c in cfg.chains if c.name != name]
        cfg.chains.append(chain)
    chain.policy.max_hops = max(hop_count, chain.policy.min_hops)
    if activate:
        cfg.active_chain = chain.name
    path = save_config(cfg)
    console.print(
        Panel(
            f"Chain [bold]{chain.name}[/] ready ({chain.profile.value}).\n"
            f"Hops configured: {len(chain.hops)} (target capacity {hop_count}).\n"
            f"Saved → {path}\n\n"
            f"[dim]Edit hop host/port in config for your real proxies.[/]",
            title="CHAIN FORGED",
            border_style="#00FF9F",
        )
    )
    console.print(say("engage"))


@chain_group.command("use")
@click.argument("name")
def chain_use(name: str) -> None:
    """Set the active chain."""
    cfg = load_config()
    if not cfg.get_chain(name):
        try:
            ensure_chain(cfg, name)
        except ValueError as exc:
            console.print(f"[red]{exc}[/]")
            sys.exit(1)
    cfg.active_chain = name
    save_config(cfg)
    console.print(f"Active chain → [bold #00FF9F]{name}[/]")


@main.command("up")
@click.option("--chain", "chain_name", default=None, help="Chain to engage.")
@click.option("--accept-legal", is_flag=True, help="Acknowledge legal notice for this machine.")
@click.option("--foreground/--background-hint", default=True, help="Run in foreground.")
@click.option(
    "--auto-tor/--no-auto-tor",
    default=True,
    show_default=True,
    help="Detect local Tor (9050/9150) and bind tor hops automatically.",
)
@click.option(
    "--wait-tor",
    type=float,
    default=0.0,
    show_default=True,
    help="Seconds to wait for Tor SOCKS before fail-closed (0 = no wait).",
)
def up_cmd(
    chain_name: Optional[str],
    accept_legal: bool,
    foreground: bool,
    auto_tor: bool,
    wait_tor: float,
) -> None:
    """Engage the cloak (start local SOCKS entry + health/rotation)."""
    from trenchcoat.engine.tor_detect import bind_chain_to_tor, detect_tor, wait_for_tor

    _ = foreground
    _print_banner(True)
    cfg = load_config()
    if accept_legal:
        cfg.accepted_legal_notice = True
        save_config(cfg)
    if not cfg.accepted_legal_notice:
        console.print(Panel(LEGAL_NOTICE, title="LEGAL NOTICE", border_style="red"))
        console.print("[yellow]Re-run with --accept-legal after you understand the terms.[/]")
        sys.exit(2)

    name = chain_name or cfg.active_chain
    chain = cfg.get_chain(name)
    if not chain:
        console.print(f"[red]No chain: {name}[/]")
        sys.exit(1)

    session = new_session()
    session.add("engage", f"Starting chain {chain.name}", profile=chain.profile.value)

    async def _run() -> None:
        if auto_tor:
            ep = detect_tor()
            if not ep and wait_tor > 0:
                console.print(f"[dim]Waiting up to {wait_tor:.0f}s for Tor SOCKS…[/]")
                ep = await wait_for_tor(timeout=wait_tor)
            if ep:
                n = bind_chain_to_tor(chain.hops, ep)
                console.print(f"[#00FF9F]•[/] Auto-Tor: {ep.label()} (rewrote {n} hop(s))")
            else:
                console.print(
                    "[yellow]•[/] No Tor SOCKS on 9050/9150. "
                    "Start Tor (`scripts/start-tor.ps1` or Tor Browser) or configure hops."
                )

        engine = CloakEngine(cfg, chain)
        status = await engine.start()
        for m in status.messages:
            console.print(f"[cyan]•[/] {m}")
        if status.snapshot:
            table = Table(title="Hop Health", border_style="#FF00AA")
            table.add_column("Hop")
            table.add_column("Status")
            table.add_column("Latency")
            table.add_column("Error")
            for h in status.snapshot.hops:
                color = {
                    "healthy": "green",
                    "degraded": "yellow",
                    "dead": "red",
                    "unknown": "dim",
                }.get(h.health.value, "white")
                table.add_row(
                    h.hop_id,
                    f"[{color}]{h.health.value}[/]",
                    f"{h.latency_ms} ms" if h.latency_ms is not None else "—",
                    h.error or "",
                )
            console.print(table)

        if not status.running:
            console.print("[red]Cloak failed to engage (fail-closed).[/]")
            session.add("error", "fail-closed")
            session.close()
            session.save_json()
            return

        console.print(
            Panel(
                f"SOCKS5 entry: [bold #00FF9F]socks5://{status.listen}[/]\n"
                f"Chain: {' → '.join(status.proxy_chain) or '(none)'}\n\n"
                f"{say('engage')}\n\n"
                "[dim]Ctrl+C to disengage.[/]",
                title="CLOAK ENGAGED",
                border_style="#00FF9F",
            )
        )
        session.add("up", f"listening {status.listen}")
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            pass
        finally:
            await engine.stop()
            session.add("down", "disengaged")
            session.close()
            path = session.save_json()
            html_path = session.export_html()
            console.print(say("disengage"))
            console.print(f"Dossier: {path}")
            console.print(f"HTML:    {html_path}")

    try:
        asyncio.run(_run())
    except KeyboardInterrupt:
        console.print("\n[dim]Interrupt — hanging up the coat…[/]")


@main.command("doctor")
@click.option("--json", "as_json", is_flag=True, help="Machine-readable self-test report.")
@click.option(
    "--no-identity",
    is_flag=True,
    help="Skip live egress identity probe (faster offline doctor).",
)
def doctor_cmd(as_json: bool, no_identity: bool) -> None:
    """Self-test: Tor, hops, fail-closed policy, entry, DNS, isolation matrix.

    Exit codes: 0 = pass, 1 = warnings only, 2 = failures (do not trust yet).
    """
    from trenchcoat.engine.self_test import run_self_test

    _print_banner(False)

    async def _run() -> int:
        report = await run_self_test(include_identity=not no_identity)
        if as_json:
            import json

            console.print_json(json.dumps(report.to_dict()))
            return report.exit_code

        console.print(Panel(LEGAL_NOTICE, border_style="dim", title="legal"))
        table = Table(title="Doctor — Self-Test", border_style="#00FF9F")
        table.add_column("Status", width=6)
        table.add_column("Check")
        table.add_column("Detail")
        marks = {"pass": "[#00FF9F]✓[/]", "warn": "[yellow]![/]", "fail": "[red]✗[/]", "info": "[dim]·[/]"}
        for c in report.checks:
            table.add_row(marks.get(c.status, "·"), c.title, c.detail)
        console.print(table)
        style = "#00FF9F" if report.exit_code == 0 else ("yellow" if report.exit_code == 1 else "red")
        console.print(f"[{style}]{report.summary}[/]")
        console.print(f"\n[dim]Config: {default_config_path()} · exit={report.exit_code}[/]")
        return report.exit_code

    code = asyncio.run(_run())
    sys.exit(code)


@main.command("first-run")
@click.option("--accept-legal", is_flag=True, help="Acknowledge legal notice (required).")
@click.option(
    "--profile",
    "profile_name",
    default="casual-shadow",
    show_default=True,
    help="Preset/chain to activate (casual-shadow recommended).",
)
@click.option("--skip-doctor", is_flag=True, help="Skip self-test at end of wizard.")
def first_run_cmd(accept_legal: bool, profile_name: str, skip_doctor: bool) -> None:
    """First-run wizard: legal → Tor detect → profile → doctor → next steps.

    Goal: careful operators go from zero to verified confidence quickly.
    """
    from trenchcoat.engine.tor_detect import detect_tor
    from trenchcoat.engine.self_test import run_self_test

    _print_banner(True)
    console.print(Panel(LEGAL_NOTICE, title="LEGAL NOTICE", border_style="#FF00AA"))

    cfg = load_config()
    if not accept_legal and not cfg.accepted_legal_notice:
        console.print(
            "[yellow]Re-run with --accept-legal after you understand the terms.[/]\n"
            "  [dim]trench first-run --accept-legal[/]"
        )
        sys.exit(2)

    if accept_legal:
        cfg.accepted_legal_notice = True

    # Activate profile / chain
    try:
        ensure_chain(cfg, profile_name)
        cfg.active_chain = profile_name
    except ValueError as exc:
        console.print(f"[red]{exc}[/]")
        sys.exit(1)
    save_config(cfg)
    console.print(f"[#00FF9F]✓[/] Legal accepted · active chain → [bold]{profile_name}[/]")

    tor = detect_tor()
    if tor:
        console.print(f"[#00FF9F]✓[/] Tor detected: {tor.label()}")
    else:
        console.print(
            "[yellow]![/] No Tor on 9050/9150. Start Tor Browser or system Tor, then:\n"
            "  [dim]trench tor status · scripts/start-tor.ps1 or start-tor.sh[/]"
        )

    if not skip_doctor:
        console.print("\n[bold]Running self-test…[/]")
        report = asyncio.run(run_self_test(cfg, include_identity=False))
        marks = {"pass": "✓", "warn": "!", "fail": "✗", "info": "·"}
        for c in report.checks:
            if c.status in ("fail", "warn", "pass") and c.id in (
                "legal",
                "tor",
                "chain",
                "fail_closed_policy",
                "live_urls",
                "entry",
                "platform_isolation",
            ):
                console.print(f"  {marks.get(c.status, '·')} {c.title}: {c.detail}")
        console.print(f"\n{report.summary}")

    console.print(
        Panel(
            "[bold]Next steps[/]\n"
            "1. Start Tor if needed (9050/9150)\n"
            "2. [cyan]trench up --accept-legal --wait-tor 60[/]\n"
            "3. [cyan]trench check-ip[/]  → expect IsTor true\n"
            "4. Point apps at [bold]socks5://127.0.0.1:1080[/]\n"
            "5. Optional GUI: [cyan]trench gui[/] → http://127.0.0.1:8742\n"
            "\n"
            "[dim]Threat model: multi-hop hides you from local observers toward the exit;\n"
            "it does not replace Tor Browser isolation or secure endpoints.[/]",
            title="FIRST-RUN COMPLETE",
            border_style="#00FF9F",
        )
    )


@main.command("check-ip")
@click.option("--via-cloak/--direct", default=True, help="Use active chain egress hop or direct.")
def check_ip_cmd(via_cloak: bool) -> None:
    """Show public IP and whether Tor Project sees you as Tor."""
    from trenchcoat.engine.identity import check_identity
    from trenchcoat.engine.tor_detect import bind_chain_to_tor, detect_tor

    cfg = load_config()
    chain = cfg.get_chain()

    async def _run() -> None:
        proxies: list[str] = []
        if via_cloak and chain:
            ep = detect_tor()
            if ep:
                bind_chain_to_tor(chain.hops, ep)
            engine = CloakEngine(cfg, chain)
            await engine.builder.build()
            proxies = engine.builder.proxy_urls()
            # Prefer cloak entry if already up
            from trenchcoat.engine.tor_detect import port_open

            if port_open(cfg.listen_host, cfg.listen_port):
                proxies = [f"socks5://{cfg.listen_host}:{cfg.listen_port}"]
        report = await check_identity(proxies or None)
        title = "EGRESS IDENTITY"
        if report.is_tor is True:
            style = "#00FF9F"
            verdict = "TOR EXIT — shadows confirmed"
        elif report.is_tor is False:
            style = "#FF00AA"
            verdict = "NOT TOR — clearnet face"
        else:
            style = "yellow"
            verdict = "UNKNOWN (check failed or partial)"
        body = (
            f"[bold]{verdict}[/]\n"
            f"IP: {report.ip or '—'}\n"
            f"Via: {report.via_proxy or 'direct'}\n"
        )
        if report.error:
            body += f"[dim]{report.error}[/]"
        console.print(Panel(body, title=title, border_style=style))

    asyncio.run(_run())


@main.group("tor")
def tor_group() -> None:
    """Local Tor SOCKS detection helpers."""


@tor_group.command("status")
def tor_status_cmd() -> None:
    """Show whether Tor Browser (9150) or system Tor (9050) is listening."""
    from trenchcoat.engine.tor_detect import detect_tor

    ep = detect_tor()
    if ep:
        console.print(Panel(f"[bold #00FF9F]{ep.label()}[/]\n{ep.as_url()}", title="TOR", border_style="#00FF9F"))
    else:
        console.print(
            Panel(
                "No Tor SOCKS on 127.0.0.1:9050 or :9150.\n"
                "Start Tor Browser, or run scripts/start-tor.ps1 / scripts/start-tor.sh",
                title="TOR",
                border_style="red",
            )
        )
        sys.exit(1)


@tor_group.command("newnym")
@click.option("--port", default=9051, show_default=True, help="Tor control port.")
@click.option("--password", default=None, help="Control port password.")
def tor_newnym_cmd(port: int, password: Optional[str]) -> None:
    """Signal Tor to build a new circuit (NEWNYM)."""
    from trenchcoat.engine.tor_control import signal_newnym

    ok, msg = asyncio.run(signal_newnym(port=port, password=password))
    if ok:
        console.print(f"[#00FF9F]NEWNYM ok[/] — {msg}")
        console.print(say("rotate"))
    else:
        console.print(f"[red]NEWNYM failed:[/] {msg}")
        sys.exit(1)


@main.group("route")
def route_group() -> None:
    """System routing / soft proxy (Phase 2 Circuit City)."""


@route_group.command("soft")
def route_soft_cmd() -> None:
    """Apply soft system proxy toward local cloak entry (WinHTTP on Windows)."""
    from trenchcoat.engine.system_route import SystemRouter

    cfg = load_config()
    r = SystemRouter(cfg.listen_host, cfg.listen_port).apply_soft()
    for m in r.messages:
        console.print(f"• {m}")
    if r.undo_hint:
        console.print(f"[dim]Undo: {r.undo_hint}[/]")
    sys.exit(0 if r.ok else 1)


@route_group.command("revert")
def route_revert_cmd() -> None:
    """Revert soft system proxy."""
    from trenchcoat.engine.system_route import SystemRouter

    r = SystemRouter().revert_soft()
    for m in r.messages:
        console.print(f"• {m}")
    sys.exit(0 if r.ok else 1)


@route_group.command("scripts")
@click.option("--out", "out_dir", default="packaging", show_default=True)
def route_scripts_cmd(out_dir: str) -> None:
    """Emit nftables / pf / WFP notes for hard routing (review before apply)."""
    from pathlib import Path

    from trenchcoat.engine.system_route import SystemRouter

    cfg = load_config()
    paths = SystemRouter(cfg.listen_host, cfg.listen_port).emit_hard_scripts(Path(out_dir))
    for p in paths:
        console.print(f"[#00FF9F]wrote[/] {p}")


@main.group("killswitch")
def killswitch_group() -> None:
    """Soft + opt-in hard kill-switch (Phase 6 Iron Collar)."""


@killswitch_group.command("soft")
def killswitch_soft_cmd() -> None:
    """Arm soft kill-switch messaging (cloak entry policy)."""
    from trenchcoat.engine.killswitch import KillSwitch

    cfg = load_config()
    st = KillSwitch(strict=False).arm(allow_uid_ports=[cfg.listen_port])
    for m in st.messages:
        console.print(f"• {m}")


@killswitch_group.command("hard")
@click.option(
    "--confirm",
    is_flag=True,
    help="Actually apply hard firewall rules (dangerous without undo).",
)
@click.option(
    "--dry-run",
    is_flag=True,
    help="Write undo/apply scripts and describe plan only (default-safe).",
)
@click.option(
    "--port",
    "ports",
    multiple=True,
    type=int,
    help="Extra local TCP ports to allow (default: config listen port).",
)
def killswitch_hard_cmd(confirm: bool, dry_run: bool, ports: tuple[int, ...]) -> None:
    """Opt-in hard kill-switch: allow-list cloak ports, block other egress.

    Always writes an undo script first under ~/.trenchcoat/killswitch/.
    """
    from trenchcoat.engine.killswitch import KillSwitch

    cfg = load_config()
    allow = list(ports) if ports else [cfg.listen_port]
    # dry-run is the default safety posture when neither flag set
    if not confirm and not dry_run:
        dry_run = True
    st = KillSwitch(strict=True).arm_hard(
        allow, confirm=confirm and not dry_run, dry_run=dry_run
    )
    for m in st.messages:
        console.print(f"• {m}")
    if st.undo_script:
        console.print(f"[dim]Undo script:[/] {st.undo_script}")
    if confirm and not st.hard_enabled and not dry_run:
        sys.exit(1)


@killswitch_group.command("disarm")
def killswitch_disarm_cmd() -> None:
    """Remove TrenchCoat-prefixed hard firewall rules (best-effort)."""
    from trenchcoat.engine.killswitch import KillSwitch

    st = KillSwitch().disarm()
    for m in st.messages:
        console.print(f"• {m}")


@killswitch_group.command("scripts")
@click.option("--out", "out_dir", default="packaging/killswitch", show_default=True)
def killswitch_scripts_cmd(out_dir: str) -> None:
    """Emit reviewable hard kill-switch scripts for Windows / Linux / macOS."""
    from pathlib import Path

    from trenchcoat.engine.killswitch import KillSwitch

    cfg = load_config()
    paths = KillSwitch().emit_hard_bundle(Path(out_dir), allow_ports=[cfg.listen_port])
    for p in paths:
        console.print(f"[#00FF9F]wrote[/] {p}")


@main.command("ipv6")
@click.argument("action", type=click.Choice(["status", "disable-hint", "disable"]), default="status")
@click.option("--force", is_flag=True, help="Actually run disable where supported (Linux).")
def ipv6_cmd(action: str, force: bool) -> None:
    """IPv6 exposure hints / optional disable (Phase 2)."""
    from trenchcoat.engine.ipv6 import status_hint, try_disable

    if action in ("status", "disable-hint"):
        r = status_hint()
    else:
        r = try_disable(dry_run=not force)
    for m in r.messages:
        console.print(f"• {m}")


@main.command("doh")
@click.argument("name", default="example.com")
@click.option("--via-cloak/--direct", default=True)
def doh_cmd(name: str, via_cloak: bool) -> None:
    """Resolve DNS via DoH (optionally through active hops)."""
    from trenchcoat.engine.doh import resolve_doh
    from trenchcoat.engine.tor_detect import bind_chain_to_tor, detect_tor

    cfg = load_config()
    chain = cfg.get_chain()

    async def _run() -> None:
        proxies: list[str] = []
        if via_cloak and chain:
            ep = detect_tor()
            if ep:
                bind_chain_to_tor(chain.hops, ep)
            engine = CloakEngine(cfg, chain)
            await engine.builder.build()
            proxies = engine.builder.proxy_urls()
        res = await resolve_doh(name, proxies or None)
        if res.error:
            console.print(f"[red]DoH error:[/] {res.error}")
            sys.exit(1)
        console.print(Panel(
            f"{name}\n" + "\n".join(res.answers or ["(no A records)"]) + f"\nvia {res.via_proxy or 'direct'}",
            title="DoH",
            border_style="#00FF9F",
        ))

    asyncio.run(_run())


@main.command("split")
def split_cmd() -> None:
    """Show active split-tunnel rules for the current chain."""
    from trenchcoat.engine.split_tunnel import SplitTunnelEngine

    cfg = load_config()
    chain = cfg.get_chain()
    if not chain:
        console.print("[red]No chain[/]")
        sys.exit(1)
    eng = SplitTunnelEngine(chain.split_tunnel)
    table = Table(title="Split Tunnel", border_style="#FF00AA")
    table.add_column("Pattern")
    table.add_column("Action")
    table.add_column("Reason")
    for row in eng.summarize():
        table.add_row(row["pattern"], row["action"], row["reason"])
    if not eng.rules:
        console.print("[dim]No split-tunnel rules on this chain.[/]")
    else:
        console.print(table)
    # demo decisions
    for sample in ("192.168.1.1", "example.com", "10.0.0.5"):
        d = eng.decide(sample)
        console.print(f"  {sample} → {'BYPASS' if d.bypass else 'CLOAK'} ({d.reason})")


@main.command("plugins")
@click.argument("action", type=click.Choice(["list"]), default="list")
def plugins_cmd(action: str) -> None:
    """List plugin API v1 modules."""
    from trenchcoat.plugins.base import default_plugin_dir, load_plugins_from_dir

    reg = load_plugins_from_dir(default_plugin_dir())
    # also user plugins/
    from pathlib import Path

    root_plugins = Path(__file__).resolve().parents[2] / "plugins"
    reg2 = load_plugins_from_dir(root_plugins)
    for k, v in reg2.obfuscators.items():
        reg.obfuscators[k] = v
    info = reg.list_plugins()
    console.print(Panel(
        f"obfuscators: {', '.join(info['obfuscators']) or '—'}\n"
        f"hop_drivers: {', '.join(info['hop_drivers']) or '—'}\n"
        f"hooks: {', '.join(info['hooks'])}",
        title="PLUGINS v1",
        border_style="#9B59B6",
    ))
    _ = action


@main.command("speak")
@click.option("--event", default="engage", show_default=True)
@click.option("--text", default=None)
def speak_cmd(event: str, text: Optional[str]) -> None:
    """Noir Mode TTS (Phase 4 Jazz for Ghosts)."""
    from trenchcoat.noir.tts import speak

    ok = speak(text=text, event=None if text else event)
    line = text or say(event)
    console.print(Panel(line, title="NOIR TTS", border_style="#00FF9F"))
    if not ok:
        console.print("[yellow]No speech backend found (SAPI/say/espeak).[/]")


@main.command("status")
def status_cmd() -> None:
    """Show config status (live engine status requires `trench up` + API)."""
    cfg = load_config()
    chain = cfg.get_chain()
    text = Text()
    text.append("Active chain: ", style="dim")
    text.append(f"{cfg.active_chain}\n", style="bold #00FF9F")
    text.append("Listen: ", style="dim")
    text.append(f"{cfg.listen_host}:{cfg.listen_port}\n", style="#FF00AA")
    text.append("Noir mode: ", style="dim")
    text.append(f"{cfg.noir_mode}\n")
    if chain:
        text.append("Hops: ", style="dim")
        text.append(" → ".join(h.display_name for h in chain.hops))
    console.print(Panel(text, title="STATUS", border_style="#9B59B6"))


@main.command("gui")
@click.option("--host", default="127.0.0.1")
@click.option("--port", default=8742, type=int)
def gui_cmd(host: str, port: int) -> None:
    """Launch local control API (and web GUI if built)."""
    import uvicorn
    from trenchcoat.api.server import create_app

    console.print(f"[#00FF9F]Control nexus on http://{host}:{port}[/]")
    console.print(say("boot"))
    uvicorn.run(create_app(), host=host, port=port, log_level="info")


@main.command("speedtest")
@click.option("--url", default="https://www.google.com/generate_204")
def speedtest_cmd(url: str) -> None:
    """Rough latency check via active chain's first healthy hop (if Tor/SOCKS up)."""
    import time
    import httpx

    cfg = load_config()
    chain = cfg.get_chain()
    if not chain:
        console.print("[red]No chain[/]")
        sys.exit(1)

    async def _run() -> None:
        engine = CloakEngine(cfg, chain)
        snap = await engine.builder.build()
        urls = engine.builder.proxy_urls()
        if not urls:
            console.print("[red]No live proxy hops for speedtest.[/]")
            return
        proxy = urls[-1]  # egress hop often Tor
        start = time.perf_counter()
        try:
            async with httpx.AsyncClient(proxy=proxy, timeout=30.0) as client:
                r = await client.get(url)
            ms = (time.perf_counter() - start) * 1000
            console.print(
                f"Via {proxy}: HTTP {r.status_code} in [bold #00FF9F]{ms:.0f} ms[/] "
                f"(chain healthy={snap.healthy})"
            )
            from trenchcoat.reporting import telemetry

            telemetry.record(
                "speedtest",
                chain_profile=chain.profile.value,
                hop_count=len(chain.hops),
                healthy_hops=sum(1 for h in snap.hops if h.health.value == "healthy"),
                total_latency_ms=ms,
            )
        except Exception as exc:  # noqa: BLE001
            console.print(f"[red]Speedtest failed: {exc}[/]")

    asyncio.run(_run())


@main.command("optimize")
@click.option("--chain", "chain_name", default=None, help="Chain to optimize.")
@click.option("--dry-run", is_flag=True, help="Show plan without rewriting hop order.")
def optimize_cmd(chain_name: Optional[str], dry_run: bool) -> None:
    """Latency-aware mid-hop reorder (Phase 5 Syndicate)."""
    from trenchcoat.engine.optimizer import optimize_chain
    from trenchcoat.reporting import telemetry

    cfg = load_config()
    chain = cfg.get_chain(chain_name)
    if not chain:
        console.print(f"[red]No chain: {chain_name or cfg.active_chain}[/]")
        sys.exit(1)

    result = asyncio.run(optimize_chain(chain, apply=not dry_run))
    table = Table(title=f"Optimize — {result.chain_name}", border_style="#00FF9F")
    table.add_column("Hop")
    table.add_column("Health")
    table.add_column("Latency")
    table.add_column("Score")
    for s in result.scores:
        table.add_row(
            s.hop_id,
            s.health,
            f"{s.latency_ms:.0f} ms" if s.latency_ms is not None else "—",
            f"{s.score:.0f}",
        )
    console.print(table)
    console.print(f"Before: {' → '.join(result.before)}")
    console.print(f"After:  {' → '.join(result.after)}")
    console.print(result.message)
    if result.changed and not dry_run:
        save_config(cfg)
        console.print("[#00FF9F]Saved reordered chain.[/]")
    telemetry.record(
        "optimize",
        chain_profile=chain.profile.value,
        hop_count=len(chain.hops),
        healthy_hops=sum(1 for s in result.scores if s.health == "healthy"),
        total_latency_ms=sum(s.latency_ms or 0 for s in result.scores) or None,
    )


@main.group("templates")
def templates_group() -> None:
    """Community chain templates (Phase 5)."""


@templates_group.command("list")
def templates_list_cmd() -> None:
    """List shipped community templates."""
    from trenchcoat.config.templates import list_templates

    rows = list_templates()
    if not rows:
        console.print("[yellow]No templates found under configs/templates/[/]")
        return
    table = Table(title="Community Templates", border_style="#9B59B6")
    table.add_column("ID", style="#00FF9F")
    table.add_column("Title")
    table.add_column("Author", style="#FF00AA")
    table.add_column("Description")
    for r in rows:
        table.add_row(r["id"], r["title"], r["author"], r["description"][:60])
    console.print(table)


@templates_group.command("import")
@click.argument("template_id")
@click.option("--activate/--no-activate", default=True)
def templates_import_cmd(template_id: str, activate: bool) -> None:
    """Import a community template into local config (edit hosts before engage)."""
    from trenchcoat.config.templates import load_template

    cfg = load_config()
    try:
        chain = load_template(template_id)
    except FileNotFoundError as exc:
        console.print(f"[red]{exc}[/]")
        sys.exit(1)
    cfg.chains = [c for c in cfg.chains if c.name != chain.name]
    cfg.chains.append(chain)
    if activate:
        cfg.active_chain = chain.name
    path = save_config(cfg)
    console.print(
        Panel(
            f"Imported [bold]{chain.name}[/] from template [cyan]{template_id}[/].\n"
            f"Hops: {len(chain.hops)} — configure host/port before `trench up`.\n"
            f"Saved → {path}",
            title="TEMPLATE IMPORTED",
            border_style="#00FF9F",
        )
    )


@main.group("telemetry")
def telemetry_group() -> None:
    """Opt-in anonymous chain quality telemetry (local, no IPs)."""


@telemetry_group.command("status")
def telemetry_status_cmd() -> None:
    """Show whether telemetry is enabled and local stats summary."""
    from trenchcoat.reporting import telemetry

    s = telemetry.summary()
    console.print(
        Panel(
            f"enabled: {s['enabled']}\n"
            f"install_id: {s['install_id']}\n"
            f"events: {s['events']}\n"
            f"avg_latency_ms: {s['avg_latency_ms']}\n"
            f"path: {s['path']}\n\n"
            "[dim]No IPs, hosts, or destinations are stored.[/]",
            title="TELEMETRY",
            border_style="#FF00AA",
        )
    )


@telemetry_group.command("enable")
def telemetry_enable_cmd() -> None:
    """Opt in to local anonymized quality counters."""
    from trenchcoat.reporting import telemetry

    cfg = load_config()
    cfg.telemetry_opt_in = True
    save_config(cfg)
    telemetry.set_enabled(True)
    console.print("[#00FF9F]Telemetry ON[/] (local file only, no network upload).")


@telemetry_group.command("disable")
def telemetry_disable_cmd() -> None:
    """Opt out of telemetry."""
    from trenchcoat.reporting import telemetry

    cfg = load_config()
    cfg.telemetry_opt_in = False
    save_config(cfg)
    telemetry.set_enabled(False)
    console.print("[yellow]Telemetry OFF[/]")


if __name__ == "__main__":
    main()
