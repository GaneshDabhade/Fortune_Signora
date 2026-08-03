#!/usr/bin/env python3
"""**A product review is a session, not a stack.**

Phase 2 of the Environment Framework. Phase 1 (`infra/environments.py`) made an
environment's identity derivable; this is the first thing to *consume* a profile,
and it is deliberately the only place that knows how a review is started.

**What the reviewer types is `make review`.** No port, no database, no compose
project, no environment variable, no second terminal. Every value below is
derived from the `review` profile — this file contains no literal `3000`, and
that is the property worth protecting: the day the allocation changes, nothing
here is edited.

### The lifecycle, and the three stages that are deliberately absent

    prepare → validate → seed → present → record        …then `end`

**Product demonstration** is not here. A guided tour is a *product* artifact —
it asserts what the product means, not what it does — and writing one inside a
launcher would make QE the author of a story it is not qualified to tell. It is
designed before it is coded.

**Playwright evidence** is not here. The repository has **one** e2e spec, so a
collector would be an empty framework wearing a lifecycle stage's name
(`CLAUDE.md` §20e — *never build an empty framework because it may be needed one
day*). It arrives when there is something to collect.

**Smoke validation is not here, and cannot be.** `infra/docker-compose.prod.yml`
binds the same two ports a review session holds, so a smoke run *during* a
review is impossible by construction — that is exactly what
`release-preflight.py` exists to explain. **The certification record answers the
same question better**: `make certify` already ran every gate against this
commit, and the session record below cites that run rather than re-asserting it.
A review that re-proved the build would be measuring a stack a reviewer is
standing on.

### The session is the artifact

*"What exactly did we demonstrate before signing that contract?"* is a question
about a past moment, and it cannot be answered by an environment that has since
been torn down. Every run writes `review/sessions/<id>/session.json` and a
rendered summary beside it: the commit, whether that commit was certified, the
dataset and its version, the accounts, the open defects a reviewer should expect
to hit, and — on `end` — the duration and whatever notes were captured.

**`review/` is git-ignored, and that is a deliberate stopping point rather than
an oversight.** Making review records part of repository history means teaching
`certification-guard.py --audit-main` to accept a new class of commit on `main`,
which is a governance change and not a slice's to make. The records are durable
local artifacts today; promoting them to repository evidence is a decision, and
it is recorded as one.

    python3 infra/review.py start
    python3 infra/review.py status
    python3 infra/review.py end [--note "..."]

Exit codes:

    0  the session started, is running, or ended cleanly
    2  a review is already running (`start`), or none is (`end`)
    3  the workstation is not in a state where a review can begin
"""

from __future__ import annotations

import argparse
import json
import os
import re
import signal
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
import webbrowser
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Final

INFRA: Final = Path(__file__).resolve().parent
REPO_ROOT: Final = INFRA.parent
sys.path.insert(0, str(INFRA))

import environments  # noqa: E402  — sys.path is set immediately above
import registers  # noqa: E402

#: Which environment a human review runs in. **The only name this file knows.**
#: Everything numbered — ports, database, Redis index, compose project — is a
#: property of the profile, so this module contains no allocation of its own.
PROFILE: Final = environments.BY_NAME["review"]

SESSIONS: Final = REPO_ROOT / "review" / "sessions"
POINTER: Final = REPO_ROOT / "review" / "current.json"

#: How long to wait for each tier to answer before giving up. The API is slow to
#: start on a cold `uv` cache; Next compiles the first route on demand.
READY_TIMEOUT: Final = 120
DEV_POSTGRES_PORT: Final = 5432
DEV_REDIS_PORT: Final = 6379


# ── the repository, as it is right now ──────────────────────────────────────


def _git(*args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=REPO_ROOT, capture_output=True, text=True, check=False
    ).stdout.strip()


