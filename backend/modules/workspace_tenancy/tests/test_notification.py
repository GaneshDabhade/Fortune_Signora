"""**The trigger every module calls, and the refusals that make it trustworthy.**

📁 **[TASK-495](../../../../docs/BACKLOG.md)**, on
[ADR-0017](../../../../docs/architecture/adr/0017-notifications.md).

## 🔴 The three properties this file exists to hold

⚡ **① A channel with no adapter FAILS.** 📁 `ai_platform`: *"There is
deliberately no fallback between them."* ⛔ **A Slack request quietly delivered
in-app reports a delivery that did not happen.**

⚡ **② All channels, or none.** 📁 The Definition of Done is *"a customer sees
that something happened, **once**"* — ⛔ **a partial delivery followed by a retry
is how *once* becomes twice.**

⚡ **③ The wire shape is the one the code produces, not the one a fixture
imagined.** ⚠️ **A hand-written payload dict would have passed every parse test
in this file while the real `to_payload()` emitted something else** — 📁 the
defect `machine_credentials` found when `token_urlsafe` put a `_` in a token and
every hand-written fixture still passed. **So the round trip is asserted.**
"""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest

from modules.workspace_tenancy.application.notify import Notify
from modules.workspace_tenancy.domain.notification import (
    NOTIFICATION_REQUESTED,
    Actor,
    ActorKind,
    Category,
    Channel,
    ChannelNotRegisteredError,
    DuplicateChannelError,
    Notification,
    NotificationChannel,
    NotificationChannelRegistry,
    NotificationError,
    NotificationRequest,
    NotificationRequested,
    Subject,
    request_from_payload,
)
from modules.workspace_tenancy.public.notifications import Notifier

NOW = datetime(2026, 8, 16, 9, 30, tzinfo=UTC)
WORKSPACE = UUID("11111111-1111-1111-1111-111111111111")
RECIPIENT = UUID("22222222-2222-2222-2222-222222222222")
SUBJECT = UUID("33333333-3333-3333-3333-333333333333")
NOTIFICATION_ID = UUID("44444444-4444-4444-4444-444444444444")

AGENT = Actor(kind=ActorKind.AGENT, agent_name="Research")


def a_request(*, channels: frozenset[Channel] = frozenset({Channel.IN_APP})) -> NotificationRequest:
    return NotificationRequest(
        workspace_id=WORKSPACE,
        recipient_id=RECIPIENT,
        category=Category.NEEDS_YOU,
        actor=AGENT,
        subject=Subject(kind="opportunity", id=SUBJECT),
        summary="Signora finished researching this account.",
        expectation="Open the account to read what Signora found.",
        channels=channels,
    )


class RecordingChannel:
    """A channel that remembers what it was handed. **Delivers nothing.**"""

    def __init__(self, channel: Channel) -> None:
        self._channel = channel
        self.delivered: list[Notification] = []

    @property
    def channel(self) -> Channel:
        return self._channel

    async def deliver(self, notification: Notification) -> None:
        self.delivered.append(notification)


class FailingChannel(RecordingChannel):
    """⚡ **A channel whose vendor is down**, which is not the same thing as one
    that is unconfigured — and the two must not be conflated."""

    async def deliver(self, notification: Notification) -> None:
        raise RuntimeError("the vendor did not answer")


def _the_use_case_is_the_published_trigger(notify: Notify) -> Notifier:
    """🔴 **The structural check, and `mypy --strict` performs it.**

    ⛔ **`hasattr` would pass for a method with the wrong signature, the wrong
    argument names or the wrong return type** — ⚡ **exactly the three ways a
    port and its implementation drift.** ✅ **Returning the use case AS the
    protocol is the real assertion**, and it resolves here rather than waiting
    for a producer to import it.
    """
    return notify


def _the_recording_double_is_a_channel(channel: RecordingChannel) -> NotificationChannel:
    """⚡ **And the double conforms too**, so a `NotificationChannel` change
    fails this file rather than only the production adapter."""
    return channel


