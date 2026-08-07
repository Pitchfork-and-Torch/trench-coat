"""Latency-aware hop optimizer (Phase 5 — Syndicate).

Probes mid-path hops and reorders them by measured RTT while keeping
entry and exit (often Tor) stable when possible.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from trenchcoat.config.models import ChainConfig, HopConfig
from trenchcoat.hops.base import HopHealth, hop_from_config

log = logging.getLogger("trenchcoat.optimizer")


@dataclass
class HopScore:
    hop_id: str
    latency_ms: float | None
    health: str
    weight: float = 1.0
    score: float = 0.0  # lower is better


@dataclass
class OptimizeResult:
    chain_name: str
    before: list[str]
    after: list[str]
    scores: list[HopScore] = field(default_factory=list)
    changed: bool = False
    message: str = ""


def _score(latency_ms: float | None, health: str, weight: float) -> float:
    if health == HopHealth.DEAD.value:
        return 1_000_000.0
    if latency_ms is None:
        base = 5_000.0
    else:
        base = float(latency_ms)
    # Prefer higher weight hops slightly (weight 1.0 default)
    return base / max(weight, 0.1)


async def probe_scores(hops: list[HopConfig]) -> list[HopScore]:
    instances = [hop_from_config(h) for h in hops if h.enabled]
    results = await asyncio.gather(*[h.probe() for h in instances], return_exceptions=True)
    scores: list[HopScore] = []
    for hop, res in zip(instances, results, strict=True):
        if isinstance(res, BaseException):
            scores.append(
                HopScore(
                    hop_id=hop.config.id,
                    latency_ms=None,
                    health=HopHealth.DEAD.value,
                    weight=hop.config.weight,
                    score=_score(None, HopHealth.DEAD.value, hop.config.weight),
                )
            )
            continue
        scores.append(
            HopScore(
                hop_id=res.hop_id,
                latency_ms=res.latency_ms,
                health=res.health.value,
                weight=hop.config.weight,
                score=_score(res.latency_ms, res.health.value, hop.config.weight),
            )
        )
    return scores


async def optimize_chain(chain: ChainConfig, apply: bool = True) -> OptimizeResult:
    """Reorder mid hops by latency. Preserves first and last hop positions."""
    hops = list(chain.hops)
    before = [h.id for h in hops]
    if len(hops) < 3:
        return OptimizeResult(
            chain_name=chain.name,
            before=before,
            after=before,
            message="Need at least 3 hops to reorder mid-path.",
        )

    head, *mid, tail = hops
    mid_scores = await probe_scores(mid)
    score_map = {s.hop_id: s.score for s in mid_scores}
    mid_sorted = sorted(mid, key=lambda h: score_map.get(h.id, 9_999.0))
    after_hops = [head, *mid_sorted, tail]
    after = [h.id for h in after_hops]
    all_scores = await probe_scores(after_hops)

    changed = after != before
    if apply and changed:
        chain.hops = after_hops
        log.info("optimized chain %s: %s → %s", chain.name, before, after)

    return OptimizeResult(
        chain_name=chain.name,
        before=before,
        after=after,
        scores=all_scores,
        changed=changed,
        message="Reordered mid hops by latency." if changed else "Already optimal order.",
    )