def _infra(filename: str) -> Any:
    """An `infra/` script whose filename is not a Python identifier.

    The pattern `hooks/allowed_here.py` established: **import the authority
    rather than restate its rule.** A second copy of *"did every gate pass?"* or
    *"who holds this port?"* would eventually disagree with the first, and the
    copy nobody maintains is the one somebody trusts (`CLAUDE.md` §2).
    """
    import importlib.util

    spec = importlib.util.spec_from_file_location(filename.replace("-", "_"), INFRA / filename)
    if spec is None or spec.loader is None:
        return None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _guard() -> Any:
    return _infra("certification-guard.py")


def _build_verification(head: str) -> dict[str, Any]:
    """**Which certified build is the reviewer actually looking at?**

    Not *"is `HEAD` certified?"* — asking that produces the wrong answer almost
    every time, and running it is how that was found. **`main`'s head is always
    a Repository Closeout commit**, and a Closeout can never be certified: a
    certification record cannot contain its own commit hash, so the commit that
    *writes* the record is always created after the run it records
    (`CLAUDE.md` §20e). A review on `main` would therefore have reported *"no
    certification record"* for a repository whose every promotion was certified.

    So this walks back to the **nearest certified ancestor**, which is sound for
    exactly the reason the exception is bounded: `--audit-main` proves a
    Closeout commit changes nothing executable, so the software the reviewer is
    running *is* the certified software. The distance is reported rather than
    hidden — a review sitting many commits above its last certification is worth
    knowing about.

    **Whether a run passed is asked, never decided here.** The manifest stores
    facts and derives the verdict — there is no `satisfied` field to read — so a
    second implementation of *"did every required gate pass?"* would be the
    duplicated truth `CLAUDE.md` §2 forbids, and the copy nobody maintained
    would be this one. `certification-guard.py` already owns that rule for
    promotion; it is imported, exactly as `hooks/allowed_here.py` imports it.

    A missing or unreadable manifest reports *unknown*, never *uncertified* —
    those are different claims and only one is knowable from an absent file.
    """
    guard = _guard()
    if guard is None or not (REPO_ROOT / "certification" / "manifest.json").exists():
        return {"known": False, "certified": False}

    return verification_from(
        passing={str(run["commit"]): run for run in guard._runs() if guard._satisfied(run)[0]},
        ancestors=_git("rev-list", "-n", "200", head).splitlines(),
        is_closeout=lambda commit: guard._is_closeout(commit)[0],
    )


def verification_from(
    *,
    passing: dict[str, dict[str, Any]],
    ancestors: list[str],
    is_closeout: Any,
) -> dict[str, Any]:
    """The walk itself, with the repository held at arm's length.

    **Extracted because this is the part that can be wrong quietly.** The first
    version asked *"is `HEAD` certified?"*, which is wrong on `main` every time
    and produced a confident *"no certification record"* for a repository whose
    every promotion was certified. A version of that mistake could return
    silently again; a pure function can be driven with the histories that
    distinguish a correct answer from a plausible one.
    """
    if not passing:
        return {"known": True, "certified": False}

    since: list[str] = []
    for ancestor in ancestors:
        if (run := passing.get(ancestor)) is not None:
            # **Checked, not asserted.** That the intervening commits change
            # nothing executable is the whole reason walking back is sound, so
            # it is verified per commit rather than trusted — and a commit that
            # is *not* a Closeout is exactly what a reviewer needs told, because
            # then the running software is not the certified software.
            executable = [commit for commit in since if not is_closeout(commit)]
            return {
                "known": True,
                "certified": not executable,
                "commit": ancestor,
                "certified_at": run.get("certified_at", ""),
                "coverage": run.get("coverage"),
                "commits_since": len(since),
                "uncertified_executable": [commit[:12] for commit in executable],
            }
        since.append(ancestor)
    return {"known": True, "certified": False}


def _dataset() -> str:
    """Which scenario the Playground seeds, read from the seeder that seeds it.

    **Named here so a review record survives the dataset changing.** The product
    owner's stated direction is several representative datasets — Enterprise,
    Startup, Manufacturing — and a record that said only *"the Playground"*
    would become ambiguous the moment the second one existed. Nothing about
    today's single dataset is assumed beyond its identity.
    """
    seed = REPO_ROOT / "backend" / "tests" / "playground" / "seed.py"
    match = re.search(r'SCENARIO\s*=\s*\(\s*"([^"]+)"\s*,\s*(\d+)\s*\)', seed.read_text())
    return f"{match.group(1)}@{match.group(2)}" if match else "unknown"


