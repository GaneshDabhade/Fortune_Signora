"""**Something happened, and one person should be told.**

📁 **[TASK-495](../../../../docs/BACKLOG.md)**, on
[ADR-0017](../../../../docs/architecture/adr/0017-notifications.md) and
[D-239](../../../../docs/DECISION_REGISTER.md).

## 🔴 What this file is, and the thing it is deliberately not

⚡ **[TASK-480](../../../../docs/BACKLOG.md) built what a person has READ.**
⛔ **It could not build what they had read, because nothing published one** —
📁 its own domain file says so: *"A notification. This records that a person
has READ one — nothing about what it said."* ✅ **This is the missing half, and
it is why the read state exists.**

⛔ **It is NOT a notification platform.** 📁 **D-239, product owner:**
*"no new module, no ADR, no abstraction, no architectural layer — we are not
building a notification platform."* ⚡ **So this lives in `workspace_tenancy`
beside the read state it completes**, and everything a notification system
usually grows — templates, digests, quiet hours, preferences, a delivery log —
**is absent.** 📁 Those are the *Notification Center*'s, Workflow 17's own
decomposition.

## ⛔ And it does not deliver

📁 **[ADR-0017](../../../../docs/architecture/adr/0017-notifications.md)
ratified **Novu** for cross-channel delivery, and no adapter is written here.**
⚡ **What this file owns is the trigger interface that ADR names** — *"a single,
channel-agnostic notification trigger interface used by every module"* —
✅ **with exactly one channel behind it: in-app, which Signora owns end to end.**

⛔ **An adapter written for a call nobody makes is the speculative abstraction
[§6](../../../../CLAUDE.md) forbids**, so the vendor arrives when a channel it
carries is actually requested.

## 🔴 A channel with no adapter FAILS. It does not degrade.

📁 **The precedent is `ai_platform/infrastructure/composition.py` and it is
followed rather than adapted**:

> ***"An adapter is registered only when its credentials exist … There is
> deliberately no fallback between them."***

⚠️ **Both halves, and the second is the one that is easy to lose.** ⛔ **A
request for `SLACK` that quietly became an in-app notice would tell the caller
it had reached Slack**, and 📁 [§10](../../../../CLAUDE.md) names exactly that
failure: *"a service running on it is indistinguishable from one that works —
which is strictly worse than the outage it would hide."*

✅ **In-app is a CHANNEL, never a substitute for one that failed to configure.**

## ⚡ Why the channels enum names four and registers one

📁 **[C-224](../../../../docs/LANE_COORDINATION.md)'s carve-out, on
`Resource`: adding an enum member is a DECLARATIVE REGISTRATION, never a
grant.** ⛔ **The three unregistered members are what make the refusal
testable** — a registry whose enum and whose registrations were the same set
could not express *"this channel is not configured"* at all, and the guard
above would be a comment.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from typing import Any, Protocol
from uuid import UUID


class NotificationError(ValueError):
    """Every refusal this file makes, so a caller catches one thing."""


class Channel(StrEnum):
    """**How a notification reaches somebody.**

    ⛔ **Naming one here does not deliver it.** ⚡ **The registry decides what is
    reachable**, and a member with no registered adapter is refused rather than
    rerouted — 📁 which is the whole point of listing more than one.
    """

    #: ✅ **The only channel this slice registers.** 📁 **Signora owns it end to
    #: end** — it writes a row this module already reads, so there is no vendor
    #: between the fact and the customer.
    IN_APP = "in_app"
    #: ⛔ **Declared, not delivered** — ADR-0017's, and Workflow 17's to build.
    EMAIL = "email"
    SLACK = "slack"
    MOBILE = "mobile"


class Category(StrEnum):
    """**Which of the panel's tabs an item belongs to.**

    📁 **The design names three tabs — *Needs you*, *Mentions*, *All*** — ⛔ **and
    `ALL` is deliberately not a member.** ⚡ **`All` is the ABSENCE of a filter,
    not a third kind of notification**: a category by that name would be one a
    producer could set, and an item that was *All* but neither of the other two
    would appear in one tab and vanish from both the others.
    """

    #: ⚡ **Something is waiting on this person.** The item states what.
    NEEDS_YOU = "needs_you"
    #: ⚡ **Somebody named them.** ⛔ **Never set by the platform about itself** —
    #: an agent that "mentioned" you would be borrowing a colleague's weight.
    MENTION = "mention"


class ActorKind(StrEnum):
    """**Who or what acted** — 📁 the design's *intelligence hue* in one field.

    > ***"Agent and AI notifications are marked with the intelligence hue so a
    > generated nudge never reads as a colleague's request."***

    🔴 **So this is a domain fact, not a rendering hint.** ⛔ **A surface that
    inferred it from the actor's name would get it wrong the first time
    somebody named a workspace after a model.**
    """

    PERSON = "person"
    AGENT = "agent"


@dataclass(frozen=True, slots=True)
class Actor:
    """**Who or what acted.**

    ## 🔴 A person is an IDENTITY here, never a name — and that is [C-203](../../../../docs/LANE_COORDINATION.md)

    ⛔ **There is no `display_name` for a person, and its absence is the whole
    point.** 📁 **[C-203](../../../../docs/LANE_COORDINATION.md) is `DEFERRED`
    with a concrete trigger** — 📁 [D-116](../../../../docs/DECISION_REGISTER.md),
    *M-E, when a provider supplies a person identifier* — **and its impact line
    names this surface in terms:** *"how **anything** names a user: AI attribution, audit
    actors, **notifications**, mentions."*

    📁 **37 §identity says why**: `MembershipResponse` returns `user_id` and
    **cannot** return a name — **Better Auth is the sole Authentication
    Authority and the Python tier only verifies**
    ([ADR-0026](../../../../docs/architecture/adr/0026-jwt-boundary-architecture.md)).

    ⚠️ **A `name: str` field here would have looked harmless and would have
    answered C-203 by accident**, in the module least entitled to: 📁 37 says
    the same question *"appears in Timeline, comments, audit history, AI
    attribution, notifications, mentions and assignments — so answering it
    inside [one page] would decide it for all of them by accident."*

    ✅ **So this carries identity and the surface resolves it**, exactly as
    {@link Subject} carries an id and no cached title.

    ## ⚡ An agent's name IS the platform's, and that is why it is here

    ⛔ **`agent_name` is not the same field wearing a different label.** 📁 An
    agent has no Better Auth identity to resolve — **the platform authored it**,
    so naming one needs nobody's answer. ⚠️ **It is a capability's name, never a
    model's** — *"Research"*, not a vendor: 📁 a vendor's name on a customer's
    screen is the neutrality leak `ai_platform` spends a whole registry
    preventing.

    🔴 **The two are mutually exclusive and the guard is here rather than at the
    surface.** ⛔ **An `AGENT` carrying a person's id would render a generated
    nudge under a colleague's avatar** — precisely the confusion the
    intelligence hue exists to prevent, arriving through the data instead of
    through the styling.
    """

    kind: ActorKind
    person_id: UUID | None = None
    agent_name: str | None = None

    def __post_init__(self) -> None:
        if self.kind is ActorKind.PERSON:
            if self.person_id is None:
                raise NotificationError(
                    "a person acted and no person was identified. The reader is "
                    "meant to be able to follow up with them, and an item that "
                    "names nobody cannot say who acted at all."
                )
            if self.agent_name is not None:
                raise NotificationError(
                    "a person carrying an agent's name would render a "
                    "colleague's request under the intelligence hue — the "
                    "confusion that hue exists to prevent, inverted."
                )
            return
        if self.person_id is not None:
            raise NotificationError(
                "an agent carrying a person's identity would render a generated "
                "nudge under a colleague's avatar — the confusion the "
                "intelligence hue exists to prevent."
            )
        if self.agent_name is None or not self.agent_name.strip():
            raise NotificationError(
                "an agent acted and nothing named it. Unlike a person, an "
                "agent's name is the platform's own to give, so a blank here is "
                "an omission rather than a question C-203 has not answered."
            )


@dataclass(frozen=True, slots=True)
class Subject:
    """**Which record this is about.**

    ⚡ **Identity only.** ⛔ **No title, no summary of the record, no link** —
    📁 *events carry identity; ports carry payload*, and the same rule holds
    here: **a notification that cached an account's name would be showing a
    name that changed last week.**
    """

    kind: str
    id: UUID

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise NotificationError(
                "a subject with no kind is an id nothing can resolve. The reader "
                "is told which record acted upon, and an untyped uuid is not one."
            )


@dataclass(frozen=True, slots=True)
class FeedItem:
    """One notification, and whether this person has read it.

    ⛔ **Two facts, deliberately not one.** The notification records *what
    happened*; :attr:`read_at` records *when this person read it*, which is a
    later and separate event with its own row and its own immutability
    ([§2](../../../../CLAUDE.md)). ⚡ **Folding a read time onto the
    notification would put a mutable-looking field on a record the module
    refuses to let anything update.**

    **The panel needs both in one place** — 📁 the design's *"unread is a 6px
    dot on the right, never a coloured row"* — and a surface that fetched the
    feed and then asked separately which were read would render every item as
    unread for one frame, on the one control whose entire job is to say how
    much is outstanding.
    """

    notification: "Notification"
    #: `None` means unread. **Not a boolean**: the time is what makes
    #: *"opening an item marks it read"* auditable afterwards, and a flag
    #: would answer *whether* without ever answering *when*.
    read_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class Notification:
    """**One thing that happened, addressed to exactly one person.**

    ## 🔴 One recipient, and that is the tenancy narrowing rather than a shape

    📁 **492 §0, quoted on [D-239](../../../../docs/DECISION_REGISTER.md):** *"a
    NARROWING of tenant-owned, never a parallel to it … one predicate is
    added."* ⛔ **A notification addressed to a workspace would be per-person
    state held collectively**, which is D-239's own exclusion — and *"everyone
    has read it"* is a coincidence, never a state.

    ✅ **Telling five people means five notifications**, and each of them can be
    read, ignored or counted independently. ⚡ **Which is what a badge is.**

    ## ⚡ The four things an item must say

    📁 **The Definition of Done, verbatim**: *"can tell what acted, on which
    record, and what is expected of them."* ✅ **{@link Actor} · {@link
    Subject} · `summary` · `expectation`** — ⛔ **and none of them is optional**,
    because an item missing any one is a row that reached a customer and told
    them nothing they could act on.
    """

    id: UUID
    workspace_id: UUID
    #: 🔴 **The person, and there is exactly one.** ⚡ **The same predicate
    #: `notification_read` narrows by** — 492 §0.
    recipient_id: UUID
    category: Category
    actor: Actor
    subject: Subject
    #: ⚡ **What happened, in the customer's vocabulary.**
    summary: str
    #: 🔴 **What is expected of the reader.** ⛔ **Not a call to action label** —
    #: 📁 the design asks the item to say what is expected, and *"View"* is not.
    expectation: str
    occurred_at: datetime

    def __post_init__(self) -> None:
        if self.occurred_at.tzinfo is None:
            raise NotificationError(
                "a notification without a timezone is a claim about no "
                "particular moment. The panel groups by day, so a naive "
                "timestamp is the one item that could land under the wrong one."
            )
        if not self.summary.strip():
            raise NotificationError(
                "a notification with no summary is an item that reached a "
                "customer and told them nothing."
            )
        if not self.expectation.strip():
            raise NotificationError(
                "a notification with no expectation is a nudge that does not "
                "say what it wants. The design asks every item to state what is "
                "expected of the reader."
            )


@dataclass(frozen=True, slots=True)
class NotificationRequest:
    """**What a caller asks for.** ⚡ *Tell this person that this happened.*

    ## 🔴 Why this is not a {@link Notification}

    ⛔ **A request carries no id and no moment.** ⚡ **Both are the platform's to
    assign** — 📁 [§2](../../../../CLAUDE.md), *hidden inputs are architecture
    defects*: **a caller that supplied `occurred_at` could date a notification
    into yesterday**, and the panel groups by day.

    ## ⚡ `channels` is required and may not be empty

    ⛔ **A request naming no channel is a notification nobody receives**, and it
    would return successfully — 📁 the [§10](../../../../CLAUDE.md) failure
    exactly: **indistinguishable from one that worked.**

    ⚠️ **There is no default.** 🔴 **A default of `{IN_APP}` would be the
    fallback this module spends a registry refusing**, arriving as a
    convenience: every caller that forgot to think about channels would
    silently get the one channel that always works.
    """

    workspace_id: UUID
    recipient_id: UUID
    category: Category
    actor: Actor
    subject: Subject
    summary: str
    expectation: str
    channels: frozenset[Channel]

    def __post_init__(self) -> None:
        if not self.channels:
            raise NotificationError(
                "a notification request naming no channel reaches nobody and "
                "returns successfully, which is worse than failing. Name the "
                "channels this should travel on."
            )


#: 📁 **The wire name, cataloged in
#: [06-events.md](../../../../docs/architecture/06-events.md).** ⚡ **Named as a
#: constant rather than only as a dataclass default** — 📁 `ai_research_engine`
#: found the hard way that `slots=True` makes the class attribute a descriptor,
#: so `Event.event_type` reads the slot and a subscription registered from it
#: points at a repr nothing publishes.
NOTIFICATION_REQUESTED: str = "notification.requested"

#: ⚡ **The wire separator for `channels`.** ⛔ **A list would serialize as JSON
#: and the payload contract is flat** — 📁 `to_payload()` returns
#: `dict[str, Any]` and every sibling event keeps its values scalar.
_CHANNEL_SEPARATOR = ","


@dataclass(frozen=True, kw_only=True)
class NotificationRequested:
    """**A module asked for somebody to be told.**

    ## 🔴 Why this is an EVENT and not a method call

    📁 **[05 §Synchronous vs. Asynchronous](../../../../docs/architecture/05-module-dependencies.md)
    lists every approved synchronous edge into this module, and every one of
    them is READ-ONLY**: *"Any module → Workspace & Tenancy: resolve/validate
    workspace context (read-only)."*

    ⛔ **A producer calling a `notify()` port directly would be a synchronous
    WRITE into another module's data** — ⚡ **not on that list, and 🔴 extending
    it is an architecture change no lane may make.** ⚠️ **The convenient version
    of this file was one import away and would have been exactly the *"I could
    just add it"* that [§20e](../../../../CLAUDE.md) names: an architectural
    decision taken inside a feature slice, small enough that nobody notices it
    was one.**

    ✅ **So the producer publishes.** 📁 **[Principle 3](../../../../docs/architecture/02-principles.md)
    makes event-driven the default and 📁 the row asked for exactly this** —
    *"Publication rides the existing outbox/relay
    ([ADR-0011](../../../../docs/architecture/adr/0011-background-processing-and-event-bus-transport.md))
    — not a new mechanism."* ⚡ **And the edge it creates is the one 05 already
    ratifies: *Workspace & Tenancy → all | Conformist | Every module conforms;
    none influences it.*** ✅ **A producer conforms to this contract; it does not
    reach into this module.**

    ## ⚡ It rides the producer's OWN outbox publisher

    ⛔ **No business module reads `outbox_event`** ([§8](../../../../CLAUDE.md)),
    **and none does here**: a producer publishes through the `EventPublisher`
    port it already holds, and the consumer receives an `EventEnvelope` from the
    dispatcher. 🔴 **Atomic with the thing being announced**, because the outbox
    row commits in the same transaction — ✅ **so a run that failed to record its
    own outcome never tells a customer it succeeded.**

    ## ⛔ Identity and vocabulary, never prose about the record

    ⚡ **`summary` and `expectation` ARE the message and are carried**; ⛔ **the
    subject's title is not** — 📁 *events carry identity; ports carry payload*,
    and a cached account name would show one that changed last week.
    """

    event_id: UUID
    workspace_id: UUID
    occurred_at: datetime
    recipient_id: UUID
    category: Category
    actor: Actor
    subject: Subject
    summary: str
    expectation: str
    channels: frozenset[Channel]
    causation_id: UUID | None = None
    event_type: str = NOTIFICATION_REQUESTED
    event_version: int = 1

    def to_payload(self) -> dict[str, Any]:
        return {
            "recipient_id": str(self.recipient_id),
            "category": self.category.value,
            "actor_kind": self.actor.kind.value,
            "actor_person_id": (
                None if self.actor.person_id is None else str(self.actor.person_id)
            ),
            "actor_agent_name": self.actor.agent_name,
            "subject_kind": self.subject.kind,
            "subject_id": str(self.subject.id),
            "summary": self.summary,
            "expectation": self.expectation,
            # ⚡ **Sorted, so the same request serializes identically twice** —
            # 📁 [§2](../../../../CLAUDE.md): a `frozenset` has no order, and an
            # event whose bytes depend on the hash seed is not replayable.
            "channels": _CHANNEL_SEPARATOR.join(
                sorted(channel.value for channel in self.channels)
            ),
            "payload_version": self.event_version,
        }


def request_from_payload(*, workspace_id: UUID, payload: Mapping[str, Any]) -> NotificationRequest:
    """**Rebuild the request a producer asked for, from the envelope.**

    🔴 **`workspace_id` comes from the ENVELOPE and never from the payload.** ⛔
    **Every event is workspace-scoped** ([§9](../../../../CLAUDE.md)) **and a
    payload that could name its own tenant would be a cross-workspace write one
    typo away** — ⚡ the same reason `to_payload()` above does not emit it.

    ⚡ **The domain's guards run here**, on data that crossed a wire — ✅ **so a
    malformed event fails at the boundary rather than persisting a row no
    surface can render.**
    """
    kind = ActorKind(str(payload["actor_kind"]))
    raw_person = payload.get("actor_person_id")
    raw_agent = payload.get("actor_agent_name")
    raw_channels = str(payload["channels"])
    return NotificationRequest(
        workspace_id=workspace_id,
        recipient_id=UUID(str(payload["recipient_id"])),
        category=Category(str(payload["category"])),
        actor=Actor(
            kind=kind,
            person_id=None if raw_person is None else UUID(str(raw_person)),
            agent_name=None if raw_agent is None else str(raw_agent),
        ),
        subject=Subject(
            kind=str(payload["subject_kind"]), id=UUID(str(payload["subject_id"]))
        ),
        summary=str(payload["summary"]),
        expectation=str(payload["expectation"]),
        channels=frozenset(
            # ⛔ **An empty string would split to `['']` and raise on `Channel`,
            # which is the right failure but the wrong message.** ⚡ The request's
            # own guard says what is missing, so the empty case reaches it.
            Channel(name)
            for name in raw_channels.split(_CHANNEL_SEPARATOR)
            if name
        ),
    )


class NotificationChannel(Protocol):
    """**One way of reaching somebody.**

    ⚡ **The interface ADR-0017 calls *channel-agnostic*, from the channel's
    side.** ⛔ **Nothing above this learns which vendor, if any, is behind it.**
    """

    @property
    def channel(self) -> Channel:
        """Which channel this adapter serves. **The registry's key.**"""
        ...

    async def deliver(self, notification: Notification) -> None:
        """Deliver it, or raise.

        ⛔ **Returning normally means delivered.** ⚡ **A channel that swallowed
        its own failure would make an outage indistinguishable from a working
        service** — 📁 [§10](../../../../CLAUDE.md), the one thing this layer
        may never do.
        """
        ...


