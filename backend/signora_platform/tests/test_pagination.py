"""Unit tests for cursor pagination primitives."""

from datetime import UTC, datetime
from uuid import uuid4

import pytest

from signora_platform.pagination import (
    CursorPosition,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
    split_overfetched,
)


class TestCursorRoundTrip:
    def test_encodes_and_decodes_a_position(self) -> None:
        position = CursorPosition(created_at=datetime.now(UTC), id=uuid4())

        assert decode_cursor(encode_cursor(position)) == position

    def test_cursor_is_url_safe(self) -> None:
        """Cursors travel in query strings, so they must survive without
        percent-encoding."""
        cursor = encode_cursor(CursorPosition(created_at=datetime.now(UTC), id=uuid4()))

        assert "+" not in cursor
        assert "/" not in cursor
        assert "=" not in cursor

    def test_preserves_microsecond_precision(self) -> None:
        """Timestamps truncated to the second would make the keyset boundary
        ambiguous for rows written in the same second."""
        position = CursorPosition(
            created_at=datetime(2026, 7, 28, 12, 30, 45, 123456, tzinfo=UTC), id=uuid4()
        )

        assert decode_cursor(encode_cursor(position)).created_at == position.created_at

    def test_preserves_timezone(self) -> None:
        position = CursorPosition(created_at=datetime.now(UTC), id=uuid4())

        assert decode_cursor(encode_cursor(position)).created_at.tzinfo is not None


class TestInvalidCursors:
    @pytest.mark.parametrize("cursor", ["not-base64!!", "", "eyJmb28iOiJiYXIifQ", "MTIz"])
    def test_rejects_malformed_cursors(self, cursor: str) -> None:
        """A bad cursor is client error (400), not a server fault — it must
        never surface as an unhandled decoding exception."""
        with pytest.raises(InvalidCursorError):
            decode_cursor(cursor)


class TestSplitOverfetched:
    def test_reports_more_when_extra_row_present(self) -> None:
        page, has_more = split_overfetched([1, 2, 3, 4], limit=3)

        assert page == [1, 2, 3]
        assert has_more is True

    def test_reports_no_more_when_exactly_full(self) -> None:
        page, has_more = split_overfetched([1, 2, 3], limit=3)

        assert page == [1, 2, 3]
        assert has_more is False

    def test_handles_partial_page(self) -> None:
        page, has_more = split_overfetched([1], limit=3)

        assert page == [1]
        assert has_more is False

    def test_handles_empty_result(self) -> None:
        empty: list[int] = []
        page, has_more = split_overfetched(empty, limit=3)

        assert page == []
        assert has_more is False