#: Module descriptions that mean *"a reviewer cannot meet this"*. The register's
#: `Module` field is prose rather than a taxonomy, so these are the literal
#: phrases it already uses — and anything unrecognised is **kept**, deliberately.
#: Over-reporting costs a reviewer one glance; under-reporting costs them the
#: session in which they rediscover a defect somebody already wrote down.
NOT_REACHABLE_BY_A_REVIEWER: Final = (
    "repository process",
    "repository tooling",
    "repository documentation",
    "repository configuration",
    "governance tooling",
    "shared test infrastructure",
    "the developer workstation",
)


def _known_limitations() -> tuple[list[str], int]:
    """Open defects a reviewer could actually meet, worst first — and a count
    of the ones deliberately left off.

    **A reviewer who rediscovers a known bug has spent their session on it.**
    But the register is a whole-repository one: fourteen open rows on the first
    run, of which most were about `make certify`, `state-check` and `RUNNING.md`
    — invisible from a browser, and pure noise on a card a product owner reads.

    The severity and state come from `registers.bug_rows`, which already owns
    the rule that a status cell's *first* lifecycle token is the operative one
    (B-101); the title and module are read here because they are presentation.
    """
    text = (REPO_ROOT / "docs" / "BUGS.md").read_text()
    sections = re.split(r"^### (B-\d+)\s*[·—-]\s*([^\n]+)\n", text, flags=re.M)
    described = {
        identifier: (title.strip(), body)
        for identifier, title, body in zip(
            sections[1::3], sections[2::3], sections[3::3], strict=False
        )
    }
    order = {"🔴": 0, "🟠": 1, "🟡": 2, "🟢": 3}
    rows = sorted(
        (row for row in registers.bug_rows(text) if row.unresolved),
        key=lambda row: order.get(row.severity, 9),
    )

    shown, hidden = [], 0
    for row in rows:
        title, body = described.get(row.identifier, ("(no title)", ""))
        cell = re.search(r"\| \*\*Module\*\* \| (.+)", body)
        module = cell.group(1).lower() if cell else ""
        if any(phrase in module for phrase in NOT_REACHABLE_BY_A_REVIEWER):
            hidden += 1
            continue
        shown.append(f"{row.severity} {row.identifier} — {title}")
    return shown, hidden


def _accounts() -> tuple[str, list[dict[str, str]]]:
    users = json.loads((INFRA / "demo-users.json").read_text())
    return users["password"], users["users"]


# ── validate ────────────────────────────────────────────────────────────────


