"""How a customer labels their own accounts.

**The first of ADR-0411's three, and the one with no prior art anywhere in the
repository** — `grep` finds `tag` only in `ai_platform`'s evidence
canonicalisation, which is a type marker and not this.
[ADR-0411](../../../../docs/architecture/adr/0411-customer-organized-account-metadata.md)
is the ruling.

### Why it is here rather than in the Knowledge Graph

ADR-0411 decides it by **authorship**, and that is the whole argument:

> *"These are customer-authored organizational concepts, distinct from
> provider/CRM commercial facts… They therefore must NOT be merged with
> C-209 / ADR-0409."*

The Knowledge Graph publishes *"identity and evidence, never a resolved
value"* — everything in it was asserted by a provider and carries provenance
back to one. **Nobody asserted a customer's own tag.** Putting one there would
make the provenance of every claim beside it ambiguous, which is the specific
harm ADR-0411 §1 names.

`commercial_profile` is the only bounded context in the repository whose
author is the customer: what they sell, who buys it, who decides, which
accounts matter. A label a seller puts on an account is that same kind of
sentence.

### A tag has an identity, and the name is not it

The same reasoning `target_accounts.py` records for its entries: without an
id, **renaming a tag is indistinguishable from deleting one and creating
another**, and those are different instructions about a customer's own filing.
A workspace that renames *"At risk"* to *"Churn risk"* keeps every account it
was on.

### Uniqueness is case-insensitive, and the display is not

`At risk` and `at risk` are one tag to a customer and two rows to a database.
Two chips a person cannot tell apart, filtering differently, is a defect they
would report — so the fold decides identity and the typed form is what shows.

### The tone is the customer's, and `ai` is not among the choices

The design gives every chip a tone — `risk`, `warn`, `pos`, `neutral` — and
there is no rule that could derive one: *"Champion lost"* is a risk and
*"Expansion"* is positive because a person judged them so, not because
anything in the platform knows. **So the customer picks it.**

⛔ **`ai` is deliberately absent from the enum.** The design reserves that
tone for what Signora itself inferred, and **a customer tag wearing it would
be a human opinion dressed as the platform's** — which is the one confusion
the whole evidence model exists to prevent. Unrepresentable rather than
discouraged (§2).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID

from modules.commercial_profile.domain.declaration import CommercialProfileError

#: Long enough for *"Renewal at risk"*, short enough that a sentence is
#: obviously the wrong field. The design renders a tag as a `nowrap` chip in a
#: table cell beside eight other columns, so a long one does not wrap — it
#: pushes the row.
MAX_TAG_NAME = 40

#: **A guard against a pasted spreadsheet, not a plan limit** — the same
#: reasoning, and the same sentence, as `target_accounts.MAX_ACCOUNTS`. A flat
#: vocabulary a person maintains by hand does not reach four figures, and one
#: that has is no longer a vocabulary.
MAX_VOCABULARY = 500


class AccountTagError(CommercialProfileError):
    """A label cannot be recorded as the customer stated it."""


class TagTone(StrEnum):
    """What a tag looks like, chosen by the person who made it.

    **Four, and the fifth is deliberately missing.** The design's palette has
    `risk`, `warn`, `pos`, `neutral` and `ai`; the last is Signora's own mark
    for something it inferred, and a customer-authored label must never be
    able to claim it.
    """

    RISK = "risk"
    WARN = "warn"
    POSITIVE = "pos"
    NEUTRAL = "neutral"


def fold(name: str) -> str:
    """The form two names are compared in. **Never the form anybody sees.**

    `casefold` rather than `lower` because the customers are not all writing
    English, and `lower("STRASSE")` and `lower("straße")` differ where the
    customer means one tag.
    """
    return " ".join(name.split()).casefold()


@dataclass(frozen=True, slots=True)
class AccountTag:
    """One label in a workspace's vocabulary.

    **Three fields, and the omissions are the design.** A description was
    considered and refused: a tag whose meaning needs a paragraph is a field,
    and the customer already has segments for that. A creator and a created-at
    are audit columns and live on the row, not in the language.
    """

    id: UUID
    name: str
    tone: TagTone

    def __post_init__(self) -> None:
        stripped = " ".join(self.name.split())
        if not stripped:
            raise AccountTagError("A tag needs a name.")
        if len(stripped) > MAX_TAG_NAME:
            raise AccountTagError(
                f"A tag name is at most {MAX_TAG_NAME} characters; this one is {len(stripped)}."
            )
        # Written back so `AccountTag(name=" At  risk ")` and
        # `AccountTag(name="At risk")` are the same tag rather than two that
        # merely fold alike — the normalisation belongs to the value, not to
        # whoever remembered to call it.
        object.__setattr__(self, "name", stripped)

    @property
    def key(self) -> str:
        """What uniqueness is decided on."""
        return fold(self.name)

    def renamed(self, name: str) -> AccountTag:
        """The same tag, said differently. **The id does not move**, which is
        what keeps it on every account it was already on."""
        return AccountTag(id=self.id, name=name, tone=self.tone)

    def retoned(self, tone: TagTone) -> AccountTag:
        return AccountTag(id=self.id, name=self.name, tone=tone)


@dataclass(frozen=True, slots=True)
class TagVocabulary:
    """Every tag a workspace has. **Flat, by ADR-0411 §3** — no parents, no
    groups, no namespaces.

    The aggregate exists because uniqueness is a property of the *set* rather
    than of any tag in it, and a rule that lives in a repository method is a
    rule the domain cannot state.
    """

    tags: tuple[AccountTag, ...]

    def __post_init__(self) -> None:
        if len(self.tags) > MAX_VOCABULARY:
            raise AccountTagError(
                f"A workspace keeps at most {MAX_VOCABULARY} tags; this one has {len(self.tags)}."
            )
        seen: dict[str, UUID] = {}
        for tag in self.tags:
            first = seen.get(tag.key)
            if first is not None and first != tag.id:
                raise AccountTagError(f"“{tag.name}” is already a tag in this workspace.")
            seen[tag.key] = tag.id
        ids = [tag.id for tag in self.tags]
        if len(set(ids)) != len(ids):
            raise AccountTagError("One tag appears twice in this vocabulary.")

    def find(self, name: str) -> AccountTag | None:
        """The tag a customer means when they type a name, or `None`."""
        key = fold(name)
        return next((tag for tag in self.tags if tag.key == key), None)

    def get(self, tag_id: UUID) -> AccountTag | None:
        return next((tag for tag in self.tags if tag.id == tag_id), None)

    def added(self, tag: AccountTag) -> TagVocabulary:
        """A new tag in the vocabulary. **Refuses a name already in use.**

        ⚠️ **Deliberately NOT idempotent, and the caller is what makes *Add
        tag* safe to repeat.** A method that quietly returned the existing tag
        would have to answer with an id the caller did not pass, so *"did my
        tag get created?"* would have two indistinguishable yes answers. **The
        use case asks `find` first** — typing a tag that exists selects it —
        and this method is reached only when the name is genuinely new.
        """
        existing = self.find(tag.name)
        if existing is not None:
            raise AccountTagError(f"“{tag.name}” is already a tag in this workspace.")
        return TagVocabulary(tags=(*self.tags, tag))

    def replaced(self, tag: AccountTag) -> TagVocabulary:
        if self.get(tag.id) is None:
            raise AccountTagError("That tag is not in this workspace.")
        return TagVocabulary(
            tags=tuple(tag if existing.id == tag.id else existing for existing in self.tags)
        )

    def removed(self, tag_id: UUID) -> TagVocabulary:
        if self.get(tag_id) is None:
            raise AccountTagError("That tag is not in this workspace.")
        return TagVocabulary(tags=tuple(tag for tag in self.tags if tag.id != tag_id))


@dataclass(frozen=True, slots=True)
class TagApplication:
    """What a bulk *Add tag* actually did, account by account.

    🔴 **This is the type the reversal needs, and the reason it exists is the
    half [TASK-466](../../../../docs/BACKLOG.md) says is normally untested:**

    > *"a batch that applies but cannot be reversed in the window is a defect,
    > not a limitation."*

    ⛔ **Reversing *Add tag* is not *remove the tag from those accounts*.** If
    three of the forty-one selected companies were already tagged *At risk*
    before the batch, taking the batch back must leave those three tagged —
    they were not this batch's doing, and stripping them would destroy a fact
    the customer authored earlier and never asked to undo.

    ⚡ **So the inverse is derived from what changed, never from what was
    asked**, and `changed` is the only thing it may read.
    """

    tag_id: UUID
    #: The accounts that did **not** carry the tag and now do. **The inverse
    #: operates on exactly these.**
    changed: tuple[UUID, ...]
    #: The accounts that already carried it. Recorded so the confirmation can
    #: tell the truth — *"38 tagged, 3 already had it"* — rather than claiming
    #: forty-one changes.
    unchanged: tuple[UUID, ...]

    def __post_init__(self) -> None:
        overlap = set(self.changed) & set(self.unchanged)
        if overlap:
            raise AccountTagError("An account cannot be both changed and unchanged by one batch.")
        if len(set(self.changed)) != len(self.changed):
            raise AccountTagError("An account appears twice in one batch.")
        if len(set(self.unchanged)) != len(self.unchanged):
            raise AccountTagError("An account appears twice in one batch.")

    @property
    def applied_count(self) -> int:
        return len(self.changed)

    @property
    def total_count(self) -> int:
        return len(self.changed) + len(self.unchanged)

    def inverse(self) -> tuple[UUID, ...]:
        """The accounts a reversal removes the tag from. **Never `unchanged`.**"""
        return self.changed


def apply_tag(
    tag_id: UUID,
    *,
    accounts: tuple[UUID, ...],
    already_tagged: frozenset[UUID],
) -> TagApplication:
    """Decide what a bulk *Add tag* changes, before anything is written.

    **A pure function over the two facts that decide it**, so the rule above is
    testable without a database and cannot be quietly re-implemented inside a
    repository method (§6, behaviour exists exactly once).
    """
    seen: set[UUID] = set()
    changed: list[UUID] = []
    unchanged: list[UUID] = []
    for account in accounts:
        # A caller that selected the same row twice is not two changes. The
        # count on the confirmation would be wrong, and the inverse would try
        # to untag it twice.
        if account in seen:
            continue
        seen.add(account)
        (unchanged if account in already_tagged else changed).append(account)
    return TagApplication(
        tag_id=tag_id, changed=tuple(changed), unchanged=tuple(unchanged)
    )


@dataclass(frozen=True, slots=True)
class TagBatch:
    """One bulk *Add tag*, and where it stands.

    🔴 **The record a consumer of the Action Batch is forced to keep.** 📁
    `ActionBatchView` publishes *"`item_count` and not the items… what each
    item *means* belongs to the domain that proposed it"* — **so the lifecycle
    module knows a batch covers forty-one things and nothing about what they
    are.** This is the other half.

    ### ⛔ `applied` is `None` before it runs, and that is not the same as empty

    ⚡ **Three states, and a boolean could only express two**:

    | | |
    |---|---|
    | `applied is None` | **Not applied yet.** There is nothing to reverse |
    | `applied.changed == ()` | **Applied, and changed nothing** — every selected
      account already carried the tag. **Still not reversible**, for a different reason |
    | `applied.changed != ()` | **Applied.** Reversal removes exactly those |

    ⛔ **A reversal that read `requested` would strip a label somebody set in
    June**, which is the defect [`TagApplication`](#) exists to prevent —
    stated here again because this is the type a caller actually holds.
    """

    batch_id: UUID
    tag_id: UUID
    #: What the customer selected. **Kept for the confirmation and the record**,
    #: never for the reversal.
    requested: tuple[UUID, ...]
    applied: TagApplication | None = None

    def __post_init__(self) -> None:
        if not self.requested:
            raise AccountTagError("A batch has to name at least one account.")
        if self.applied is not None and self.applied.tag_id != self.tag_id:
            raise AccountTagError("A batch cannot apply a different tag than it proposed.")

    @property
    def is_applied(self) -> bool:
        return self.applied is not None

    def with_application(self, application: TagApplication) -> TagBatch:
        """Record what running it actually did.

        ⛔ **Once, and never again.** 📁 A batch applies at one moment
        ([ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md)),
        and a second application would overwrite the record a reversal depends
        on — **so the customer's undo would operate on the wrong set.**
        """
        if self.applied is not None:
            raise AccountTagError("That batch has already been applied.")
        return TagBatch(
            batch_id=self.batch_id,
            tag_id=self.tag_id,
            requested=self.requested,
            applied=application,
        )

    def to_reverse(self) -> tuple[UUID, ...]:
        """The accounts a reversal untags. **Empty until it has applied.**"""
        return () if self.applied is None else self.applied.inverse()
