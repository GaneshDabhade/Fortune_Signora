"""**A credential value cannot reach a log sink.** [ADR-0412](../../../docs/architecture/adr/0412-environment-and-secret-safe-logging.md).

The ADR asks for this suite by name, and says why: *"a rule verified by review
is a rule that lapses on the day nobody reviews."* 📁 [§11](../../../CLAUDE.md)
makes a Security Invariant a statement of an architectural guarantee rather
than of feature behaviour — **this one states that no configured secret this
platform holds can be emitted, in any sink, at any level.**

### ⚠️ Why the URI case is the one that mattered

**Every credential this platform actually holds is a URI.** `SIGNORA_DATABASE_URL`,
`SIGNORA_REDIS_URL` and the object-store URL are the secrets most likely to
reach a log — and until [B-267](../../../docs/BUGS.md) **none of them was
caught**: the field is named `url`, so key-based redaction misses it, and the
value is neither a JWT nor a bearer token.

🔴 **Measured, not foreseen.** A single `logger.info` naming a Postgres URL
emitted the password verbatim, through the JSON formatter, with redaction
enabled.

### ⛔ And a format choice was silently a security choice

`configure_logging(json_output=False)` installed a bare `logging.Formatter`, so
**the only sink that redacted anything was the JSON one.** A developer who
turned on readable logs turned off redaction, without asking to and without
being told — against the ruling's own words: ***"a developer must opt IN to
verbosity, never opt OUT of redaction."***
"""

from __future__ import annotations

import io
import logging

import pytest

from signora_platform.observability.logging import REDACTED, configure_logging, redact

#: **Real shapes, not invented ones.** Each is a form this repository's own
#: configuration actually takes — `.env.example`, the compose files and the
#: object-store settings between them produce all four.
CONNECTION_STRINGS: dict[str, str] = {
    "postgres": "postgres://signora_app:S3cr3tPassw0rd@db:5432/signora",
    # ⚠️ **No username, which is how Redis URLs are written** — and the first
    # version of the pattern required one, so this walked straight through it.
    "redis": "redis://:AnotherSecret@cache:6379/2",
    "amqp": "amqp://guest:guest@rabbit:5672/",
    "s3": "s3://AKIAIOSFODNN7:wJalrXUtnFEMI+K7MDENG@bucket/key",
}

SECRETS: tuple[str, ...] = (
    "S3cr3tPassw0rd",
    "AnotherSecret",
    "wJalrXUtnFEMI+K7MDENG",
)


def _emitted(*, json_output: bool, message: str = "connecting", **extra: object) -> str:
    """One log line, through the real handler this process installs."""
    buffer = io.StringIO()
    configure_logging(level="DEBUG", json_output=json_output)
    logging.getLogger().handlers[0].stream = buffer  # type: ignore[attr-defined]
    logging.getLogger("invariant").info(message, extra=extra)
    return buffer.getvalue()


@pytest.mark.parametrize("scheme", sorted(CONNECTION_STRINGS))
@pytest.mark.parametrize("json_output", [True, False])
def test_a_connection_string_password_never_reaches_a_sink(
    scheme: str, json_output: bool
) -> None:
    """🔴 **The invariant ADR-0412 §4 asks for, stated for both sinks.**

    ⛔ **Both formatters, deliberately.** The format a process happens to be
    configured with must not decide whether a credential is protected.
    """
    uri = CONNECTION_STRINGS[scheme]

    line = _emitted(json_output=json_output, message=f"connecting to {uri}")

    assert not any(secret in line for secret in SECRETS)
    assert REDACTED in line


def test_a_credential_in_a_structured_field_never_reaches_a_sink() -> None:
    """A URI arriving as a *field* rather than inside the message — the shape
    a `Settings` object produces when something logs its own configuration.

    ⚠️ **JSON only, and the omission is deliberate.** The plain sink's format
    is `levelname name message` and **renders no `extra` at all**, so the same
    assertion there passes whether redaction runs or not — 📁 [§2](../../../CLAUDE.md)'s
    *guard that cannot fail*. **Found by fire-testing this file**, where the
    parametrized `False` case stayed green with redaction disabled. The plain
    sink's real property is asserted below instead.
    """
    line = _emitted(json_output=True, url=CONNECTION_STRINGS["redis"])

    assert "AnotherSecret" not in line


def test_the_plain_sink_renders_no_structured_field_to_leak() -> None:
    """⚡ **The plain sink's actual guarantee**, asserted rather than assumed.

    It is why the test above is JSON-only: a field cannot leak through a
    formatter that never emits one. **Stated as a property so that a future
    change adding `%(url)s` to the plain format breaks here** rather than
    quietly reopening the gap the test above stopped covering.
    """
    line = _emitted(json_output=False, url=CONNECTION_STRINGS["redis"], password="hunter2")

    assert "cache:6379" not in line
    assert "hunter2" not in line


def test_the_host_and_database_survive_redaction() -> None:
    """⚠️ **The half that makes the guard usable rather than merely safe.**

    Redacting the whole URI would remove the diagnostic value the line exists
    for — *which host, which database* is the question the operator is asking —
    and **a guard that destroys the reason to log would be turned off.** The
    username is not the secret either.
    """
    redacted = redact(CONNECTION_STRINGS["postgres"])

    assert redacted == f"postgres://signora_app:{REDACTED}@db:5432/signora"


def test_a_url_carrying_no_credential_is_left_alone() -> None:
    """A vendor endpoint is not a secret, and a redactor that mangled every
    URL would be one nobody could read past."""
    assert redact("https://api.anthropic.com/v1/messages") == (
        "https://api.anthropic.com/v1/messages"
    )


def test_a_named_secret_field_never_reaches_a_sink() -> None:
    """The key-based case that already held, pinned.

    ⚠️ **JSON only, for the same reason as above** — a named field is still a
    field, and the plain sink emits none. **Parametrizing this over both sinks
    is what fire-testing caught**: the `False` case survived an unredacting
    formatter, so it was asserting nothing.
    """
    line = _emitted(json_output=True, password="hunter2", api_key="sk-live-42")

    assert "hunter2" not in line
    assert "sk-live-42" not in line


@pytest.mark.parametrize("json_output", [True, False])
def test_a_bearer_token_never_reaches_a_sink(json_output: bool) -> None:
    token = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.c2ln"

    line = _emitted(json_output=json_output, message=f"Authorization: Bearer {token}")

    assert token not in line