def _listening(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(0.5)
        return probe.connect_ex(("127.0.0.1", port)) == 0


def _holders() -> dict[int, str]:
    """Who holds each review port, **named**.

    Delegated to `release-preflight.py`, which already learned the lesson this
    would otherwise have to relearn: **a published container port belongs to
    `docker-proxy`, not to the process inside it**, so `ss` alone reports
    `unknown` and sends the operator hunting for something the tool could have
    named. A first version of this function did exactly that, and the very first
    run reported `unknown` for two containers of QE's own leftover `make dr`
    stack.
    """
    preflight = _infra("release-preflight.py")
    if preflight is None:
        return {}
    return {holder.port: holder.process for holder in preflight._listeners()}


def _validate() -> list[str]:
    """Everything that must be true before a review can begin, in one pass.

    **Reported together rather than one failure at a time.** A validator that
    stops at the first problem makes the reviewer run it once per problem, and
    the whole point of this stage is that a reviewer never debugs an
    environment.
    """
    problems: list[str] = []

    for tool in ("docker", "node", "npm", "uv", "git"):
        if subprocess.run(["which", tool], capture_output=True, check=False).returncode:
            problems.append(f"`{tool}` is not on PATH — docs/RUNNING.md lists what a workstation needs")

    if not _listening(DEV_POSTGRES_PORT):
        problems.append(
            f"PostgreSQL is not reachable on {DEV_POSTGRES_PORT}. "
            "`docker compose -f infra/docker-compose.yml up -d --wait`"
        )
    if not _listening(DEV_REDIS_PORT):
        problems.append(
            f"Redis is not reachable on {DEV_REDIS_PORT}. "
            "`docker compose -f infra/docker-compose.yml up -d --wait`"
        )

    holders = _holders()
    for port, tier in ((PROFILE.web_port, "web"), (PROFILE.api_port, "API")):
        if _listening(port):
            problems.append(f"port {port} ({tier}) is held by {holders.get(port, 'unknown')}")

    # The two values that have no default and never should (B-104). Absent, the
    # tier refuses to start — correctly, but several seconds later and with the
    # message buried in a dev server's output.
    env_local = REPO_ROOT / "frontend" / ".env.local"
    if not env_local.exists():
        problems.append("frontend/.env.local is missing — `cp frontend/.env.example frontend/.env.local`")
    else:
        text = env_local.read_text()
        for variable in ("SIGNORA_AUTH_DATABASE_URL", "BETTER_AUTH_SECRET", "SIGNORA_JWT_PRIVATE_KEY"):
            if not re.search(rf"^{variable}=\S", text, re.M):
                problems.append(f"{variable} is not set in frontend/.env.local — it has no default")
    if not (REPO_ROOT / "backend" / ".env").exists():
        problems.append("backend/.env is missing — `cp backend/.env.example backend/.env`")

    return problems


# ── present ─────────────────────────────────────────────────────────────────


def _api_environment() -> dict[str, str]:
    """The API tier's configuration, **derived from the profile**.

    `SIGNORA_JWT_PUBLIC_KEY` is deliberately absent: `backend/.env` holds it,
    and setting it here would override a value the reviewer pasted in. It was
    once sourced from a directory nothing in this repository creates, which
    emptied it silently (B-016).
    """
    return {
        **os.environ,
        "SIGNORA_DATABASE_URL": (
            f"postgresql+asyncpg://signora_app:signora_app_local_dev@localhost:"
            f"{DEV_POSTGRES_PORT}/{PROFILE.database}"
        ),
        "SIGNORA_REDIS_URL": f"redis://localhost:{DEV_REDIS_PORT}/{PROFILE.redis_index}",
        "SIGNORA_JWT_ISSUER": f"http://localhost:{PROFILE.web_port}",
        "SIGNORA_JWT_AUDIENCE": "signora-api",
    }


def _dotenv(path: Path) -> dict[str, str]:
    """`KEY=value` pairs from an env file, quotes stripped.

    **Next.js loads `frontend/.env.local` for `next dev`; nothing loads it for
    `tsx`.** So `npm run auth:migrate` and `npm run demo:users` — both steps of
    the documented quickstart — see none of it, and since B-104 removed the
    fallbacks they now fail outright rather than silently using somebody else's
    database. Correct, and fatal to a one-command review.

    This makes the review path work. **The documented `make demo` path is still
    broken for anyone running it directly** — that is [B-105](../docs/BUGS.md),
    reported rather than patched here, because a second env-loading mechanism
    hidden inside a launcher is how two environments start disagreeing about
    what configuration means.
    """
    if not path.exists():
        return {}
    found: dict[str, str] = {}
    for line in path.read_text().splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, _, value = stripped.partition("=")
        found[key.strip()] = value.strip().strip('"').strip("'")
    return found


def _spawn(command: list[str], *, cwd: Path, log: Path, env: dict[str, str]) -> int:
    """Start a tier detached, with its output going somewhere findable.

    **The log path is printed, and that is not housekeeping.** Signing up as
    yourself needs the verification link, and the console transport writes it to
    the frontend's stdout — which a backgrounded process no longer has. A
    reviewer who cannot find that link cannot create an account.
    """
    handle = log.open("w")
    process = subprocess.Popen(
        command, cwd=cwd, stdout=handle, stderr=subprocess.STDOUT, env=env, start_new_session=True
    )
    return process.pid


def _await(url: str, *, label: str, timeout: int) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2):
                return True
        except urllib.error.HTTPError:
            # Any HTTP status means something is answering; an unauthenticated
            # redirect or a 404 is still a live tier.
            return True
        except (urllib.error.URLError, TimeoutError, ConnectionError, OSError):
            time.sleep(1)
        print(f"    waiting for {label}…", end="\r", flush=True)
    return False


