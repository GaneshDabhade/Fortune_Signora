"""Invariants: every tenant-owned table satisfies the Tenant Isolation Policy.

The behavioural isolation tests in ``test_authorization.py`` prove that
*today's* tables isolate correctly. These prove that tomorrow's do too — the
realistic regression is not that RLS stops working on ``membership``, but
that module fourteen adds a table and never gives it a policy.

The policy itself lives in ``tenancy_policy.py``, declared rather than
inferred; see that module for why.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from tests.security_invariants.tenancy_policy import (
    IMMUTABLE_TENANT_TABLES,
    PLATFORM_INFRASTRUCTURE_TABLES,
    REQUIRED_POLICY_COMMANDS,
    RUNTIME_ROLES,
    TENANCY_ROOT,
    TENANT_IDENTIFIER,
    TENANT_OWNED_TABLES,
)

pytestmark = pytest.mark.integration


async def _all_tables(factory: async_sessionmaker[AsyncSession]) -> set[str]:
    async with factory() as session, session.begin():
        rows = (
            await session.execute(
                text(
                    """
                    SELECT c.relname FROM pg_class c
                    JOIN pg_namespace n ON n.oid = c.relnamespace
                    WHERE n.nspname = 'public' AND c.relkind = 'r'
                    """
                )
            )
        ).scalars()
        return set(rows)


class TestClassification:
    async def test_every_table_is_classified(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A new table must be declared tenant-owned or platform
        infrastructure. Neither is a default.

        This is the check that makes the rest of the file complete. Without
        it, a table that forgot its ``workspace_id`` would simply not match
        any rule and pass by omission — which is precisely how tenancy gaps
        reach production.
        """
        declared = TENANT_OWNED_TABLES | PLATFORM_INFRASTRUCTURE_TABLES
        unclassified = await _all_tables(admin_session_factory) - declared

        assert unclassified == set(), (
            f"undeclared table(s): {sorted(unclassified)}. Add each to "
            "TENANT_OWNED_TABLES (and give it workspace_id + forced RLS + "
            "policies) or, if it is genuinely platform-owned and spans "
            "workspaces, to PLATFORM_INFRASTRUCTURE_TABLES with a stated "
            "reason. See docs/architecture/11-tenancy.md."
        )

    async def test_the_two_classifications_do_not_overlap(self) -> None:
        assert TENANT_OWNED_TABLES.isdisjoint(PLATFORM_INFRASTRUCTURE_TABLES)

    async def test_declared_tables_actually_exist(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Guards the opposite drift: a dropped table left in the policy
        would silently reduce what is checked while the file still looks
        thorough."""
        existing = await _all_tables(admin_session_factory)
        declared = TENANT_OWNED_TABLES | PLATFORM_INFRASTRUCTURE_TABLES

        assert declared - existing == set(), (
            f"policy names table(s) that no longer exist: {sorted(declared - existing)}"
        )


class TestTenantIdentifier:
    """Policy 1 — a tenant identifier exists and cannot be null."""

    async def test_every_tenant_owned_table_carries_a_non_null_tenant_identifier(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            rows = (
                await session.execute(
                    text(
                        """
                        SELECT table_name, is_nullable
                        FROM information_schema.columns
                        WHERE table_schema = 'public'
                          AND column_name = :identifier
                        """
                    ),
                    {"identifier": TENANT_IDENTIFIER},
                )
            ).all()
        columns: dict[str, str] = {name: nullable for name, nullable in rows}

        for table in sorted(TENANT_OWNED_TABLES - {TENANCY_ROOT}):
            assert table in columns, f"{table} has no {TENANT_IDENTIFIER} column"
            assert columns[table] == "NO", (
                f"{table}.{TENANT_IDENTIFIER} is nullable — a null tenant identifier "
                "is a row that belongs to no workspace and is matched by no policy"
            )

    async def test_the_tenancy_root_is_its_own_tenant_identifier(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """``workspace`` cannot carry a ``workspace_id`` pointing elsewhere —
        its own ``id`` is the identifier. Stated so the exemption above is
        deliberate rather than an oversight."""
        async with admin_session_factory() as session, session.begin():
            has_column = (
                await session.execute(
                    text(
                        """
                        SELECT count(*) FROM information_schema.columns
                        WHERE table_schema = 'public' AND table_name = :root
                          AND column_name = :identifier
                        """
                    ),
                    {"root": TENANCY_ROOT, "identifier": TENANT_IDENTIFIER},
                )
            ).scalar_one()

        assert has_column == 0


class TestForcedRowLevelSecurity:
    """Policy 2 — RLS enabled *and* forced."""

    async def test_every_tenant_owned_table_has_rls_enabled_and_forced(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            state = {
                name: (enabled, forced)
                for name, enabled, forced in (
                    await session.execute(
                        text(
                            """
                            SELECT c.relname, c.relrowsecurity, c.relforcerowsecurity
                            FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            WHERE n.nspname = 'public' AND c.relkind = 'r'
                            """
                        )
                    )
                ).all()
            }

        for table in sorted(TENANT_OWNED_TABLES):
            enabled, forced = state[table]
            assert enabled, f"{table} does not have Row-Level Security enabled"
            assert forced, (
                f"{table} has RLS enabled but not FORCED — the table owner is "
                "exempt from its own policies, so isolation depends on which "
                "role happens to connect"
            )


class TestRequiredPolicies:
    """Policy 3 — read and write are covered separately."""

    async def test_every_tenant_owned_table_has_the_required_policies(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """A table with RLS forced but no policy denies everything, which
        fails loudly. A table with only a ``SELECT`` policy is the dangerous
        shape: reads look correct while writes are silently impossible, or —
        with a permissive ``ALL`` — never considered at all.
        """
        async with admin_session_factory() as session, session.begin():
            rows = (
                await session.execute(
                    text("SELECT tablename, cmd FROM pg_policies WHERE schemaname = 'public'")
                )
            ).all()

        by_table: dict[str, set[str]] = {}
        for table, command in rows:
            by_table.setdefault(table, set()).add(command)

        for table in sorted(TENANT_OWNED_TABLES):
            commands = by_table.get(table, set())
            covered = commands | (
                {"SELECT", "INSERT", "UPDATE", "DELETE"} if "ALL" in commands else set()
            )
            # An immutable table has no update path by design. Demanding a
            # policy would mean weakening immutability to satisfy a test,
            # which is exactly backwards.
            required = REQUIRED_POLICY_COMMANDS - (
                {"UPDATE"} if table in IMMUTABLE_TENANT_TABLES else set()
            )
            missing = required - covered

            assert not missing, f"{table} has no policy for: {sorted(missing)}"

    async def test_platform_tables_have_no_policies(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """Their isolation is by grant, not by policy. A policy appearing on
        one would mean the classification is wrong — the table holds tenant
        data after all."""
        async with admin_session_factory() as session, session.begin():
            policied = set(
                (
                    await session.execute(
                        text("SELECT DISTINCT tablename FROM pg_policies WHERE schemaname='public'")
                    )
                ).scalars()
            )

        assert policied.isdisjoint(PLATFORM_INFRASTRUCTURE_TABLES)


class TestNoRuntimeRoleBypassesRls:
    """Policy 4 — the control that makes policies 1–3 mean anything."""

    async def test_no_runtime_role_is_superuser_or_holds_bypassrls(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            roles = (
                await session.execute(
                    text(
                        "SELECT rolname, rolsuper, rolbypassrls FROM pg_roles "
                        "WHERE rolname = ANY(:names) ORDER BY rolname"
                    ),
                    {"names": list(RUNTIME_ROLES)},
                )
            ).all()

        found = {name for name, _, _ in roles}
        assert found == set(RUNTIME_ROLES), f"missing runtime role(s): {set(RUNTIME_ROLES) - found}"

        for name, is_superuser, bypasses_rls in roles:
            assert not is_superuser, f"{name} is a superuser and ignores every policy above"
            assert not bypasses_rls, f"{name} holds BYPASSRLS and ignores every policy above"


class TestPlatformTablesAreUnreachableFromModules:
    """The Platform Infrastructure Policy: business modules never read
    infrastructure tables.

    These tables carry ``workspace_id`` but have no RLS, so a read by the
    application role would return every workspace's rows. Isolation here is
    the grant, and nothing else.
    """

    async def test_the_application_role_cannot_read_the_outbox(self, app_engine: object) -> None:
        from sqlalchemy.ext.asyncio import AsyncEngine

        assert isinstance(app_engine, AsyncEngine)
        async with app_engine.connect() as conn, conn.begin():
            with pytest.raises(Exception) as exc_info:
                await conn.execute(text("SELECT count(*) FROM outbox_event"))

        assert "permission denied" in str(exc_info.value).lower()

    async def test_the_application_role_cannot_read_dead_letters(self, app_engine: object) -> None:
        from sqlalchemy.ext.asyncio import AsyncEngine

        assert isinstance(app_engine, AsyncEngine)
        async with app_engine.connect() as conn, conn.begin():
            with pytest.raises(Exception) as exc_info:
                await conn.execute(text("SELECT count(*) FROM dead_letter_event"))

        assert "permission denied" in str(exc_info.value).lower()

    async def test_the_application_role_can_still_publish(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        """The positive control. A revoke that also broke publishing would
        satisfy both tests above while breaking the pipeline entirely."""
        async with admin_session_factory() as session, session.begin():
            privileges = set(
                (
                    await session.execute(
                        text(
                            """
                            SELECT privilege_type FROM information_schema.table_privileges
                            WHERE table_name = 'outbox_event' AND grantee = 'signora_app'
                            """
                        )
                    )
                ).scalars()
            )

        assert privileges == {"INSERT"}

    async def test_only_the_relay_identity_may_consume_the_outbox(
        self, admin_session_factory: async_sessionmaker[AsyncSession]
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            readers = set(
                (
                    await session.execute(
                        text(
                            """
                            SELECT grantee FROM information_schema.table_privileges
                            WHERE table_name = 'outbox_event' AND privilege_type = 'SELECT'
                            """
                        )
                    )
                ).scalars()
            )

        assert "signora_app" not in readers
        assert "signora_relay" in readers


class TestImmutableTablesAreImmutable:
    """Some tables hold history, and history is never edited.

    `claim` holds evidence; `resolution_decision` holds the reasoning that
    turned evidence into knowledge. New information is a **new row**, never
    an overwrite — Timeline, the Observation Engine, and AI Reasoning all
    depend on seeing what was believed *when*, and an invariant guarded only
    by convention lasts until the first inconvenient deadline.

    Enforced by the database: `signora_app` holds no `UPDATE` on any of
    them, so an attempted overwrite fails with a permission error rather
    than succeeding quietly.

    Driven by `IMMUTABLE_TENANT_TABLES` rather than naming tables inline, so
    that declaring a table immutable and *proving* it cannot drift apart.
    """

    @pytest.mark.parametrize("table", sorted(IMMUTABLE_TENANT_TABLES))
    async def test_the_application_role_cannot_update_it(
        self, admin_session_factory: async_sessionmaker[AsyncSession], table: str
    ) -> None:
        async with admin_session_factory() as session, session.begin():
            privileges = set(
                (
                    await session.execute(
                        text(
                            "SELECT privilege_type FROM information_schema.table_privileges "
                            "WHERE table_name = :table AND grantee = 'signora_app'"
                        ),
                        {"table": table},
                    )
                )
                .scalars()
                .all()
            )

        assert "UPDATE" not in privileges, (
            f"signora_app can UPDATE {table}, which is declared immutable. New information is a "
            "new row. An update grant makes the invariant a convention rather than a guarantee."
        )
        assert {"SELECT", "INSERT"} <= privileges

    @pytest.mark.parametrize("table", sorted(IMMUTABLE_TENANT_TABLES))
    async def test_it_remains_deletable_for_regeneration(
        self, admin_session_factory: async_sessionmaker[AsyncSession], table: str
    ) -> None:
        """Deliberately different from mutation. Both tables hold *derived*
        data: dropping and regenerating them is the rollback for a broken
        mapper or a bad resolution rule, and a regenerated row is a new row
        rather than an edited one."""
        async with admin_session_factory() as session, session.begin():
            can_delete = (
                await session.execute(
                    text("SELECT has_table_privilege('signora_app', :table, 'DELETE')"),
                    {"table": table},
                )
            ).scalar_one()

        assert can_delete is True

    @pytest.mark.parametrize("table", sorted(IMMUTABLE_TENANT_TABLES))
    async def test_no_update_policy_exists_on_it(
        self, admin_session_factory: async_sessionmaker[AsyncSession], table: str
    ) -> None:
        """Defence in depth: even were the grant restored by mistake, no
        RLS policy permits an update."""
        async with admin_session_factory() as session, session.begin():
            count = (
                await session.execute(
                    text(
                        "SELECT count(*) FROM pg_policies "
                        "WHERE tablename = :table AND cmd = 'UPDATE'"
                    ),
                    {"table": table},
                )
            ).scalar_one()

        assert count == 0