class TestAChannelWithNoAdapterFailsRatherThanDegrading:
    """🔴 **The rule the row corrected itself on.**

    📁 *"Registered-where-a-credential-exists: yes. Falling back: no."*
    """

    def test_resolving_an_unregistered_channel_names_what_is_registered(self) -> None:
        """⚡ **The error names the alternatives**, so an operator learns which
        channel is missing rather than only that one is."""
        registry = NotificationChannelRegistry()
        registry.register(RecordingChannel(Channel.IN_APP))

        with pytest.raises(ChannelNotRegisteredError, match="in_app") as raised:
            registry.resolve(Channel.SLACK)
        assert "slack" in str(raised.value)

    def test_an_empty_registry_says_none_rather_than_an_empty_list(self) -> None:
        with pytest.raises(ChannelNotRegisteredError, match="registered: none"):
            NotificationChannelRegistry().resolve(Channel.IN_APP)

    def test_two_adapters_cannot_claim_one_channel(self) -> None:
        """⛔ **Allowed silently, WHICH adapter delivers would depend on
        registration order** — a decision nobody made."""
        registry = NotificationChannelRegistry()
        registry.register(RecordingChannel(Channel.IN_APP))
        with pytest.raises(DuplicateChannelError, match="already has an adapter"):
            registry.register(RecordingChannel(Channel.IN_APP))

    def test_the_enum_names_more_channels_than_the_registry_serves(self) -> None:
        """🔴 **This is what makes the refusal expressible at all.**

        ⛔ **A registry whose enum and whose registrations were the same set
        could not represent *this channel is not configured*** — and the guard
        above would be a comment. 📁 The same shape as
        [C-224](../../../../docs/LANE_COORDINATION.md)'s `Resource`: **declaring
        a member is a registration, never a grant.**
        """
        registry = NotificationChannelRegistry()
        registry.register(RecordingChannel(Channel.IN_APP))
        assert registry.registered() < frozenset(Channel)


class TestEveryChannelIsResolvedBeforeAnyIsDelivered:
    """🔴 **All, or none.** 📁 *"a customer sees that something happened, once."*"""

    @pytest.mark.asyncio
    async def test_an_unregistered_channel_delivers_none_of_the_others(self) -> None:
        """⛔ **The ordering defect this file exists to catch.**

        ⚡ **Resolving lazily would deliver in-app, then fail on Slack** —
        leaving the caller with an exception and the customer with a
        notification. **The retry that follows delivers the in-app one twice.**
        """
        in_app = RecordingChannel(Channel.IN_APP)
        registry = NotificationChannelRegistry()
        registry.register(in_app)

        notify = Notify(channels=registry, clock=lambda: NOW, new_id=lambda: NOTIFICATION_ID)
        with pytest.raises(ChannelNotRegisteredError):
            await notify.notify(a_request(channels=frozenset({Channel.IN_APP, Channel.SLACK})))

        assert in_app.delivered == [], (
            "in-app was delivered before the unreachable channel was discovered — "
            "the retry that follows will deliver it a second time"
        )

    @pytest.mark.asyncio
    async def test_every_registered_channel_receives_the_same_notification(self) -> None:
        in_app = RecordingChannel(Channel.IN_APP)
        email = RecordingChannel(Channel.EMAIL)
        registry = NotificationChannelRegistry()
        registry.register(in_app)
        registry.register(email)

        notify = Notify(channels=registry, clock=lambda: NOW, new_id=lambda: NOTIFICATION_ID)
        delivered = await notify.notify(
            a_request(channels=frozenset({Channel.IN_APP, Channel.EMAIL}))
        )

        assert in_app.delivered == [delivered]
        assert email.delivered == [delivered]

    @pytest.mark.asyncio
    async def test_a_channel_that_raises_is_not_swallowed(self) -> None:
        """⚠️ **An unconfigured channel and a broken one are different failures.**

        ⛔ **The first is a composition error; the second is an outage** — and 📁
        [§10](../../../../CLAUDE.md) forbids hiding either: *"a service running
        on it is indistinguishable from one that works."*
        """
        registry = NotificationChannelRegistry()
        registry.register(FailingChannel(Channel.IN_APP))
        notify = Notify(channels=registry, clock=lambda: NOW, new_id=lambda: NOTIFICATION_ID)

        with pytest.raises(RuntimeError, match="did not answer"):
            await notify.notify(a_request())

    @pytest.mark.asyncio
    async def test_the_moment_and_the_identity_come_from_the_injected_sources(self) -> None:
        """📁 [§2](../../../../CLAUDE.md), *hidden inputs are architecture
        defects* — ⛔ **and the panel groups by day, so a wall-clock read here
        would make *which day* untestable.**"""
        registry = NotificationChannelRegistry()
        registry.register(RecordingChannel(Channel.IN_APP))
        notify = Notify(channels=registry, clock=lambda: NOW, new_id=lambda: NOTIFICATION_ID)

        delivered = await notify.notify(a_request())

        assert delivered.occurred_at == NOW
        assert delivered.id == NOTIFICATION_ID

    @pytest.mark.asyncio
    async def test_the_use_case_satisfies_the_published_trigger(self) -> None:
        """⚡ **Makes the conformance function's DELETION visible in a run** —
        ⛔ otherwise removing it silently removes the only place `Notifier` is
        resolved."""
        registry = NotificationChannelRegistry()
        registry.register(RecordingChannel(Channel.IN_APP))
        notify = Notify(channels=registry)
        assert _the_use_case_is_the_published_trigger(notify) is notify
        assert _the_recording_double_is_a_channel(RecordingChannel(Channel.IN_APP)) is not None


