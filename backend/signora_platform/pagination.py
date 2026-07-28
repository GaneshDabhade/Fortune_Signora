"""Cursor pagination primitives (19-api-conventions.md).

Deliberately transport-neutral and framework-free: keyset positions and
cursor encoding are a *query* concern that application-layer use cases
express, not an HTTP concern. The HTTP response envelope built on top of
these lives in ``signora_platform.api.responses``, so the application layer
never has to depend on the API layer to describe a page of results.

Keyset pagination on ``(created_at, id)``. Offset pagination is deliberately
not offered: ``OFFSET`` degrades linearly as it grows because the database
must scan and discard skipped rows, and it is unstable under concurrent
writes — rows shift between pages, silently duplicating or skipping items.
Signora's pipeline writes continuously, so that is a routine failure mode
rather than a theoretical one.
"""

import base64
import binascii
import json
from dataclasses import dataclass
from datetime import datetime
from typing import Final
from uuid import UUID

DEFAULT_PAGE_LIMIT: Final[int] = 50
MAX_PAGE_LIMIT: Final[int] = 200


class InvalidCursorError(Exception):
    """The supplied cursor is not one this API issued. Maps to HTTP 400."""

    def __init__(self) -> None:
        super().__init__("The supplied pagination cursor is not valid.")


@dataclass(frozen=True)
class CursorPosition:
    """The keyset position a cursor encodes: the sort key of the last item
    on the previous page."""

    created_at: datetime
    id: UUID


def encode_cursor(position: CursorPosition) -> str:
    """Encode a keyset position as an opaque, URL-safe string.

    Opaque by contract: clients echo it back and never construct or parse
    one. That is what lets the underlying keyset change without breaking
    clients. Base64 is encoding, not encryption — it carries no secret, only
    a timestamp and an id the caller already received.
    """
    payload = json.dumps(
        {"created_at": position.created_at.isoformat(), "id": str(position.id)}
    ).encode()
    return base64.urlsafe_b64encode(payload).decode().rstrip("=")


def decode_cursor(cursor: str) -> CursorPosition:
    """Decode a cursor, raising ``InvalidCursorError`` on anything malformed.

    A bad cursor is client error, not server error: it is rejected as 400
    rather than allowed to raise a decoding exception deeper in the request.
    """
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = json.loads(base64.urlsafe_b64decode(padded))
        return CursorPosition(
            created_at=datetime.fromisoformat(raw["created_at"]), id=UUID(raw["id"])
        )
    except (binascii.Error, ValueError, KeyError, TypeError) as exc:
        raise InvalidCursorError() from exc


def split_overfetched[T](rows: list[T], *, limit: int) -> tuple[list[T], bool]:
    """Split an over-fetched result into a page and a ``has_more`` flag.

    Callers fetch ``limit + 1`` rows; the presence of that extra row is how
    ``has_more`` is determined without a second ``COUNT`` query.
    """
    has_more = len(rows) > limit
    return rows[:limit], has_more
