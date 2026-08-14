"""**The environment vocabulary agrees across tiers.** [ADR-0412](../../../docs/architecture/adr/0412-environment-and-secret-safe-logging.md) §4.

The ADR asks for two invariants and this is the second — *"the one that would
actually have caught [C-298](../../../docs/LANE_COORDINATION.md)"*, whose whole
subject is that **the auth tier and the registry do not agree what an
environment is called.** ⛔ *"Two tiers disagreeing about a name is invisible
until the day it matters."*

### 🔴 What the measurement found, before any of this was written

**Four readers of `SIGNORA_ENVIRONMENT`, and three different answers to *"is
this a development environment?"***

| Reader | Said development | Otherwise |
|---|---|---|
| `ai_platform/infrastructure/composition.py` | **`local` alone** | ⛔ the deterministic mock **refused** |
| `frontend/lib/auth/config.ts` `isDeployed()` | `local` · `test` · `development` | ⛔ console and mailbox email transports **refused** |
| `infra/environments.py` | `review` · `lane-qe` · `lane-a`…`lane-e` · `demo` · `prod-local` | resolves to `None`, silently falling back to the shared stack |

⚠️ **The intersections were empty in both directions**, and two values made it
concrete:

- **`development`** — the auth tier called it local; **`ai_platform` refused
  the mock**, so a fresh clone would have needed Ollama, which
  [ADR-0028](../../../docs/architecture/adr/0028-model-runtime-by-environment.md)
  forbids in as many words.
- **`lane-a`** — the value `infra/environments.py` *defines*, and whose own
  docstring invites a lane to set it: *"a lane driving a stack that is not its
  own must be able to say so out loud."* ⛔ **It broke development twice** —
  the mock refused **and** the console email transport throwing at startup.

### ⚡ What this file asserts

**Agreement, and the disjointness of two name spaces.** Which members exist is
[ADR-0412](../../../docs/architecture/adr/0412-environment-and-secret-safe-logging.md)
§7's *"deliberately does not decide"* list, proposed in the Slice Handoff —
**what may never happen is two tiers answering one question differently.**
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from signora_platform.environment import SignoraEnvironment

#: The auth tier's own list, **read from source rather than restated** — a copy
#: here would be the second representation this file exists to forbid, and it
#: would agree with itself forever while the tier drifted.
_FRONTEND_CONFIG = (
    Path(__file__).resolve().parents[3] / "frontend" / "lib" / "auth" / "config.ts"
)


def _frontend_development_names() -> frozenset[str]:
    """What the auth tier treats as *not deployed*."""
    source = _FRONTEND_CONFIG.read_text()
    match = re.search(r"isDeployed\(\)[^{]*\{\s*return !\[([^\]]*)\]", source)
    assert match, (
        "frontend/lib/auth/config.ts no longer exposes isDeployed() in the shape this "
        "invariant reads. **That is a finding, not a reason to weaken the check** — "
        "the guarantee is that the tiers agree, and a check that cannot read one of "
        "them has stopped proving it."
    )
    return frozenset(
        name.strip().strip("'\"") for name in match.group(1).split(",") if name.strip()
    )


def _backend_development_names() -> frozenset[str]:
    """The closed vocabulary's own answer — **the authority, not a copy.**

    ⚡ **This is what changed when C-298 was fixed.** It used to read a string
    literal out of `ai_platform`'s guard, because there was nothing else to
    read: that tier's answer *was* a comparison against `"local"`. Both tiers
    now derive from `SignoraEnvironment.is_development`.
    """
    return frozenset(member.value for member in SignoraEnvironment if member.is_development)


def test_both_tiers_agree_which_environments_are_development() -> None:
    """🔴 **The invariant C-298 asked for.**

    ⛔ **Not *"each tier is individually sensible"*** — both were. The defect is
    that one question had two answers, and **the day it matters is the day a
    deployment reads one tier's answer and gets the other tier's behaviour.**
    """
    frontend = _frontend_development_names()
    backend = _backend_development_names()

    assert frontend == backend, (
        f"the auth tier treats {sorted(frontend)} as development and the closed "
        f"vocabulary treats {sorted(backend)} — one variable, two answers. A value in "
        "the difference is development to one tier and deployed to the other, and "
        "ADR-0412 §2 requires identical semantics across tiers."
    )


@pytest.mark.parametrize("name", ["local", "test", "development", "production", "demo"])
def test_a_name_either_side_calls_development_is_development_to_both(name: str) -> None:
    """The same guarantee stated per value, so a failure names the value rather
    than only a set difference — **which is what an engineer reading a red build
    actually needs.**"""
    frontend = _frontend_development_names()
    backend = _backend_development_names()

    assert (name in frontend) == (name in backend), (
        f"SIGNORA_ENVIRONMENT={name!r} is development to "
        f"{'the auth tier' if name in frontend else 'the closed vocabulary'} and not to "
        f"{'the closed vocabulary' if name in frontend else 'the auth tier'}."
    )


def test_no_stack_name_is_a_member_of_the_deployment_vocabulary() -> None:
    """⛔ **`SIGNORA_ENVIRONMENT` carries ONE concept.**

    `infra/environments.py` names **stacks** — `lane-a`, `review`, `demo` —
    answering *"which ports, which database, which Redis index"*. The
    vocabulary answers *"is it safe to serve a stub, or to write a credential
    to stdout"*. **Different questions, and a value that answers one cannot
    answer the other.**

    ⚠️ **`demo` is deliberately excluded from this check and IS a member**, and
    the collision is real rather than an oversight: the demonstration stack and
    the demonstration deployment class are the same thing by intent. **Every
    other stack name must stay out.**
    """
    stack_only = frozenset({"lane-a", "lane-b", "lane-c", "lane-qe", "review", "prod-local"})

    overlap = stack_only & frozenset(member.value for member in SignoraEnvironment)

    assert not overlap, (
        f"{sorted(overlap)} names a STACK in infra/environments.py and a DEPLOYMENT "
        "CLASS in the vocabulary. One variable cannot answer both questions — which "
        "is what made SIGNORA_ENVIRONMENT=lane-a break development twice."
    )


def test_an_unrecognised_environment_is_unrepresentable() -> None:
    """📁 ADR-0412 §2: *"an unrecognised environment value must be
    unrepresentable, never silently treated as development."* ⛔ **A `str` field
    is exactly the shape that treats an unknown value as *not production* by
    accident.**"""
    with pytest.raises(ValueError):
        SignoraEnvironment("prod")


def test_a_value_outside_the_vocabulary_would_not_be_development() -> None:
    """The safe direction, asserted rather than assumed: `is_development` is an
    **allow-list**, so a member added later is deployed until somebody says
    otherwise."""
    assert not SignoraEnvironment.PRODUCTION.is_development
    assert not SignoraEnvironment.PRODUCTION_LOCAL.is_development
    assert not SignoraEnvironment.STAGING.is_development
    assert not SignoraEnvironment.DEMO.is_development
    assert SignoraEnvironment.LOCAL.is_development
    assert SignoraEnvironment.TEST.is_development


#: Every backend module that reads `SIGNORA_ENVIRONMENT` and guards on it.
#: **Three of them, and all three compared against a string literal** before
#: ADR-0412 — `!= "local"` in the AI Platform and in the Provider Platform,
#: and a three-name list in the auth tier.
_GUARDING_MODULES = (
    Path(__file__).resolve().parents[2] / "modules" / "ai_platform" / "infrastructure",
    Path(__file__).resolve().parents[2] / "modules" / "provider_platform" / "infrastructure",
)


@pytest.mark.parametrize("package", _GUARDING_MODULES, ids=lambda p: p.parent.name)
def test_no_module_decides_development_by_comparing_a_string(package: Path) -> None:
    """⛔ **The re-divergence guard, and it is the one that matters.**

    Aligning three readers once is worth nothing if the fourth is written the
    old way. 🔴 **Every one of them compared `settings.environment` against a
    string literal**, and **none of the comparisons was ever compared with
    another** — which is C-298 stated mechanically.

    ⚡ **`is_development` is the only permitted answer**, so a module cannot
    hold a private opinion about what `local` means. **A new guard written as
    `!= "local"` fails here rather than being discovered by a lane whose
    development environment stopped working.**
    """
    offenders = [
        f"{source.name}:{number}"
        for source in package.rglob("*.py")
        for number, line in enumerate(source.read_text().splitlines(), start=1)
        if re.search(r"""\.environment\s*[!=]=\s*['"]""", line)
    ]

    assert not offenders, (
        f"{offenders} decides an environment by comparing a string. Use "
        "`SignoraEnvironment.is_development` — ADR-0412 §2, and the reason C-298 "
        "existed: three modules each held their own list and none was ever compared "
        "with another."
    )
