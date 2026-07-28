"""workspace_tenancy: make RLS membership checks self-sufficient

Revision ID: 0003
Revises: 0002
Create Date: 2026-07-28

Fixes two defects in the policies created by migration 0001.

**1. Membership subqueries were silently filtered to nothing.**

``workspace_select`` decided visibility with a subquery over ``membership``.
But ``membership`` carries its own RLS policy keyed on ``app.workspace_id``,
and that policy applies *inside* the subquery. In a user-scoped session —
one where a user is authenticated but has not selected a workspace, which is
exactly the state "list the workspaces I belong to" runs in — no workspace
id is set, so the subquery matched nothing and the user could see none of
their own workspaces.

**2. Membership visibility depended on application discipline, not RLS.**

``membership_isolation`` granted read access on the sole basis of
``workspace_id = app.workspace_id``. Nothing in the policy required the
caller to actually *be* a member of that workspace; the only thing stopping
a session from reading another tenant's membership list was that the
application verifies membership before setting the variable. That makes the
application, not the database, the real enforcement point — the opposite of
what docs/architecture/11-tenancy.md commits to.

Both are fixed by a ``SECURITY DEFINER`` helper that answers "is the current
user a member of this workspace?" while bypassing RLS on ``membership``
itself, which is the standard PostgreSQL escape from exactly this recursion.
The function is deliberately minimal: read-only, single-purpose, returning a
boolean, with a pinned ``search_path`` so it cannot be subverted by a
caller-controlled schema.
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None

APP_ROLE = "signora_app"


def upgrade() -> None:
    # --- SECURITY DEFINER membership predicates ---
    #
    # SET search_path is not optional here: without it, a caller able to
    # create objects in a schema earlier on the path could shadow
    # `membership` and change what the function returns.
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_current_user_id() RETURNS uuid
        LANGUAGE sql STABLE
        SET search_path = pg_catalog, public
        AS $$
          SELECT NULLIF(current_setting('app.user_id', true), '')::uuid
        $$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_is_workspace_member(target_workspace uuid)
        RETURNS boolean
        LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT EXISTS (
            SELECT 1 FROM membership
            WHERE workspace_id = target_workspace
              AND user_id = app_current_user_id()
          )
        $$
        """
    )
    op.execute(
        """
        CREATE OR REPLACE FUNCTION app_is_workspace_owner(target_workspace uuid)
        RETURNS boolean
        LANGUAGE sql STABLE SECURITY DEFINER
        SET search_path = pg_catalog, public
        AS $$
          SELECT EXISTS (
            SELECT 1 FROM membership
            WHERE workspace_id = target_workspace
              AND user_id = app_current_user_id()
              AND role = 'owner'
          )
        $$
        """
    )

    for function in (
        "app_current_user_id()",
        "app_is_workspace_member(uuid)",
        "app_is_workspace_owner(uuid)",
    ):
        op.execute(f"GRANT EXECUTE ON FUNCTION {function} TO {APP_ROLE}")

    # --- workspace policies ---
    op.execute("DROP POLICY IF EXISTS workspace_select ON workspace")
    op.execute("DROP POLICY IF EXISTS workspace_update ON workspace")
    op.execute(
        """
        CREATE POLICY workspace_select ON workspace
          FOR SELECT
          USING (app_is_workspace_member(id))
        """
    )
    op.execute(
        """
        CREATE POLICY workspace_update ON workspace
          FOR UPDATE
          USING (app_is_workspace_owner(id))
        """
    )

    # --- membership policies ---
    #
    # Split by operation, because read and write have genuinely different
    # requirements:
    #
    # SELECT is now membership-based rather than context-based, so it holds
    # regardless of whether app.workspace_id happens to be set. This is what
    # makes isolation self-sufficient — the database no longer trusts the
    # application to have scoped the session correctly.
    #
    # INSERT remains context-based. It has to: the founding membership of a
    # brand-new workspace is written by a user who is not yet a member, so a
    # membership-based check would make workspace creation impossible (the
    # bootstrap pattern in 11-tenancy.md).
    op.execute("DROP POLICY IF EXISTS membership_isolation ON membership")
    op.execute(
        """
        CREATE POLICY membership_select ON membership
          FOR SELECT
          USING (app_is_workspace_member(workspace_id))
        """
    )
    op.execute(
        """
        CREATE POLICY membership_insert ON membership
          FOR INSERT
          WITH CHECK (
            workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
          )
        """
    )
    op.execute(
        """
        CREATE POLICY membership_update ON membership
          FOR UPDATE
          USING (
            workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
            AND app_is_workspace_member(workspace_id)
          )
        """
    )
    op.execute(
        """
        CREATE POLICY membership_delete ON membership
          FOR DELETE
          USING (
            workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
            AND app_is_workspace_owner(workspace_id)
          )
        """
    )


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS membership_delete ON membership")
    op.execute("DROP POLICY IF EXISTS membership_update ON membership")
    op.execute("DROP POLICY IF EXISTS membership_insert ON membership")
    op.execute("DROP POLICY IF EXISTS membership_select ON membership")
    op.execute(
        """
        CREATE POLICY membership_isolation ON membership
          USING (
            workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
          )
          WITH CHECK (
            workspace_id = NULLIF(current_setting('app.workspace_id', true), '')::uuid
          )
        """
    )

    op.execute("DROP POLICY IF EXISTS workspace_update ON workspace")
    op.execute("DROP POLICY IF EXISTS workspace_select ON workspace")
    op.execute(
        """
        CREATE POLICY workspace_select ON workspace
          FOR SELECT
          USING (
            id IN (
              SELECT workspace_id FROM membership
              WHERE user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
            )
          )
        """
    )
    op.execute(
        """
        CREATE POLICY workspace_update ON workspace
          FOR UPDATE
          USING (
            id IN (
              SELECT workspace_id FROM membership
              WHERE user_id = NULLIF(current_setting('app.user_id', true), '')::uuid
                AND role = 'owner'
            )
          )
        """
    )

    op.execute("DROP FUNCTION IF EXISTS app_is_workspace_owner(uuid)")
    op.execute("DROP FUNCTION IF EXISTS app_is_workspace_member(uuid)")
    op.execute("DROP FUNCTION IF EXISTS app_current_user_id()")
