"""A unique, well-formed organization URL for a test that does not care what it is.

⚡ **`Workspace.create` requires a slug** — 📁 screen `03` made the address a
required part of creating an organization, and the domain refuses to invent one
([§2](../../CLAUDE.md): the value stored is the one a person accepted).

⛔ **Most tests do not care.** They create a workspace to have a tenant, not to
exercise addressing, and **the one thing they DO need is uniqueness** — the
column carries a unique constraint, so two workspaces built from the same
literal name would collide and fail for a reason unrelated to the test.

✅ **So this derives a valid slug from the name and appends entropy.** Tests
that are genuinely about slugs pass their own literal instead — see
`modules/workspace_tenancy/tests/test_entities.py`.
"""

from __future__ import annotations

import re
from uuid import uuid4


def test_slug(name: str) -> str:
    stem = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")[:40] or "ws"
    return f"{stem}-{uuid4().hex[:8]}"
