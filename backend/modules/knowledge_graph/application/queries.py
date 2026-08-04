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
from datetime import datetime
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
from modules.provider_normalization.public import (
    ClaimAttribute,
    ClaimReader,
    ClaimView,
    SubjectRef,
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
