#!/usr/bin/env python3
"""**Make this machine able to run Signora, and say what that cost.**

RS-2. *Repository Health · **Configuration Safety**.*

`backend/.env` and `frontend/.env.local` hold a generated RSA pair and a signing
secret. They are **correctly never committed** (`CLAUDE.md` §13) and they are
**not reproducible** — regenerating the pair invalidates every existing session,
and a *mismatched* pair mints tokens the API rejects with no clue why. So they
sit in none of the four resilience states: not repository, not generated, not a
versioned artifact, not disposable ([`REPOSITORY_RESILIENCE.md`](../docs/REPOSITORY_RESILIENCE.md) §2).

**What was missing is the command, not the category.** QE reconstructed
`frontend/.env.local` on 2026-08-03 by reading four files and writing a
throwaway script, and **nothing in the repository described that as a
procedure** — which is R-5's exposure, measured on QE itself.

### The step this removes

`RUNNING.md`'s quickstart said *"`npm run keys:generate` — paste both halves
in"*. **Pasting is where it goes wrong**, and the failure is silent in the worst
way: the public half lands in `backend/.env`, the private half in
`frontend/.env.local`, and if they are from different runs every request 401s
with nothing naming the cause. The key material also has to survive being
copied through a terminal with embedded newlines escaped.

**Generating both files from one pair removes the transcription entirely.**

### What it deliberately will not do

**It never overwrites an existing file without being told to.** A `.env` holds
the only copy of a working pair, and a setup command that quietly replaced one
would be the class of defect this whole document is about. `--force` exists and
prints what it is about to invalidate.

**It writes no production value.** Every credential below is a local development
one, already committed in the `.example` files it reads. Production configuration
comes from AWS Secrets Manager ([ADR-0022](../docs/architecture/adr/0022-devops-infrastructure-and-deployment-topology.md)).

    python3 infra/workstation.py            # set up what is missing
    python3 infra/workstation.py --check    # report, change nothing
    python3 infra/workstation.py --force    # regenerate the pair, invalidating sessions
"""

from __future__ import annotations

import argparse
import re
import secrets
import os
import subprocess
import sys
from pathlib import Path
from typing import Final

REPO_ROOT: Final = Path(__file__).resolve().parent.parent
BACKEND_ENV: Final = REPO_ROOT / "backend" / ".env"
FRONTEND_ENV: Final = REPO_ROOT / "frontend" / ".env.local"

#: Values with no safe default, from `frontend/.env.example`'s own warnings.
#: **The auth database is per-environment** — sharing it is [B-104](../docs/BUGS.md),
#: where a review session wrote users into another environment's database.
REQUIRED_FRONTEND: Final = (
    "SIGNORA_AUTH_DATABASE_URL",
    "BETTER_AUTH_SECRET",
    "SIGNORA_JWT_PRIVATE_KEY",
)


#: The three that must name ONE database, and the order a reader would set them.
#:
#: 🔴 **Setting a subset is the trap this pair of names exists to catch.** The
#: suite then reads a DIFFERENT database from the one the migrations ran
#: against and reports ``relation "action_batch" does not exist`` — **against a
#: schema already at head 0046.** ⛔ **The diagnostic points at migrations, and
#: migrations are fine**, so the search starts in the wrong place.
#:
#: ⚠️ **Measured cost: twice.** The first occurrence took two lanes an hour
#: (`B-228`, which was WITHDRAWN — the seeder was never broken, the invocation
#: had split one database into two). The second cost Lane A part of a slice on
#: 2026-08-10, with only ``SIGNORA_TEST_APP_DATABASE_URL`` set.
#:
#: ✅ **Checked only when at least one is set** — a clone configuring no test
#: run has nothing to disagree about, which keeps this silent on a Product
#: Office clone that holds no database at all (`CLAUDE.md` §20e).
TEST_DATABASE_VARS: Final = (
    "SIGNORA_TEST_ADMIN_DATABASE_URL",
    "SIGNORA_TEST_APP_DATABASE_URL",
    "SIGNORA_DATABASE_URL",
)


