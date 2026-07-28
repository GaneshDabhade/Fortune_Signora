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

# Runtime roles. None may bypass RLS, whatever else they are permitted.
RUNTIME_ROLES: Final[tuple[str, ...]] = ("signora_app", "signora_auth", "signora_relay")
