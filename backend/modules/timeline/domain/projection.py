"""What each upstream event projects to — a table, not a branch per event.

**This is static knowledge a domain expert owns**, so it is a reviewed table
rather than a chain of `if event_type == ...` (`CLAUDE.md` §2, least-powerful
author). Three things follow from that shape and none of them follows from
branching code:

**Adding an upstream is a row.** When M11 resumes and `recommendation.created`
exists, Timeline gains a line here and a kind — no handler changes, no new
branch, and the test that every kind has a rule fails loudly until both exist.

**What each entry copies is declared, bounded and reviewable in one place.** See
`detail_keys`: a projection that copied whole payloads would duplicate upstream
truth into rows that can never be corrected.

**An unmapped event cannot be projected at all.** `rule_for` returns `None`
rather than guessing, so a subscription added without a rule produces nothing
instead of an entry nobody can render.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from modules.timeline.domain.entry import EntryKind


@dataclass(frozen=True, slots=True)
class ProjectionRule:
    """How one event type becomes one entry."""

    kind: EntryKind
    source_module: str
    source_ref_key: str
    """The payload key naming the upstream row this entry points back to.

    **Every entry must be able to say where its meaning lives.** Timeline
    deliberately holds no interpretation, so a reader who wants *why* follows
    this reference to the module that decided it.
    """

    detail_keys: tuple[str, ...] = ()
    """The payload fields carried onto the entry — **an allow-list, never the
    whole payload.**

    This is a copy, and the copy is deliberate and bounded. A feed that stored
    only references would need six queries into six modules to render one page,
    which is the N+1 a projection exists to remove. So each key here earns its
    place by being needed *to read the row*, and nothing is carried because it
    happened to be in the payload.

    **A copied value is never corrected.** Upstream supersession arrives as its
    own event and its own new entry; the earlier entry stays readable as what
    was true then, which is the immutability rule applied to a copy.
    """

    time_key: str | None = None
    """A payload key holding the time to order by, when the envelope's is wrong.

    The envelope's `occurred_at` is when the *event* became true. For most
    upstreams that is also when the *thing* happened. `business_event.detected`
    is the exception worth handling: detection can lag the event by days, and a
    seller reading a feed wants the funding round on the day it was announced,
    not the day Signora noticed. Absent, the envelope's time is used.
    """


PROJECTIONS: Final[dict[str, ProjectionRule]] = {
    "observation.recorded": ProjectionRule(
        kind=EntryKind.OBSERVATION_RECORDED,
        source_module="observation_engine",
        source_ref_key="observation_id",
        # `attribute` and `direction` are what distinguish one observation from
        # another on a feed — *headcount, up* is a readable row and
        # *"an observation was recorded"* is not.
        detail_keys=("attribute", "direction", "provider", "kind"),
    ),
    "observation.superseded": ProjectionRule(
        kind=EntryKind.OBSERVATION_SUPERSEDED,
        source_module="observation_engine",
        source_ref_key="observation_id",
        detail_keys=("attribute", "supersedes"),
    ),
    "business_event.detected": ProjectionRule(
        kind=EntryKind.BUSINESS_EVENT_DETECTED,
        source_module="business_event_engine",
        source_ref_key="business_event_id",
        detail_keys=("type_key", "domain", "taxonomy_version"),
        # Detection lags occurrence; the feed shows when it happened.
        time_key="occurred_at",
    ),
    "business_event.superseded": ProjectionRule(
        kind=EntryKind.BUSINESS_EVENT_SUPERSEDED,
        source_module="business_event_engine",
        source_ref_key="business_event_id",
        detail_keys=("type_key", "supersedes"),
    ),
    "signal.generated": ProjectionRule(
        kind=EntryKind.SIGNAL_GENERATED,
        source_module="signal_engine",
        source_ref_key="signal_id",
        detail_keys=("signal_type", "relevance", "catalog_version"),
    ),
    "signal.superseded": ProjectionRule(
        kind=EntryKind.SIGNAL_SUPERSEDED,
        source_module="signal_engine",
        source_ref_key="signal_id",
        detail_keys=("signal_type", "supersedes"),
    ),
    "buying_score.updated": ProjectionRule(
        kind=EntryKind.BUYING_SCORE_UPDATED,
        source_module="buying_score_engine",
        source_ref_key="score_id",
        # `trigger` is the pipeline's own answer to *why now*, already decided
        # upstream — deriving a second one here would be Timeline interpreting.
        detail_keys=("score", "trend", "delta", "contested", "trigger"),
    ),
    "opportunity.created": ProjectionRule(
        kind=EntryKind.OPPORTUNITY_CREATED,
        source_module="opportunity_engine",
        source_ref_key="opportunity_id",
        detail_keys=("qualification", "stage", "score_at_creation"),
    ),
    "opportunity.stage_changed": ProjectionRule(
        kind=EntryKind.OPPORTUNITY_STAGE_CHANGED,
        source_module="opportunity_engine",
        source_ref_key="opportunity_id",
        # The only upstream whose entry names a person. `actor_id` is carried
        # because a stage change is the one thing on this feed a human did, and
        # *"who moved it"* is the first question asked about it.
        detail_keys=("previous_stage", "new_stage", "actor_id", "reason"),
    ),
}
"""Every event type Timeline projects, and nothing else.

**Nine rules for six live upstreams**, because three of them publish a
supersession event that the catalog names Timeline as a consumer of. A
supersession is a thing that happened to an account and belongs on its feed —
suppressing it would make the feed disagree with the module it projects.

**`recommendation.created` is deliberately absent.** M11 is deferred; a rule
citing an event nothing publishes would be a contract with no counterparty.
"""

ENTITY_KEY: Final = "entity_id"
"""Every projected event carries the account it concerns under this key.

Uniform across all nine, which is why it is a constant rather than a per-rule
field — and if a future upstream names it differently, the rule gains a field
rather than the handler gaining a branch.
"""


def rule_for(event_type: str) -> ProjectionRule | None:
    """The rule for `event_type`, or `None` if Timeline does not project it.

    **`None` rather than a raise.** A projection is a read-side convenience; an
    event it has no opinion about must not fail the delivery that carries it,
    because that would let a Timeline gap block an upstream's own consumers.
    """
    return PROJECTIONS.get(event_type)
