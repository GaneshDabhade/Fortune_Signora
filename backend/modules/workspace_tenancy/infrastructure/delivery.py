"""Getting an invitation to the person it names.

**One adapter, and it writes to stdout.** The same choice `lib/auth/email.ts`
made for verification links, for the same reason: a real transport is a vendor
decision nobody has taken, and a console adapter proves the seam without
pretending to be production.

**It is a port because delivery may not stay here.** Notifications (M14a) is the
natural long-term home for anything Signora sends a person, and if it moves,
only this file does — the offer, the revocation and the acceptance are unchanged
either way.

**Structured, to stdout, and it never logs the address's owner into the
message body.** The Infrastructure Contract requires fielded JSON to stdout, and
`CLAUDE.md` §16 forbids logging PII without an approved policy — so the *event*
records that an invitation was delivered and to which workspace, while the
address appears only in the message being delivered.
"""

from __future__ import annotations

from modules.workspace_tenancy.domain.invitation import Invitation
from signora_platform.observability import get_logger

_log = get_logger(__name__)


class ConsoleInvitationDelivery:
    """Writes the invitation where a developer will see it.

    The link is the one a customer would click. It carries the **workspace id
    and no token** — acceptance matches the address against the verified `email`
    claim the JWT already carries, so there is nothing in this URL that would
    let a forwarded copy be used by somebody else ([C-208](../../../../docs/LANE_COORDINATION.md)).
    """

    def __init__(self, *, app_url: str) -> None:
        self._app_url = app_url.rstrip("/")

    async def send(self, invitation: Invitation, *, workspace_name: str) -> None:
        link = f"{self._app_url}/join/{invitation.workspace_id}"
        _log.info(
            "invitation.delivered",
            extra={
                "workspace_id": str(invitation.workspace_id),
                "invitation_id": str(invitation.id),
                "role": invitation.role.value,
                "expires_at": invitation.expires_at.isoformat(),
            },
        )
        print(  # noqa: T201 — this adapter *is* the console; the write is the delivery
            "\n".join(
                (
                    "",
                    "  ┌─ Signora ────────────────────────────────────────────",
                    f"  │  {invitation.invited_email} has been invited to join",
                    f"  │  {workspace_name} as a {invitation.role.value}.",
                    f"  │  {link}",
                    "  └──────────────────────────────────────────────────────",
                    "",
                )
            )
        )


__all__ = ["ConsoleInvitationDelivery"]
