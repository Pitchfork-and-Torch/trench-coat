"""Split-tunnel engine — CIDR, domain, and process-name rules."""

from __future__ import annotations

import ipaddress
import logging
import re
from dataclasses import dataclass
from typing import Iterable

from trenchcoat.config.models import SplitTunnelRule

log = logging.getLogger("trenchcoat.split")


@dataclass
class SplitDecision:
    bypass: bool  # True = go direct (exclude from cloak)
    matched_rule: str | None = None
    reason: str = ""


class SplitTunnelEngine:
    """
    Evaluate whether a destination should bypass the cloak.

    Rule semantics:
      - action=exclude → bypass cloak (direct)
      - action=include → force through cloak (never bypass for that match)
    First matching rule wins (list order). Default: through cloak (bypass=False).
    """

    def __init__(self, rules: Iterable[SplitTunnelRule] | None = None) -> None:
        self.rules = list(rules or [])

    def decide(
        self,
        host: str,
        port: int | None = None,
        process_name: str | None = None,
    ) -> SplitDecision:
        _ = port
        for rule in self.rules:
            if self._matches(rule.pattern, host, process_name):
                bypass = rule.action == "exclude"
                return SplitDecision(
                    bypass=bypass,
                    matched_rule=rule.pattern,
                    reason=rule.reason or rule.action,
                )
        return SplitDecision(bypass=False, reason="default-cloak")

    def _matches(self, pattern: str, host: str, process_name: str | None) -> bool:
        p = pattern.strip()
        if not p:
            return False
        # CIDR / IP
        if "/" in p or re.fullmatch(r"\d+\.\d+\.\d+\.\d+", p):
            try:
                net = ipaddress.ip_network(p if "/" in p else f"{p}/32", strict=False)
                try:
                    addr = ipaddress.ip_address(host)
                    return addr in net
                except ValueError:
                    return False
            except ValueError:
                pass
        # process name
        if process_name and p.lower() in process_name.lower():
            return True
        # domain: exact, suffix, or glob-ish *
        host_l = host.lower().rstrip(".")
        pat_l = p.lower().rstrip(".")
        if pat_l.startswith("*."):
            return host_l.endswith(pat_l[1:]) or host_l == pat_l[2:]
        if pat_l.startswith("."):
            return host_l.endswith(pat_l) or host_l == pat_l[1:]
        if host_l == pat_l or host_l.endswith("." + pat_l):
            return True
        # keyword process-like without process context (banking apps label)
        if process_name is None and not re.search(r"[./]", p) and p.isalpha():
            return False
        return False

    def summarize(self) -> list[dict[str, str]]:
        return [
            {"pattern": r.pattern, "action": r.action, "reason": r.reason}
            for r in self.rules
        ]