# ── the session record ──────────────────────────────────────────────────────


def _write(session: dict[str, Any]) -> Path:
    directory = SESSIONS / session["id"]
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "session.json").write_text(json.dumps(session, indent=2, sort_keys=True))
    (directory / "summary.md").write_text(_render(session))
    POINTER.write_text(json.dumps({"id": session["id"]}))
    return directory


def _load() -> dict[str, Any] | None:
    if not POINTER.exists():
        return None
    try:
        identifier = json.loads(POINTER.read_text())["id"]
        return json.loads((SESSIONS / identifier / "session.json").read_text())
    except (json.JSONDecodeError, KeyError, FileNotFoundError):
        return None


def _verdict(certification: dict[str, Any], *, long: bool) -> str:
    """One sentence a non-engineer can act on.

    **`unknown` and `not certified` stay distinct**, in both renderings. An
    absent manifest means nobody measured; a manifest with no passing ancestor
    means somebody measured and it did not pass. Collapsing them would make the
    friendlier of the two absorb the alarming one.
    """
    if not certification.get("known"):
        return "unknown — no certification manifest to read"
    if uncertified := certification.get("uncertified_executable"):
        return (
            f"**NOT CERTIFIED** — {len(uncertified)} commit(s) since "
            f"`{certification['commit'][:12]}` change executable code: "
            f"{', '.join(uncertified[:3])}"
        )
    if not certification.get("certified"):
        return "**NOT CERTIFIED** — no certified build in this commit's history"

    coverage = certification.get("coverage")
    measured = f", coverage {coverage:.2f}%" if isinstance(coverage, (int, float)) else ""
    since = certification.get("commits_since", 0)
    verdict = f"certified{measured}"
    if since:
        verdict += f" at `{certification['commit'][:12]}`, +{since} Closeout commit(s)"
    if long:
        verdict += f" — {certification['certified_at']}"
    return verdict


def _render(session: dict[str, Any]) -> str:
    verdict = _verdict(session["certification"], long=True)
    lines = [
        f"# Review session {session['id']}",
        "",
        f"- **Commit** `{session['commit'][:12]}` on `{session['branch']}`"
        + ("" if session["tree_clean"] else " — **working tree was dirty**"),
        f"- **Build verification** {verdict}",
        f"- **Dataset** `{session['dataset']}` — {session['seeded_accounts']}",
        f"- **Application** {session['url']}",
        f"- **Started** {session['started_at']}",
    ]
    if session.get("ended_at"):
        lines.append(f"- **Ended** {session['ended_at']} ({session['duration_minutes']} minutes)")
    lines += ["", "## Sign-in", "", f"Password for all accounts: `{session['password']}`", ""]
    lines += ["| Email | Persona | Role |", "|---|---|---|"]
    lines += [
        f"| `{account['email']}` | {account['persona']} | {account['role']} |"
        for account in session["accounts"]
    ]
    lines += ["", "## Known limitations at this commit", ""]
    lines += [f"- {limitation}" for limitation in session["known_limitations"]] or [
        "- none a reviewer could meet"
    ]
    if hidden := session.get("limitations_not_reachable"):
        lines += [
            "",
            f"*{hidden} further open defect(s) are in repository tooling, process or "
            "documentation — invisible from a browser, and listed in `docs/BUGS.md`. "
            "Nothing is hidden; they are simply not reachable from this session.*",
        ]
    if session.get("notes"):
        lines += ["", "## Product notes", ""] + [f"- {note}" for note in session["notes"]]
    lines += [
        "",
        "---",
        "",
        "*Written by `infra/review.py`. Every field is measured from the repository "
        "at the moment the session started; nothing here is entered by hand except "
        "the product notes.*",
        "",
    ]
    return "\n".join(lines)


# ── commands ────────────────────────────────────────────────────────────────