class ChannelNotRegisteredError(NotificationError):
    """**A channel was requested and nothing serves it.**

    🔴 **This is the refusal, and it must never become a fallback.** 📁
    `ai_platform`'s registry says it in terms — *"There is deliberately no
    fallback between them"* — and the reason is 📁 [§10](../../../../CLAUDE.md):
    ⛔ **a Slack request quietly delivered in-app tells the caller it reached
    Slack**, and nobody learns otherwise until a customer asks why they were
    never told.
    """

    def __init__(self, channel: Channel, registered: frozenset[Channel]) -> None:
        available = ", ".join(sorted(c.value for c in registered)) or "none"
        super().__init__(
            f"no adapter serves the '{channel.value}' channel (registered: {available}). "
            "A channel with no adapter is refused rather than rerouted: delivering "
            "this somewhere else would report a delivery that did not happen."
        )
        self.channel = channel


class DuplicateChannelError(NotificationError):
    """**Two adapters claimed one channel.**

    ⛔ **Almost always a composition mistake**, and allowed silently it would
    mean *which* adapter delivers depends on registration order — 📁 the same
    argument `SubscriptionRegistry` makes about a duplicate subscription.
    """

    def __init__(self, channel: Channel) -> None:
        super().__init__(
            f"the '{channel.value}' channel already has an adapter. Two would make "
            "delivery depend on registration order, which is not a decision "
            "anybody made."
        )


