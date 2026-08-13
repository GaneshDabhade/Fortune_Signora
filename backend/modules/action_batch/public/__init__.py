"""An action is approved before it is effective, and reversible after.

**The contract, and nothing else** — slice 1 of six
([455 §5](../../../../docs/architecture/455-context-definitions-r02-r03.md)),
ratified by
[ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md)
and assigned to Lane B by [D-127](../../../../docs/DECISION_REGISTER.md).

> ## **This context coordinates lifecycle. Business domains own business behaviour.**

| **This context owns** | **The consuming domain owns** |
|---|---|
| The action as the canonical unit of work · approval · withdrawal · approval
state · the reversible window · execution metadata · **this contract** |
**Interpreting** the action · **performing** the operation · **validating**
business rules · **executing** the change · **implementing the inverse** |

⛔ **It is not responsible for business semantics**, and that sentence is the
whole boundary. It is [ADR-0402](../../../../docs/architecture/adr/0402-a-rule-is-data.md)'s
shape reused: **the module that owns an operation is the only thing that knows
how to perform or undo it.**

### Why the contract ships alone

**[P-E](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md), ratified at
[D-121](../../../../docs/DECISION_REGISTER.md).** Seven consumers are waiting,
and **publishing first is what stops seven approval models being invented while
this is built.** ADR-0405 states the same thing as architecture rather than as
review practice:

> **Any future workflow requiring approval, deferred execution, reversible
> execution, withdrawal, human confirmation or staged execution must first
> evaluate whether it should *consume* this capability before introducing
> another approval model.**

**A consumer can compile, type-check and write its tests against this before a
single row is persisted** — and `lint-imports` proves the coupling never forms
while `mypy --strict` proves the contract is honoured.

### ⚠️ `action_batch` is the identity of the context, not the product's word

**No customer-facing name is ratified.** [D-127](../../../../docs/DECISION_REGISTER.md)
forbids a placeholder becoming production terminology because implementation
started first, and ADR-0405 leaves the name deliberately open: *"a name is
[ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)'s test
— would a salesperson use this word unprompted? — and it is worth one
deliberate pass rather than a placeholder that ships."*

**So nothing here names the concept in customer language**, and a consumer
rendering it must take its wording from the ratified name when there is one.

### What is deliberately absent

**No table, no endpoint, no events.** Events are slice 4 and neither is
designed — **[P-C](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): an event
exists when a consumer appears.**

> ⚠️ **Updated by slice 2.** `ApprovalState` was **defined here** while there
> was no domain to hold it. **It now lives in
> [`domain/batch.py`](../domain/batch.py) and is re-exported from here** —
> §6, *a port belongs to the module that owns the language it represents… it
> lives in that module's `domain/` and is published through its `public/`*,
> and the shape `knowledge_graph/public/attributes.py` and
> `commercial_profile/public/` both already use.
>
> ⚡ **The published API is unchanged**: same names, same `__all__`, same
> import path for every consumer. **What changed is which layer defines them**,
> and it changed because the alternative was `domain/` importing from
> `public/` — a dependency pointing outward, which every later slice would
> have inherited.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Protocol
from uuid import UUID

from modules.action_batch.domain.batch import ApprovalState, has_settled


@dataclass(frozen=True, slots=True)
class ActionBatchView:
    """One named unit of work, and where it stands.

    **`item_count` and not the items.** A consumer needs to know how large the
    thing it is describing is; **what each item *means* belongs to the domain
    that proposed it**, and publishing the items here would put business
    semantics in the context whose whole boundary is that it holds none.
    """

    id: UUID
    workspace_id: UUID
    #: What the customer called it. **Their words**, so a history reads as a
    #: record of decisions rather than a list of identifiers.
    name: str
    state: ApprovalState
    #: How many things it covers. **A count, never the payload.**
    item_count: int
    proposed_at: datetime
    proposed_by: UUID
    #: When it became effective. `None` until then — and **`APPROVED` with no
    #: `applied_at` is a real state**, not an inconsistency: approval and
    #: application are two moments, and slice 5 makes the gap between them
    #: visible.
    applied_at: datetime | None = None
    #: How long a reversal remains possible after it applied.
    reversible_for: timedelta | None = None

    def is_settled(self, *, now: datetime) -> bool:
        """Whether the reversible window has elapsed.

        > **A predicate, never a stored state** — ADR-0405 §2.

        **`now` is a parameter with no default.** A stored `is_settled` column
        would be two representations of one fact (§2), and a scheduler to flip
        it is machinery [P-B](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md)
        exists to refuse. **The precedent is `Snoozed.until` in
        `signal_engine`**, which
        [447](../../../../docs/architecture/447-signal-center-traceability-audit.md)
        named *"the pattern R-03 should copy."*

        **An action that never applied is not settled** — it has no window to
        have elapsed — and neither is one with no window declared, which means
        reversal was never offered rather than that it has expired.

        ⚡ **Slice 2: this delegates rather than restates.** The rule is
        `domain.batch.has_settled`, and the aggregate that *enforces* the
        window on reversal calls the same function. **Two implementations of
        one window would eventually disagree about whether a customer may
        still undo something** (§2, *behaviour exists exactly once*).
        """
        return has_settled(self.applied_at, self.reversible_for, now=now)


class ActionBatchReader(Protocol):
    """Where a consuming module asks about the actions it proposed.

    ⛔ **Read-only, and deliberately.** Proposing, approving and reversing were
    slice 4's application layer; **a port that could write before the domain
    exists would let a consumer commit to a lifecycle nobody has built.**

    ⚠️ **Amended 2026-08-13, [D-235](../../../../docs/DECISION_REGISTER.md) ①.**
    **The reasoning above was right and its premise expired**: slices 4 and 5
    shipped, [TASK-465](../../../../docs/BACKLOG.md) is promoted, the domain
    exists. ✅ **One write is published — {@link ActionBatchProposer} — and it
    is `propose` alone.** ⛔ **This reader stays read-only**, because *"what did
    I propose"* and *"propose one"* are different questions and a consumer that
    needs only the first should not be handed the second.

    ⚠️ **The sentence *"nothing implements this yet, and that is the slice"* is
    corrected rather than deleted** ([§2](../../../../CLAUDE.md)) — **and only
    its second half was stale.** 🔴 **Measured, after a first draft of this
    amendment claimed an adapter that does not exist**: `grep` finds
    `ActionBatchReader` in this file and in `test_public_contract.py`, **and
    nowhere else.** ⛔ **Still no implementation** — what changed is that the
    slice it was waiting for has shipped, so the absence is now a *consumer*
    that has not needed it rather than a domain that did not exist.
    """

    async def by_id(self, workspace_id: UUID, batch_id: UUID) -> ActionBatchView | None:
        """One action, or `None` when this workspace has no such action.

        **`None` rather than an exception**, on the terms every reader in this
        repository uses: absence is an answer a caller acts on, not a failure.
        """
        ...

    async def proposed_by(
        self, workspace_id: UUID, actor_id: UUID
    ) -> tuple[ActionBatchView, ...]:
        """Everything this person proposed, **newest first**.

        **The read a *"what did I just do?"* surface needs**, and the reason it
        is scoped to one actor rather than paginated over everybody: a person
        recalling their own action is looking at a short list, and a
        workspace-wide feed is a different question with different
        authorization.
        """
        ...


class ActionBatchProposer(Protocol):
    """**How a consuming domain asks for a batch. `propose`, and nothing else.**

    📁 [D-235](../../../../docs/DECISION_REGISTER.md) ① is the ruling and it is
    deliberately narrow:

    > ✅ ***"`action_batch/public/` may expose `propose` and nothing else.
    > `propose` creates the batch and its payload atomically · ⛔ does NOT
    > approve · ⛔ does NOT apply · human approval stays a separate product
    > boundary · ⛔ no batch-without-payload state is representable · ⛔ no
    > further write operations without an explicit later requirement."***

    ## ⛔ Why `approve` and `apply` are absent, and must stay absent

    ⚡ **Approval is a human decision on a screen**, not a call in a stack. 📁
    [ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md):
    *intelligence suggests; humans commit* — **and a port that could approve
    would let a domain commit on somebody's behalf**, which is the one thing
    the whole context exists to prevent.

    ⛔ **A consumer that finds itself wanting either has a product question**,
    not a missing method.

    ## 🔴 Atomicity is the caller's transaction, and it is the point

    ⚠️ **`propose` writes on the session the caller is already in.** 📁 A batch
    that exists with no payload is an `APPROVED` action that applies nothing —
    **[ADR-0405](../../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md)'s
    *no partial state*, broken by construction** — and two endpoints called in
    sequence would make it representable. **One transaction makes it not.**
    """

    async def propose(
        self,
        *,
        workspace_id: UUID,
        name: str,
        item_count: int,
        proposed_by: UUID,
        reversible_for: timedelta | None = None,
    ) -> UUID:
        """Create a batch and return its id.

        ⚡ **Keyword-only, and the id comes back** — the consumer needs it to
        key its own payload, and 📁 [C-1504](../../../../docs/LANE_COORDINATION.md)
        records that this is why an event-based propose was refused: *"the
        caller gets no `batch_id` back, so the confirmation cannot name what it
        created."*

        ⚠️ **`name` is the customer's own words**, because a history reads as a
        record of decisions rather than a list of identifiers.

        ⛔ **`reversible_for` of `None` says reversal was never offered**, which
        is a different answer from a window that has closed — and the customer
        is told them differently.
        """
        ...


__all__ = [
    "ActionBatchProposer",
    "ActionBatchReader",
    "ActionBatchView",
    "ApprovalState",
]