def _database_name(url: str) -> str:
    """The database a URL names, ignoring credentials, host and query."""
    return url.rsplit("/", 1)[-1].split("?", 1)[0]


def test_database_findings(env: dict[str, str]) -> list[str]:
    """Do the three test database variables agree, if any of them is set?

    **A pure function of its argument**, so the trap can be reproduced in a
    test without touching the process environment — which is what makes this a
    guard rather than a comment (`CLAUDE.md` §2).
    """
    present = {k: v for k in TEST_DATABASE_VARS if (v := env.get(k, "").strip())}
    if not present:
        return []

    findings: list[str] = []
    absent = [k for k in TEST_DATABASE_VARS if k not in present]
    if absent:
        findings.append(
            f"{len(present)} of 3 test database variables set — {', '.join(absent)} "
            f"missing. The suite will read a DIFFERENT database from the one "
            f"migrations ran against and report `relation ... does not exist` "
            f"against a schema that is already at head. Set all three to one database"
        )

    names = {_database_name(v) for v in present.values()}
    if len(names) > 1:
        findings.append(
            f"the test database variables name {len(names)} different databases — "
            f"{', '.join(sorted(names))}. They must name one"
        )
    return findings


def _profile(name: str) -> object:
    sys.path.insert(0, str(REPO_ROOT / "infra"))
    import environments

    return environments.BY_NAME[name]


