"""The named single-purpose path invitation acceptance is allowed to take.

**This file exists because of one ruling and should be read before it is
reused.** [C-208](../../../../docs/LANE_COORDINATION.md): *"Introduce an
explicit authenticated-but-not-member state. Do not weaken general RLS. Provide
only the minimum read path required for invitation acceptance."* — and
`signora_platform/db/` is frozen (§20a), so **a named single-purpose path,
never a policy change.**

### What it does, said plainly

An invitation is workspace-owned, and every policy on it reads
`workspace_id = current_setting('app.workspace_id')`. The person accepting is
by definition not a member, so no membership grants them that setting, and the
row addressed to them is invisible.

`accepting_workspace` sets `app.workspace_id` **for one transaction**, on a
workspace the caller named in the URL, without verifying membership — because
membership is what they are asking for.

### Why that is not a hole

**The setting is transaction-local.** `set_config(..., true)` is `SET LOCAL`
semantics: it lasts until the transaction ends and reaches nothing else.

**And the caller gains nothing by naming a workspace they were not invited
to.** The only query this path performs is *read one invitation by id and
accept it*, and acceptance refuses unless the invitation's address matches the
caller's **verified** email claim. Guessing a workspace id yields a session
that can read one row the guesser cannot act on.

> **The risk is real and it is the reason for the name.** Inside this
> transaction, RLS would admit any query against that workspace. What keeps
> that safe is that exactly one use case is reachable from here. **A second
> caller is not a refactor; it is a new decision, and it needs C-208 reopened.**

### What was refused, and why it is recorded here

| | |
|---|---|
| A second session setting — `app.user_email` — with a policy of
  `workspace_id = … OR invited_email = …` | ❌ Changes `signora_platform/db/`,
  which is frozen, **and widens a policy every tenant-owned table depends
  on** |
| A workspace-less read under a role that is not `signora_app` | ❌ **A role
  that bypasses RLS is what §8 forbids**, and the exemption would be
  permanent |

**Neither would have been smaller. Both would have been permanent.**
"""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

#: Transaction-local, exactly as the platform's own session helpers set it. The
#: statement is written here rather than imported because the platform's is
#: private — and copying six characters is cheaper than reaching through an
#: underscore into a frozen module.
_SET_WORKSPACE_CONTEXT = text("SELECT set_config('app.workspace_id', :workspace_id, true)")


@asynccontextmanager
async def accepting_workspace(
    session: AsyncSession, *, workspace_id: UUID
) -> AsyncIterator[AsyncSession]:
    """Scope this transaction to the workspace an invitation names.

    **Callers: there is one, and it is the acceptance endpoint.** If you are
    reaching for this to read something else, the answer is no — see the module
    docstring. Adding a second caller reopens
    [C-208](../../../../docs/LANE_COORDINATION.md).

    Takes the session from `CurrentUser`, which is already authenticated and
    already scoped to `app.user_id`, and adds the workspace the request named.
    **No membership is verified**, because membership is the thing being
    requested.
    """
    await session.execute(_SET_WORKSPACE_CONTEXT, {"workspace_id": str(workspace_id)})
    yield session


__all__ = ["accepting_workspace"]