class NotificationChannelRegistry:
    """**What is reachable in this deployment.**

    📁 **Shaped after `AIProviderRegistry`**, and for the identical reason:
    ✅ **an adapter is registered only where its configuration exists**, so a
    deployment that has not configured a channel behaves exactly as it did
    before that adapter was written.

    ⛔ **It resolves; it never chooses.** ⚡ **There is no `default`, no
    `first_available` and no ordering** — every one of those is a fallback
    wearing a different word.
    """

    def __init__(self) -> None:
        self._channels: dict[Channel, NotificationChannel] = {}

    def register(self, adapter: NotificationChannel) -> None:
        if adapter.channel in self._channels:
            raise DuplicateChannelError(adapter.channel)
        self._channels[adapter.channel] = adapter

    def resolve(self, channel: Channel) -> NotificationChannel:
        """The adapter serving `channel`, or {@link ChannelNotRegisteredError}."""
        found = self._channels.get(channel)
        if found is None:
            raise ChannelNotRegisteredError(channel, self.registered())
        return found

    def registered(self) -> frozenset[Channel]:
        """⚡ **What this deployment can actually reach.** Read by the error
        above so the refusal names the alternatives rather than only the gap."""
        return frozenset(self._channels)


__all__ = [
    "NOTIFICATION_REQUESTED",
    "Actor",
    "ActorKind",
    "Category",
    "Channel",
    "ChannelNotRegisteredError",
    "DuplicateChannelError",
    "Notification",
    "NotificationChannel",
    "NotificationChannelRegistry",
    "NotificationError",
    "NotificationRequest",
    "NotificationRequested",
    "Subject",
    "request_from_payload",
]
