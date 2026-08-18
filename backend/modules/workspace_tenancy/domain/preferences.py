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

from collections.abc import Mapping
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime, timedelta, tzinfo
from enum import StrEnum
from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from modules.workspace_tenancy.domain.exceptions import InvalidHomeCompositionError

#: The design's segmented control offers `3 · 4 · 5`, and `3` is where it sits.
#: ⚠️ **A floor, not a threshold anybody else can lower** — the design says
#: *"yours can be stricter … never looser"*, and the workspace half of that
#: does not exist yet ([C-249](../../../../docs/LANE_COORDINATION.md)).
#: 📁 **Home's four compositions**, as the design names them.
#: ⛔ **Closed, so a fifth cannot be stored by a client that invents one.**
HOME_COMPOSITIONS = frozenset({"executive", "seller", "revenue_operations", "activation"})

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


class TextSize(StrEnum):
    """📁 The design's segmented control: *100% · 112% · 125%*.

    ⚡ **Stored without the percent sign** — the symbol is how it is rendered,
    not what it is, and a value carrying its own formatting is one a second
    surface has to strip.
    """

    HUNDRED = "100"
    ONE_TWELVE = "112"
    ONE_TWENTY_FIVE = "125"


class ScreenReaderVerbosity(StrEnum):
    """📁 The design's segmented control: *Concise · Detailed*."""

    CONCISE = "concise"
    DETAILED = "detailed"


#: ⚡ **How many compositions a layout may cover**, and it is not a guess: 📁 Home
#: has exactly four, and {@link HOME_COMPOSITIONS} is the set. **A bound at the
#: boundary rather than a validation of membership** — see {@link HomeCardLayout}.
MAX_LAID_OUT_COMPOSITIONS = len(HOME_COMPOSITIONS)
#: ⚡ **A generous ceiling on one composition's cards.** 📁 Home's registry holds
#: sixteen; **this is input hygiene rather than a second copy of that number**,
#: which is why it is not sixteen.
MAX_LAID_OUT_CARDS = 64
#: A card id is a slug. ⛔ **Bounded so a client cannot store prose here.**
MAX_CARD_ID_LENGTH = 64


