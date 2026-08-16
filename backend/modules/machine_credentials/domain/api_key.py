"""An inbound machine credential — issued once, shown once, and never a grant.

**[TASK-1413](../../../../docs/BACKLOG.md) slice ⓐ**, on
[ADR-0414](../../../../docs/architecture/adr/0414-machine-credentials-bounded-context.md),
which ratified the bounded context and left this file everything it withheld:

> 📁 ***"The module's name · its table names · its API shape · the key format
> and hashing scheme · the per-call audit record's fields · the retention of
> that audit. All Lane A's, and settled in the implementation task rather than
> here."***

## 🔴 The secret exists in exactly one moment, and the type says so

📁 **The design: *"A key is shown once at creation and never again."*** ⛔ **A
rule stated in prose is a rule somebody will break by writing a helpful
`get_key()`.**

⚡ **So the plaintext is {@link IssuedSecret}, it is returned by
{@link issue} and by nothing else, and no field on {@link ApiKey} can hold
it.** ✅ **A repository cannot persist what the record cannot carry** — the
§2 shape, *a violation that is unrepresentable over one that is merely
discouraged*.

## ⛔ The scope can only SUBTRACT, and that is a type rather than a promise

📁 **[TASK-1413](../../../../docs/BACKLOG.md)'s Security Invariant: *"a key's
scope is enforced by the same enforcer as a human's, never by a parallel
check."***

🔴 **It is not directly expressible, and finding that out is what shaped this
file.** 📁 **`Authorizer.is_allowed(role, workspace_id, resource, action)` —
**the subject term is a ROLE STRING**, and a key has a scope rather than a
role. ⛔ **A per-key policy row cannot be written**: 📁
[ADR-0010](../../../../docs/architecture/adr/0010-identity-and-access.md) makes
`policy.csv` read-only at runtime — *"policy changes ship as code review"*.

✅ **So the model is:**

> ## **The GRANT is Casbin's alone. A scope can only take away.**

⚡ **{@link KeyScope.narrow} REQUIRES the enforcer's answer as an argument, and
there is no public method that answers without one.** ⛔ **A caller physically
cannot ask a scope whether something is permitted** — it can only hand over
what Casbin already decided and receive something equal or smaller. **That is
the difference between a filter and a second enforcer, expressed where it
cannot be forgotten.**

## ⚠️ Why SHA-256 and not a password hash, stated because it looks wrong

⛔ **bcrypt and argon2 exist to make GUESSING expensive**, and they buy that by
being slow. ⚡ **A secret here is {@link SECRET_BYTES} bytes from
`secrets.token_urlsafe` — there is nothing to guess**, and a slow hash would
add its cost to *every API call* rather than to an attacker.

✅ **What matters instead is that the comparison is constant-time and the
lookup does not need the secret** — 📁 which is why the token carries a public
{@link ApiKey.public_id}: **the row is found by that, and only then is one
digest compared.** ⛔ **Without it, verifying a key would mean hashing the
candidate against every key in the workspace**, which is both slow and a
timing oracle for how many keys exist.
"""

from __future__ import annotations

import hmac
import secrets
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import StrEnum
from hashlib import sha256
from typing import Final
from uuid import UUID

from signora_platform.authorization.enforcer import Action, Resource

#: ⚡ **Every token starts with this.** 📁 Not decoration — a leaked credential
#: is found by scanning for a known prefix, and a token nobody can recognise is
#: a token nobody can revoke. ⛔ Deliberately not the brand name: `signora_` in
#: a customer's log is the product; `sig_` is a credential.
TOKEN_PREFIX: Final = "sig"

#: ⛔ **The public half, and it is NOT a secret.** ⚡ Long enough that two keys
#: in one workspace never collide, short enough to read aloud in support.
#:
#: 🔴 **Hex, not `token_urlsafe` — and the tests are why.** ⚠️ **`token_urlsafe`
#: emits `-` and `_`**, so a public id could contain the separator and
#: {@link split_token} would cut the token in the wrong place. ⛔ **It failed on
#: a REAL issued token while every hand-written fixture passed**, which is the
#: shape a fixture-only suite never finds.
PUBLIC_ID_BYTES: Final = 6

#: ⚡ **~256 bits.** 📁 See the note above on why the hash is fast and this is
#: long: **the entropy is the defence, and it is here rather than in the KDF.**
#:
#: ⚠️ **This one MAY contain `_`, and that is fine**: it is the last field, so
#: {@link split_token} splits at most twice and the remainder is the secret
#: whatever it contains.
SECRET_BYTES: Final = 32


class CredentialError(Exception):
    """Every failure this module raises, so a caller catches one thing."""


class MalformedTokenError(CredentialError):
    """The presented string is not a Signora token at all.

    ⚠️ **Distinct from *the secret is wrong*, and the distinction never reaches
    a caller** — 📁 [§7](../../../../CLAUDE.md): the endpoint answers both the
    same way. ✅ **It exists so the LOG can tell a misconfigured client from an
    attack**, which are different operational problems.
    """


