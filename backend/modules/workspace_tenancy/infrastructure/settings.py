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


@dataclass(frozen=True, slots=True)
class TenancySettings:
    #: The customer-facing origin an invitation link points at. Read from the
    #: environment **only here**, at the composition root's edge — no domain,
    #: application or interface code sees `os.environ` (§20b).
    app_url: str = DEFAULT_APP_URL


def load_tenancy_settings() -> TenancySettings:
    return TenancySettings(app_url=os.environ.get("SIGNORA_APP_URL", DEFAULT_APP_URL))


__all__ = ["DEFAULT_APP_URL", "TenancySettings", "load_tenancy_settings"]
