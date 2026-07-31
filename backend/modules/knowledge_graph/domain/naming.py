"""How an account gets a name, and why that is a decision rather than a lookup.

**An `Entity` carries no name.** It is an identity, not a record — *"a `name`
column here would be truth-resolution in miniature, and it would immediately
disagree with the claims underneath it"* (`identity.py`). A company's name is a
`LEGAL_NAME` claim: from a provider, at a time, and two providers may assert
different ones.

So naming an account is the truth-resolution the graph deliberately declined to
store. This module makes it, in one place, deterministically:

**Resolved at read time, never stored.** The same discipline `evidence_state`
uses in the Opportunity Engine. A stored display name is a cached derivation
that eventually contradicts the claims beneath it, which is precisely the
failure `Entity` was shaped to avoid.

**Disagreement is reported, not resolved away.** The caller learns which name
was selected *and* whether the sources agreed. A product that silently picks one
of two names is asserting a fact it cannot defend; one that says *"two providers
call this company different things"* has told the truth and lost nothing.

**One rule, isolated here.** Selection is `select_name` and nothing else calls
into it — so a future policy change is a change to this function, not an
archaeology exercise across a query layer, a router and a component.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum

from modules.provider_normalization.public import ClaimAttribute, ClaimView

#: The attribute a company's name lives in.
NAME_ATTRIBUTE = ClaimAttribute.LEGAL_NAME


class NameAgreement(StrEnum):
    """Whether the sources agree about what this account is called.

    Four states rather than a boolean, because *"nobody has said"*,
    *"one source said"* and *"two sources disagree"* are three different
    situations for a seller and only the last is worth interrupting them for.
    """

    UNKNOWN = "unknown"
    """No source has named this account. The name is absent, not disputed."""

    SINGLE_SOURCE = "single_source"
    """Exactly one provider names it. **Uncorroborated rather than agreed** —
    a lone claim is not consensus, and calling it agreement would overstate
    what one source can establish."""

    AGREED = "agreed"
    """Every provider that names it says the same thing."""

    DISPUTED = "disputed"
    """Providers name it differently. The selected name is shown *and said to
    be one of several* — this is the one state worth a seller's attention."""


@dataclass(frozen=True, slots=True)
class SelectedName:
    """A name, and everything needed to defend having chosen it."""

    value: str
    #: Who supplied the name being shown. Named rather than counted, so a
    #: seller who distrusts one provider can see when it is the one talking.
    provider: str
    #: When that provider observed it. **Not when Signora stored it** — the
    #: distinction matters when deciding whether a rename has been picked up.
    observed_at: datetime


def select_name(claims: tuple[ClaimView, ...]) -> tuple[SelectedName | None, NameAgreement]:
    """Choose the name to display, and report whether the sources agreed.

    **The rule is: the most recently observed claim wins.** A company that
    renamed should display its new name, and recency is the only ordering the
    claim record supports without inventing a ranking of provider
    trustworthiness. **Provider precedence is a customer policy** — the same
    category as the scoring model and the opportunity policy, both versioned,
    reviewed artifacts — and encoding one here would put an unreviewed
    judgement in the substrate (recorded as D7).

    Ties break on provider name so two providers observing at the same instant
    resolve identically on every run and every machine. A display name that
    depended on row order would make the same account render differently to two
    people looking at once.
    """
    named = tuple(claim for claim in claims if _text(claim) is not None)
    if not named:
        return None, NameAgreement.UNKNOWN

    latest_per_provider: dict[str, ClaimView] = {}
    for claim in sorted(named, key=lambda c: (c.observed_at, c.provider)):
        latest_per_provider[claim.provider] = claim

    winner = max(latest_per_provider.values(), key=lambda c: (c.observed_at, c.provider))
    value = _text(winner)
    assert value is not None  # `named` filtered these out

    distinct = {_text(claim) for claim in latest_per_provider.values()}
    if len(latest_per_provider) == 1:
        agreement = NameAgreement.SINGLE_SOURCE
    elif len(distinct) == 1:
        agreement = NameAgreement.AGREED
    else:
        agreement = NameAgreement.DISPUTED

    return (
        SelectedName(value=value, provider=winner.provider, observed_at=winner.observed_at),
        agreement,
    )


def _text(claim: ClaimView) -> str | None:
    """A claim's name value, if it is usable as one.

    A claim whose value is not a non-empty string is treated as **absent**
    rather than rendered. `value` is stored JSON and a provider can put
    anything in it; a name is the most visible field on the screen, and
    `null` or `""` reaching a row as a company name would look like a product
    defect rather than missing data.
    """
    value = claim.value
    return value.strip() if isinstance(value, str) and value.strip() else None
