# Signora frontend — Next.js 15, and the Authentication Authority.
#
# This tier holds the JWT *private* key and Better Auth's credentials, which
# makes it the most security-sensitive image in the stack: a build that
# leaks a layer here leaks the ability to mint tokens the API will accept
# (ADR-0026). Nothing secret is copied in — every value arrives from the
# environment at start.

# ------------------------------------------------------------ dependencies
FROM node:22-bookworm-slim AS deps

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

# ----------------------------------------------------------------- builder
FROM node:22-bookworm-slim AS builder

WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Next collects a build-time telemetry payload by default. Disabled: a build
# should make no network call we did not ask for.
ENV NEXT_TELEMETRY_DISABLED=1

# The build type-checks and lints (next.config.ts sets ignoreBuildErrors and
# ignoreDuringBuilds to false), so a type error fails the image rather than
# shipping inside it.
RUN npm run build

# ----------------------------------------------------------------- runtime
FROM node:22-bookworm-slim AS runtime

# The node image already ships a non-root `node` user at uid 1000. Reusing
# it is simpler than creating a second identity at the same uid, which the
# base image refuses anyway.
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME=0.0.0.0

# The standalone output carries only the node_modules actually imported —
# no build toolchain, no dev dependencies.
#
# B-219 / TASK-1465 moved the build's output to `.next-build/` so a build can
# no longer overwrite a running dev server's `.next/`. These paths move with
# it, on both sides of the copy: the standalone bundle contains its own
# `.next-build/` directory, and `server.js` resolves static assets under the
# distDir it was built with. Copying to `.next/static` would leave the server
# looking in a directory nothing wrote — a production image that starts and
# serves no CSS.
#
# Caught by QE reading the interaction rather than by the build failing: the
# builder stage succeeds either way, and only the copy is wrong.
COPY --from=builder --chown=node:node /app/.next-build/standalone ./
COPY --from=builder --chown=node:node /app/.next-build/static ./.next-build/static
COPY --from=builder --chown=node:node /app/public ./public

USER node

EXPOSE 3000

CMD ["node", "server.js"]
