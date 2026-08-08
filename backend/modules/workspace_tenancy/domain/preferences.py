"""What a person chose about how Signora looks and speaks to them.

**[TASK-470](../../../../docs/BACKLOG.md) · Workflow 9 · User Profile**,
against `docs/design-snapshot/screens/Fortune Signora User Profile.dc.html`
([D-138](../../../../docs/DECISION_REGISTER.md)).

## 🔴 The scoping question the row told this lane to answer, not assume

**The row says these are *account*-scoped**: *"Theme, density, locale and AI
preference are account-scoped, not workspace-scoped — which makes this the
first row in the migration whose data is not workspace-owned."*

⛔ **The repository has already answered differently, and the architecture
wins.** [418](../../../../docs/architecture/418-platform-foundation-assessment.md),
quoted in [492 §2](../../../../docs/architecture/492-person-scoped-tenancy.md):

> ***"A profile preference, a notification matrix and a session belong to a
> person within a workspace."***

**So this is scoped to the person *within* a workspace**, and
[492 §0](../../../../docs/architecture/492-person-scoped-tenancy.md) gives the
shape: ***"a third tenancy class … which is a narrowing of tenant-owned, never
a parallel to it. `workspace_id` stays non-nullable and every existing
guarantee still applies. One predicate is added."***

⚠️ **The disagreement is recorded rather than resolved silently** — the row
asked for *which and why*, and this is the why. **Three reasons, in order:**

**①** **418 already ruled the aggregate**, and a feature row does not overturn
an architecture assessment in passing ([§21](../../../../CLAUDE.md): implement
the design, never redesign as you go).

**②** ⛔ **Account-global has no lawful home today.** [§8](../../../../CLAUDE.md)
gives two classes: tenant-owned needs a non-nullable `workspace_id`, and
platform-infrastructure tables are *"owned exclusively by platform services…
a business module must never query one"* — **which a profile panel does on
every render.** A genuinely account-global table would need a third
classification list, and **introducing one changes what the Security
Invariants mean**; that is not this row's to do.

**③** ⚡ **The design's own sentence does not contradict this.** *"Applies to
this account on every device you sign in from, **not to this browser**"*
contrasts the account with the *browser*, never with the organization — it
settles that preferences are server-persisted, which they are.

> ⚠️ **What this costs, stated plainly:** a person in two organizations has two
> preference rows and could see two themes. **If that is wrong, it is a product
> decision** and it is raised as [C-247](../../../../docs/LANE_COORDINATION.md)
> rather than decided here.

## ⛔ What this aggregate refuses

**To know what a theme looks like.** It holds the *choice*; rendering it is the
frontend's. A `Theme` that carried colours would put the design system in the
database, where a token edit could not reach it.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from uuid import UUID


class Theme(StrEnum):
    """The design's three, and `SYSTEM` is not a fourth kind of thing.

    *"Follows your device, switching at sunset"* — it is a **deferral**, so the
    stored value stays `SYSTEM` and the browser resolves it per render. ⛔ **The
    server must never resolve it to `LIGHT` or `DARK` and store that**: the
    person asked to follow the device, and answering with a fixed value is
    replacing their choice with one reading of it.
    """

    LIGHT = "light"
    DARK = "dark"
    SYSTEM = "system"


class Density(StrEnum):
    """How much fits on a screen. **Two, because the design draws two.**"""

    COMFORTABLE = "comfortable"
    COMPACT = "compact"


class TimeFormat(StrEnum):
    """The design's segmented control: *24-hour* · *12-hour*."""

    TWENTY_FOUR_HOUR = "24h"
    TWELVE_HOUR = "12h"


@dataclass(frozen=True, slots=True)
class PersonPreferences:
    """One person's choices, inside one workspace.

    **Frozen**, and every field has a default — **because a person who has
    never opened this screen still has preferences.** ⛔ **The absence of a row
    is not the absence of an answer**: it means *the defaults*, and a screen
    that rendered blank for a new account would be showing a state the product
    does not have.
    """

    workspace_id: UUID
    person_id: UUID

    #: ⚡ **`SYSTEM` is the honest default**, not `LIGHT`. The product has no
    #: opinion about a person's lighting until they express one, and following
    #: the device is the choice that assumes least.
    theme: Theme = Theme.SYSTEM
    density: Density = Density.COMFORTABLE

    #: An IANA zone. **`None` means *not chosen*, which is different from UTC**
    #: — the design offers to change it and never asserts one, so a stored UTC
    #: would be an answer nobody gave.
    timezone: str | None = None
    #: A BCP-47 tag. `None` means the interface follows its own default.
    language: str | None = None
    time_format: TimeFormat = TimeFormat.TWENTY_FOUR_HOUR

    #: ⚡ **Optional and person-authored** — the design says *"Optional.
    #: Appears beside your name in mentions."* ⛔ **Never inferred from a name**:
    #: guessing somebody's pronouns is worse than leaving the field empty.
    pronouns: str | None = None
    #: *"Used in mentions and comments"*, 2–32 characters per the design.
    display_name: str | None = None

    def choose_theme(self, theme: Theme) -> PersonPreferences:
        return replace(self, theme=theme)

    def choose_density(self, density: Density) -> PersonPreferences:
        return replace(self, density=density)

    def choose_timezone(self, timezone: str | None) -> PersonPreferences:
        """Set the zone the person confirmed.

        ⛔ **Only ever called from an accepted offer.** The design's prompt
        *"Your timezone changed · Switch to Singapore · Keep Copenhagen"*
        **offers and does not switch**, so nothing in the request path may call
        this from a browser reading alone.
        """
        return replace(self, timezone=timezone)
