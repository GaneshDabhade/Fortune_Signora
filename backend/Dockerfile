# Signora backend — API, workers, and the migration runner.
#
# One image, three entry points. They share every dependency and differ only
# in the command they run, so building three images would triple build time
# and registry cost to express a distinction the command already makes.
#
# Multi-stage: the builder holds uv and the toolchain needed to resolve and
# compile dependencies; the runtime holds the virtualenv and the source, and
# nothing else. A compiler in a production image is a tool an attacker
# inherits.

# ---------------------------------------------------------------- builder
FROM python:3.13-slim-bookworm AS builder

# Pinned by digest-bearing tag rather than `latest`: an unpinned installer
# makes the build unreproducible, and a build you cannot reproduce is one
# you cannot audit after an incident.
COPY --from=ghcr.io/astral-sh/uv:0.5.11 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never

WORKDIR /app

# Dependencies before source. Application code changes on nearly every
# build; the lockfile rarely does, so this layer stays cached and the
# expensive resolve is skipped.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project --no-dev

COPY signora_platform ./signora_platform
COPY modules ./modules
COPY apps ./apps
COPY migrations ./migrations
COPY alembic.ini ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# ---------------------------------------------------------------- runtime
FROM python:3.13-slim-bookworm AS runtime

# Non-root. A container process running as root that escapes its namespace
# is root on the host; one running as uid 1000 is not.
RUN groupadd --gid 1000 signora \
    && useradd --uid 1000 --gid signora --create-home --shell /usr/sbin/nologin signora

ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/app

WORKDIR /app

COPY --from=builder --chown=signora:signora /app/.venv ./.venv
COPY --from=builder --chown=signora:signora /app/signora_platform ./signora_platform
COPY --from=builder --chown=signora:signora /app/modules ./modules
COPY --from=builder --chown=signora:signora /app/apps ./apps
COPY --from=builder --chown=signora:signora /app/migrations ./migrations
COPY --from=builder --chown=signora:signora /app/alembic.ini ./

USER signora

# No secret is baked in, and none can be: every value the application reads
# arrives from the environment at start (docs/architecture/10-security.md).
# The image is identical across every environment — what differs is what is
# handed to it.

EXPOSE 8000

# Default to the API. Workers and the migration runner override this; see
# infra/docker-compose.prod.yml.
# `--factory` because the API is exposed as create_app(settings), not a
# module-level singleton — settings are injected at the composition root
# rather than read at import time.
CMD ["uvicorn", "apps.api.main:create_app", "--factory", "--host", "0.0.0.0", "--port", "8000"]