class ScopeExceedsGrantError(CredentialError):
    """A scope was asked for that its creator does not itself hold.

    🔴 **Raised at ISSUANCE, not at use.** ⚡ **A key that silently narrows to
    what its creator could grant would look like it worked and then fail on the
    one call the customer built it for.**
    """


@dataclass(frozen=True, slots=True)
class IssuedSecret:
    """The plaintext token, in the one moment it exists.

    ⛔ **Returned by {@link issue} and stored by nothing.** 📁 There is no
    field of this type on {@link ApiKey}, so a repository has nowhere to put
    it even if somebody tried.
    """

    token: str

    def __str__(self) -> str:
        """⛔ **Never the token.**

        ⚡ **A credential reaches a log through `f"{secret}"` far more often
        than through a deliberate write**, and `workspace_tenancy`'s
        `SecurityEvent` contract already refuses a `detail` key that carries
        one. **This closes the accidental path as well as the deliberate one.**
        """
        return "<IssuedSecret redacted>"

    __repr__ = __str__


@dataclass(frozen=True, slots=True)
class KeyScope:
    """What a key may do — **as a narrowing, never as a grant.**

    See the header. ⛔ **There is no public `permits(resource, action)`**, and
    its absence is the invariant.
    """

    pairs: frozenset[tuple[Resource, Action]]

    @staticmethod
    def of(*pairs: tuple[Resource, Action]) -> KeyScope:
        return KeyScope(frozenset(pairs))

    def narrow(self, *, granted: bool, resource: Resource, action: Action) -> bool:
        """**Take the enforcer's answer and return the same or less.**

        🔴 **`granted` is required and comes from
        {@link signora_platform.authorization.enforcer.Authorizer}.** ⛔ **This
        method can only ever return `False` where the enforcer said `False`** —
        which is the Security Invariant, written as the only shape the code
        offers.
        """
        return granted and (resource, action) in self.pairs

    def within(self, allowed: frozenset[tuple[Resource, Action]]) -> bool:
        """⚡ **Is this scope a subset of what its creator holds?**

        📁 The design: *"a scope narrower than its creator's."* ⛔ **Subset,
        not equality** — a key narrower than its owner is the point; a key
        wider is {@link ScopeExceedsGrantError}.
        """
        return self.pairs <= allowed


class KeyState(StrEnum):
    """⛔ **Three states and no `EXPIRED`.**

    ⚠️ **Expiry is a PREDICATE over `expires_at`, never a stored state** — 📁
    [§2](../../../../CLAUDE.md), *truth has exactly one authoritative
    representation*. **A stored `EXPIRED` would need a job to write it, and
    between the deadline and that job the row would say the key is live.**
    """

    ACTIVE = "active"
    #: 📁 *"Rotation with an overlap window."* ⚡ **The old key still works and
    #: is visibly on its way out**, which is what makes rotation something a
    #: customer can do without an outage.
    SUPERSEDED = "superseded"
    REVOKED = "revoked"


@dataclass(frozen=True, slots=True)
class ApiKey:
    """One issued credential. **Never carries its secret.**

    ⚡ **`workspace_id` and `owner_user_id` are both required and neither has a
    default** — 📁 [495](../../../../docs/architecture/495-principal-and-identity-boundary.md):
    *"a machine identity that is not workspace-scoped is a cross-tenant
    credential"* and *"every machine principal is owned by a human… what makes
    revocation on offboarding tractable and audit attributable."*
    """

    id: UUID
    workspace_id: UUID
    owner_user_id: UUID
    #: The token's public half — how a presented key finds its row.
    public_id: str
    #: ⛔ **The digest, never the secret.**
    digest: str
    #: What the customer called it. 📁 The design's list shows a name per row.
    label: str
    scope: KeyScope
    state: KeyState
    created_at: datetime
    #: `None` means *no deadline*, which is different from *not yet expired*.
    expires_at: datetime | None = None
    #: ⚡ Set when this key is superseded, so the overlap window is a fact
    #: about the row rather than a guess from timestamps.
    supersedes_id: UUID | None = None
    revoked_at: datetime | None = None
    #: ⚠️ Present so a support answer can be given without reading the audit
    #: stream. ⛔ Never used for authorization.
    last_used_at: datetime | None = field(default=None)

    def is_usable(self, *, now: datetime) -> bool:
        """⚡ **Whether this key may authenticate at `now`.**

        ⛔ **`now` is an argument, never a reading** — 📁
        [§2](../../../../CLAUDE.md): a clock read inside a domain method is a
        hidden input, and the same declared inputs would then produce different
        answers.

        ⚠️ **A `SUPERSEDED` key is still usable**, and that is the whole point
        of an overlap window. **It stops being usable when it is revoked or its
        deadline passes**, like any other.
        """
        if self.state is KeyState.REVOKED:
            return False
        return self.expires_at is None or now < self.expires_at

    def revoked(self, *, now: datetime) -> ApiKey:
        """⛔ **Terminal, and it does not ask whether the key was active.**

        ⚡ **Revoking an already-revoked key is not an error** — a customer who
        clicks twice, or a cascade that runs after a manual revocation, must
        not be told something went wrong. **The record keeps the FIRST
        revocation time**, because that is the fact an audit needs.
        """
        if self.state is KeyState.REVOKED:
            return self
        return replace(self, state=KeyState.REVOKED, revoked_at=now)

    def superseded(self) -> ApiKey:
        """⚠️ **Rotation marks the OLD key, and does not end it.**

        ⛔ **A rotation that revoked immediately would be a rotation nobody
        could perform without downtime**, which is why 📁 the design says
        *"rotation with an overlap window"* rather than *replace*.
        """
        if self.state is not KeyState.ACTIVE:
            return self
        return replace(self, state=KeyState.SUPERSEDED)


