"""The resolution rule engine.

Pure and deterministic: given a hint and the existing bindings, it decides
what should happen. It performs no I/O and holds no state, so the same
inputs produce the same decision on every machine and in any processing
order — the property that makes graph rebuilds and regression tests
meaningful.

**Biased against merging.** When two candidates match, the engine returns
AMBIGUOUS and merges nothing. That bias is the whole design: an
under-merge is a visible duplicate; an over-merge silently mixes two
customers' intelligence and looks clean while doing it.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID, uuid4

from modules.knowledge_graph.domain.identity import (
    RULE_PRECEDENCE,
    IdentityState,
    ResolutionDecision,
    ResolutionOutcome,
    ResolutionReason,
    ResolutionRule,
)


@dataclass(frozen=True, slots=True)
class ResolutionCandidate:
    """An existing binding a new hint might match, flattened to just the
    fields the rules compare. Keeping the engine ignorant of storage is
    what lets it stay pure."""

    entity_id: UUID
    provider: str
    provider_external_id: str
    domain: str | None
    legal_name: str | None
    country: str | None


@dataclass(frozen=True, slots=True)
class ResolutionInput:
    provider: str
    provider_external_id: str
    domain: str | None
    legal_name: str | None
    country: str | None
    evidence_claim_ids: tuple[UUID, ...]


def normalize_domain(raw: str | None) -> str | None:
    """One place, deliberately.

    Real provider data is messier than fixtures: `WWW.Acme.example/`,
    trailing whitespace, mixed case. When authentic payloads arrive these
    rules will need extending, and centralising the normalization means
    that extension is a single edit rather than a hunt.
    """
    if raw is None:
        return None
    cleaned = raw.strip().lower().rstrip("/")
    for prefix in ("https://", "http://", "www."):
        cleaned = cleaned.removeprefix(prefix)
    cleaned = cleaned.removeprefix("www.")
    return cleaned or None


def normalize_name(raw: str | None) -> str | None:
    if raw is None:
        return None
    return " ".join(raw.strip().lower().split()) or None


def _matches(
    rule: ResolutionRule, request: ResolutionInput, candidate: ResolutionCandidate
) -> ResolutionReason | None:
    if rule is ResolutionRule.SAME_PROVIDER_ID:
        if (
            candidate.provider == request.provider
            and candidate.provider_external_id == request.provider_external_id
        ):
            return ResolutionReason(rule, "provider_external_id", request.provider_external_id)
        return None

    if rule is ResolutionRule.EXACT_DOMAIN:
        left, right = normalize_domain(request.domain), normalize_domain(candidate.domain)
        if left is not None and left == right:
            return ResolutionReason(rule, "domain", left)
        return None

    left_name, right_name = normalize_name(request.legal_name), normalize_name(candidate.legal_name)
    if (
        left_name is not None
        and left_name == right_name
        and request.country is not None
        and request.country == candidate.country
    ):
        return ResolutionReason(rule, "legal_name_and_country", f"{left_name}|{request.country}")
    return None


def resolve(
    request: ResolutionInput,
    candidates: tuple[ResolutionCandidate, ...],
    *,
    workspace_id: UUID,
    now: datetime,
) -> tuple[ResolutionDecision, IdentityState]:
    """Decide what to do with one provider identity.

    Rules are evaluated in precedence order and the **first rule that
    matches anything decides** — a certain match is never passed over for a
    weaker one. Within that rule, matching more than one distinct entity is
    ambiguity.
    """
    for rule in RULE_PRECEDENCE:
        matched: dict[UUID, ResolutionReason] = {}
        for candidate in candidates:
            reason = _matches(rule, request, candidate)
            if reason is not None:
                matched.setdefault(candidate.entity_id, reason)

        if not matched:
            continue

        if len(matched) > 1:
            # Two entities matched under the same rule. Merging would be a
            # guess, and a wrong merge is invisible and damaging — so the
            # graph records what it could not choose between and stops.
            return (
                ResolutionDecision(
                    id=uuid4(),
                    workspace_id=workspace_id,
                    provider=request.provider,
                    provider_external_id=request.provider_external_id,
                    outcome=ResolutionOutcome.AMBIGUOUS,
                    reasons=tuple(sorted(matched.values(), key=lambda r: r.value)),
                    entity_id=None,
                    candidate_entity_ids=tuple(sorted(matched)),
                    evidence_claim_ids=request.evidence_claim_ids,
                    decided_at=now,
                ),
                IdentityState.AMBIGUOUS,
            )

        entity_id, reason = next(iter(matched.items()))
        return (
            ResolutionDecision(
                id=uuid4(),
                workspace_id=workspace_id,
                provider=request.provider,
                provider_external_id=request.provider_external_id,
                outcome=ResolutionOutcome.BOUND,
                reasons=(reason,),
                entity_id=entity_id,
                candidate_entity_ids=(entity_id,),
                evidence_claim_ids=request.evidence_claim_ids,
                decided_at=now,
            ),
            IdentityState.IDENTIFIED,
        )

    # No rule matched. Creating a new entity is a normal outcome, not a
    # failure — a company Signora has not seen before has to start
    # somewhere.
    return (
        ResolutionDecision(
            id=uuid4(),
            workspace_id=workspace_id,
            provider=request.provider,
            provider_external_id=request.provider_external_id,
            outcome=ResolutionOutcome.CREATED,
            reasons=(),
            entity_id=None,
            candidate_entity_ids=(),
            evidence_claim_ids=request.evidence_claim_ids,
            decided_at=now,
        ),
        IdentityState.IDENTIFIED,
    )
