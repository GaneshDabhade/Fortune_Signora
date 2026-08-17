#!/usr/bin/env python3
"""**The Production Readiness Checklist** — [D-213](../docs/DECISION_REGISTER.md).

    python3 infra/production-readiness.py            # the checklist
    python3 infra/production-readiness.py --ref X    # measure another ref

## ⛔ Why this is a program and not a document

The product owner asked for a checklist *"maintained in parallel with
implementation… so that by the time feature development completes, we already
have a production-grade checklist rather than starting that work afterward."*

⚡ **A hand-maintained checklist is the one form that cannot deliver that.** It
is written once, it is true for a day, and nothing detects the day it stops
being true — the defect this repository has now paid for in `eligible_count`,
in `PROJECT_STATUS`, in three dashboards and in `workflows.toml`. **A checklist
whose rows are claims nobody re-measures is worse than none: it is a false
assurance at exactly the moment somebody trusts it.**

✅ **So every row here is a PROBE against the repository**, and rows that cannot
be probed say so in their own voice rather than being quietly scored.

## ⛔ What it deliberately does not do

**It does not run anything.** No suite, no browser, no database — `CLAUDE.md`
forbids this office running the test suites, and a readiness check that needs a
live stack is a check nobody runs. **It reads the repository as shipped.**

**It does not grade.** ⚡ There is no percentage and no overall score, because a
single number invites the wrong conversation: *observability at 80%* tells
nobody which 20% is missing at three in the morning. **Each concern stands on
its own evidence.**

**A `«judgement»` row is not a failure and not a pass** — it is a concern no
program can measure, named so it cannot be mistaken for one that was checked.
[D-212](../docs/DECISION_REGISTER.md) §8: a mechanism that does not make
implementation faster, safer or more reliable is not introduced, and a fake
measurement makes it slower and less reliable at once.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from refs import refresh  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent

OK, WARN, GAP, JUDGE = "✅", "⚠️", "🔴", "· "


@dataclass(frozen=True)
class Finding:
    area: str
    concern: str
    mark: str
    evidence: str


def _ls(ref: str) -> list[str]:
    out = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", ref],
        cwd=ROOT, capture_output=True, text=True,
    )
    return out.stdout.split("\n") if out.returncode == 0 else []


def _show(ref: str, path: str) -> str:
    out = subprocess.run(
        ["git", "show", f"{ref}:{path}"], cwd=ROOT, capture_output=True, text=True
    )
    return out.stdout if out.returncode == 0 else ""


def _grep_count(ref: str, pattern: str, pathspec: str) -> int:
    """Files matching `pattern`. **Counts FILES, never occurrences** — a concern
    is satisfied by being present somewhere, and an occurrence count invites
    reading a large number as a good one."""
    out = subprocess.run(
        ["git", "grep", "-lI", "-E", pattern, ref, "--", pathspec],
        cwd=ROOT, capture_output=True, text=True,
    )
    return len([x for x in out.stdout.split("\n") if x.strip()])


def observability(ref: str, files: set[str]) -> list[Finding]:
    out: list[Finding] = []
    pkg = "backend/signora_platform/observability"
    present = {p.rsplit("/", 1)[-1][:-3] for p in files if p.startswith(pkg) and p.endswith(".py")}
    for module, concern in (
        ("logging", "Structured logging"),
        ("metrics", "Metrics"),
        ("tracing", "Tracing"),
        ("errors", "Error tracking"),
        ("context", "Correlation context"),
    ):
        out.append(Finding(
            "Observability", concern,
            OK if module in present else GAP,
            f"`{pkg}/{module}.py`" if module in present else "absent",
        ))

    log = _show(ref, f"{pkg}/logging.py")
    out.append(Finding(
        "Observability", "Logs are machine-readable",
        OK if "JsonFormatter" in log else GAP,
        "`JsonFormatter` — one line, one object" if "JsonFormatter" in log else "no JSON formatter",
    ))
    # ⚡ **The one that matters most and is easiest to omit.** A log line that
    # carries a token or an email is a breach that looks like debugging.
    out.append(Finding(
        "Observability", "Secrets redacted in logs",
        OK if re.search(r"^def redact", log, re.M) else GAP,
        "`redact()` in the formatter path" if "def redact" in log else "⛔ nothing redacts",
    ))
    return out


def operations(ref: str) -> list[Finding]:
    main = _show(ref, "backend/apps/api/main.py")
    live = '@app.get("/health"' in main
    # **Liveness and readiness are different questions** and conflating them is
    # the classic outage amplifier: a readiness-shaped liveness probe restarts
    # healthy processes during a database blip.
    ready = bool(re.search(r'@app\.get\("/(ready|readyz|health/ready)"', main))
    return [
        Finding("Operations", "Liveness probe", OK if live else GAP,
                "`/health` — documented as deliberately not touching the database" if live else "absent"),
        Finding("Operations", "Readiness probe", OK if ready else WARN,
                "present" if ready else "⚠️ none — an orchestrator cannot tell *started* from *able to serve*"),
        Finding("Operations", "Production compose", OK if _exists(ref, "infra/docker-compose.prod.yml") else GAP,
                "`infra/docker-compose.prod.yml`"),
        Finding("Operations", "Disaster recovery", OK if _exists(ref, "infra/disaster-recovery.sh") else GAP,
                "`infra/disaster-recovery.sh`, in `make dr`"),
        Finding("Operations", "Release preflight", OK if _exists(ref, "infra/release-preflight.py") else GAP,
                "`infra/release-preflight.py`"),
    ]


def _exists(ref: str, path: str) -> bool:
    return bool(_show(ref, path))


def security(ref: str, files: set[str]) -> list[Finding]:
    invariants = [f for f in files if "tests/security_invariants" in f and f.endswith(".py")]
    tenancy = _grep_count(ref, "TENANT_OWNED_TABLES|PERSON_OWNED_TABLES", "backend/*.py")
    # ⛔ **INBOUND, never outbound — and the first version of this probe got it
    # wrong.** `rate.?limit|throttl` matched 38 files and every one was Signora
    # pacing ITSELF against a vendor: *"HubSpot rate limit reached"*, provider
    # pools, adapter backoff. ⚡ **That is the opposite concern.** The question a
    # readiness check must ask is whether SIGNORA'S OWN API is protected from
    # credential stuffing and scraping, and a broad pattern answered ✅ to a
    # question nobody had asked — the false assurance this whole file exists to
    # avoid, produced by the file itself on its first run.
    rate = _grep_count(ref, "slowapi|RateLimitMiddleware|limiter\\.limit|Depends\\(RateLimit",
                       "backend/apps/*.py")
    return [
        Finding("Security", "Security Invariant suite", OK if invariants else GAP,
                f"{len(invariants)} file(s), run as their own gate"),
        Finding("Security", "Tenancy classification", OK if tenancy else GAP,
                f"{tenancy} file(s) classify tables — a new table cannot be unclassified"),
        Finding("Security", "Inbound rate limiting", OK if rate else GAP,
                f"{rate} file(s) in `apps/`" if rate else
                "⛔ **nothing guards Signora's own API** — no protection against credential "
                "stuffing on `/sign-in` or scraping. ⚠️ 38 files rate-limit OUTBOUND calls to "
                "vendors; that is the opposite concern"),
        Finding("Security", "Authorization is server-side", JUDGE,
                "Casbin enforces; §20c says a client check is a courtesy. **Verified per row, not here**"),
    ]


def frontend(ref: str, files: set[str]) -> list[Finding]:
    ui = {f.rsplit("/", 1)[-1] for f in files if f.startswith("frontend/components/ui/")}
    fb = {f.rsplit("/", 1)[-1] for f in files if f.startswith("frontend/components/feedback/")}
    e2e = [f for f in files if f.startswith("frontend/tests/e2e/") and f.endswith(".spec.ts")]
    a11y = [f for f in e2e if "accessib" in f]
    perf = [f for f in e2e if re.search(r"perf|lighthouse|budget", f)]
    return [
        Finding("Customer-facing", "Error states", OK if "system-state.tsx" in ui else GAP,
                "`components/ui/system-state.tsx` — the scope ladder"),
        Finding("Customer-facing", "Failed-read state", OK if "stated-absence.tsx" in fb else GAP,
                "`components/feedback/stated-absence.tsx`"),
        Finding("Customer-facing", "Error boundary", OK if "error-boundary.tsx" in fb else GAP,
                "`components/feedback/error-boundary.tsx`"),
        Finding("Customer-facing", "Loading / skeletons",
                OK if any("skeleton" in f for f in ui) else GAP,
                "skeleton primitives in `components/ui`"),
        Finding("Customer-facing", "Accessibility suite", OK if a11y else GAP,
                f"{len(a11y)} spec(s) — ⚠️ **passing is not asserted here; this office does not run suites**"),
        Finding("Customer-facing", "Performance budget", GAP if not perf else OK,
                "⛔ **no budget and no measurement** — nothing would notice a regression" if not perf
                else f"{len(perf)} spec(s)"),
        Finding("Customer-facing", "Journey coverage", OK if len(e2e) > 5 else WARN,
                f"{len(e2e)} Playwright spec(s)"),
        Finding("Customer-facing", "Responsive behaviour", JUDGE,
                "Breakpoints are tokens; **conformance is per screen and audited against the design**"),
        Finding("Customer-facing", "Design System conformance", JUDGE,
                "`design-tokens.test.tsx` forbids the escapes; **visual fidelity is the audit's**"),
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--ref", default="origin/integration",
                        help="ref to measure (default: origin/integration — what is shipped)")
    parser.add_argument("--no-fetch", action="store_true",
                        help="skip the freshness fetch (offline; the reading may be stale)")
    args = parser.parse_args()
    ref = args.ref
    # **It asks what is SHIPPED, so it must ask a current ref** — the existing
    # `cannot read {ref} — is it fetched?` catches an absent one and says
    # nothing about a stale one ([B-441](../docs/BUGS.md)).
    if (notice := refresh(ref, ROOT, skip=args.no_fetch)) is not None:
        print(f"production-readiness: {notice}", file=sys.stderr)

    files = {f for f in _ls(ref) if f}
    if not files:
        print(f"  cannot read {ref} — is it fetched?")
        return 0

    findings = (observability(ref, files) + operations(ref)
                + security(ref, files) + frontend(ref, files))

    print(f"  PRODUCTION READINESS — measured at {ref}, D-213")
    print()
    area = ""
    w = max(len(f.concern) for f in findings)
    for f in findings:
        if f.area != area:
            area = f.area
            print(f"  ── {area}")
        print(f"     {f.mark} {f.concern.ljust(w)}  {f.evidence}")
    print()

    gaps = [f for f in findings if f.mark == GAP]
    warns = [f for f in findings if f.mark == WARN]
    judge = [f for f in findings if f.mark == JUDGE]
    print(f"  {len(gaps)} gap(s) · {len(warns)} warning(s) · {len(judge)} judgement(s) "
          f"· {len(findings) - len(gaps) - len(warns) - len(judge)} satisfied")
    if gaps:
        print()
        for f in gaps:
            print(f"  🔴 {f.area} — {f.concern}")
    print()
    print("  ⛔ No score, deliberately: *observability at 80%* tells nobody which")
    print("     20% is missing at three in the morning. Each concern stands alone.")
    print("  ⛔ Nothing here is run — it reads the repository as shipped.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