def start() -> int:
    existing = _load()
    if existing and not existing.get("ended_at"):
        print(f"\n  A review session is already running — {existing['id']}\n")
        print(f"    {existing['url']}")
        print("\n  `make review-end` closes it, `make review-status` describes it.\n")
        return 2

    print("\n  Preparing a review session\n")

    print("  1  validate")
    problems = _validate()
    if problems:
        print("\n  BLOCKED — the workstation is not ready for a review\n")
        for problem in problems:
            print(f"    ✗ {problem}")
        print("\n  Nothing was started, and nothing was changed.\n")
        return 3
    print("     workstation ready")

    print("  2  seed")
    frontend_env = {**os.environ, **_dotenv(REPO_ROOT / "frontend" / ".env.local")}
    if subprocess.run(
        ["make", "demo-prepare"], cwd=REPO_ROOT, env=frontend_env, check=False
    ).returncode:
        print("\n  BLOCKED — preparation failed. Its output is above.\n")
        return 3

    print("\n  3  present")
    SESSIONS.mkdir(parents=True, exist_ok=True)
    identifier = f"{datetime.now(UTC):%Y%m%d-%H%M%S}-{_git('rev-parse', '--short', 'HEAD')}"
    directory = SESSIONS / identifier
    directory.mkdir(parents=True, exist_ok=True)

    api_pid = _spawn(
        [
            "uv", "run", "uvicorn", "apps.api.main:create_app",
            "--factory", "--reload", "--port", str(PROFILE.api_port),
        ],
        cwd=REPO_ROOT / "backend",
        log=directory / "api.log",
        env=_api_environment(),
    )
    web_pid = _spawn(
        ["npm", "run", "dev", "--", "--port", str(PROFILE.web_port)],
        cwd=REPO_ROOT / "frontend",
        log=directory / "web.log",
        env=frontend_env,
    )

    url = f"http://localhost:{PROFILE.web_port}"
    if not _await(f"http://localhost:{PROFILE.api_port}/health", label="the API", timeout=READY_TIMEOUT):
        print(f"\n  BLOCKED — the API never answered. {directory / 'api.log'}\n")
        _stop([api_pid, web_pid])
        return 3
    if not _await(url, label="the product", timeout=READY_TIMEOUT):
        print(f"\n  BLOCKED — the product never answered. {directory / 'web.log'}\n")
        _stop([api_pid, web_pid])
        return 3

    commit = _git("rev-parse", "HEAD")
    password, accounts = _accounts()
    limitations, hidden = _known_limitations()
    session: dict[str, Any] = {
        "id": identifier,
        "commit": commit,
        "branch": _git("rev-parse", "--abbrev-ref", "HEAD"),
        "tree_clean": not _git("status", "--porcelain"),
        "certification": _build_verification(commit),
        "dataset": _dataset(),
        "seeded_accounts": "twelve accounts through the real pipeline",
        "url": url,
        "api_url": f"http://localhost:{PROFILE.api_port}",
        "password": password,
        "accounts": accounts,
        "known_limitations": limitations,
        "limitations_not_reachable": hidden,
        "pids": {"api": api_pid, "web": web_pid},
        "logs": {"api": str(directory / "api.log"), "web": str(directory / "web.log")},
        "started_at": datetime.now(UTC).isoformat(timespec="seconds"),
        "ended_at": "",
        "notes": [],
    }
    _write(session)
    _card(session)
    webbrowser.open(url)
    return 0


def _card(session: dict[str, Any]) -> None:
    """What the reviewer reads. **The only output that matters.**"""
    verdict = _verdict(session["certification"], long=False)
    print("\n\n  ✓  Review environment ready\n")
    print(f"     Application   {session['url']}")
    print(f"     API           {session['api_url']}/docs")
    print(f"     Commit        {session['commit'][:12]} on {session['branch']}")
    print(f"     Build         {verdict}")
    print(f"     Dataset       {session['dataset']} — {session['seeded_accounts']}")
    print(f"\n     Sign in as    {session['accounts'][0]['email']}")
    print(f"     Password      {session['password']}")
    print(f"                   three more accounts in {SESSIONS / session['id'] / 'summary.md'}")
    limitations = session["known_limitations"]
    if limitations:
        print(f"\n     Known issues  {len(limitations)} you could meet in the product:")
        for limitation in limitations[:4]:
            print(f"                   {limitation}")
        if len(limitations) > 4:
            print(f"                   … and {len(limitations) - 4} more in docs/BUGS.md")
    else:
        print("\n     Known issues  none open that a reviewer could reach")
    print(f"\n     Logs          {session['logs']['web']}")
    print("                   the sign-up verification link is written there")
    print("\n     When finished  make review-end\n")


