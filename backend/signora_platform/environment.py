"""**Which deployment this process is, in one closed vocabulary.**

[ADR-0412](../../docs/architecture/adr/0412-environment-and-secret-safe-logging.md),
ratified as [C-298](../../docs/LANE_COORDINATION.md): *"`SIGNORA_ENVIRONMENT`
is the single name, defined consistently across the application and the
runtime"*, and *"do not create a second environment taxonomy."*

### 🔴 There were three, and the intersections were empty

**The defect C-298 recorded, measured before this file was written:**

| Reader | Called it development | Otherwise |
|---|---|---|
| `ai_platform` | **`local` alone** | ⛔ the deterministic mock is refused |
| the auth tier | `local` · `test` · `development` | ⛔ console and mailbox email transports refused |
| `infra/environments.py` | `review` · `lane-a`…`lane-e` · `demo` · `prod-local` | resolves to `None` |

⚠️ **Two values make it concrete.** `development` was local to the auth tier
and deployed to the AI Platform, **so a fresh clone would have needed Ollama**
— which [ADR-0028](../../docs/architecture/adr/0028-model-runtime-by-environment.md)
forbids in as many words. And `lane-a` — **the value `infra/environments.py`
defines, and whose own docstring invites a lane to set it** — read as deployed
to both, **breaking development twice at once** and explaining neither.

### ⚡ One variable, one question

**This enum answers *"what kind of deployment is this?"* and nothing else.**
⛔ **It does not answer *"which ports, which database, which Redis index"*** —
that is `infra/environments.py`'s stack allocation, a genuinely different fact
about the same process. **A value that answers one cannot answer the other**,
and a Security Invariant pins that the two name spaces stay disjoint.

### ⛔ Why an enum rather than a string

📁 [§2](../../CLAUDE.md), *types should make incorrect architecture
impossible*. **An unrecognised environment must be unrepresentable, never
silently treated as development** — ADR-0412 §2 — and a `str` comparison is
exactly the shape that treats an unknown value as *"not production"* by
accident. **Two tiers cannot drift apart on a closed set the way they drifted
apart on two string literals.**
"""

from __future__ import annotations

from enum import StrEnum


class SignoraEnvironment(StrEnum):
    """What kind of deployment this process is.

    ⚠️ **`development` is deliberately absent, and `local` is the member that
    replaces it.** The auth tier accepted both and they meant one thing — 📁
    [§2](../../CLAUDE.md), *truth has exactly one authoritative
    representation*. **Two spellings of one environment is how a guard comes to
    be written against the spelling somebody happened to use.**
    """

    LOCAL = "local"
    """A developer's own machine. **The default a fresh clone is productive
    on**, and the only one where the deterministic mock provider may serve."""

    TEST = "test"
    """An automated test run. **Development for every safety purpose** — it
    holds no customer data and serves nobody."""

    DEMO = "demo"
    """The demonstration stack. ⛔ **Deployed**, because somebody who is not
    the person who started it is looking at it."""

    PRODUCTION_LOCAL = "production-local"
    """**Production-shaped, on a developer's machine** — what `make smoke` and
    `make dr` exercise.

    ⚠️ **A real member rather than a convenience alias**, because it is a real
    thing: the production composition, running locally. **It is deployed for
    every safety purpose**, which is what makes it worth exercising — a stack
    that relaxed the rules would prove nothing about the one it stands in for.
    """

    STAGING = "staging"
    PRODUCTION = "production"

    @property
    def is_development(self) -> bool:
        """**Whether it is safe to serve a stub or write a credential to stdout.**

        ⛔ **The single answer both tiers read.** It replaces `!= "local"` in
        the AI Platform and `!['local','test','development']` in the auth tier
        — **two independent lists that disagreed**, which is the whole of
        C-298.

        ⚡ **Stated as *development* rather than *not deployed*** so the two
        tiers cannot re-diverge by negating it differently, which is how one
        list came to have three members and the other one.
        """
        return self in _DEVELOPMENT


#: **Deliberately not `not in {STAGING, PRODUCTION, ...}`.** An allow-list
#: makes a new member deployed by default; a deny-list would make it
#: development by default, and the safe direction for a value nobody has
#: thought about yet is the restrictive one.
_DEVELOPMENT = frozenset({SignoraEnvironment.LOCAL, SignoraEnvironment.TEST})


__all__ = ["SignoraEnvironment"]
