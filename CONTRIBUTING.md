# Contributing to Trench Coat

The rain is friendlier when more hands hold the umbrella — **if** those hands stay clean.

## Ground rules

1. **Legal-first.** No PRs that add offensive tooling, exploit packs, credential stealers, or guides for crime.
2. **Honesty in opsec.** Document limitations. Never market a feature as “untraceable.”
3. **Reliability over chrome.** A boring kill-switch beats a glitch animation that leaks DNS.
4. **Least privilege.** Prefer user-space paths; elevate only when required and explain why.
5. **Tests.** New engine behavior ships with tests where feasible.

## Dev setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
pytest
ruff check src tests
```

## PR style

- Small, reviewable commits.
- Update docs when behavior changes.
- Keep the noir voice optional in user-facing docs; keep error messages clear.

## Code map

- `src/trenchcoat/engine/` — cloak runtime  
- `src/trenchcoat/hops/` — hop drivers  
- `src/trenchcoat/cli.py` — CLI  
- `gui/web/` — Command Nexus  
- `docs/` — architecture & security  

## Security reports

Do not open public issues for vulnerabilities. See [SECURITY.md](SECURITY.md).

---

*The shadows are your ally. The law is still the law.*