def _generate_pair() -> tuple[str, str]:
    """One RSA pair, from the repository's own generator.

    **`npm run keys:generate` rather than a second implementation.** It already
    prints both halves escaped for a `.env` file, it is the command `RUNNING.md`
    documents, and a duplicate here would drift from it the first time the
    format changed.
    """
    printed = subprocess.run(
        ["npm", "run", "--silent", "keys:generate"],
        cwd=REPO_ROOT / "frontend",
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    private = re.search(r'SIGNORA_JWT_PRIVATE_KEY="([^"]+)"', printed)
    public = re.search(r'SIGNORA_JWT_PUBLIC_KEY="([^"]+)"', printed)
    if not (private and public):
        raise RuntimeError(
            "npm run keys:generate did not print a pair in the expected form. "
            "Its output format changed, and this would otherwise write an empty key."
        )
    return private.group(1), public.group(1)


def _set(text: str, key: str, value: str) -> str:
    """Replace a `KEY=…` line, or append it. Comments and order are preserved."""
    line = f"{key}={value}"
    if re.search(rf"^{key}=", text, re.M):
        return re.sub(rf"^{key}=.*$", line, text, count=1, flags=re.M)
    return text.rstrip() + f"\n{line}\n"


def _missing(path: Path, keys: tuple[str, ...]) -> list[str]:
    if not path.exists():
        return list(keys)
    text = path.read_text()
    return [key for key in keys if not re.search(rf"^{key}=\S", text, re.M)]


def public_key(path: Path) -> str | None:
    """The PEM a tier holds, **normalised**, or `None`.

    **Two encodings of one key are the same key**, and the first version of this
    check did not know that. `.env.example` writes the PEM escaped onto one line
    (`\\n` between armour and body); a value pasted from `openssl` arrives as
    real newlines inside quotes. Comparing the raw text reported *"the two tiers
    hold DIFFERENT public keys"* about a correctly configured workstation whose
    halves were verified matching by `openssl rsa -pubout`.

    **A setup check that cries wolf is worse than no setup check** — it sends
    somebody to regenerate a working pair, which is the one destructive thing
    this command can do.
    """
    if not path.exists():
        return None
    found = re.search(r'^SIGNORA_JWT_PUBLIC_KEY="(.*?)"', path.read_text(), re.S | re.M)
    return found.group(1).replace("\\n", "\n").strip() if found else None


def check() -> int:
    """Report; change nothing. **The mode a gate would use.**"""
    print("\n  Workstation — can this machine run Signora?\n")
    problems: list[str] = []

    for path, keys in ((BACKEND_ENV, ()), (FRONTEND_ENV, REQUIRED_FRONTEND)):
        if not path.exists():
            problems.append(f"{path.relative_to(REPO_ROOT)} is missing")
            continue
        for key in _missing(path, keys):
            problems.append(f"{key} is not set in {path.relative_to(REPO_ROOT)} — it has no default")

    if BACKEND_ENV.exists() and FRONTEND_ENV.exists():
        backend = public_key(BACKEND_ENV)
        frontend = public_key(FRONTEND_ENV)
        if backend and frontend and backend != frontend:
            # **The failure this command exists to prevent.** A mismatched pair
            # mints tokens successfully and 401s every request, with nothing in
            # either tier naming the cause.
            problems.append(
                "the two tiers hold DIFFERENT public keys — every request will 401 "
                "with no diagnostic. `--force` regenerates a matched pair"
            )

    problems.extend(test_database_findings(dict(os.environ)))

    if problems:
        for problem in problems:
            print(f"    ✗ {problem}")
        print("\n  `make workstation` fixes these.\n")
        return 1
    print("    ✓ both env files present, required values set, key pair matched\n")
    return 0


def setup(*, force: bool) -> int:
    review = _profile("review")
    existing = BACKEND_ENV.exists() and FRONTEND_ENV.exists() and not _missing(
        FRONTEND_ENV, REQUIRED_FRONTEND
    )

    if existing and not force:
        print("\n  Workstation already configured. Nothing changed.\n")
        return check()

    if existing and force:
        # **Say what is about to be lost, before losing it.** Regenerating is
        # not free: every issued token stops verifying, and anybody signed in
        # is signed out. That is recoverable — sign in again — but it must not
        # be a surprise.
        print(
            "\n  ⚠️  Regenerating the key pair.\n"
            "\n     Every existing session stops verifying and every signed-in user is"
            "\n     signed out. Sign in again afterwards; no data is lost.\n"
        )

    private, public = _generate_pair()
    secret = secrets.token_urlsafe(32)

    if not BACKEND_ENV.exists():
        BACKEND_ENV.write_text((REPO_ROOT / "backend" / ".env.example").read_text())
    backend = BACKEND_ENV.read_text()
    backend = _set(backend, "SIGNORA_JWT_PUBLIC_KEY", f'"{public}"')
    BACKEND_ENV.write_text(backend)

    if not FRONTEND_ENV.exists():
        FRONTEND_ENV.write_text((REPO_ROOT / "frontend" / ".env.example").read_text())
    frontend = FRONTEND_ENV.read_text()
    for key, value in (
        # **The public half goes to both tiers deliberately.** The frontend's copy
        # lets startup verify the pair actually matches; without it a mismatched
        # pair is only discovered as a 401 storm (`frontend/.env.example`).
        ("SIGNORA_JWT_PRIVATE_KEY", f'"{private}"'),
        ("SIGNORA_JWT_PUBLIC_KEY", f'"{public}"'),
        ("BETTER_AUTH_SECRET", secret),
        (
            "SIGNORA_AUTH_DATABASE_URL",
            f"postgresql://signora_auth:signora_auth_local_dev@localhost:5432/{review.database}",  # type: ignore[attr-defined]
        ),
    ):
        frontend = _set(frontend, key, value)
    FRONTEND_ENV.write_text(frontend)

    print("\n  Workstation configured\n")
    print(f"    backend/.env         public key only — it can verify, never mint (ADR-0026)")
    print(f"    frontend/.env.local  private key, a fresh BETTER_AUTH_SECRET, auth database")
    print(f"    auth database        {review.database}  (the `review` profile)")  # type: ignore[attr-defined]
    print(
        "\n  **The signing secret is generated, not copied.** `.env.example` carries a"
        "\n  committed one, and every clone using it signs JWTs any other clone can"
        "\n  forge ([B-104](../docs/BUGS.md)).\n"
        "\n  Next:  make review\n"
    )
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="report, change nothing")
    parser.add_argument(
        "--force", action="store_true", help="regenerate the key pair, invalidating sessions"
    )
    args = parser.parse_args()
    return check() if args.check else setup(force=args.force)


if __name__ == "__main__":
    sys.exit(main())
