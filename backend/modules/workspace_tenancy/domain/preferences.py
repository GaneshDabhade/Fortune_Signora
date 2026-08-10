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
from datetime import datetime
from enum import StrEnum
from uuid import UUID

#: The design's segmented control offers `3 · 4 · 5`, and `3` is where it sits.
#: ⚠️ **A floor, not a threshold anybody else can lower** — the design says
#: *"yours can be stricter … never looser"*, and the workspace half of that
#: does not exist yet ([C-249](../../../../docs/LANE_COORDINATION.md)).
MIN_CONFIDENCE_FLOOR = 3
MAX_CONFIDENCE_FLOOR = 5


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


class AnswerStyle(StrEnum):
    """*"Direct gives the conclusion first. Detailed shows the reasoning
    inline before the answer."*"""

    DIRECT = "direct"
    DETAILED = "detailed"


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

    #: 🔴 **When this person last entered THIS workspace** —
    #: [TASK-1422](../../../../docs/BACKLOG.md).
    #:
    #: ⚡ **A timestamp per workspace, never a pointer to one.**
    #: 📁 [§2](../../../../CLAUDE.md): *truth has exactly one authoritative
    #: representation; everything else derives from it.* ⛔ **A stored
    #: `last_used_workspace_id` would be a second representation of a fact
    #: these rows already carry**, and the two would disagree the first time a
    #: membership ended without something remembering to rewrite the pointer.
    #:
    #: 🔴 **That disagreement is exactly the hazard
    #: [D-196](../../../../docs/DECISION_REGISTER.md) named**: *"a stored
    #: preference that OUTLIVES membership."* ✅ **Deriving the answer over the
    #: person's LIVE memberships makes a departed member's row unreachable
    #: rather than merely stale** — the workspace they left is not in the set
    #: the derivation reads, so there is nothing to forget to clear.
    #:
    #: ⚠️ **`None` means never entered**, which is not the same as *entered
    #: long ago*: rule 12 `LAST_USED` must not fire for somebody who has never
    #: been anywhere.
    last_entered_at: datetime | None = None

    # ── Screen `04 · AI preferences` ──────────────────────────────────────
    #
    # ⚡ **Every default here is the conservative end**, and that is the
    # design's rule rather than a taste: *"Consent is never inferred."* ⛔ **A
    # preference nobody has expressed must not read as one they granted.**

    #: *"Unprompted findings, ranked. Off means Signora only answers what you
    #: ask."* ⚠️ **On by default because the design draws it on** — it is the
    #: product working, not a permission over the customer's data.
    ai_insights: bool = True
    #: *"Drafts open in your composer. **Nothing is ever sent on your
    #: behalf.**"* ⛔ **The second sentence is the reason the first is safe**,
    #: and it is a property of the product rather than of this flag.
    ai_drafts: bool = True
    #: *"Expands evidence under every claim instead of keeping it one click
    #: away."* **Off by default, as drawn.**
    always_show_citations: bool = False
    answer_style: AnswerStyle = AnswerStyle.DIRECT
    #: *"Hide anything below this."* ⚠️ **The design adds *"yours can be
    #: stricter than the workspace floor of 3, never looser"* — and no
    #: workspace AI floor exists**, so the personal floor is stored and the
    #: comparison is not asserted ([C-249](../../../../docs/LANE_COORDINATION.md)).
    confidence_floor: int = MIN_CONFIDENCE_FLOOR

    def entered(self, at: datetime) -> PersonPreferences:
        """Record that this person is in this workspace, now.

        ⛔ **Monotonic.** An `at` older than what is already stored is ignored
        rather than written: entries can arrive out of order — a retried
        request, a clock that stepped back — and **letting an older moment win
        would move somebody's last-used workspace backwards**, which is
        precisely the wrong answer at the one moment it matters.

        ⚡ **Not a `choose_` method, deliberately.** The others record a
        decision the person made about the product; this records something they
        did. **Naming it `choose_last_workspace` would imply a setting they can
        see and change**, and there is no such control in the design.
        """
        if self.last_entered_at is not None and at <= self.last_entered_at:
            return self
        return replace(self, last_entered_at=at)

    def left(self) -> PersonPreferences:
        """Forget that they were ever here.

        ⚡ **Called when a membership ends**, and 🔴 **it is hygiene rather than
        the control.** The control is that the derivation reads only live
        memberships, so this row is already unreachable by the time this runs —
        ⛔ **but a record of where somebody used to work should not outlive
        their access to it**, and leaving it costs nothing to remove.

        ⚠️ **Returns `self` when there is nothing to forget, and that is not an
        optimisation.** ⚡ **Every membership that ends calls this, and most people
        have never entered most of their workspaces** — so a `replace` that always
        produced a new object would make the caller write a preferences row **that
        did not previously exist**, for somebody who never opened a screen, in
        order to store the absence of a fact.
        """
        if self.last_entered_at is None:
            return self
        return replace(self, last_entered_at=None)

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
