"""Structured self-test (doctor) — machine-readable confidence checks."""

from __future__ import annotations

import platform
from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from trenchcoat.config.loader import load_config
from trenchcoat.config.models import AppConfig, ChainConfig
from trenchcoat.engine.dns_guard import DnsGuard
from trenchcoat.engine.killswitch import KillSwitch
from trenchcoat.engine.router import CloakEngine
from trenchcoat.engine.tor_detect import bind_chain_to_tor, detect_tor, port_open
from trenchcoat.security.leak_guard import run_leak_checklist

Severity = Literal["pass", "warn", "fail", "info"]


@dataclass
class CheckResult:
    id: str
    title: str
    status: Severity
    detail: str
    data: dict[str, Any] = field(default_factory=dict)


@dataclass
class SelfTestReport:
    ok: bool
    exit_code: int  # 0 pass, 1 warn-only, 2 fail
    platform: str
    checks: list[CheckResult] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "exit_code": self.exit_code,
            "platform": self.platform,
            "summary": self.summary,
            "checks": [asdict(c) for c in self.checks],
        }


def _rank(status: Severity) -> int:
    return {"pass": 0, "info": 0, "warn": 1, "fail": 2}.get(status, 0)


async def run_self_test(
    cfg: AppConfig | None = None,
    *,
    include_identity: bool = True,
    hard_ks_dry_run: bool = True,
) -> SelfTestReport:
    """Probe Tor, hops, fail-closed policy, entry, DNS, optional identity."""
    cfg = cfg or load_config()
    chain = cfg.get_chain()
    checks: list[CheckResult] = []
    system = platform.system()

    # Legal
    checks.append(
        CheckResult(
            id="legal",
            title="Legal notice accepted",
            status="pass" if cfg.accepted_legal_notice else "warn",
            detail=(
                "accepted_legal_notice=true"
                if cfg.accepted_legal_notice
                else "Not accepted yet — run trench first-run or trench up --accept-legal"
            ),
        )
    )

    # Tor
    tor_ep = detect_tor()
    if tor_ep:
        checks.append(
            CheckResult(
                id="tor",
                title="Local Tor SOCKS",
                status="pass",
                detail=tor_ep.label(),
                data={"host": tor_ep.host, "port": tor_ep.port, "url": tor_ep.as_url()},
            )
        )
        if chain:
            bind_chain_to_tor(chain.hops, tor_ep)
    else:
        checks.append(
            CheckResult(
                id="tor",
                title="Local Tor SOCKS",
                status="warn",
                detail="No Tor on 9050/9150 — Casual Shadow needs Tor or another hop",
            )
        )

    # Active chain + fail-closed policy
    if not chain:
        checks.append(
            CheckResult(
                id="chain",
                title="Active chain",
                status="fail",
                detail="No active chain configured",
            )
        )
    else:
        checks.append(
            CheckResult(
                id="chain",
                title="Active chain",
                status="pass",
                detail=f"{chain.name} ({chain.profile.value}) · {len(chain.hops)} hop(s)",
                data={"name": chain.name, "profile": chain.profile.value},
            )
        )
        fc = chain.policy.fail_closed
        checks.append(
            CheckResult(
                id="fail_closed_policy",
                title="Fail-closed policy",
                status="pass" if fc else "warn",
                detail=(
                    "fail_closed=true — empty chain refuses clearnet via cloak entry"
                    if fc
                    else "fail_closed=false — empty chain may allow direct (not recommended)"
                ),
                data={
                    "fail_closed": fc,
                    "allow_partial_chain": chain.policy.allow_partial_chain,
                    "kill_switch": chain.policy.kill_switch,
                    "strict_kill_switch": chain.policy.strict_kill_switch,
                },
            )
        )

        engine = CloakEngine(cfg, chain)
        snap = await engine.builder.build()
        urls = engine.builder.proxy_urls()
        dead = 0
        for h_cfg, st in zip(chain.hops, snap.hops, strict=False):
            status: Severity = "pass"
            if st.health.value == "dead":
                status = "fail"
                dead += 1
            elif st.health.value in ("unknown", "degraded"):
                status = "warn"
            checks.append(
                CheckResult(
                    id=f"hop:{st.hop_id}",
                    title=f"Hop {st.hop_id}",
                    status=status,
                    detail=st.error
                    or (f"{st.latency_ms} ms" if st.latency_ms is not None else st.health.value),
                    data={
                        "type": h_cfg.type.value,
                        "health": st.health.value,
                        "latency_ms": st.latency_ms,
                    },
                )
            )
        if chain.policy.fail_closed and not urls:
            checks.append(
                CheckResult(
                    id="live_urls",
                    title="Live hop URLs",
                    status="fail",
                    detail="No live hops — cloak will refuse engage (fail-closed)",
                )
            )
        else:
            checks.append(
                CheckResult(
                    id="live_urls",
                    title="Live hop URLs",
                    status="pass" if urls else "warn",
                    detail=f"{len(urls)} proxy URL(s) ready" if urls else "No proxy URLs",
                    data={"urls_count": len(urls)},
                )
            )

    # Cloak entry
    entry_up = port_open(cfg.listen_host, cfg.listen_port)
    checks.append(
        CheckResult(
            id="entry",
            title="Cloak entry listener",
            status="pass" if entry_up else "info",
            detail=(
                f"socks5://{cfg.listen_host}:{cfg.listen_port} is up"
                if entry_up
                else f"Not listening on {cfg.listen_host}:{cfg.listen_port} — run trench up"
            ),
        )
    )

    # DNS / IPv6
    dns = DnsGuard().audit()
    for i, rec in enumerate(dns.recommendations):
        checks.append(
            CheckResult(
                id=f"dns:{i}",
                title="DNS / IPv6",
                status="warn" if "IPv6" in rec or "ipv6" in rec.lower() else "info",
                detail=rec,
            )
        )

    # Leak checklist — pre-flight: missing cloak entry is informational, not a hard fail.
    # (Fail-closed hop death / live_urls already cover "do not trust" when hops are dead.)
    kill_switch_policy = bool(chain and chain.policy.kill_switch)
    for c in run_leak_checklist(
        proxy_active=entry_up,
        ipv6_enabled=dns.ipv6_likely_enabled,
        kill_switch=kill_switch_policy,
    ):
        status: Severity = c.status  # type: ignore[assignment]
        detail = c.detail
        if c.id == "proxy" and not entry_up:
            status = "info"
            detail = (
                "Cloak entry not listening yet — expected before `trench up`. "
                "After engage, re-run doctor; this should become pass."
            )
        checks.append(
            CheckResult(id=f"leak:{c.id}", title=c.title, status=status, detail=detail)
        )

    # Hard kill-switch dry-run (undo-first)
    if hard_ks_dry_run:
        ks = KillSwitch(strict=True)
        state = ks.arm_hard(
            allow_ports=[cfg.listen_port],
            confirm=False,
            dry_run=True,
        )
        has_undo = bool(state.undo_script)
        checks.append(
            CheckResult(
                id="hard_ks_scripts",
                title="Hard kill-switch (dry-run)",
                status="pass" if has_undo else "warn",
                detail=(
                    f"Undo script path ready: {state.undo_script}"
                    if has_undo
                    else "Hard KS dry-run did not produce undo script"
                ),
                data={"platform": system, "messages": state.messages[:5]},
            )
        )

    # Platform isolation honesty
    wfp = "unavailable (userspace netsh only; signed WFP deferred)"
    if system == "Linux":
        hard = "nftables script emit + optional apply"
    elif system == "Darwin":
        hard = "pf anchor script emit + optional apply"
    elif system == "Windows":
        hard = f"netsh advfirewall; WFP callout {wfp}"
    else:
        hard = "not implemented"
    checks.append(
        CheckResult(
            id="platform_isolation",
            title="System-level isolation capability",
            status="info",
            detail=f"{system}: soft=SOCKS refuse-direct; hard={hard}",
            data={"system": system},
        )
    )

    # Identity (optional live)
    if include_identity and entry_up:
        try:
            from trenchcoat.engine.identity import check_identity

            report = await check_identity(
                [f"socks5://{cfg.listen_host}:{cfg.listen_port}"]
            )
            if report.is_tor is True:
                checks.append(
                    CheckResult(
                        id="identity",
                        title="Egress identity (via cloak)",
                        status="pass",
                        detail=f"Tor exit confirmed · IP {report.ip or '?'}",
                        data=report.to_dict(),
                    )
                )
            elif report.is_tor is False:
                checks.append(
                    CheckResult(
                        id="identity",
                        title="Egress identity (via cloak)",
                        status="warn",
                        detail=f"IsTor=false · IP {report.ip or '?'} — verify hop chain",
                        data=report.to_dict(),
                    )
                )
            else:
                checks.append(
                    CheckResult(
                        id="identity",
                        title="Egress identity (via cloak)",
                        status="info",
                        detail=f"Could not determine Tor status · IP {report.ip or 'n/a'}",
                        data=report.to_dict(),
                    )
                )
        except Exception as exc:  # noqa: BLE001
            checks.append(
                CheckResult(
                    id="identity",
                    title="Egress identity (via cloak)",
                    status="info",
                    detail=f"Identity probe skipped: {exc}",
                )
            )

    worst = max((_rank(c.status) for c in checks), default=0)
    exit_code = 0 if worst == 0 else (1 if worst == 1 else 2)
    ok = exit_code < 2
    fails = [c for c in checks if c.status == "fail"]
    if exit_code == 0:
        summary = "All critical checks passed. Cloak posture looks healthy."
    elif exit_code == 1:
        summary = "Warnings present — review before high-risk use."
    else:
        # Point operators at the actual blockers (usually: start Tor).
        heads = "; ".join(f"{c.title}: {c.detail}" for c in fails[:3])
        more = f" (+{len(fails) - 3} more)" if len(fails) > 3 else ""
        summary = (
            "Failures detected — do not trust the cloak until fixed. "
            f"{heads}{more}"
        )
        if any(c.id in ("tor", "live_urls") or c.id.startswith("hop:") for c in fails):
            summary += (
                " | Next: start Tor (9050/9150) or Tor Browser, then "
                "`trench tor status` → `trench up --accept-legal --wait-tor 60`."
            )

    return SelfTestReport(
        ok=ok,
        exit_code=exit_code,
        platform=system,
        checks=checks,
        summary=summary,
    )
