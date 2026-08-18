"""This module's own configuration.

**A typed Settings object owned by the module whose behaviour it governs**
(`CLAUDE.md` §6). Not added to `signora_platform/settings.py`, which is the
platform's own configuration and would become the registry of every module's
surface if each new value landed there.

One value today: where a customer's browser is, so an invitation can carry a
link to it.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

DEFAULT_APP_URL = "http://localhost:3000"

#: 📁 Session Continuity state 14 — *"tier 4 kept 30 days"*.
DEFAULT_RECENTS_RETENTION_DAYS = 30


@dataclass(frozen=True, slots=True)
class TenancySettings:
    #: The customer-facing origin an invitation link points at. Read from the
    #: environment **only here**, at the composition root's edge — no domain,
    #: application or interface code sees `os.environ` (§20b).
    app_url: str = DEFAULT_APP_URL

    #: 📁 **How long a recently-viewed record is offered back** — Session
    #: Continuity state 14, *"tier 4 kept 30 days"*.
    #:
    #: ⛔ **Configuration, not a constant, and the design says why.** Its
    #: `U-01` — owner **Legal + Security** — reads *"implement 7 and 30 as
    #: configuration"*, because a viewed-record history may be constrained by
    #: the DPA and by regional policy. **A literal here would need a release to
    #: satisfy a compliance answer.**
    recents_retention_days: int = DEFAULT_RECENTS_RETENTION_DAYS


def load_tenancy_settings() -> TenancySettings:
    return TenancySettings(
        app_url=os.environ.get("SIGNORA_APP_URL", DEFAULT_APP_URL),
        recents_retention_days=int(
            os.environ.get(
                "SIGNORA_RECENTS_RETENTION_DAYS", DEFAULT_RECENTS_RETENTION_DAYS
            )
        ),
    )


__all__ = [
    "DEFAULT_APP_URL",
    "DEFAULT_RECENTS_RETENTION_DAYS",
    "TenancySettings",
    "load_tenancy_settings",
]
