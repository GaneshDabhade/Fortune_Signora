"""Shared HTTP response envelopes (19-api-conventions.md).

Only collection responses are wrapped. Single resources are returned as the
resource object itself — an envelope there would add a level of nesting to
every client access path and buy nothing, since pagination (the usual
justification for wrapping) applies only to collections.
"""

from pydantic import BaseModel, ConfigDict, Field


class CursorPage[T](BaseModel):
    """The envelope every collection endpoint returns.

    Used even where a result set is currently small: retrofitting pagination
    onto an unpaginated endpoint is a breaking change, whereas starting
    paginated costs nothing.
    """

    model_config = ConfigDict(frozen=True)

    items: list[T]
    next_cursor: str | None = Field(
        default=None,
        description=("Opaque cursor for the next page. Echo it back unmodified; never parse it."),
    )
    has_more: bool = Field(
        description=(
            "Whether further pages exist. Explicit rather than inferred from "
            "next_cursor being non-null, so client code reads clearly."
        )
    )