@dataclass(frozen=True, slots=True)
class HomeCardLayout:
    """One composition's arrangement, as a person left it.

    🔴 **Home's *Customise* control** — 📁 `Fortune Signora Home.dc.html` §10:
    *"opens the card-order panel as a drawer"*, and **`U-05`'s interim ruling**:
    *"**reorder and remove only.** Adding cross-composition cards is out of scope
    for the first implementation."* 📁 `3.2.3`: *"**card order within a
    composition is stable across visits**."*

    ## ⛔ Two lists, because one cannot tell *removed* from *new*

    ⚡ **`order` holds every card this person has arranged; `hidden` names the
    subset they took away.** ⛔ **A single list of kept cards would make a card's
    absence ambiguous** — removed, or added to the registry after they last
    customised? — **and the product would silently suppress every card it ships
    from then on.**

    ✅ **A card in neither list is new**, and Home draws it at its registry
    position. ✅ **A removed card keeps its place in `order`**, so restoring it
    puts it back where it was rather than at the end — 📁 the same instinct
    `P-05` states for activation: *"reordering shifts the list under the cursor."*

    ## ⛔ Card ids are not validated here, and that is deliberate

    📁 **Home is the composition authority** and its registry is the frontend's.
    ⚡ **This module validates SHAPE and BOUNDS, never membership** — a card
    catalogue in two places is the duplication [§2](../../../../CLAUDE.md)
    forbids, and it would reject a card the moment Home shipped one.
    """

    #: Every card this person has arranged, in the order they left it.
    order: tuple[str, ...] = ()
    #: The subset they removed. ⛔ **Not deleted from `order`** — see above.
    hidden: tuple[str, ...] = ()


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
    #: 🔴 **[TASK-1424] — when the first-run overlay was closed.** ⛔ `None` is
    #: *not dismissed*, and the design's word is *"dismissible forever"*, so
    #: this outlives the session by construction.
    first_run_dismissed_at: datetime | None = None
    #: 🔴 **[TASK-1424] — when the invite-the-team card was skipped.** ⛔ `None`
    #: is *not skipped*, and the design's window is derived from this moment
    #: rather than stored beside it.
    invite_skipped_at: datetime | None = None
    #: 🔴 **Home state 04 — when this person was told setup had finished.**
    #:
    #: 📁 *"A one-time strip states that setup is finished and what changed"*,
    #: and `AC-H03`: *"the setup-complete strip shown **exactly once**"*.
    #:
    #: ⛔ **The moment, not a `seen` boolean.** ⚡ Same reasoning as
    #: `first_run_dismissed_at` beside it: *once* is a claim about a specific
    #: earlier moment, and a bare flag cannot answer *when* — which is the only
    #: question anybody asks when a strip appears twice.
    #:
    #: ⚠️ **Per person, not per workspace.** 📁 The design says *"one-time"* of
    #: a strip a person reads, and a colleague who joins later has still never
    #: been told. **Their first entry is their once.**
    setup_complete_seen_at: datetime | None = None

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
    #: 📁 **Home's rule 2** — *"Person has set a start-page preference of a
    #: specific composition… Honoured over role."*
    #:
    #: ⛔ **`None` means *not set*, and that is not the same as *seller*.** 📁 The
    #: resolver falls through to the role rules when it is absent; storing a
    #: default here would silently pin every person to one composition and make
    #: rule 3 unreachable.
    #:
    #: ⚠️ **Text rather than an enum in the database, exactly as `language` and
    #: `timezone` are.** ⚡ The four names are the DESIGN's closed set and the
    #: domain validates against it; a PostgreSQL enum would make adding a fifth
    #: composition a migration rather than a design decision.
    home_composition: str | None = None
    #: 🔴 **Home's *Customise* panel, per composition** — 📁 §10 and `3.2.3`'s
    #: *"card order within a composition is stable across visits."*
    #:
    #: ⛔ **Keyed by composition**, because the design scopes the control *"within
    #: a composition"*. ⚡ **An absent key is *never customised***, which is not
    #: the same as *customised to nothing*: the first renders the registry's own
    #: order, the second would render an empty Home.
    home_layout: Mapping[str, HomeCardLayout] = field(default_factory=dict)

    # ── Language & region ─────────────────────────────────────────────────
    #: ⛔ **Text rather than an enum, and deliberately.** ⚡ The design shows
    #: ONE value for each — *"31 Dec 2026"*, *"1.234,56"*, *"Monday"* — and
    #: never lists the options. **Inventing a `DateFormat` enum from a single
    #: sample would decide which formats Signora supports**, which is a product
    #: question this file is not entitled to answer. 📁 `language` and
    #: `timezone` above are stored the same way for the same reason.
    date_format: str | None = None
    number_format: str | None = None
    week_starts_on: str | None = None

    # ── Accessibility ─────────────────────────────────────────────────────
    #: 🔴 **The OVERRIDE, not the system's setting.** 📁 The design shows
    #: *"On — from system"*, and the system half already works without a
    #: column: `globals.css` carries `@media (prefers-reduced-motion: reduce)`
    #: and the shell uses `motion-reduce:` throughout. ⛔ **Defaulting this true
    #: would force reduced motion on everybody who never opened the screen**,
    #: and storing what the device already reports is the hidden input
    #: [§2](../../../../CLAUDE.md) forbids.
    reduce_motion: bool = False
    increase_contrast: bool = False
    always_show_focus_ring: bool = False
    #: ⚡ **On by default, because the design shows it on.** ⛔ Links that
    #: stopped being underlined for somebody who never opened this screen would
    #: be a regression delivered by a migration.
    underline_links: bool = True
    text_size: TextSize = TextSize.HUNDRED
    screen_reader_verbosity: ScreenReaderVerbosity = ScreenReaderVerbosity.DETAILED

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

    def dismissed_first_run(self, at: datetime) -> PersonPreferences:
        """Record that this person closed the first-run overlay.

        ⚡ **Idempotent, and the FIRST moment wins.** ⛔ A second dismissal must
        not move the timestamp forward: *"dismissible forever"* is answered by
        the earliest close, and overwriting it would lose the only fact the
        column exists to carry — **when this person stopped being new.**

        ⚠️ **Deliberately not a `choose_` method**, for the reason
        {@link entered} gives one paragraph up: the others record a decision
        about a setting somebody can see and change, **and there is no control
        in the design that un-dismisses this.**
        """
        if self.first_run_dismissed_at is not None:
            return self
        return replace(self, first_run_dismissed_at=at)

    def first_entry_today(self, at: datetime) -> bool:
        """Whether `at` is this person's **first** entry into this workspace today.

        🔴 **Home state 13 · `state.returningpartial`'s sibling** — 📁 *"second or
        later entry on the same calendar day in this workspace"* renders *"identical
        to state 06 with the workspace confirmation strip suppressed. **Home does
        not congratulate people for returning.**"* ⚡ And 📁 Entry rule 12's strip is
        *"gone on the second visit that day."*

        ⛔ **Asked BEFORE the entry is recorded**, because recording it makes the
        answer `False` for the rest of the day. {@link RecordWorkspaceEntry} reads
        this and then writes, in that order, which is why the use case returns it
        rather than a caller re-deriving it afterwards.

        ⚠️ **A calendar day needs a zone, and it is this person's.** 📁 `U-06`'s
        interim ruling for the same question one card over is *"per person in
        profile timezone"*, and `timezone` on this aggregate is where that lives.
        ⛔ **`None` means *not chosen*, which is not UTC** — but a day boundary has
        to fall somewhere, and UTC is the only zone the platform can assert without
        inventing a preference nobody expressed. **Recorded rather than hidden:** a
        person in Auckland who has not set a zone sees the strip again at noon.

        ⚡ **Never entered is a first entry**, which is the reading that makes rule
        11 and rule 12 agree: somebody who has been nowhere has not been here today.
        """
        if self.last_entered_at is None:
            return True
        zone = self._zone()
        return self.last_entered_at.astimezone(zone).date() != at.astimezone(zone).date()

    def _zone(self) -> tzinfo:
        """This person's zone, or UTC when they have expressed none.

        ⛔ **Not a stored default.** 📁 `timezone`'s own comment: *"`None` means
        not chosen, which is different from UTC — a stored UTC would be an answer
        nobody gave."* ✅ **This derives a day boundary from the absence** without
        writing one back.
        """
        if self.timezone is None:
            return UTC
        try:
            return ZoneInfo(self.timezone)
        except (ZoneInfoNotFoundError, ValueError):
            # ⚠️ **A zone the platform cannot resolve is not a reason to refuse an
            # entry.** ⛔ The strip is a courtesy; failing the whole entry over an
            # unrecognised IANA string would make it a blocker.
            return UTC

    def choose_home_layout(
        self, composition: str, layout: HomeCardLayout
    ) -> PersonPreferences:
        """Record how this person arranged one composition's cards.

        📁 Home §10's *Customise* drawer, and `U-05`'s interim: **reorder and
        remove only**.

        ⛔ **One composition at a time.** ⚡ Replacing the whole map would let a
        panel that only ever shows the current composition wipe the arrangement
        of a composition the person is not looking at — which they would meet the
        next time they switched, with no way to know what happened.
        """
        if composition not in HOME_COMPOSITIONS:
            raise InvalidHomeCompositionError(composition)
        return replace(self, home_layout={**self.home_layout, composition: layout})

    def saw_setup_complete(self, at: datetime) -> PersonPreferences:
        """Record that this person has been told setup is finished.

        ⚡ **Idempotent, and the FIRST moment wins** — the same rule
        {@link dismissed_first_run} follows, and for the same reason: 📁 *"shown
        exactly once"* is answered by the earliest showing, and overwriting it
        would lose the only fact the column carries.

        ⛔ **Not `choose_`.** There is no control in the design that un-shows it.
        """
        if self.setup_complete_seen_at is not None:
            return self
        return replace(self, setup_complete_seen_at=at)

    #: 📁 ***"Hides them for 30 days per person."***
    INVITE_SKIP_DAYS = 30

    def skipped_invite(self, at: datetime) -> PersonPreferences:
        """Put the invite card away for a while.

        ⚠️ **The LATEST skip wins here, and that is the opposite of
        {@link dismissed_first_run}** — deliberately. ⛔ A dismissal answers
        *when did this person stop being new*, which the first close settles
        forever; **a skip restarts a window**, and somebody who skips again a
        month later is asking for another thirty days rather than repeating an
        old request.
        """
        return replace(self, invite_skipped_at=at)

    def unskipped_invite(self) -> PersonPreferences:
        """📁 ***"Reversible from the progress line."*** ⛔ Setting it back to
        `None` is the whole of it — no second column to contradict the date."""
        if self.invite_skipped_at is None:
            return self
        return replace(self, invite_skipped_at=None)

    def invite_is_hidden(self, now: datetime) -> bool:
        """⚡ **Derived, never stored.** 📁 [§2]: a stored expiry would be a
        second representation of a fact this column already carries, **and the
        two would disagree the first time a clock moved.**"""
        if self.invite_skipped_at is None:
            return False
        return now - self.invite_skipped_at < timedelta(days=self.INVITE_SKIP_DAYS)

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
