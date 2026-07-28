-- LOCAL DEVELOPMENT ONLY.
--
-- Grants the authentication role a login credential so the frontend tier can
-- connect as `signora_auth` rather than as the database owner.
--
-- This matters more than it looks. Migration 0005 revokes `signora_app` from
-- the `auth` schema so the API tier cannot read authentication data. That
-- isolation is worthless if the frontend connects as the owner role, which
-- has full access to every application table and is not subject to
-- Row-Level Security. The two tiers must hold genuinely disjoint
-- credentials, or the boundary is a diagram rather than a permission.
--
-- Migration 0005 creates the role NOLOGIN; a password is deployment
-- configuration, not schema. In every deployed environment it is issued by
-- AWS Secrets Manager (ADR-0022) and this file is not used. The credential
-- here is intentionally trivial and must never be reused outside local
-- Docker.
--
-- Runs only on first initialisation of an empty data volume, before
-- migrations. The CREATE here and the one in migration 0005 are each
-- guarded, so either order works.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'signora_auth') THEN
    CREATE ROLE signora_auth LOGIN PASSWORD 'signora_auth_local_dev';
  ELSE
    ALTER ROLE signora_auth LOGIN PASSWORD 'signora_auth_local_dev';
  END IF;
END
$$;
