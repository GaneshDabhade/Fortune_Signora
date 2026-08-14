"""A named, saved grouping of accounts — the third of ADR-0411's three.

📁 **[ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)
§3**: *"A named, saved grouping of accounts. Whether a segment is a stored list
or a stored predicate is an implementation choice and is Lane A's — **but it is
ONE choice, made once, not per screen**."*

📁 **And [D-235](../../../../docs/DECISION_REGISTER.md) ② settles which word
this is**, on [C-1503](../../../../docs/LANE_COORDINATION.md), which this lane
raised and the product owner closed: **a customer says *ICP* for
[ADR-0041](../../../../docs/architecture/adr/0041-icp-aggregate.md)'s
aggregate — a stored predicate — and *Segment* for the customer-organized
enumerated grouping built here.** ⛔ **`icp_segment` stays an internal name and
nothing is renamed.**

## 🔴 Membership is enumerated, and the panel is what says so

📁 **`Fortune Signora Companies` draws segments in two places, and the two do
not share a vocabulary:**

| | |
|---|---|
| **The table's `Segment` column** | **One value per row**, from a tier |
| | vocabulary — `Enterprise`, `Mid-market` |
| **The `Segments` panel** | **Five named groupings with counts** — |
| | `Renewal risk — 90 days` 41 · `Expansion-ready` 118 · |
| | `Board reporting set` 212 · `Competitive watch` 26 · |
| | `Dormant enterprise` 304 |

⛔ **No row's `Segment` cell holds any panel segment's name, and no panel entry
is named `Enterprise` or `Mid-market`.** ⚠️ **The two sets are disjoint**, so
they cannot be one thing rendered twice — **and that is a reading of the
snapshot rather than an inference from it.**

⚡ **This model follows the PANEL**, because the panel is the only place a
segment is created, named and counted, and **`Board reporting set` —
*"manually curated for the quarterly pack"* — is ADR-0411's enumerated
grouping in the design's own words.** ✅ **The column is raised as
[C-1511](../../../../docs/LANE_COORDINATION.md) rather than guessed at**: 📁
[D-235](../../../../docs/DECISION_REGISTER.md) ② ruled that the column carries
the ADR-0411 meaning, and the values drawn in it are unexplained by that
meaning.

⚠️ **An earlier draft of this paragraph argued from arithmetic — that the
counts sum to 701 over 312 companies and therefore overlap.** 🔴 **312 is the
CSV export of the *current view*; the table holds 8,412.** ⛔ **701 over 8,412
proves nothing about overlap, and the claim is recorded as withdrawn rather
than quietly removed** — **found by Lane C re-measuring rather than relaying,
which is the practice, and it is the same defect this file exists to avoid:
a number taken from the nearest place it appears rather than from the one that
answers the question.**

## ⚠️ What a Segment is NOT, and it is a Tag

🔴 **A tag and a segment are both named, customer-authored, enumerated
groupings of accounts, and one of them would be [§4](../../../../CLAUDE.md)'s
duplicated vocabulary.** **What separates them is what the customer does with
each, and the design says it rather than this file inventing it:**

| | **Tag** | **Segment** |
|---|---|---|
| **Rendered as** | many chips in one cell | a name with a **count** |
| **Carries** | a **tone** a person picked | a **membership** a person curated |
| **Answers** | *"what is true of this account?"* | *"which accounts am I working through?"* |

⚡ **A tag describes an account; a segment collects them.** ⛔ **That is why a
segment has a count and a tag does not**, and why nothing here has a tone.

## ⛔ The Dynamic kind is not built, and it is not an omission

📁 **The panel draws two kinds — `Dynamic` (*"Recalculates hourly"*) and
`Static` (*"Manually curated for the quarterly pack"*)** — **and four of the
five drawn are Dynamic.** ⚠️ **A recalculating segment is a stored PREDICATE,
which is the other half of the one choice ADR-0411 says must be made once.**

🔴 **Measured rather than assumed** — of the predicates the five drawn rules
name: **`score below 50`** has a source (`buying_score_engine` publishes it)
and **`open ACV above $100K`** has one (`opportunity_engine`); **`no contact
14d`, `Usage above 88%`, `healthy support` and `No activity in 60 days` have
no source anywhere in `backend/modules/`** — zero occurrences, the same ⬜
class [414](../../../../docs/architecture/414-wave-1-account-360.md) records
for product usage and calls. **Building a rule engine over facts that do not
exist would be a screen section against invented data.**

✅ **Raised as [C-1511](../../../../docs/LANE_COORDINATION.md)**, with the
measurement, because *which kind a segment is* is the choice ADR-0411 reserved
and the design draws both.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.commercial_profile.domain.account_tag import fold
from modules.commercial_profile.domain.declaration import CommercialProfileError

#: Long enough for *"Renewal risk — 90 days"* and *"Board reporting set"*, the
#: two longest the design draws. **Wider than a tag's 40** because a segment
#: name is a heading in a panel rather than a chip in a table cell, and the
#: design gives it a whole line.
MAX_SEGMENT_NAME = 60

#: **A guard against a runaway import, not a plan limit** — the same reasoning
#: `account_tag.MAX_VOCABULARY` gives. A set of saved lists a person maintains
#: by hand does not reach three figures; the design draws five.
MAX_SEGMENTS = 200


class AccountSegmentError(CommercialProfileError):
    """A grouping cannot be recorded as the customer stated it."""


@dataclass(frozen=True, slots=True)
class AccountSegment:
    """One saved grouping in a workspace.

    **Two fields, and the omissions are deliberate.** ⛔ **No `rule`** — a rule
    is the Dynamic kind, which is not built and is C-1511's subject; a nullable
    column for it would be a half-built predicate engine sitting in the schema
    inviting somebody to finish it. ⛔ **No count** — a count is a fact about
    the membership table at a moment, and storing it would be a second
    representation that goes stale the next time anybody adds an account
    ([§2](../../../../CLAUDE.md)).
    """

    id: UUID
    name: str

    def __post_init__(self) -> None:
        stripped = " ".join(self.name.split())
        if not stripped:
            raise AccountSegmentError("A segment needs a name.")
        if len(stripped) > MAX_SEGMENT_NAME:
            raise AccountSegmentError(
                f"A segment name is at most {MAX_SEGMENT_NAME} characters; "
                f"this one is {len(stripped)}."
            )
        object.__setattr__(self, "name", stripped)

    @property
    def key(self) -> str:
        """What uniqueness is decided on.

        ⚡ **`fold` is imported from `account_tag` rather than copied.** The
        rule — *`At risk` and `at risk` are one name to a customer* — is one
        rule, and `casefold` over collapsed whitespace is the same answer for a
        segment as for a tag. **A second copy is the one that stops being
        fixed** (§2).
        """
        return fold(self.name)

    def renamed(self, name: str) -> AccountSegment:
        """The same grouping, said differently. **The id does not move**, which
        is what keeps every account already in it."""
        return AccountSegment(id=self.id, name=name)


@dataclass(frozen=True, slots=True)
class SegmentDirectory:
    """Every segment a workspace has.

    The aggregate exists for the reason `TagVocabulary` gives: **uniqueness is
    a property of the set**, and a rule enforced only inside a repository
    method is a rule the domain cannot state.
    """

    segments: tuple[AccountSegment, ...]

    def __post_init__(self) -> None:
        if len(self.segments) > MAX_SEGMENTS:
            raise AccountSegmentError(
                f"A workspace keeps at most {MAX_SEGMENTS} segments; "
                f"this one has {len(self.segments)}."
            )
        seen: dict[str, UUID] = {}
        for segment in self.segments:
            first = seen.get(segment.key)
            if first is not None and first != segment.id:
                raise AccountSegmentError(
                    f"“{segment.name}” is already a segment in this workspace."
                )
            seen[segment.key] = segment.id
        ids = [segment.id for segment in self.segments]
        if len(set(ids)) != len(ids):
            raise AccountSegmentError("One segment appears twice in this directory.")

    def find(self, name: str) -> AccountSegment | None:
        key = fold(name)
        return next((segment for segment in self.segments if segment.key == key), None)

    def get(self, segment_id: UUID) -> AccountSegment | None:
        return next((segment for segment in self.segments if segment.id == segment_id), None)

    def added(self, segment: AccountSegment) -> SegmentDirectory:
        """A new grouping. **Refuses a name already in use**, and deliberately
        does not quietly return the existing one — the same reasoning
        `TagVocabulary.added` records: two indistinguishable *yes* answers to
        *"did my segment get created?"* is worse than one refusal."""
        if self.find(segment.name) is not None:
            raise AccountSegmentError(
                f"“{segment.name}” is already a segment in this workspace."
            )
        return SegmentDirectory(segments=(*self.segments, segment))

    def replaced(self, segment: AccountSegment) -> SegmentDirectory:
        if self.get(segment.id) is None:
            raise AccountSegmentError("That segment is not in this workspace.")
        return SegmentDirectory(
            segments=tuple(
                segment if existing.id == segment.id else existing for existing in self.segments
            )
        )

    def removed(self, segment_id: UUID) -> SegmentDirectory:
        if self.get(segment_id) is None:
            raise AccountSegmentError("That segment is not in this workspace.")
        return SegmentDirectory(
            segments=tuple(segment for segment in self.segments if segment.id != segment_id)
        )


@dataclass(frozen=True, slots=True)
class SegmentAddition:
    """What a bulk *Add to segment* actually did, account by account.

    🔴 **The same shape as `TagApplication` and for the same reason, which is
    the reason worth restating rather than cross-referencing:** ⛔ **reversing
    *Add to segment* is not *remove those accounts from the segment*.** If
    three of the forty-one selected companies were already in *Board reporting
    set*, taking the batch back must leave them in it — **they were not this
    batch's doing, and removing them would delete curation the customer did in
    June and never asked to undo.**

    ⚡ **So the inverse is derived from what changed, never from what was
    asked.**
    """

    segment_id: UUID
    #: The accounts that were **not** in the segment and now are. **The inverse
    #: operates on exactly these.**
    added: tuple[UUID, ...]
    #: The accounts already in it. Recorded so the confirmation can say *"38
    #: added, 3 already there"* rather than claiming forty-one changes.
    unchanged: tuple[UUID, ...]

    def __post_init__(self) -> None:
        if set(self.added) & set(self.unchanged):
            raise AccountSegmentError(
                "An account cannot be both added and unchanged by one batch."
            )
        if len(set(self.added)) != len(self.added):
            raise AccountSegmentError("An account appears twice in one batch.")
        if len(set(self.unchanged)) != len(self.unchanged):
            raise AccountSegmentError("An account appears twice in one batch.")

    @property
    def added_count(self) -> int:
        return len(self.added)

    @property
    def total_count(self) -> int:
        return len(self.added) + len(self.unchanged)

    def inverse(self) -> tuple[UUID, ...]:
        """The accounts a reversal removes. **Never `unchanged`.**"""
        return self.added


def add_to_segment(
    segment_id: UUID,
    *,
    accounts: tuple[UUID, ...],
    already_in: frozenset[UUID],
) -> SegmentAddition:
    """Decide what a bulk *Add to segment* changes, before anything is written.

    **A pure function over the two facts that decide it**, so the rule is
    testable without a database and cannot be quietly re-implemented inside a
    repository method (§6, behaviour exists exactly once).
    """
    seen: set[UUID] = set()
    added: list[UUID] = []
    unchanged: list[UUID] = []
    for account in accounts:
        # A caller that selected one row twice is not two additions: the
        # confirmation's count would be wrong and the inverse would try to
        # remove it twice.
        if account in seen:
            continue
        seen.add(account)
        (unchanged if account in already_in else added).append(account)
    return SegmentAddition(
        segment_id=segment_id, added=tuple(added), unchanged=tuple(unchanged)
    )


@dataclass(frozen=True, slots=True)
class SegmentBatch:
    """One bulk *Add to segment*, and where it stands.

    🔴 **The record a consumer of the Action Batch is forced to keep**, on the
    terms `ActionBatchView` states: it publishes *"`item_count` and not the
    items"*, so the lifecycle module knows a batch covers forty-one things and
    nothing about what they are.

    ### ⛔ `applied` is `None` before it runs, and that is not the same as empty

    | | |
    |---|---|
    | `applied is None` | **Not applied.** There is nothing to reverse |
    | `applied.added == ()` | **Applied, and added nobody** — every |
    | | selected account was already in it |
    | `applied.added != ()` | **Applied.** Reversal removes exactly those |

    ⚠️ **A boolean could express two of those three**, and the one it
    would lose is the difference between *nobody has approved this yet*
    and *somebody approved it and it changed nothing*. **Only the first
    is still waiting for a person.**
    """

    batch_id: UUID
    segment_id: UUID
    #: What the customer selected. **Kept for the confirmation and the record**,
    #: never for the reversal.
    requested: tuple[UUID, ...]
    applied: SegmentAddition | None = None

    def __post_init__(self) -> None:
        if not self.requested:
            raise AccountSegmentError("A batch has to name at least one account.")
        if self.applied is not None and self.applied.segment_id != self.segment_id:
            raise AccountSegmentError(
                "A batch cannot apply to a different segment than it proposed."
            )

    @property
    def is_applied(self) -> bool:
        return self.applied is not None

    def with_application(self, application: SegmentAddition) -> SegmentBatch:
        """Record what running it actually did.

        ⛔ **Once, and never again.** 📁 A batch applies at one moment
        ([ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md)),
        and a second application would overwrite the record a reversal depends
        on — **so the customer's undo would operate on the wrong set.**
        """
        if self.applied is not None:
            raise AccountSegmentError("That batch has already been applied.")
        return SegmentBatch(
            batch_id=self.batch_id,
            segment_id=self.segment_id,
            requested=self.requested,
            applied=application,
        )

    def to_reverse(self) -> tuple[UUID, ...]:
        """The accounts a reversal removes. **Empty until it has applied.**"""
        return () if self.applied is None else self.applied.inverse()
