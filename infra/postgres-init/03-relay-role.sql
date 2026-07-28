-- LOCAL DEVELOPMENT ONLY.
--
-- Login credential for the outbox relay, the one runtime identity permitted
-- to READ platform infrastructure tables.
--
-- The application role may publish into the outbox but never read it back:
-- those tables span every workspace and deliberately carry no RLS, so the
-- grant is the only thing separating tenants there (migration 0006,
-- docs/architecture/11-tenancy.md).
--
-- Migration 0006 creates the role NOLOGIN; a password is deployment
-- configuration, not schema. In every deployed environment it is issued by
-- AWS Secrets Manager (ADR-0022) and this file is not used.
--
-- Runs only on first initialisation of an empty data volume.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'signora_relay') THEN
    CREATE ROLE signora_relay LOGIN PASSWORD 'signora_relay_local_dev';
  ELSE
    ALTER ROLE signora_relay LOGIN PASSWORD 'signora_relay_local_dev';
  END IF;
END
$$;
