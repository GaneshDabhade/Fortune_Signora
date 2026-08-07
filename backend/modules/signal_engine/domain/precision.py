"""How often a rule was right — **the catalog learning which rules misfire**.

**TASK-444.** [447](../../../../docs/architecture/447-signal-center-traceability-audit.md)
found it: *"dismissal reasons feed rule precision"*. A signal type that keeps
being dismissed is a rule that keeps being wrong, and until this the platform
had no way to notice.

### Two of the four outcomes are judgements, and two are not

`Resolution` carries one of four: `Actioned`, `Assigned`, `Snoozed`,
`Dismissed`. **Only two of them say anything about whether the rule was
right.**

| Outcome | Counted | Why |
|---|---|---|
| **`Actioned`** | ✅ **as right** | Somebody did something about it — *"the
  queue's success case"* |
| **`Dismissed`** | ✅ **as wrong** | *"why this signal should not have been
  raised"*, in the domain's own words |
| **`Assigned`** | ⛔ **not counted** | ***"Still open. Assigning is routing,
  not resolving"*** — `resolution.py`. A colleague has it; nobody has judged it |
| **`Snoozed`** | ⛔ **not counted** | *Later* is not *wrong*. A snooze counted
  against a rule would punish it for arriving at a bad moment |

⚠️ **Counting `Assigned` or `Snoozed` as either would be the defect.** As a
success it flatters every rule whose signals get passed around; as a failure
it punishes the busiest queue in the workspace. **Both readings are wrong for
the same reason: neither outcome is anybody saying the signal was right or
wrong.**

### A rule nobody has judged has no precision, and says so

⛔ **Never `0.0`.** [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md):
*"absence can never distinguish itself from failure."* **A rule with no
judgements and a rule that is always wrong are opposite facts**, and a float
cannot hold the difference — so `ratio` is `None`, and every reader is forced
to decide what to render rather than being handed a zero that looks like an
answer.

### Computed, never stored

**No table** ([P-B](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md), and
`Snoozed.until` is the precedent in this module). A stored precision is a
second representation of what the resolutions already say, and it would be
stale from the first resolution written after it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RulePrecision:
    """One signal type's record, as far as anybody has judged it."""

    signal_type: str
    #: Signals of this type somebody acted on.
    actioned: int
    #: Signals of this type somebody said should not have been raised.
    dismissed: int

    def __post_init__(self) -> None:
        if self.actioned < 0 or self.dismissed < 0:
            raise ValueError("a count of resolutions cannot be negative")

    @property
    def judged(self) -> int:
        """How many of this type anybody has actually ruled on.

        ⛔ **Not how many were raised.** Signals still in the queue, assigned
        or snoozed are excluded — the denominator is *judgements*, and calling
        it anything else would make the figure answer a question nobody asked.
        """
        return self.actioned + self.dismissed

    @property
    def ratio(self) -> float | None:
        """The share that were right, or **`None` when nobody has judged one**.

        ⚡ **`None` rather than `0.0`, and this is the whole of P-A here.** A
        new rule and a rule that is always wrong are opposite facts; a zero
        would render them identically, and the reading a person takes from
        *0%* is the second one.
        """
        return None if self.judged == 0 else self.actioned / self.judged


__all__ = ["RulePrecision"]
