"""Base for SQLAlchemy repositories.

Deliberately thin. A generic CRUD base class parameterised over model and
entity types is a well-known trap: it either leaks ORM concepts into the
domain or forces every repository into a shape that fits none of them well.
What is genuinely shared is narrower than that — session ownership and
transaction discipline — so that is all this provides.

Mapping between ORM models and domain entities stays explicit in each
concrete repository, where it is readable.
"""

from sqlalchemy.ext.asyncio import AsyncSession


class SqlAlchemyRepository:
    """Holds the request-scoped session and standardises flush semantics.

    **A repository never commits.** The transaction is owned by whoever
    opened the session — the API dependency chain or an ARQ job handler — so
    that a single business operation spanning several repositories, plus its
    outbox writes, commits atomically. A repository that commits on its own
    silently breaks that guarantee and the transactional outbox with it
    (06-events.md).
    """

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def _add(self, model: object) -> None:
        """Stage a new row and flush it.

        Flushing (not committing) makes the row visible to later statements
        in the same transaction — a foreign-key check, or a uniqueness
        violation surfacing here rather than at commit time, where it would
        be far harder to attribute to a specific operation.
        """
        self._session.add(model)
        await self._session.flush()
