"""The Tenant Isolation Policy — what makes a table safe to hold tenant data.

Every table in the application schema is exactly one of two things, and the
distinction is declared here rather than inferred:

* **Tenant-owned** — holds a workspace's data. Subject to the full policy
  below, without exception.
* **Platform infrastructure** — owned by platform services, spanning every
  workspace by design (the relay cannot sweep the outbox one tenant at a
  time). Isolated by *privilege* instead of by RLS, and unreachable from
  business modules (migration 0006).

Declaring the split explicitly is the point. Inferring "tenant-owned" from
the presence of a ``workspace_id`` column — the earlier approach — meant a
new table that simply forgot the column was silently classified as platform
infrastructure and exempted from every check. The failure mode of a
misclassification is now a build failure rather than a silent exemption:
a table appearing in neither list fails ``test_every_table_is_classified``.

The policy, per docs/architecture/11-tenancy.md:

1. A tenant identifier column exists and is ``NOT NULL``.
2. Row-Level Security is **enabled and forced** — ``FORCE`` matters
   separately, because without it the table's owner is exempt from its own
   policies.
3. The required policies exist, covering read and write separately: a table
   with only a ``SELECT`` policy silently permits no writes, and one with a
   permissive ``ALL`` policy usually means the write path was never
   considered.
4. No runtime role can bypass RLS.
5. Enforcement is proven by regression tests that fail when the policy is
   removed — not merely asserted to be configured.
"""

from typing import Final

TENANT_IDENTIFIER: Final = "workspace_id"

# Tables holding workspace data. Every one is subject to the full policy.
TENANT_OWNED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "workspace",
        "membership",
        # Provider Platform (M2.1). Each carries workspace_id with forced
        # RLS and the full policy set, created in migration 0007.
        "provider_sync",
        "provider_watermark",
        "raw_provider_record",
        # Provider Normalization (M2.2), migration 0008.
        "claim",
        "normalization_outcome",
        # Knowledge Graph (M3A), migration 0009.
        "entity",
        "identity_binding",
        "resolution_decision",
        "relationship",
        # Observation Engine (M3B), migration 0010.
        "observation",
        # Business Event Engine (M4), migration 0011.
        "business_event",
        # Signal Engine (M5A), migration 0012. `signal_profile` is the first
        # **customer-authored** table in the platform — not derived data.
        "signal",
        "signal_profile",
    }
)

# Platform infrastructure. Spans workspaces by design; isolated by grant
# rather than by RLS, and readable only by platform identities.
#
# Adding a table here is a deliberate architectural act, not a way to make a
# failing test pass. It asserts that the table holds no data a tenant could
# read that belongs to another — or that the only roles able to read it are
# platform services.
PLATFORM_INFRASTRUCTURE_TABLES: Final[frozenset[str]] = frozenset(
    {
        "outbox_event",
        "processed_event",
        "dead_letter_event",
        "alembic_version",
    }
)

# `workspace` is the tenancy root and cannot have a `workspace_id` pointing
# at something else — its own `id` *is* the tenant identifier. Its policies
# are split INSERT/SELECT/UPDATE to break the bootstrap circularity of
# creating the first workspace before any membership exists.
TENANCY_ROOT: Final = "workspace"

# Commands every tenant-owned table must have a policy for. DELETE is not
# required: a table with no delete path is a legitimate design, and
# demanding a policy would encourage adding one that is never used.
REQUIRED_POLICY_COMMANDS: Final[frozenset[str]] = frozenset({"SELECT", "INSERT", "UPDATE"})

# Tables whose rows are **immutable by design**. These legitimately have no
# UPDATE policy and no UPDATE grant — requiring one would mean weakening
# immutability to satisfy a test, which is exactly backwards.
#
# `claim` holds evidence. Evidence is never edited: new information is a new
# claim. Timeline, the Observation Engine, and AI Reasoning all depend on
# being able to see what was believed *when*
# (docs/architecture/20-provider-simulation.md; M2.2 ruling).
#
# `resolution_decision` holds knowledge's history. A decision that can be
# edited is a decision whose history cannot be trusted, so a correction is a
# new decision naming the one it supersedes — which is also why its
# supersession pointer points backwards (migration 0009; M3A ruling).
#
# `observation` records what changed. A late-arriving claim makes an earlier
# observation *less precise*, never false, so the finer observations name the
# coarser one they refine and it stays readable as what was believed then
# (migration 0010; M3B ruling).
#
# `business_event` is durable business history. A phenomenon that extends
# or a conclusion that is corrected produces a new event naming the one it
# replaces — future intelligence modules are expected to reason over
# complete historical sequences, which requires the sequence to exist
# (migration 0011; M4 ruling).
#
# `signal` holds commercial hypotheses; a hypothesis that gains evidence
# becomes a new signal naming the one it replaces. `signal_profile` is
# customer-authored configuration: an edit in place would make every
# historical signal unexplainable, because the reason it exists would have
# changed underneath it (migration 0012; M5A ruling).
#
# Adding a table here is a deliberate architectural act. The immutability it
# claims is separately asserted in test_tenancy_policy.py.
IMMUTABLE_TENANT_TABLES: Final[frozenset[str]] = frozenset(
    {
        "claim",
        "resolution_decision",
        "observation",
        "business_event",
        "signal",
        "signal_profile",
    }
)

# Runtime roles. None may bypass RLS, whatever else they are permitted.
RUNTIME_ROLES: Final[tuple[str, ...]] = ("signora_app", "signora_auth", "signora_relay")
