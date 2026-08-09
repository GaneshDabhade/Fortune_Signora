"""What happened to an account, recorded once and never edited.

**[TASK-492](../../../../docs/BACKLOG.md)**, migration `0046`, on
[493 §5](../../../../docs/architecture/493-security-platform-architecture.md)
and [496 §3](../../../../docs/architecture/496-security-architecture-blueprint.md).

### It is an account-activity stream, not a security log

**A security-only log means building the second one later** (493 §5).
Compliance, support and the customer's own timeline all read the same facts,
and a stream scoped to *security* is re-derived the first time somebody asks
*"what happened to my account?"* — which is the same question with a different
reader.

### 🔴 The two identities, and why a type refuses what a convention allows

> **Every event carries `subject_id` AND `acting_for`, both always** (496 §3).

**A line naming only the agent cannot answer *who authorised this*. A line
naming only the human is a lie whenever an agent acted.**

⛔ **Neither is optional and neither has a default**, which is
[§2](../../../../CLAUDE.md)'s *types should make incorrect architecture
impossible* applied to attribution: **a caller that has only one identity
cannot construct an event at all**, so the question *on whose authority?* is
answered at the call site or not asked. **When a person acts directly the two
are equal** — {@link SecurityEvent.self_directed} says so, and
{@link SecurityEvent.on_behalf} is the case an auditor is looking for.

### ⛔ `detail` is context, never payload

**Whatever the producing module needs to make its own line readable** — a role
that changed, an address a link went to. ⛔ **Never a credential, never a
token, never a password** ([§13](../../../../CLAUDE.md),
[§16](../../../../CLAUDE.md)): **this stream is read by support and by
compliance**, which is exactly the population that must never be handed one.
{@link SecurityEvent} refuses a key from {@link FORBIDDEN_DETAIL_KEYS} rather
than trusting every future producer to remember.

### Why `kind` is a string here and a constant in the producer

**Every module publishes into this stream.** A native enum would make a new
event kind a migration on a type every module's inserts depend on — so the
database constrains *presence and length*, and the domain constrains *shape*:
lower snake case, dotted, `noun.verb_past`. **The vocabulary lives with the
producer that owns the fact**, which is the same reason
[06-events.md](../../../../docs/architecture/06-events.md) catalogues event
types rather than the platform owning them.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Final
from uuid import UUID

#: 📁 `noun.verb_past` — *"a fact about a moment"*, so the verb is past tense.
#: **Checked rather than described**: a stream carrying `sign_in` beside
#: `session.signed_in` is a stream nobody can filter.
KIND_PATTERN: Final = re.compile(r"^[a-z][a-z0-9_]*\.[a-z][a-z0-9_]*$")

#: The database's `character varying(80)`, named here so the two agree.
MAX_KIND_LENGTH: Final = 80

#: ⛔ **Keys a detail payload may never carry.**
#:
#: **Not a sanitiser and not a scrubber** — it *refuses*. A stream read by
#: support and compliance must never be the place a credential turns up, and
#: silently dropping the key would leave the producer believing it recorded
#: something. **The failure is loud at the call site, where it can be fixed.**
FORBIDDEN_DETAIL_KEYS: Final[frozenset[str]] = frozenset(
    {
        "password",
        "new_password",
        "current_password",
        "token",
        "access_token",
        "refresh_token",
        "id_token",
        "secret",
        "client_secret",
        "api_key",
        "authorization",
        "session_token",
        "credential",
    }
)


class ForbiddenDetailKey(ValueError):
    """A producer tried to record a credential in the activity stream.

    ⛔ **A `ValueError` rather than a filtered dictionary.** Dropping the key
    quietly would leave the producer believing the value was recorded, and the
    first person to notice would be an auditor reading a gap.
    """

    def __init__(self, key: str) -> None:
        super().__init__(
            f"`{key}` may not be recorded in a security event. This stream is read by "
            "support and by compliance; a credential in it is a credential disclosed "
            "(CLAUDE.md §13, §16). Record that the thing happened, never the secret."
        )
        self.key = key


class MalformedEventKind(ValueError):
    """The kind is not `noun.verb_past` in lower snake case."""

    def __init__(self, kind: str, why: str) -> None:
        super().__init__(f"security event kind {kind!r} is {why}")
        self.kind = kind


@dataclass(frozen=True, slots=True)
class SecurityEvent:
    """One thing that happened, stated once.

    **Frozen, because it records something that WAS true**
    ([§2](../../../../CLAUDE.md), *immutability is the default for anything
    that records a fact*). ⛔ **The table has no `UPDATE` grant and this type
    has no setter** — the two agree by construction rather than by review.
    """

    workspace_id: UUID
    kind: str
    #: Who the event is **about**.
    subject_id: UUID
    #: **On whose authority it happened.** Equal to `subject_id` when a person
    #: acted directly — ⛔ **stated rather than left `None` for a reader to
    #: interpret**, because a `NULL` here would mean *unattributed* and
    #: *self-directed* at the same time.
    acting_for: UUID
    #: When the **fact** happened. Distinct from the row's `created_at`, which
    #: the database owns because it cannot be mistaken.
    occurred_at: datetime
    detail: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.kind:
            raise MalformedEventKind(self.kind, "empty")
        if len(self.kind) > MAX_KIND_LENGTH:
            raise MalformedEventKind(
                self.kind, f"longer than {MAX_KIND_LENGTH} characters"
            )
        if KIND_PATTERN.match(self.kind) is None:
            raise MalformedEventKind(
                self.kind,
                "not `noun.verb_past` in lower snake case, e.g. `session.signed_in`",
            )
        # ⛔ Case-insensitively, because `Token` is a credential too.
        for key in self.detail:
            if key.lower() in FORBIDDEN_DETAIL_KEYS:
                raise ForbiddenDetailKey(key)
        if self.occurred_at.tzinfo is None:
            # A naive timestamp in an audit stream is a timestamp nobody can
            # compare across regions. The column is `timestamptz`; the domain
            # refuses rather than letting the driver guess a zone.
            raise ValueError(
                "security event `occurred_at` must be timezone-aware — an audit "
                "record with an ambiguous moment cannot be ordered or cited."
            )

    @property
    def self_directed(self) -> bool:
        """The person acted on their own behalf."""
        return self.subject_id == self.acting_for

    @property
    def on_behalf(self) -> bool:
        """⚡ **Somebody or something acted for somebody else** — the case an
        auditor is looking for, and the reason both columns exist."""
        return not self.self_directed


__all__ = [
    "FORBIDDEN_DETAIL_KEYS",
    "KIND_PATTERN",
    "MAX_KIND_LENGTH",
    "ForbiddenDetailKey",
    "MalformedEventKind",
    "SecurityEvent",
]
