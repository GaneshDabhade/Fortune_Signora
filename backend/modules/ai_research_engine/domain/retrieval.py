"""What research is allowed to look at, and in whose vocabulary.

**A port, in `domain/`, because it is this module's language rather than its
plumbing.** Research asks *"what does Signora already know about this
account?"*; how that is answered — an SQL query, a fake, a recorded fixture —
belongs to whatever implements it.

---

**It returns `EvidenceFact`, and deliberately defines no fact type of its own.**
The AI Platform already publishes the vocabulary for *an addressed, attributed,
typed fact*, M9 already uses it, and a second one here would be two shapes for
one idea — with two canonical forms and, eventually, two digests.

**It retrieves facts, never explanations.** Every attribute below restates
something the deterministic pipeline already computed, addressed by the id the
pipeline already minted. Nothing here totals, ranks, infers, or summarises
anything into existence. A derivation may *compare* these facts; a synthesis may
*narrate* them; retrieval only fetches.

---

## Why this exists when `OpportunityExplanationSource` already assembles evidence

M8 turns an `OpportunityExplanation` into a closed evidence set of three kinds —
`opportunity`, `buying_score` and `signal_contribution` — and that assembler is
**not** reimplemented here. It is also not extended: it belongs to a module M10
consumes rather than reshapes, and its own docstring names the stop condition
it would cross.

**What it omits is exactly what research exists to look at:**

- **Business events**, the layer beneath every signal — and with them
  `corroborating_providers`, the only place in the reachable chain where
  *which providers agreed* is visible. Provider disagreement is presently
  surfaced by nothing.
- **Dissenting signals** — readings the buying score preserves precisely so
  they are not netted away, which the assembler drops because they contribute
  no counted arithmetic.

**So the two sources are disjoint by kind, and that is asserted by a test rather
than promised here.** If both emitted `buying_score:<id>`, one citation would
resolve to two different sentences depending on who assembled it — the
duplicate-truth failure, one level down from where ADR-0031 found it.
"""

from __future__ import annotations

from typing import Final, Protocol
from uuid import UUID

from modules.ai_platform.public import EvidenceFact

#: One business event beneath a contributing signal. Named for *what the
#: pipeline calls the thing*, so a citation resolves back to a row a human can
#: open.
BUSINESS_EVENT: Final = "business_event"

#: A reading the score preserved but outweighed. A signal is never both this
#: and a counted contribution — dissent is by definition what did not count —
#: so the two kinds can never address the same row.
DISSENTING_SIGNAL: Final = "dissenting_signal"

#: Attribute names, declared once. Retrieval writes them and derivations read
#: them, and a name spelled two ways would make a derivation silently compare
#: nothing — the failure that looks exactly like a finding of nothing.
EVENT_TYPE: Final = "event_type"
OCCURRED_ON: Final = "occurred_on"
PROVIDER_COUNT: Final = "provider_count"
PROVIDERS: Final = "providers"
CORROBORATED: Final = "corroborated"
SIGNAL_TYPE: Final = "signal_type"
RELEVANCE: Final = "relevance"
OBSERVED_ON: Final = "observed_on"

#: Every kind this module retrieves. Declared once so the disjointness test
#: reads it rather than restating it, and so a new kind cannot be added without
#: appearing here.
RESEARCH_FACT_KINDS: Final = frozenset({BUSINESS_EVENT, DISSENTING_SIGNAL})


class ResearchFactSource(Protocol):
    """The facts research may retrieve about one account."""

    async def facts_for(
        self, workspace_id: UUID, entity_id: UUID
    ) -> tuple[EvidenceFact, ...]:
        """Every retrievable fact about this account, in canonical order.

        **Ordered and deduplicated by the implementation, not by the caller.**
        Two signals may cite one business event, and the same account read
        twice must produce the same tuple — otherwise a derivation over these
        facts would depend on traversal order, which is a hidden input.

        Returns an empty tuple when the account has no open opportunity. That
        is an answer, not an absence: research is invoked on qualified
        opportunities, and an account without one has nothing to research.
        """
        ...
