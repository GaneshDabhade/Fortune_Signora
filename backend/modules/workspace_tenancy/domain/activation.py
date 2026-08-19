"""What a workspace must do about its own membership before Signora is useful.

**One step, and it belongs here rather than with the connections.** Inviting
colleagues is not an integration: nothing is connected, no credential is held,
and the thing obtained is people. The module that owns membership owns the
declaration that membership is something a new workspace has to attend to.

**Declaration, never progress.** Whether a workspace has done it is a count of
its members, which the members read already answers, and whether one person has
put it aside is that person's preference. Neither belongs in the registry: a
declaration that changed as people acted on it could not be cached, compared or
reasoned about.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final


@dataclass(frozen=True, slots=True)
class ActivationStep:
    """One step, as this module declares it."""

    id: str
    #: Lower is earlier. **An integer rather than a position**, so the surfaces
    #: that compose several modules' steps order them without any module
    #: knowing what the others declared.
    priority: int
    #: Whether Signora can conclude anything without it.
    blocking: bool


#: **Non-blocking, and it is the only step that is.**
#:
#: A workspace of one still gets conclusions — they are simply thinner, because
#: Signora scores relationships and one person is a small sample of a buying
#: committee. That is a weaker product rather than no product, which is exactly
#: the line between a step that blocks and one that does not.
INVITE_MEMBERS: Final[ActivationStep] = ActivationStep(
    id="invite_members", priority=300, blocking=False
)


def activation_registry() -> tuple[ActivationStep, ...]:
    """The steps this module currently asks a workspace to take.

    **Unconditional on purpose.** It is tempting to withhold the step from
    somebody who may not invite anybody, and the surfaces that render it are
    forbidden from doing so — a person who cannot invite still needs to know
    the workspace is short of people, so they can ask somebody who can.
    """
    return (INVITE_MEMBERS,)
