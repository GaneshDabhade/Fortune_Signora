"""The claim read contract — how the rest of Signora sees evidence.

Downstream modules reason over claims constantly, and none of them may
reach into the `claim` table to do it. This port is the whole of the
permitted surface: frozen views, the canonical vocabulary, and two queries.

**Claims are returned, never a resolved value.** There is deliberately no
`current_value(subject, attribute)` method here. Offering one would put
truth resolution behind an innocuous-looking call, and every consumer would
use it instead of looking at the evidence — which is precisely the collapse
the architecture rejects (docs/architecture/22-knowledge-graph.md, Option A).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, datetime
from typing import Any, Protocol
from uuid import UUID

from modules.provider_normalization.domain.vocabulary import (
    ClaimAttribute,
    CommercialStage,
    CommercialStageValue,
    MoneyValue,
)


def _as_date(raw: object) -> date | None:
    """Dates are stored as ISO strings so a claim stays readable in psql
    during an incident. A malformed one yields None rather than raising:
    the claim itself is still evidence, and losing all of it because one
    optional field is unparseable would be a worse failure."""
    if not isinstance(raw, str):
        return None
    try:
        return date.fromisoformat(raw)
    except ValueError:
        return None


@dataclass(frozen=True, slots=True)
class SubjectRef:
    """A provider identity, as the provider stated it. Never a resolved
    one — resolving these is the Knowledge Graph's job, not this module's."""

    provider: str
    provider_external_id: str


@dataclass(frozen=True, slots=True)
class TechnologyRef:
    """The part of a technographic claim a consumer can act on.

    The detection window travels with it. A vendor reporting a technology
    as *removed* usually reports when it was last seen too, and that
    interval is the whole of what makes a displacement observable —
    discarding it would leave a consumer knowing something ended without
    knowing when it ran.
    """

    name: str
    category: str
    first_seen: date | None = None
    last_seen: date | None = None


@dataclass(frozen=True, slots=True)
class NameMatch:
    """A provider identity, and **the name that actually matched**.

    The name is here rather than left to be looked up, because it is the one
    fact a caller cannot recover afterwards. A search matches *every* name a
    source has ever given, and the Knowledge Graph displays the newest one —
    so a company that renamed comes back under a name the customer did not
    type and cannot see. **Which name matched is therefore the whole
    explanation of why the row is there**, and it was already read from the
    database to order the results.

    **Not a relevance score, and there is deliberately nowhere to put one.**
    The ordering is by the matched name, which is derivable and repeatable;
    a number here would be the first step of a ranking nobody could defend,
    the same door `MatchStrength` closes in identity resolution.
    """

    subject: SubjectRef
    name: str


@dataclass(frozen=True, slots=True)
class ClaimView:
    """One piece of evidence, with its provenance intact.

    `value` is the stored JSON form. The typed accessors below exist so a
    consumer never has to know that encoding — reaching into the raw shape
    would couple every downstream module to this module's storage.
    """

    id: UUID
    provider: str
    attribute: ClaimAttribute
    value: Any
    observed_at: datetime
    subject_external_id: str
    subject_domain: str | None
    subject_legal_name: str | None
    payload_provenance: str

    @property
    def subject(self) -> SubjectRef:
        return SubjectRef(provider=self.provider, provider_external_id=self.subject_external_id)

    def as_text(self) -> str | None:
        """The value of a string-valued attribute (`COUNTRY`, `INDUSTRY`,
        `LEGAL_NAME`), or None when this claim is not one."""
        return self.value if isinstance(self.value, str) else None

    def as_technology(self) -> TechnologyRef | None:
        """The technology a technographic claim is about, or None."""
        if self.attribute not in (
            ClaimAttribute.TECHNOLOGY_DETECTED,
            ClaimAttribute.TECHNOLOGY_REMOVED,
        ):
            return None
        if not isinstance(self.value, dict):
            return None
        name, category = self.value.get("name"), self.value.get("category")
        if not isinstance(name, str) or not isinstance(category, str):
            return None
        return TechnologyRef(
            name=name,
            category=category,
            first_seen=_as_date(self.value.get("first_seen")),
            last_seen=_as_date(self.value.get("last_seen")),
        )

    def as_money(self) -> MoneyValue | None:
        """The figure a money-valued attribute carries, or None.

        **`OPEN_ACV` today**, and the accessor is named for the shape rather
        than for the attribute so the next money-valued member needs no second
        method — the same reason `as_text` is not `as_country`.

        **Both halves or nothing.** `MoneyValue` requires an amount *and* a
        currency ([ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
        §3: *"a figure without its currency is not a fact"*), so a stored
        object missing either yields None rather than a half-built value a
        caller would render as a bare number.
        """
        if self.attribute is not ClaimAttribute.OPEN_ACV:
            return None
        return money_from(self.value)

    def as_day(self) -> date | None:
        """The day a date-valued attribute names, or None.

        Reuses the module's own ISO decoding, which returns None on a
        malformed string rather than raising — *"the claim itself is still
        evidence"*.
        """
        if self.attribute is not ClaimAttribute.RENEWAL_DATE:
            return None
        return _as_date(self.value)

    # ⚡ **`day_from` is `_as_date` under its published name** — ⛔ **not a
    # second implementation**, which is why this method delegates to the same
    # function the module-level decoder does.

    def as_stage(self) -> CommercialStageValue | None:
        """The commercial position, **and the tenant's own word for it**, or None.

        ⚠️ **`position` may legitimately be absent while `label` is present.**
        That is the *unmapped* state the CRM Integrations design shows,
        counts and acts on — *"214 opportunities now sit in stages Signora
        treats as unmapped"* — so an unrecognised position decodes to
        `position=None` **with the label intact**, never to None overall.
        ⛔ **Coercing an unknown tenant stage into the nearest canonical one
        is the invention ADR-0409 exists to prevent.**

        **The label is required**, because it is the half a screen shows.
        """
        if self.attribute is not ClaimAttribute.COMMERCIAL_STAGE:
            return None
        return stage_from(self.value)


class ClaimReader(Protocol):
    """Read-only access to evidence, scoped by the caller's tenant session."""

    async def for_record(self, raw_record_id: UUID) -> tuple[ClaimView, ...]:
        """Every claim derived from one raw record."""
        ...

    async def for_subjects(
        self,
        subjects: Sequence[SubjectRef],
        *,
        attribute: ClaimAttribute | None = None,
    ) -> tuple[ClaimView, ...]:
        """Every claim about any of these provider identities.

        Queried by subject rather than by a stored list of claim ids so
        that evidence recorded *after* a resolution still appears: a
        snapshot taken at binding time would silently stop growing.
        """
        ...

    async def subjects_named_like(self, text: str, *, limit: int) -> tuple[NameMatch, ...]:
        """Provider identities some source has called something matching `text`,
        **each carrying the name that matched**.

        Case-insensitive substring over `LEGAL_NAME` claims, ordered by the
        matched name then by identity, so the same query returns the same
        rows on every run and every machine. **That order is the ranking**,
        and returning the name it sorted on is what makes it explicable
        rather than merely stable.

        **Every name a source has ever given, not the one being displayed.**
        The displayed name is chosen by the Knowledge Graph's selection rule
        — newest per provider — and matching only that would require
        resolving every account in the workspace before knowing which to
        keep. Matching the claims means a
        company that has renamed is **found under its old name**, which is
        what somebody who has not heard about the rename is typing.

        **This is the searchable text, and it is the only one.**
        `identity_binding.legal_name` looks like a faster answer and is a
        resolution hint frozen at binding time — searching it would find an
        account under a name the product does not display.

        Returns identities, never accounts: resolving these to entities is
        the Knowledge Graph's job and this module has no idea they exist.
        """
        ...

    async def latest_observed_at(
        self, subjects: Sequence[SubjectRef]
    ) -> dict[SubjectRef, datetime]:
        """When the newest evidence about each of these identities was
        observed. Subjects with no claims are **absent**, not null-valued.

        **This is a time, never a value, and the distinction is what keeps
        it on the right side of the refusal above.** `current_value` was
        rejected because resolving truth behind a convenience call would
        stop every consumer looking at the evidence. A maximum over
        `observed_at` resolves nothing: it says *when the most recent thing
        we know was seen*, and answering it still requires reading the
        claims if you want to know **what** was seen.

        **Why it exists rather than being a `max()` over `for_subjects`.**
        That is what the first draft did, and it is an obvious N+1 in
        aggregate clothing — fetching every claim about fifty companies to
        keep fifty timestamps, on the list surface that renders fifty rows.
        The database can answer it with one grouped scan (§14: fix what you
        know is wrong).
        """
        ...


# ---------------------------------------------------------------- decoders
#
# ⚡ **The stored JSON shape decoded once, published for the one caller that
# cannot go through a `ClaimView`.**
#
# 🔴 **Why these exist beside the accessors above rather than instead of them.**
# `knowledge_graph` resolves a commercial attribute through its own
# `resolve_value`, which returns **the winning claim's raw value** and
# deliberately not the claim — *"a provider identity crossing this boundary
# would let a consumer resolve them itself."* ⛔ **So that caller has a value
# and no `ClaimView` to ask.**
#
# ⚠️ **The alternative was for it to reach into the dict itself**, which is the
# coupling this file's opening refuses: *"reaching into the raw shape would
# couple every downstream module to this module's storage."*
#
# ⛔ **The accessors above DELEGATE to these.** ⚡ **One implementation each** —
# 📁 [§2](../../../../CLAUDE.md): behaviour exists exactly once, and a copy is
# always the one that stops being fixed.


def money_from(raw: object) -> MoneyValue | None:
    """A stored money value, or None when it is not one.

    ⛔ **Both halves or nothing.** 📁 [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
    §3: *"a figure without its currency is not a fact"* — so a stored object
    missing either yields None rather than a half-built value a caller would
    render as a bare number.
    """
    if not isinstance(raw, dict):
        return None
    amount, currency = raw.get("amount"), raw.get("currency")
    # ⚠️ **`bool` is an `int` in Python, and `True` is not an amount.**
    if not isinstance(amount, int) or isinstance(amount, bool):
        return None
    if not isinstance(currency, str):
        return None
    return MoneyValue(amount=amount, currency=currency)


def day_from(raw: object) -> date | None:
    """A stored ISO day, or None when it is unparseable.

    ⚡ **The module's own decoding**, which returns None rather than raising —
    *"the claim itself is still evidence."*
    """
    return _as_date(raw)


def stage_from(raw: object) -> CommercialStageValue | None:
    """A stored commercial stage, **with the tenant's word intact**, or None.

    ⚠️ **An unrecognised position decodes to `position=None` with the label
    kept** — 📁 the *unmapped* state the CRM Integrations design shows, counts
    and acts on. ⛔ **Coercing an unknown tenant stage into the nearest
    canonical one is the invention [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md)
    exists to prevent.**
    """
    if not isinstance(raw, dict):
        return None
    label = raw.get("label")
    # ⛔ **Blank is refused here rather than left to the constructor**: a stored
    # claim is untrusted input, and a read surface must not raise on one.
    if not isinstance(label, str) or not label.strip():
        return None
    position: CommercialStage | None = None
    named = raw.get("position")
    if isinstance(named, str):
        try:
            position = CommercialStage(named)
        except ValueError:
            position = None
    return CommercialStageValue(position=position, label=label)
