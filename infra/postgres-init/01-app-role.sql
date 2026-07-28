-- LOCAL DEVELOPMENT ONLY.
--
-- Grants the least-privilege application role a login credential so the
-- backend can connect as a non-superuser and therefore actually be subject
-- to Row-Level Security (see migration 0002 and
-- docs/architecture/11-tenancy.md).
--
-- In every deployed environment this password is issued by AWS Secrets
-- Manager (ADR-0022) and this file is not used. The credential here is
-- intentionally trivial and must never be reused outside local Docker.
--
-- Runs only on first initialisation of an empty data volume.

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'signora_app') THEN
    CREATE ROLE signora_app LOGIN PASSWORD 'signora_app_local_dev';
  ELSE
    ALTER ROLE signora_app LOGIN PASSWORD 'signora_app_local_dev';
  END IF;
END
$$;