class TestARequestNamesItsChannels:
    def test_naming_no_channel_is_refused_rather_than_defaulted(self) -> None:
        """🔴 **A default of `{IN_APP}` would be the fallback the registry
        refuses, arriving as a convenience.**"""
        with pytest.raises(NotificationError, match="reaches nobody"):
            a_request(channels=frozenset())


class TestAnActorIsWhoOrWhatActed:
    """🔴 **[C-203](../../../../docs/LANE_COORDINATION.md) is why there is no
    person name here**, and these assert the shape that keeps it that way."""

    def test_a_person_actor_carries_an_identity(self) -> None:
        person = uuid4()
        actor = Actor(kind=ActorKind.PERSON, person_id=person)
        assert actor.person_id == person
        assert actor.agent_name is None

    def test_a_person_actor_without_an_identity_is_refused(self) -> None:
        with pytest.raises(NotificationError, match="no person was identified"):
            Actor(kind=ActorKind.PERSON)

    def test_a_person_actor_may_not_carry_an_agents_name(self) -> None:
        """⛔ **It would render a colleague's request under the intelligence
        hue** — the confusion that hue exists to prevent, inverted."""
        with pytest.raises(NotificationError, match="intelligence hue"):
            Actor(kind=ActorKind.PERSON, person_id=uuid4(), agent_name="Research")

    def test_an_agent_may_not_carry_a_persons_identity(self) -> None:
        with pytest.raises(NotificationError, match="under a colleague's avatar"):
            Actor(kind=ActorKind.AGENT, agent_name="Research", person_id=uuid4())

    def test_an_agent_with_no_name_is_refused(self) -> None:
        """⚠️ **Unlike a person, an agent's name is the platform's own to give**
        — so a blank is an omission rather than a question C-203 has not
        answered."""
        with pytest.raises(NotificationError, match="nothing named it"):
            Actor(kind=ActorKind.AGENT)

    def test_a_blank_agent_name_is_refused_as_well_as_a_missing_one(self) -> None:
        with pytest.raises(NotificationError, match="nothing named it"):
            Actor(kind=ActorKind.AGENT, agent_name="   ")

    def test_there_is_no_display_name_field_for_a_person(self) -> None:
        """🔴 **The ABSENCE is the assertion.**

        ⛔ **A `name` field would have answered C-203 by accident** — for
        Timeline, comments, audit history, AI attribution and mentions at the
        same time, in the module least entitled to decide it.
        """
        fields = set(Actor.__dataclass_fields__)
        assert fields == {"kind", "person_id", "agent_name"}


class TestANotificationSaysAllFourThings:
    """📁 **The Definition of Done**: *"can tell what acted, on which record, and
    what is expected of them."*"""

    def _notification(self, **overrides: object) -> Notification:
        values: dict[str, object] = {
            "id": NOTIFICATION_ID,
            "workspace_id": WORKSPACE,
            "recipient_id": RECIPIENT,
            "category": Category.NEEDS_YOU,
            "actor": AGENT,
            "subject": Subject(kind="opportunity", id=SUBJECT),
            "summary": "Signora finished researching this account.",
            "expectation": "Open the account to read what Signora found.",
            "occurred_at": NOW,
        }
        values.update(overrides)
        return Notification(**values)  # type: ignore[arg-type]

    def test_a_naive_moment_is_refused(self) -> None:
        """⚠️ **The panel groups by day**, so a naive timestamp is the one item
        that could land under the wrong one."""
        with pytest.raises(NotificationError, match="without a timezone"):
            self._notification(occurred_at=datetime(2026, 8, 16, 9, 30))  # noqa: DTZ001

    def test_an_empty_summary_is_refused(self) -> None:
        with pytest.raises(NotificationError, match="told them nothing"):
            self._notification(summary="   ")

    def test_an_empty_expectation_is_refused(self) -> None:
        """⛔ **A nudge that does not say what it wants.**"""
        with pytest.raises(NotificationError, match="does not say what it wants"):
            self._notification(expectation="")

    def test_a_subject_with_no_kind_is_refused(self) -> None:
        with pytest.raises(NotificationError, match="nothing can resolve"):
            self._notification(subject=Subject(kind=" ", id=SUBJECT))

    def test_it_names_exactly_one_recipient(self) -> None:
        """🔴 **Telling five people is five notifications** — 📁 492 §0's
        narrowing. ⛔ **A `recipient_ids` field would make read state a workspace
        fact, which is D-239's own exclusion.**"""
        fields = set(Notification.__dataclass_fields__)
        assert "recipient_id" in fields
        assert not {f for f in fields if f.endswith("_ids")}


