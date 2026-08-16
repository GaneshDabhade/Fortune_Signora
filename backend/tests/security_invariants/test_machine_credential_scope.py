"""**A key's scope can only subtract from what Casbin granted.**

📁 **[TASK-1413](../../../docs/BACKLOG.md)'s own Security Invariant**: *"a key's
scope is enforced by the same enforcer as a human's, never by a parallel
check."*

## 🔴 Why this file enumerates rather than samples

⛔ **A sampled version of this test passes on the day somebody adds a
`Resource` member and leaves it unguarded.** ⚡ **So every test below walks the
FULL cross product of `Resource × Action`** — **the invariant grows with the
product rather than with this file.**

⚠️ **That is the property QE said it would check**, and it is the difference
between an invariant and an example.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from itertools import product
from uuid import uuid4

import pytest

from modules.machine_credentials.domain.api_key import (
    ApiKey,
    IssuedSecret,
    KeyScope,
    KeyState,
    MalformedTokenError,
    ScopeExceedsGrantError,
    issue,
    matches,
    split_token,
)
from signora_platform.authorization.enforcer import Action, Resource

NOW = datetime(2026, 8, 16, 12, 0, tzinfo=UTC)

#: ⚡ **Every pair the product can express**, read from the enums rather than
#: listed — so a new `Resource` enters these tests the moment it is registered.
EVERY_PAIR = frozenset(product(Resource, Action))


def a_key(
    scope: KeyScope, *, creator: frozenset[tuple[Resource, Action]] | None = None
) -> tuple[ApiKey, IssuedSecret]:
    return issue(
        key_id=uuid4(),
        workspace_id=uuid4(),
        owner_user_id=uuid4(),
        label="CI pipeline",
        scope=scope,
        creator_allows=EVERY_PAIR if creator is None else creator,
        now=NOW,
    )


class TestTheScopeCanOnlySubtract:
    """🔴 **The invariant, over the whole product.**"""

    def test_a_key_never_permits_what_the_enforcer_denied(self) -> None:
        """⛔ **The one that matters.** ⚡ **Over every pair, with the widest
        possible scope**: if Casbin says no, the answer is no.

        **This is what makes the scope a filter rather than a second
        enforcer** — and it holds for a key scoped to *everything*, which is
        the case a narrower key could never expose.
        """
        key, _ = a_key(KeyScope(EVERY_PAIR))

        for resource, action in EVERY_PAIR:
            assert (
                key.scope.narrow(granted=False, resource=resource, action=action) is False
            ), f"a scope widened a denial for {resource}:{action}"

    def test_a_key_permits_only_the_intersection(self) -> None:
        """✅ **Where Casbin says yes, the scope decides — and only downwards.**"""
        held = (Resource.ACCOUNT, Action.READ)
        key, _ = a_key(KeyScope.of(held))

        for resource, action in EVERY_PAIR:
            allowed = key.scope.narrow(granted=True, resource=resource, action=action)
            assert allowed is ((resource, action) == held), f"{resource}:{action}"

    def test_the_scope_cannot_be_asked_without_the_enforcers_answer(self) -> None:
        """🔴 **The invariant as a property of the TYPE, not of the callers.**

        ⛔ **`narrow` takes `granted` as a keyword-only argument with no
        default**, so there is no way to ask a scope what it permits. ⚡ **A
        public method that answered alone would be a second enforcer**, and
        this asserts that none exists.
        """
        scope = KeyScope.of((Resource.ACCOUNT, Action.READ))

        public = {name for name in dir(scope) if not name.startswith("_")}
        assert public == {"pairs", "of", "narrow", "within"}, (
            "a new public method on KeyScope may be a parallel authorization "
            "check — every one must take the enforcer's answer as an input"
        )

        with pytest.raises(TypeError):
            scope.narrow(resource=Resource.ACCOUNT, action=Action.READ)  # type: ignore[call-arg]


class TestIssuanceRefusesAScopeWiderThanItsIssuer:
    def test_a_scope_wider_than_the_creators_is_refused_at_issuance(self) -> None:
        """🔴 **Refused, never silently narrowed.**

        📁 **A key that quietly does less than asked fails on the one call the
        customer built it for**, and it fails in their system rather than ours.
        """
        creator_may = frozenset({(Resource.ACCOUNT, Action.READ)})

        with pytest.raises(ScopeExceedsGrantError):
            a_key(
                KeyScope.of((Resource.ACCOUNT, Action.READ), (Resource.MEMBER, Action.REMOVE)),
                creator=creator_may,
            )

    def test_a_narrower_scope_is_the_point_and_is_allowed(self) -> None:
        creator_may = frozenset(
            {(Resource.ACCOUNT, Action.READ), (Resource.MEMBER, Action.REMOVE)}
        )
        key, _ = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)), creator=creator_may)
        assert key.scope.pairs == {(Resource.ACCOUNT, Action.READ)}

    def test_an_empty_scope_is_refused(self) -> None:
        """⛔ **A key that can do nothing is a support ticket, not a credential.**"""
        with pytest.raises(ScopeExceedsGrantError):
            a_key(KeyScope(frozenset()))

    @pytest.mark.parametrize(("resource", "action"), sorted(EVERY_PAIR))
    def test_every_single_pair_is_issuable_and_stays_that_pair(
        self, resource: Resource, action: Action
    ) -> None:
        """⚡ **Enumerated, so a new `Resource` is covered the day it lands.**"""
        key, _ = a_key(KeyScope.of((resource, action)))
        assert key.scope.narrow(granted=True, resource=resource, action=action) is True


class TestTheSecretExistsOnce:
    def test_the_record_cannot_carry_the_secret(self) -> None:
        """🔴 **Unrepresentable rather than discouraged** — 📁 [§2](../../../CLAUDE.md).

        ⛔ **There is no field of the plaintext's type on the record**, so a
        repository has nowhere to persist it even if somebody added a column.
        """
        key, secret = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)))

        assert isinstance(secret, IssuedSecret)
        assert not any(isinstance(getattr(key, f), IssuedSecret) for f in ApiKey.__slots__)
        assert secret.token not in repr(key)
        assert key.digest != secret.token

    def test_the_secret_does_not_survive_being_printed(self) -> None:
        """⚡ **The accidental path, which is the common one.**

        ⛔ **A credential reaches a log through an f-string far more often than
        through a deliberate write.**
        """
        _, secret = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)))

        assert secret.token not in f"{secret}"
        assert secret.token not in repr(secret)
        assert secret.token not in str([secret])

    def test_two_keys_never_share_a_secret_or_a_public_id(self) -> None:
        scope = KeyScope.of((Resource.ACCOUNT, Action.READ))
        first_key, first = a_key(scope)
        second_key, second = a_key(scope)

        assert first.token != second.token
        assert first_key.public_id != second_key.public_id
        assert first_key.digest != second_key.digest


class TestVerification:
    def test_the_issued_token_verifies_against_its_own_record(self) -> None:
        key, secret = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)))
        public_id, plaintext = split_token(secret.token)

        assert public_id == key.public_id
        assert matches(key, plaintext) is True

    def test_a_secret_from_another_key_does_not_verify(self) -> None:
        scope = KeyScope.of((Resource.ACCOUNT, Action.READ))
        key, _ = a_key(scope)
        _, other = a_key(scope)

        assert matches(key, split_token(other.token)[1]) is False

    @pytest.mark.parametrize(
        "candidate",
        [
            "",
            "sig",
            "sig_only",
            "sig__missing_public",
            "sig_public_",
            "wrong_public_secret",
            # ⚠️ **NOT `sig_public_secret_extra`** — that IS well formed now:
            # the secret is the remainder and may contain `_`. ⛔ **Asserting it
            # was malformed would have pinned the bug this file just found.**
            "_public_secret",
            "SIG_public_secret",
        ],
    )
    def test_a_malformed_token_is_refused_rather_than_parsed(self, candidate: str) -> None:
        """⛔ **Raises rather than returning `None`.**

        ⚡ **A `None` would be checked at some call sites and not others**, and
        the one that forgot would compare a digest against an empty string.
        """
        with pytest.raises(MalformedTokenError):
            split_token(candidate)


class TestTheLifecycle:
    def test_an_active_key_is_usable(self) -> None:
        key, _ = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)))
        assert key.is_usable(now=NOW) is True

    def test_a_revoked_key_is_not(self) -> None:
        key, _ = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)))
        assert key.revoked(now=NOW).is_usable(now=NOW) is False

    def test_revoking_twice_keeps_the_first_time(self) -> None:
        """⚡ **A double click is not an error, and the audit needs the first.**"""
        key, _ = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)))
        once = key.revoked(now=NOW)
        twice = once.revoked(now=NOW + timedelta(hours=1))

        assert twice.revoked_at == NOW
        assert twice is once

    def test_a_superseded_key_still_works_because_that_is_the_overlap(self) -> None:
        """🔴 **The half a rotation is FOR.**

        ⛔ **A rotation that ended the old key immediately is a rotation nobody
        can perform without downtime** — 📁 the design says *"rotation with an
        overlap window."*
        """
        key, _ = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)))
        old = key.superseded()

        assert old.state is KeyState.SUPERSEDED
        assert old.is_usable(now=NOW) is True

    def test_a_superseded_key_can_still_be_revoked_and_then_is_not_usable(self) -> None:
        key, _ = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)))
        assert key.superseded().revoked(now=NOW).is_usable(now=NOW) is False

    def test_supersede_does_not_reopen_a_revoked_key(self) -> None:
        key, _ = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)))
        assert key.revoked(now=NOW).superseded().state is KeyState.REVOKED

    def test_expiry_is_a_predicate_over_time_rather_than_a_state(self) -> None:
        """⛔ **No stored `EXPIRED`** — 📁 [§2](../../../CLAUDE.md).

        ⚡ **A stored one needs a job to write it, and between the deadline and
        that job the row says a dead key is live.**
        """
        deadline = NOW + timedelta(days=30)
        key, _ = issue(
            key_id=uuid4(),
            workspace_id=uuid4(),
            owner_user_id=uuid4(),
            label="expires",
            scope=KeyScope.of((Resource.ACCOUNT, Action.READ)),
            creator_allows=EVERY_PAIR,
            now=NOW,
            expires_at=deadline,
        )

        assert key.is_usable(now=deadline - timedelta(seconds=1)) is True
        assert key.is_usable(now=deadline) is False
        assert key.state is KeyState.ACTIVE, "expiry must not rewrite the stored state"

    def test_no_deadline_is_different_from_not_yet_expired(self) -> None:
        key, _ = a_key(KeyScope.of((Resource.ACCOUNT, Action.READ)))
        assert key.expires_at is None
        assert key.is_usable(now=NOW + timedelta(days=3650)) is True
