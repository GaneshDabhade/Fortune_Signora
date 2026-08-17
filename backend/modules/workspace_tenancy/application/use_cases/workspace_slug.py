"""Is this workspace URL free? — 📁 screen `03`.

⛔ **A use case rather than a repository call from the router**, because the
answer is not the repository's boolean: *taken* and *not a valid slug* are
different answers and the screen shows different things for them.
"""

from __future__ import annotations

from dataclasses import dataclass

from modules.workspace_tenancy.application.ports import WorkspaceRepository
from modules.workspace_tenancy.domain.entities import (
    normalize_workspace_slug,
    validate_workspace_slug,
)
from modules.workspace_tenancy.domain.exceptions import InvalidWorkspaceSlugError


@dataclass(frozen=True)
class SlugAvailability:
    """⚡ **Three states, not two.**

    ⛔ **`available=False` cannot carry both meanings.** 📁 The design shows a
    green *Available* against a taken slug's very different message, and a
    screen given one boolean would have to say *"taken"* about `A!!`, which is
    not true and not actionable.
    """

    slug: str
    available: bool
    #: `None` when the slug is well-formed. ⚠️ **A reason, not a rule number** —
    #: whoever reads it is two words into a form.
    reason: str | None


class CheckWorkspaceSlugUseCase:
    """⛔ **No authorization check, deliberately, and it gives nothing away.**

    ⚡ **Any signed-in person may create a workspace**, so any signed-in person
    must be able to ask whether a URL is free. 📁 The repository answers with a
    bare boolean over one column — **no name, no id, no count** — so this
    reveals exactly what pressing *Create* would reveal a moment later, and
    nothing more.
    """

    def __init__(self, *, workspace_repository: WorkspaceRepository) -> None:
        self._workspaces = workspace_repository

    async def execute(self, candidate: str) -> SlugAvailability:
        try:
            slug = validate_workspace_slug(candidate)
        except InvalidWorkspaceSlugError:
            return SlugAvailability(
                slug=normalize_workspace_slug(candidate),
                available=False,
                reason="Use 3–63 lowercase letters, numbers and hyphens.",
            )

        if await self._workspaces.slug_is_taken(slug):
            return SlugAvailability(
                slug=slug, available=False, reason="That URL is already taken."
            )

        return SlugAvailability(slug=slug, available=True, reason=None)