class TestTheCategoriesAreTheTabsAndAllIsNotOne:
    def test_all_is_not_a_category(self) -> None:
        """⚡ **`All` is the ABSENCE of a filter.** ⛔ **A member by that name is
        one a producer could set** — and an item that was *All* but neither of
        the others would appear in one tab and vanish from both the rest."""
        assert {c.value for c in Category} == {"needs_you", "mention"}


class TestTheWireShapeIsTheOneTheCodeProduces:
    """🔴 **The round trip, not a fixture.**

    ⚠️ **A hand-written payload dict would pass every parse assertion here while
    `to_payload()` emitted something else** — 📁 exactly the defect
    `machine_credentials` found when `token_urlsafe` put a `_` in a token and
    every hand-written fixture still passed.
    """

    def _event(self, **overrides: object) -> NotificationRequested:
        values: dict[str, object] = {
            "event_id": uuid4(),
            "workspace_id": WORKSPACE,
            "occurred_at": NOW,
            "recipient_id": RECIPIENT,
            "category": Category.NEEDS_YOU,
            "actor": AGENT,
            "subject": Subject(kind="opportunity", id=SUBJECT),
            "summary": "Signora finished researching this account.",
            "expectation": "Open the account to read what Signora found.",
            "channels": frozenset({Channel.IN_APP}),
        }
        values.update(overrides)
        return NotificationRequested(**values)  # type: ignore[arg-type]

    def test_an_agent_request_survives_the_round_trip(self) -> None:
        event = self._event()
        rebuilt = request_from_payload(workspace_id=WORKSPACE, payload=event.to_payload())

        assert rebuilt.recipient_id == RECIPIENT
        assert rebuilt.category is Category.NEEDS_YOU
        assert rebuilt.actor == AGENT
        assert rebuilt.subject == Subject(kind="opportunity", id=SUBJECT)
        assert rebuilt.summary == event.summary
        assert rebuilt.expectation == event.expectation
        assert rebuilt.channels == frozenset({Channel.IN_APP})

    def test_a_person_request_survives_the_round_trip(self) -> None:
        """⚡ **The other actor shape**, because `actor_person_id` and
        `actor_agent_name` are the two nullable columns and exactly one is set —
        ⛔ **a round trip on one of them proves nothing about the other.**"""
        person = uuid4()
        event = self._event(
            actor=Actor(kind=ActorKind.PERSON, person_id=person), category=Category.MENTION
        )
        rebuilt = request_from_payload(workspace_id=WORKSPACE, payload=event.to_payload())

        assert rebuilt.actor.kind is ActorKind.PERSON
        assert rebuilt.actor.person_id == person
        assert rebuilt.actor.agent_name is None
        assert rebuilt.category is Category.MENTION

    def test_several_channels_survive_the_round_trip(self) -> None:
        event = self._event(channels=frozenset({Channel.IN_APP, Channel.EMAIL, Channel.SLACK}))
        rebuilt = request_from_payload(workspace_id=WORKSPACE, payload=event.to_payload())
        assert rebuilt.channels == frozenset({Channel.IN_APP, Channel.EMAIL, Channel.SLACK})

    def test_the_serialized_channels_are_ordered(self) -> None:
        """📁 [§2](../../../../CLAUDE.md), *hidden inputs are architecture
        defects* — ⛔ **a `frozenset` has no order, and an event whose bytes vary
        with the hash seed is not replayable.**"""
        channels = frozenset({Channel.SLACK, Channel.IN_APP, Channel.EMAIL})
        assert self._event(channels=channels).to_payload()["channels"] == "email,in_app,slack"

    def test_the_payload_does_not_carry_its_own_workspace(self) -> None:
        """🔴 **The tenant comes from the ENVELOPE.** ⛔ **A payload that could
        name its own workspace is a cross-tenant write one typo away.**"""
        assert "workspace_id" not in self._event().to_payload()

    def test_the_payload_carries_no_subject_title(self) -> None:
        """⚡ **Identity only** — a cached account name would render one that
        changed last week."""
        payload = self._event().to_payload()
        assert payload["subject_id"] == str(SUBJECT)
        assert not {k for k in payload if k.endswith("_title") or k.endswith("_name")} - {
            "actor_agent_name"
        }

    def test_the_event_type_constant_matches_what_an_instance_publishes(self) -> None:
        """⚠️ **`ai_research_engine` found this exactly this way**: with
        `slots=True`, `Event.event_type` reads the slot descriptor rather than
        the default, so **a subscription registered from the class points at a
        repr nothing publishes.**"""
        assert self._event().event_type == NOTIFICATION_REQUESTED

    def test_a_payload_naming_no_channel_is_refused_at_the_boundary(self) -> None:
        """⛔ **A malformed event fails where it arrives**, rather than
        persisting a row no surface can render."""
        payload = dict(self._event().to_payload())
        payload["channels"] = ""
        with pytest.raises(NotificationError, match="reaches nobody"):
            request_from_payload(workspace_id=WORKSPACE, payload=payload)
