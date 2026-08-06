"""What Signora can honestly say about its own attempts to read a company.

**A7, and it exists because A4 proved the fact was missing.** A4 says *"Latest
evidence · 5 weeks ago"*, which answers *how old is what we know* and cannot
answer *is Signora still watching this*. Those diverge exactly where it
matters: **an account nobody has found anything about looks identical to one
nobody has checked**, and one of those is a reason to stop working the account
while the other is a reason to distrust the page.

### Why this is keyed by subject rather than by account

**[C-219](../../../../docs/LANE_COORDINATION.md), ratified by Lane C
2026-08-06, option ③.** `subject` is the company name a customer typed into
their target-account list, and it is *by construction* the same string
`RunProviderSync` is given — [ADR-0036][adr36] §5 keeps resolution downstream,
so a `TargetAccount` carries no entity id and never will. **There is therefore
no join to perform**: the key on both sides is one string from one source.
The alternative — a subject↔entity binding table —
was sequenced behind a trigger that has not fired, and name matching was
refused outright as a second resolver by a weaker method than the resolver's.

### The four states, and none of them may collapse into another

| `last_attempt` | `stored_anything` | What is true |
|---|---|---|
| `None` | `False` | **Nobody has ever checked.** No watermark row exists |
| a moment | `False` | **Checked, and nothing came back.** The case A4 could not express |
| a moment | `True` | **Checked, and evidence arrived** |
| `None` | `True` | **Read before this field existed.** Honest rather than convenient |

**The fourth row is why `last_attempt` is nullable independently of
`stored_anything`.** Rows written before `attempted_at` existed carry a
position and no time; those subjects *were* read and nothing recorded when.
Backfilling a date would invent one, and collapsing them into *never checked*
would state something false about a subject the platform demonstrably has
evidence for.

[adr36]: ../../../../docs/architecture/adr/0036-target-account-contract.md
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime

from modules.provider_platform.domain.sync import SyncWatermark


@dataclass(frozen=True, slots=True)
class SubjectCoverage:
    """One company, and what this module knows about reading it.

    **Two facts, not a rendered sentence.** The words a customer reads are the
    frontend's (ADR-0034 — the translation lives at the edge and never travels
    inward), and a module that shipped the sentence would own a vocabulary it
    cannot see the screen for.
    """

    subject: str
    #: When a provider last **completed** a read, whether or not anything came
    #: back. `None` means no completed read is recorded — which is two
    #: different things, and `stored_anything` is what tells them apart.
    last_attempt: datetime | None
    #: Whether any read of this subject has ever stored evidence. Derived from
    #: the watermark having a position, which advances only when records
    #: arrive — the same test `subjects_needing_sync` already applies.
    stored_anything: bool


def coverage(
    subjects: Iterable[str], watermarks: Iterable[SyncWatermark]
) -> tuple[SubjectCoverage, ...]:
    """One entry per subject asked about, in the order asked.

    **Every subject gets an entry, including ones with no watermark at all.**
    Omitting them would make *never checked* arrive as an absent key, and a
    caller reading a missing key renders a blank — which is the state A4
    already refuses in words rather than in whitespace.

    **Rows collapse across providers and capabilities.** A subject has one
    watermark per `(provider, capability)`, and the question a seller asks is
    *when did anybody last look*, not *when did Apollo's company enrichment
    last look*. The latest attempt wins; evidence from any of them counts.

    Duplicates in `subjects` collapse, matching `subjects_needing_sync`: two
    entries naming the same company are one company however many times it was
    typed.
    """
    by_subject: dict[str, list[SyncWatermark]] = {}
    for watermark in watermarks:
        by_subject.setdefault(watermark.subject, []).append(watermark)

    seen: set[str] = set()
    found: list[SubjectCoverage] = []
    for subject in subjects:
        if subject in seen:
            continue
        seen.add(subject)
        rows = by_subject.get(subject, [])
        attempts = [row.attempted_at for row in rows if row.attempted_at is not None]
        found.append(
            SubjectCoverage(
                subject=subject,
                last_attempt=max(attempts) if attempts else None,
                stored_anything=any(row.position is not None for row in rows),
            )
        )
    return tuple(found)


__all__ = ["SubjectCoverage", "coverage"]