def _stop(pids: list[int], *, grace: int = 10) -> bool:
    """Stop the tiers, and **wait until they are actually gone.**

    The first version signalled and returned, so `end` printed *"ports are
    released"* while the sockets were still bound — `release-preflight` run
    immediately afterwards still reported a live review session. A false
    sentence, and the reviewer's next action (`make certify`) would have failed
    on it. **A claim is made after it is true, or it is not made.**
    """
    for pid in pids:
        try:
            os.killpg(os.getpgid(pid), signal.SIGTERM)
        except (ProcessLookupError, PermissionError):
            pass

    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        if not any(_alive(pid) for pid in pids):
            break
        time.sleep(0.25)

    for pid in (pid for pid in pids if _alive(pid)):
        try:
            os.killpg(os.getpgid(pid), signal.SIGKILL)
        except (ProcessLookupError, PermissionError):
            pass

    # The ports are what the next operation needs, and a process can be gone a
    # moment before its listening socket is.
    deadline = time.monotonic() + grace
    while time.monotonic() < deadline:
        if not (_listening(PROFILE.web_port) or _listening(PROFILE.api_port)):
            return True
        time.sleep(0.25)
    return False


def end(notes: list[str]) -> int:
    session = _load()
    if session is None or session.get("ended_at"):
        print("\n  No review session is running.\n")
        return 2
    released = _stop(list(session["pids"].values()))
    started = datetime.fromisoformat(session["started_at"])
    ended = datetime.now(UTC)
    session["ended_at"] = ended.isoformat(timespec="seconds")
    session["duration_minutes"] = round((ended - started).total_seconds() / 60)
    session["notes"] = notes
    directory = _write(session)
    POINTER.unlink(missing_ok=True)
    print(f"\n  Review session {session['id']} closed after {session['duration_minutes']} minutes\n")
    print(f"    {directory / 'summary.md'}")
    print("\n  The seeded data is untouched — `make review` resumes from it.")
    if released:
        print(f"  Ports {PROFILE.web_port} and {PROFILE.api_port} are free — `make certify` may run.\n")
    else:
        print(
            f"  ⚠️  Ports {PROFILE.web_port}/{PROFILE.api_port} are still held by something this"
            "\n      session did not start. `python3 infra/release-preflight.py` names it.\n"
        )
    return 0


def status() -> int:
    session = _load()
    if session is None or session.get("ended_at"):
        print("\n  No review session is running.\n")
        past = sorted(SESSIONS.glob("*/session.json")) if SESSIONS.exists() else []
        if past:
            print(f"    {len(past)} recorded session(s) in {SESSIONS}\n")
        return 0
    alive = [tier for tier, pid in session["pids"].items() if _alive(pid)]
    print(f"\n  Review session {session['id']} — started {session['started_at']}\n")
    print(f"    {session['url']}")
    print(f"    tiers running: {', '.join(alive) if alive else 'none — the session died'}")
    print(f"    {SESSIONS / session['id'] / 'summary.md'}\n")
    return 0


def _alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="action")
    sub.add_parser("start", help="prepare, validate, seed, present, record")
    sub.add_parser("status", help="is a review running?")
    ender = sub.add_parser("end", help="stop the session and finalize its record")
    ender.add_argument("--note", action="append", default=[], help="a product note; repeatable")
    args = parser.parse_args()

    if args.action == "end":
        return end(args.note)
    if args.action == "status":
        return status()
    return start()


if __name__ == "__main__":
    sys.exit(main())
