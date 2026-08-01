"""What the Commercial Profile publishes to other modules.

**Deliberately empty, and the emptiness is the current architectural
statement.** Nothing downstream consumes a customer's declaration yet: the
product catalog anchors the ICP, buying committee and priorities that follow,
and none of those exists. Publishing a reader now would be a contract with no
counterparty — the speculative abstraction §6 forbids.

The package exists because the layering contract names it, so the day a
consumer arrives it arrives *here*, through `public/`, rather than by
reaching into `domain/` — which the `commercial_profile` boundary contracts
in `pyproject.toml` already refuse.

**The first genuine entry will be `TargetAccountReader`** (slice 5), when
Provider Platform finally has a source for the `subject` it has taken since
M2.1 and never been given.
"""
