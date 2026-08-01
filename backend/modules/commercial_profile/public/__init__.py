"""What the Commercial Profile publishes to other modules.

**The module's first public contract, and it stayed empty for four slices on
purpose.** A product catalog, an ideal customer, a buying committee and a
commercial focus are all declared and none of them is published, because
nothing downstream consumes a declaration yet — a reader with no counterparty
is the speculative abstraction §6 forbids.

`TargetAccountReader` is different: Provider Platform has taken a `subject`
since M2.1 and nothing has ever supplied one. It is published because somebody
is waiting for it, which is the only good reason a contract exists.

### What this surface is, and what it can never become

**It answers *"which companies did the customer name?"* and nothing else.**
Governed by [ADR-0036](../../../../docs/architecture/adr/0036-target-account-contract.md),
which makes four ownership boundaries permanent — intent here, synchronization
in Provider Platform, understanding in the Knowledge Graph, relevance in the
Signal Engine.

Three things this port must never grow, each of which would look helpful:

- **A delta.** *What has and has not been fetched is not a fact this module
  holds.* The delta a consumer needs is against its own watermark, not against
  the previous declaration — and a declaration-delta would call a re-added,
  never-fetched account *"no change"*.
- **A resolved company, a domain, or any canonical value.** The name is what
  the customer typed. Resolving it here would make the recording module
  resolve, and it is the one least equipped to review a resolution.
- **Anything about synchronization** — cadence, cost, provider, health,
  priority. None of it is a customer's to declare and none is this module's to
  know.

### Frozen views, never domain objects

The views below are copies, deliberately. Handing a consumer a
`TargetAccountList` would hand it this module's domain — its validation rules,
its constructors, and a shape that must then stay still for reasons outside
this module's control. A view can be widened without touching the aggregate,
and the aggregate can be refactored without touching consumers.

### It is a stable interface from today

The next change to anything in this file is a compatibility question, not an
edit: add fields, never remove or repurpose them, and a breaking change is a
new version with a stated deprecation window (§9). That is the price of being
consumed, and it is why the surface is as small as it is.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class TargetAccountView:
    """One company a customer named.

    `name` is **exactly what they typed** — unresolved, unnormalised, and not
    guaranteed to identify anything. Interpreting it is the consumer's job,
    which is why `ProviderRequest.subject` is opaque to the platform.

    `id` is stable across every revision of the list, which is what lets a
    consumer tell a rename from a remove-and-add.
    """

    id: UUID
    name: str


@dataclass(frozen=True, slots=True)
class TargetAccountListView:
    """Every company a workspace wants watched, in the version in force.

    **The whole list, never a delta** — see the module docstring.

    `version` is the same integer that travels on
    `commercial_profile.target_accounts_changed`. A consumer that reads this
    after handling an event can confirm it is acting on the declaration the
    event announced rather than one that has moved on since.
    """

    workspace_id: UUID
    version: int
    accounts: tuple[TargetAccountView, ...]


class TargetAccountReader(Protocol):
    """The read side of the target account list.

    Implemented in this module's `infrastructure/` and injected by the
    composition root, so a consumer never learns that this is backed by SQL —
    and never learns anything else about this module either.
    """

    async def current(self, workspace_id: UUID) -> TargetAccountListView | None:
        """The list in force, or ``None`` when the workspace has never
        declared one.

        **`None` rather than an empty list**, because the two are different
        facts and a consumer should be able to tell them apart: *"they have
        not told us yet"* is a state to wait in, and *"they told us to watch
        nobody"* is an instruction to act on.
        """
        ...


__all__ = ["TargetAccountListView", "TargetAccountReader", "TargetAccountView"]