def _digest(secret: str) -> str:
    return sha256(secret.encode("utf-8")).hexdigest()


def issue(
    *,
    key_id: UUID,
    workspace_id: UUID,
    owner_user_id: UUID,
    label: str,
    scope: KeyScope,
    creator_allows: frozenset[tuple[Resource, Action]],
    now: datetime,
    expires_at: datetime | None = None,
) -> tuple[ApiKey, IssuedSecret]:
    """**Mint a key. The only place a secret ever exists.**

    🔴 **`creator_allows` is required and has no default.** ⚡ **It is what the
    ENFORCER says the issuing human may do**, and passing it in keeps this
    function pure while making *"narrower than its creator's"* impossible to
    skip — ⛔ **a default of *everything* would have made the check optional in
    practice while looking mandatory in the signature.**

    ⚠️ **Returns the record and the secret as a pair, deliberately.** **A
    function that returned only the record would need a second call to reveal
    the secret, and a second call is a second chance to store it.**
    """
    if not scope.pairs:
        raise ScopeExceedsGrantError("a key with an empty scope can do nothing; it is not a key")
    if not scope.within(creator_allows):
        raise ScopeExceedsGrantError(
            "the requested scope is wider than the issuer's own permissions — "
            "refused at issuance rather than silently narrowed, because a key that "
            "quietly does less than asked fails on the one call it was made for"
        )

    public_id = secrets.token_hex(PUBLIC_ID_BYTES)
    secret = secrets.token_urlsafe(SECRET_BYTES)
    token = f"{TOKEN_PREFIX}_{public_id}_{secret}"

    key = ApiKey(
        id=key_id,
        workspace_id=workspace_id,
        owner_user_id=owner_user_id,
        public_id=public_id,
        digest=_digest(secret),
        label=label,
        scope=scope,
        state=KeyState.ACTIVE,
        created_at=now,
        expires_at=expires_at,
    )
    return key, IssuedSecret(token)


def split_token(token: str) -> tuple[str, str]:
    """**`sig_<public>_<secret>` → `(public, secret)`.**

    ⛔ **Raises {@link MalformedTokenError} rather than returning `None`.** ⚡ **A
    `None` here would be checked at some call sites and not others**, and the
    one that forgot would compare a digest against an empty string.
    """
    # ⛔ **`maxsplit=2`, and it is not a micro-optimisation.** ⚡ **The secret
    # is `token_urlsafe`, which emits `_`** — an unbounded split would cut a
    # perfectly valid token into four parts and reject it. 🔴 **The public id is
    # hex precisely so the FIRST two boundaries are unambiguous.**
    parts = token.split("_", 2)
    if len(parts) != 3 or parts[0] != TOKEN_PREFIX or not parts[1] or not parts[2]:
        raise MalformedTokenError("not a Signora API token")
    return parts[1], parts[2]


def matches(key: ApiKey, secret: str) -> bool:
    """**Constant-time comparison of one candidate against one row.**

    ⛔ **`hmac.compare_digest`, never `==`.** ⚡ **A short-circuiting comparison
    leaks the length of the shared prefix through timing**, which turns a
    256-bit secret into a character-at-a-time search. ⚠️ **The digests are the
    same length here, so the leak would be small — and *small* is not a
    property worth defending when the correct call is the same length.**
    """
    return hmac.compare_digest(key.digest, _digest(secret))


__all__ = [
    "PUBLIC_ID_BYTES",
    "SECRET_BYTES",
    "TOKEN_PREFIX",
    "ApiKey",
    "CredentialError",
    "IssuedSecret",
    "KeyScope",
    "KeyState",
    "MalformedTokenError",
    "ScopeExceedsGrantError",
    "issue",
    "matches",
    "split_token",
]
