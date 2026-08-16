"""The graph's read surface.

**Claim sets, never resolved values.** For `(entity, attribute)` this
returns every contributing claim with its provider, value, and time — a
*set*, deliberately not a value. The graph adds knowledge (these claims
describe the same company) without destroying evidence (they disagree, and
here is exactly how).

Adding a `current_value()` here would be Option A arriving by the back
door: within a year every consumer would call it and nobody would read the
claims. If a downstream module demonstrates it needs a resolved value, that
is a projection to design with its rule stated — not a convenience method
(docs/architecture/22-knowledge-graph.md).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from enum import StrEnum
from typing import Any
from uuid import UUID

from modules.knowledge_graph.application.ports import GraphRepository
from modules.knowledge_graph.domain.identity import (
    Entity,
    EntityKind,
    IdentityBinding,
    Relationship,
    ResolutionDecision,
)
from modules.knowledge_graph.domain.naming import (
    NAME_ATTRIBUTE,
    NameAgreement,
    select_name,
)
from signora_platform.pagination import CursorPosition
from modules.knowledge_graph.domain.attributes import resolve_value
from modules.provider_normalization.public import (
    ClaimAttribute,
    ClaimReader,
    ClaimView,
    CommercialStageValue,
    MoneyValue,
    SubjectRef,
    day_from,
    money_from,
    stage_from,
)


def _subjects(bindings: tuple[IdentityBinding, ...]) -> list[SubjectRef]:
    """The provider identities that resolved to one entity.

    Claims are fetched by subject rather than from a stored evidence list so
    that claims recorded *after* a resolution still appear — a snapshot
    taken at binding time would silently stop growing.
    """
    return [
        SubjectRef(provider=b.provider, provider_external_id=b.provider_external_id)
        for b in bindings
    ]


def _comparable(value: Any) -> str:
    """A stable form for equality across providers.

    JSON with sorted keys rather than the raw object: two providers can
    report the same technology with their keys in a different order, and
    that is agreement, not disagreement.
    """
    return json.dumps(value, sort_keys=True, default=str)


@dataclass(frozen=True, slots=True)
class ClaimSet:
    """Everything known about one attribute of one entity."""

    entity_id: UUID
    attribute: ClaimAttribute
    claims: tuple[ClaimView, ...]

    @property
    def providers(self) -> tuple[str, ...]:
        return tuple(sorted({claim.provider for claim in self.claims}))

    @property
    def latest_by_provider(self) -> dict[str, ClaimView]:
        latest: dict[str, ClaimView] = {}
        for claim in sorted(self.claims, key=lambda c: (c.observed_at, str(c.id))):
            latest[claim.provider] = claim
        return latest

    @property
    def agrees(self) -> bool:
        """Whether the sources agree — comparing each provider's *most
        recent* observation, not every claim ever recorded.

        Comparing all claims would report disagreement whenever a value
        legitimately changed over time, which is a different fact and one
        the Observation Engine exists to read. Fewer than two providers
        agrees trivially.

        This is the one derived signal the graph offers, and it is computed
        rather than stored, because "do sources agree?" is a question about
        identity resolution having grouped them — which is the graph's own
        job.
        """
        values = {_comparable(claim.value) for claim in self.latest_by_provider.values()}
        return len(values) <= 1


@dataclass(frozen=True, slots=True)
class EntityEvidence:
    entity: Entity
    bindings: tuple[IdentityBinding, ...]
    claims: tuple[ClaimView, ...]


@dataclass(frozen=True, slots=True)
class AccountIdentity:
    """**What Signora knows about who an account is.**

    Deliberately not a name. The UI is not asking for a string — it is asking
    for an identity, and an identity that cannot say *how sure* it is about the
    name is one a seller has to take on trust. Every field here is derivable
    from claims the repository already holds; nothing is stored.

    **What is deliberately absent, and why** — each would be a field a caller
    could read and not act on, which is the defect M12.1 removed from the
    attention row:

    - **The winning claim's id.** Nothing can resolve a claim id yet: there is
      no claims endpoint. Exposing an address nobody can follow is the same
      mistake as putting `originating_buying_score_id` on a list row. It
      arrives with evidence resolution (M12.3), which gives it somewhere to go.
    - **The per-provider breakdown.** *"Who said what"* is the disclosure step,
      not the summary — returning every claim on every row of a fifty-account
      page is exactly the payload progressive disclosure exists to avoid.
      `agreement` and `source_count` are what a row needs to decide whether to
      ask; the breakdown arrives with the surface that can show it.
    - **Anything about industry, headcount or domain.** Real, claimed, and not
      identity. A read model that grew every firmographic attribute would
      become the entity record `Entity` refuses to be.

    **`last_observed_at` was weighed against that last rule and admitted.** It
    is not a firmographic attribute: it says nothing about the *company* and
    everything about **how current Signora's knowledge of it is**, which is a
    property of this module's own work. The test the exclusions above apply is
    *"a field a caller could read and not act on"* — a seller reading *"nothing
    since March"* acts on it immediately, by not trusting the rest of the page.
    """

    entity_id: UUID
    #: `None` when no provider has named this account. **Absence, not a
    #: placeholder** — a caller decides how to render an unnamed account, and
    #: a manufactured string here would be indistinguishable from a real name.
    name: str | None
    agreement: NameAgreement
    #: How many providers named it. `0` when nobody has; the denominator
    #: behind `agreement`, so a caller can say *"2 of 3 sources"* without a
    #: second call.
    source_count: int
    #: Who supplied the displayed name, and when they observed it. Both `None`
    #: exactly when `name` is.
    source: str | None
    observed_at: datetime | None
    #: **When the newest evidence about this account was observed** — across
    #: every attribute, not only the name. `None` when no provider has ever
    #: reported anything about it.
    #:
    #: Distinct from `observed_at` above, and the difference is the whole
    #: point: that one dates the *name*, which almost never changes, so a
    #: brief rendering it would say *"3 months ago"* about a company somebody
    #: read this morning.
    #:
    #: **Not "when Signora last checked", and the product must not say it
    #: is.** Nothing in the repository records that: `provider_sync` carries
    #: no subject, and `provider_watermark.position` advances only when
    #: records arrive, so an account nobody found anything about is
    #: indistinguishable from one nobody looked at. Recorded in
    #: [51](../../../../docs/architecture/51-implementation-specifications.md).
    #:
    #: **No default**, though it is the last field and one would be legal.
    #: A default here means a future construction site can omit it and get
    #: `None` — which renders as *"No evidence collected yet"* on an
    #: account that has plenty. Requiring it makes that unrepresentable
    #: rather than merely discouraged (§2).
    last_observed_at: datetime | None

    @property
    def is_disputed(self) -> bool:
        """The one state worth interrupting a seller for."""
        return self.agreement is NameAgreement.DISPUTED


class SearchCoverage(StrEnum):
    """Whether Signora looked for this kind of thing, and if not, why not.

    **Ratified 2026-08-05 by the product owner**, answering the contradiction
    [TASK-408](../../../../docs/BACKLOG.md) was skipped on four times:

    > *"Return the group with zero matches rather than omitting it. The
    > absence of results and the absence of the group represent different
    > business meanings."*

    **Three states, and they may not be collapsed.** An empty list can mean
    *we looked and found nothing*, *we cannot look for this*, or *you did not
    ask* — and a customer deciding whether to trust a search needs to know
    which. Omitting the group, which is what shipped before this, said all
    three at once and therefore said none of them.
    """

    SEARCHED = "searched"
    """Signora looked. `matches` may still be empty, and that is an answer."""

    NOT_APPLICABLE = "not_applicable"
    """Signora cannot look for this kind, and the reason is structural.

    Search matches a **legal name**, and only a company has one. A technology
    is in the graph and has no legal name, so it is not that the query missed
    — the question does not apply to it.
    """

    NOT_REQUESTED = "not_requested"
    """The caller narrowed the search and excluded this kind.

    **Distinct from `NOT_APPLICABLE` on purpose**: one is a fact about
    Signora and the other is a fact about the request, and a customer
    widening their search needs to know which one they can change.
    """


#: What Signora does about each kind the graph knows, declared once.
#:
#: **A mapping rather than a branch**, so adding a kind to `EntityKind`
#: without deciding what search does about it fails a test rather than
#: silently omitting a group — which is the defect the ruling closed.
#:
#: **The order is the render order**, and it is fixed here rather than by
#: result count: a group that moves when its results change makes the same
#: query look different for a reason nobody asked about.



SEARCH_COVERAGE: dict[EntityKind, "SearchCoverage"] = {
    EntityKind.COMPANY: SearchCoverage.SEARCHED,
    EntityKind.TECHNOLOGY: SearchCoverage.NOT_APPLICABLE,
    # **`NOT_APPLICABLE`, and it is a product statement rather than a gap.**
    # Search matches a legal name; a `Person` in this repository has none by
    # specification — C-221 narrows the People domain to *"role-based and
    # organization-level intelligence"*, with no person's name anywhere.
    # **So the honest sentence is "Signora does not search people by name"**,
    # which is exactly what this coverage renders — **and it stayed correct
    # when TASK-429 supplied the provider identifier, because an identifier is
    # not a name either.** A `Person` in this repository still holds neither.
    #
    # ⚡ **Added because `EntityKind.PERSON` was added and the suite refused
    # the omission** — `test_every_kind_the_graph_knows_gets_a_group` failed
    # on the same commit, which is the guard doing precisely what TASK-408's
    # ruling asked of it.
    EntityKind.PERSON: SearchCoverage.NOT_APPLICABLE,
}


@dataclass(frozen=True, slots=True)
class AccountCommercial:
    """**What this account is worth to us, and where it stands.**

    📁 [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md),
    ratified 2026-08-12 — *"Signora owns commercial account facts: Open ACV,
    Renewal, and commercial/opportunity stage."* ⚡ **Three attributes, and
    this type adds none.**

    ## 🔴 This is a projection, and its rule is stated

    📁 The module's own refusal stands: *"if a downstream module demonstrates
    it needs a resolved value, that is a projection to design **with its rule
    stated** — not a convenience method."* ⛔ **`claim_set` is still the
    evidence read and is untouched.**

    > **The rule is [`resolve_value`](../domain/attributes.py)'s, applied to
    > each attribute independently** — *"the most recently observed claim
    > wins; ties break on provider name."*

    🔴 **Inherited, never restated.** 📁 That file warns that **a consumer
    projecting a `ClaimSet` into one value has become a second resolver** —
    *"free to disagree with it"* — ⚠️ **and the first version of this type did
    exactly that**, breaking ties on the claim id rather than the provider
    name. **One account, two possible answers, depending on which surface
    asked.**

    ⚡ **Independently, because the three are separate facts.** A CRM that
    updates a stage without touching the renewal date must not blank the
    renewal date, which is what resolving them as one record would do.

    ⛔ **No agreement field, unlike `ResolvedAttribute`.** 📁 [ADR-0401](../../../../docs/architecture/adr/0401-a-customers-crm-is-not-a-provider.md):
    **a commercial fact is the customer's own system of record describing
    their own relationship**, not two vendors disagreeing about the world — so
    a *disputed* ACV is not the ordinary case the way a disputed industry is,
    and a column for it would be a control nobody could act on.

    ## ⛔ Absence is absence

    📁 ADR-0409 §5: *"a claim is only produced where the provider supplies the
    fact. Absence is never inferred, defaulted or zero-filled."* **`None`
    means no source has said**, and a zero ACV would be a figure a seller
    would act on.
    """

    #: ⛔ **Never a bare number** — the currency travels or the fact does not.
    open_acv: MoneyValue | None
    renewal_date: date | None
    #: ⚠️ **May carry a label with no canonical position** — the *unmapped*
    #: state, which the design shows rather than hides.
    stage: CommercialStageValue | None

    @property
    def is_known(self) -> bool:
        """Whether any source has said anything commercial about this account.

        ⚡ **The one predicate a surface needs to tell *"nothing connected"*
        from *"connected and empty"*** — and it lives here rather than in
        three `is None` checks repeated per column.
        """
        return not (
            self.open_acv is None and self.renewal_date is None and self.stage is None
        )


#: The attributes `AccountCommercial` is built from, in the order it reads them.
#:
#: ⚡ **Declared once so the reads and the type cannot drift.** A fourth
#: commercial attribute would need an RFC (ADR-0409 §1) and lands here.
COMMERCIAL_ATTRIBUTES: tuple[ClaimAttribute, ...] = (
    ClaimAttribute.OPEN_ACV,
    ClaimAttribute.RENEWAL_DATE,
    ClaimAttribute.COMMERCIAL_STAGE,
)


@dataclass(frozen=True, slots=True)
class ListedAccount:
    """One account on a browse page: **who it is, and what kind of thing.**

    **Not an `AccountMatch`**, and the difference is the three fields it does
    not have. A match carries `matched_name`, `matched_source` and
    `is_renamed` because a search result has to explain *why it is in the
    list*; **a browse row is in the list because it exists**, and those fields
    would be null on every one of them — a field that is null wherever it is
    not a search is a field in the wrong type.
    """

    account: AccountIdentity
    kind: EntityKind
    #: **What this account is worth and where it stands.** ⚡ **Always present
    #: as a value, never as an absent field** — a row whose commercial facts
    #: are all `None` is a row nothing has been said about, and the surface
    #: renders that as absence. ⛔ **Making the whole object optional would
    #: collapse *"nothing said"* into *"not asked"***, which is the same
    #: conflation `SearchCoverage` exists to prevent one read away.
    commercial: AccountCommercial
    #: When the account first entered the graph. **Carried because the page is
    #: ordered by it** — a cursor derived from anything the row does not hold
    #: would walk a different sequence from the one the page came back in, and
    #: `AccountIdentity` deliberately holds no such field: it answers *"who is
    #: this?"*, not *"when did we learn about it?"*
    created_at: datetime


@dataclass(frozen=True, slots=True)
class AccountPage:
    """One page of accounts, **oldest first**."""

    items: tuple[ListedAccount, ...]
    has_more: bool

    @property
    def next_position(self) -> CursorPosition | None:
        """Where the next page resumes, or `None` at the end.

        **Keyed on the entity's own `created_at` and id**, which is what the
        repository ordered by — a cursor derived from anything else would walk
        a different sequence from the one the page came back in.
        """
        if not self.has_more or not self.items:
            return None
        last = self.items[-1]
        return CursorPosition(created_at=last.created_at, id=last.account.entity_id)


@dataclass(frozen=True, slots=True)
class AccountMatchGroup:
    """One kind of thing, what Signora did about it, and what it found.

    **The group exists whether or not it has results**, which is the whole of
    the ruling. `matches` is empty for every coverage except `SEARCHED`, and
    the constructor refuses the combination that would lie.
    """

    kind: EntityKind
    coverage: SearchCoverage
    matches: tuple[AccountMatch, ...] = ()

    def __post_init__(self) -> None:
        if self.coverage is not SearchCoverage.SEARCHED and self.matches:
            raise ValueError(
                f"a {self.coverage} group carries {len(self.matches)} matches. "
                "Results can only come from a search that happened, and a group that "
                "reports both that it was not searched and what it found is the "
                "collapsed state the ruling forbids."
            )


@dataclass(frozen=True, slots=True)
class AccountMatch:
    """A search result: **an account, what kind of thing it is, and why it is
    here.**

    ### Why `matched_name` exists

    The search matches every name a source has ever given; the product
    displays the newest one. **So a company that renamed comes back under a
    name the customer did not type and cannot see on the row.** The surface
    handled that by refusing to highlight anything — *"highlighting would
    promise the match is in the text, and sometimes it is not"* — which is
    honest and leaves the customer with an unexplained row.

    **Carrying the matched name replaces a refusal with a disclosure.** The
    row can say *matched «Facebook, Inc.»* exactly when that is not what it
    is showing, and stay silent when the name speaks for itself.

    ### Why `kind` is read and not assumed

    A caller grouping results by type must be told the type. Deriving it
    from *which endpoint was called* is the assumption that breaks the first
    time one endpoint answers for two kinds — and it puts the graph's own
    vocabulary in a caller's hands rather than in the graph's.

    ### What is deliberately absent

    **A score.** The order is the matched name, ascending; it is derivable,
    repeatable and stated. A number here would be a ranking nobody could
    defend, which is the door `MatchStrength` closes in resolution and the
    same one stays shut here.
    """

    account: AccountIdentity
    kind: EntityKind
    #: The name that matched, exactly as some source claimed it.
    matched_name: str
    #: Which source claimed it. **The provider, never a person** — a claim is
    #: made by a source about the world, and naming it is what lets a
    #: customer weigh the match.
    matched_source: str

    @property
    def is_renamed(self) -> bool:
        """Whether the row matched under a name it is not being shown under.

        **The one case worth explaining to a customer**, and the reason the
        surface can stay quiet the rest of the time: a search that found what
        it looks like it found needs no annotation.
        """
        return self.matched_name != self.account.name


class GraphQueries:
    """Read-only. Every method is scoped to one workspace, explicitly."""

    def __init__(self, *, repository: GraphRepository, claims: ClaimReader) -> None:
        self._repository = repository
        self._claims = claims

    async def claim_set(
        self, workspace_id: UUID, entity_id: UUID, attribute: ClaimAttribute
    ) -> ClaimSet:
        bindings = await self._repository.bindings_for_entity(workspace_id, entity_id)
        claims = await self._claims.for_subjects(_subjects(bindings), attribute=attribute)
        return ClaimSet(entity_id=entity_id, attribute=attribute, claims=claims)

    async def entity_evidence(self, workspace_id: UUID, entity_id: UUID) -> EntityEvidence | None:
        """*"Why do we believe this?"* — the export an enterprise customer
        asks for, and the reason every link in the chain is preserved."""
        entity = await self._repository.entity_by_id(workspace_id, entity_id)
        if entity is None:
            return None
        bindings = await self._repository.bindings_for_entity(workspace_id, entity_id)
        claims = await self._claims.for_subjects(_subjects(bindings))
        return EntityEvidence(entity=entity, bindings=bindings, claims=claims)

    async def identities(
        self, workspace_id: UUID, entity_ids: tuple[UUID, ...]
    ) -> dict[UUID, AccountIdentity]:
        """Who these accounts are, in **one** pass over bindings and claims.

        A mapping rather than a sequence: a caller asking about *these*
        accounts needs to know which came back, and an entity the workspace
        does not own is simply absent rather than represented by an empty
        identity it might render.
        """
        if not entity_ids:
            return {}

        bindings = await self._repository.bindings_for_entities(workspace_id, entity_ids)
        subjects = _subjects(bindings)
        claims = await self._claims.for_subjects(subjects, attribute=NAME_ATTRIBUTE)
        # A second, narrow read rather than widening the one above. Dropping
        # the attribute filter would pull every claim about every account on
        # the page to keep one timestamp each.
        latest = await self._claims.latest_observed_at(subjects)

        owner = {
            (binding.provider, binding.provider_external_id): binding.entity_id
            for binding in bindings
            if binding.entity_id is not None
        }
        grouped: dict[UUID, list[ClaimView]] = {entity_id: [] for entity_id in entity_ids}
        for claim in claims:
            entity_id = owner.get((claim.provider, claim.subject_external_id))
            if entity_id is not None and entity_id in grouped:
                grouped[entity_id].append(claim)

        # **The newest across every provider bound to the account**, not the
        # newest of one. Two sources reading the same company is the ordinary
        # case, and *"how current is this?"* is answered by whichever looked
        # most recently.
        freshest: dict[UUID, datetime] = {}
        for subject, observed_at in latest.items():
            entity_id = owner.get((subject.provider, subject.provider_external_id))
            if entity_id is None or entity_id not in grouped:
                continue
            known = freshest.get(entity_id)
            if known is None or observed_at > known:
                freshest[entity_id] = observed_at

        return {
            entity_id: _identity(entity_id, tuple(found), freshest.get(entity_id))
            for entity_id, found in grouped.items()
        }

    async def commercial(
        self, workspace_id: UUID, entity_ids: tuple[UUID, ...]
    ) -> dict[UUID, AccountCommercial]:
        """What these accounts are worth and where they stand, in **one pass
        per attribute** over bindings and claims.

        📁 **The rule is `AccountCommercial`'s** — newest claim wins, per
        attribute, independently.

        ⚡ **Three narrow reads rather than one wide one**, which is the same
        trade `identities()` already makes for `latest_observed_at`: dropping
        the attribute filter would pull every claim about every account on the
        page — every technology, every funding round — to keep three values
        each.

        ⛔ **Not a loop over rows.** A page of fifty accounts costs three
        queries, not a hundred and fifty (§14).

        **Every requested id comes back**, carrying an all-`None`
        `AccountCommercial` when nothing has been said — 📁 the same contract
        as `AccountMatchGroup`: *the absence of results and the absence of the
        group represent different business meanings.*
        """
        if not entity_ids:
            return {}

        requested = set(entity_ids)
        bindings = await self._repository.bindings_for_entities(workspace_id, entity_ids)
        subjects = _subjects(bindings)
        owner = {
            (binding.provider, binding.provider_external_id): binding.entity_id
            for binding in bindings
            if binding.entity_id is not None
        }

        grouped: dict[tuple[UUID, ClaimAttribute], list[ClaimView]] = {}
        for attribute in COMMERCIAL_ATTRIBUTES:
            for claim in await self._claims.for_subjects(subjects, attribute=attribute):
                entity_id = owner.get((claim.provider, claim.subject_external_id))
                if entity_id is None or entity_id not in requested:
                    continue
                grouped.setdefault((entity_id, attribute), []).append(claim)

        def won(entity_id: UUID, attribute: ClaimAttribute) -> object | None:
            """The winning value, **by this module's own resolution rule.**

            🔴 **`resolve_value` and not a rule written here.** 📁
            [`attributes.py`](../domain/attributes.py) states it once — *"the
            most recently observed claim wins, and the providers that agreed
            with it are named"* — and warns in the same file that **a consumer
            projecting a `ClaimSet` into one value has become a second
            resolver**, free to disagree with the first.

            ⚠️ **The first version of this method WAS that second resolver.**
            It broke ties on the claim id where `resolve_value` breaks them on
            the provider name, so one account could have answered two ways
            depending on which surface asked.
            """
            return resolve_value(tuple(grouped.get((entity_id, attribute), ()))).value

        return {
            entity_id: AccountCommercial(
                open_acv=money_from(won(entity_id, ClaimAttribute.OPEN_ACV)),
                renewal_date=day_from(won(entity_id, ClaimAttribute.RENEWAL_DATE)),
                stage=stage_from(won(entity_id, ClaimAttribute.COMMERCIAL_STAGE)),
            )
            for entity_id in requested
        }

    async def count_accounts(self, workspace_id: UUID) -> int:
        """How many accounts this workspace holds.

        📁 **The design's header prints it beside the page count** — *"8,412
        total · 312 in view"* — ⚡ **and the two are different facts.** The
        second is what the customer is looking at; **the first is the size of
        their book, and a screen cannot infer it from a page.**

        ⛔ **A separate read rather than a field on the page.** The page
        envelope is `CursorPage`, which is platform-owned and frozen
        ([§20a](../../../../CLAUDE.md)) — **and a count on every page request
        would charge a `COUNT(*)` to a customer who is only scrolling.**
        """
        return await self._repository.count_entities(workspace_id)

    async def list_accounts(
        self, workspace_id: UUID, *, after: CursorPosition | None = None, limit: int = 50
    ) -> "AccountPage":
        """Every account the graph knows, a page at a time.

        **Browse, not search — and deliberately a second read.**
        `find_accounts` refuses blank input because *"an empty pattern matches
        every claim in the workspace… the one that forgets ships a search box
        that dumps the customer's whole book of business on the first
        keystroke."* **Relaxing that guard to build this would break search**
        ([TASK-472](../../../../docs/BACKLOG.md)).

        **The rows carry the same identity a search result does**, resolved by
        the same rule, so a table renders one type whether the customer typed
        something or not.

        **Keyset, never offset**: the graph is written continuously and an
        offset page skips or repeats rows between two requests.
        """
        page = await self._repository.entity_page(
            workspace_id, after=after, limit=limit + 1
        )
        entities = page[:limit]
        ids = tuple(entity.id for entity in entities)
        identities = await self.identities(workspace_id, ids)
        # **Read for the page, not for the row.** The design's table draws Open
        # ACV, Renewal and Stage as columns, so the alternative is a request
        # per row — the N+1 §14 calls a defect at write time.
        commercial = await self.commercial(workspace_id, ids)
        return AccountPage(
            items=tuple(
                ListedAccount(
                    account=identities[entity.id],
                    kind=entity.kind,
                    commercial=commercial[entity.id],
                    created_at=entity.created_at,
                )
                for entity in entities
                if entity.id in identities
            ),
            has_more=len(page) > limit,
        )

    async def find_accounts(
        self, workspace_id: UUID, text: str, *, limit: int
    ) -> tuple[AccountMatch, ...]:
        """Accounts some source has called something matching `text`, **each
        saying what kind of thing it is and which name matched**.

        **Three steps, and none of them is a join across a module boundary.**
        Provider Normalization finds the identities a `legal_name` claim
        matched, and says what each was named; this module maps those to
        accounts through its own bindings; `identities()` then resolves each
        account's *displayed* name.

        **So a result can be named something other than what was searched
        for**, and that is the behaviour rather than a defect: a company that
        renamed is found by its old name and shown under its new one, which is
        precisely what somebody who has not heard about the rename needs.
        **The matched name travels with the row so the difference can be
        shown** instead of leaving the customer to wonder.

        **Ranking is the matched name, ascending, and nothing else.** It is
        decided by Provider Normalization's ordering and preserved through
        both later steps — so the same query returns the same rows in the same
        order on every run, and the field the order was computed from is on
        every row. **That is what makes it explicable**; a relevance score
        would make it neither.

        **Blank input finds nothing, and does not find everything.** An empty
        pattern matches every claim in the workspace, so the guard is here
        rather than left to the caller — every future caller would have to
        remember it, and the one that forgets ships a search box that dumps
        the customer's whole book of business on the first keystroke.

        **The bound is on identities considered, not accounts returned**, and
        it is a real limitation: several providers naming one company are
        several matches, so a workspace where one account has many sources can
        return fewer than `limit` accounts while more exist. Recorded rather
        than hidden — collapsing in the database would need the cross-module
        join this deliberately does not have.
        """
        if not text.strip():
            return ()

        matches = await self._claims.subjects_named_like(text, limit=limit)
        resolved = await self._repository.entities_for_subjects(
            workspace_id, [match.subject for match in matches]
        )
        if not resolved:
            return ()

        resolved = resolved[:limit]
        found = await self.identities(
            workspace_id, tuple(subject.entity_id for subject in resolved)
        )
        # The name each identity matched under, keyed the way the binding
        # names it. Built from the same list the resolution walked, so a
        # result can never be annotated with another identity's name.
        named = {(match.subject.provider, match.subject.provider_external_id): match.name
                 for match in matches}

        # `identities()` returns a mapping, and a mapping has no order worth
        # relying on. The order that means something is the one the match
        # produced, so it is re-imposed here.
        return tuple(
            AccountMatch(
                account=found[subject.entity_id],
                kind=subject.kind,
                matched_name=named[(subject.provider, subject.provider_external_id)],
                matched_source=subject.provider,
            )
            for subject in resolved
            if subject.entity_id in found
        )

    async def find_accounts_grouped(
        self, workspace_id: UUID, text: str, *, limit: int
    ) -> tuple[AccountMatchGroup, ...]:
        """The same search, said in a way a customer can trust.

        **Every kind the graph knows gets a group**, whether or not it has
        results, because the product owner ruled that *"the absence of results
        and the absence of the group represent different business meanings"*
        (2026-08-05).

        **What each group says, and why it is not a judgement:**

        | Kind | Coverage | Because |
        |---|---|---|
        | `COMPANY` | `SEARCHED` | `subjects_named_like` matches a **legal name** claim, and a company is the thing that has one |
        | `TECHNOLOGY` | `NOT_APPLICABLE` | It is in the graph and has no legal name. **Not a gap and not a miss** — the question does not apply |

        **`NOT_REQUESTED` is defined and never produced here**, because this
        endpoint takes no kind filter. It exists so that the surface which
        eventually adds one has a state to report rather than inventing a
        fourth meaning for an empty list, and so that a reader can tell *"we
        cannot"* from *"you did not ask"* the day both are possible.

        **This did not merely become buildable; it became worth building.**
        The flat list this wraps is correct and, with one searchable kind,
        silently indistinguishable from a search that covers everything.
        Saying `TECHNOLOGY · not_applicable` out loud is the information that
        was missing — which is why grouping is not the decorative shape it
        looks like when only one kind can match.

        **Ordering inside a group is the flat search's, unchanged**: the
        matched name ascending, deterministic for identical input.
        """
        matches = await self.find_accounts(workspace_id, text, limit=limit)
        by_kind: dict[EntityKind, list[AccountMatch]] = {}
        for match in matches:
            by_kind.setdefault(match.kind, []).append(match)

        return tuple(
            AccountMatchGroup(
                kind=kind,
                coverage=coverage,
                matches=tuple(by_kind.get(kind, ()))
                if coverage is SearchCoverage.SEARCHED
                else (),
            )
            # Ordered by the enum's own declaration, never by result count:
            # a group that moves when its results change makes the same query
            # render differently for a reason nobody asked about.
            for kind, coverage in SEARCH_COVERAGE.items()
        )

    async def relationships(
        self,
        workspace_id: UUID,
        entity_id: UUID,
        *,
        kind: str | None = None,
        as_of: datetime | None = None,
    ) -> tuple[Relationship, ...]:
        return await self._repository.relationships_for_entity(
            workspace_id, entity_id, kind=kind, as_of=as_of
        )

    async def resolution_history(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[ResolutionDecision, ...]:
        """Every decision that bound an identity to this entity, oldest
        first — the full explanation of how it came to be what it is."""
        return await self._repository.decisions_for_entity(workspace_id, entity_id)


def _identity(
    entity_id: UUID, claims: tuple[ClaimView, ...], last_observed_at: datetime | None
) -> AccountIdentity:
    selected, agreement = select_name(claims)
    return AccountIdentity(
        entity_id=entity_id,
        name=selected.value if selected else None,
        agreement=agreement,
        source_count=len({claim.provider for claim in claims}),
        source=selected.provider if selected else None,
        observed_at=selected.observed_at if selected else None,
        last_observed_at=last_observed_at,
    )
