# 501 · The rate-limiting boundary — two policies, and neither covers both tiers

**Recorded 2026-08-17 by Lane C, on the product owner's ruling of [C-287](../LANE_COORDINATION.md) ⓓ.**
**Implementation: [TASK-1430](../BACKLOG.md).**

> ## ⛔ **No single limiter protects Signora. Two do, they protect different things, and the gap between them is deliberate rather than an oversight.**

---

## 1 · Why this document exists at all

**[ADR-0408](adr/0408-inbound-rate-limiting.md) specified an ASGI middleware in
`signora_platform/api/` (§4) and named the routes it should protect (§10):
`/signin`, `/register`, password-reset request, verification resend.**

🔴 **Those routes are not in that tier and never will be.** [§13](../../CLAUDE.md)
and [ADR-0026](adr/0026-jwt-boundary-architecture.md) make Better Auth the sole
Authentication Authority; **the Python tier only verifies tokens.** An ASGI
middleware there cannot see a request that never reaches it.

⚡ **That is the contradiction [C-287](../LANE_COORDINATION.md) raised**, and the
product owner ruled ⓓ: **build both, and say plainly what each one does.**

⛔ **The failure this document prevents is the tempting one** — reading *"rate
limiting: done"* on a status page and believing one control covers the surface.

---

## 2 · ✅ The two policies

| | **Authentication abuse** | **Business API throttling** |
|---|---|---|
| **Where** | **Better Auth, in Next.js** — [`frontend/lib/auth/server.ts`](../../frontend/lib/auth/server.ts) | **ASGI middleware** — [`signora_platform/api/rate_limit.py`](../../backend/signora_platform/api/rate_limit.py) |
| **Protects** | `/signin` · `/register` · reset request · verification resend | **Every route the Python tier serves** — 105 of them |
| **Attacker's goal** | Achieved by **volume against credentials** | Achieved by **volume against capacity** |
| **Counters** | **PostgreSQL**, `auth` schema, Better Auth's own `rateLimit` table | **Redis**, keyed per route template per identity |
| **Window and budget** | ⛔ **The vendor's** — deliberately not restated | **Signora's** — [`RateLimitSettings`](../../backend/signora_platform/rate_limit_settings.py) |
| **On failure** | The vendor's | ✅ **Fail-open, loudly** — ADR-0408 §12 |
| **Authorized by** | [C-240](../LANE_COORDINATION.md) ② · [D-170](../DECISION_REGISTER.md) §3 ③ · **storage by [C-287](../LANE_COORDINATION.md) ⓐ** | ⚠️ **[C-287](../LANE_COORDINATION.md) ⓓ — NOT by ADR-0408 alone; see §4** |

---

## 3 · 🔴 What each one does NOT protect

⛔ **The Python limiter cannot see `/signin`.** It is a different process, a
different tier, and a different framework. **No configuration change makes it
see one.**

⛔ **Better Auth's limiter cannot see `/workspaces/{id}/products`.** It guards
its own routes and knows nothing about the business API.

⚠️ **So a claim that *"the API is rate limited"* is only ever true of one of
them, and the honest sentence names which.**

### ⚪ Still not covered by either, and deferred rather than forgotten

| | |
|---|---|
| **The edge** | **A CDN or WAF layer in front of both tiers** — [ADR-0408](adr/0408-inbound-rate-limiting.md) §6, deferred to **M14.5** with the rest of infrastructure ([§20b](../../CLAUDE.md)) |
| **Distributed volume** | ⚠️ **The Python limiter keys on the client address.** Behind a proxy every caller shares one until a trusted forwarded-header configuration exists — **which is the same M14.5 infrastructure.** **It bounds a burst; it does not bound a botnet** |
| **Per-tenant quotas** | ADR-0408 §6, explicitly not decided |

---

## 4 · ⚠️ The authorization trail, stated rather than blurred

**ADR-0408 §13 places business-API throttling OUTSIDE its own scope:**

> ⛔ *"General API throttling (NOT this ADR) — authenticated routes, capacity
> protection, fair use. A different policy, a different key, a different failure
> posture — and it does not belong in the same slice."*

📁 **The measurement that made that scope empty here: all 105 Python-tier routes
carry a workspace or user context.** ⛔ **ADR-0408's own subject — unauthenticated,
credential-sensitive routes — has no members in this tier**, so a middleware
built strictly to §10 would guard nothing at all.

✅ **So the middleware is authorized by the C-287 ⓓ ruling**, which re-scoped it:
*"ⓒ is worth doing on its own merits and should be re-scoped rather than
cancelled — but its row must say the business API, not `/signin`."*

⚠️ **And one citation is worth flagging rather than leaving for somebody to
trip over.** ADR-0408's status line reads *"ACCEPTED — product owner,
2026-08-10, [D-232](../DECISION_REGISTER.md) §4"*, while
[D-237](../DECISION_REGISTER.md) ④ later ruled that **"D-232 must not be treated
as authority anywhere it is cited."** ⛔ **This document does not resolve that** —
the work proceeded on the product owner's direct 2026-08-17 instruction, which
is the authority [§20a](../../CLAUDE.md) requires either way. **Recorded so the
next reader does not have to rediscover it.**

---

## 5 · ✅ What was verified, and how

| Claim | How it was established |
|---|---|
| **Better Auth's limiter was already enabled** | `server.ts:147` — `rateLimit: { enabled: true }`, since [C-240](../LANE_COORDINATION.md) ② |
| 🔴 **…and its counters were in process** | **The vendor's own types**: `storage` defaults to `"memory"`, and neither `rateLimit.storage` nor `secondaryStorage` was configured |
| ✅ **`storage: 'database'` genuinely changes behaviour** | **Diffed the vendor's migration plan against a real database.** `memory` → `["account","session","user","verification"]`; `database` → the same **plus `rateLimit`** |
| **The Python limiter refuses at the budget** | 9 integration tests, including the `429` shape and `Retry-After` |
| 🔴 **A concrete id does not buy a fresh budget** | **A test that FAILED first.** `add_middleware` runs before routing, so `scope["route"]` is never populated and the first implementation keyed on the concrete path — **three workspaces passed a budget of two.** The middleware now resolves templates against `app.routes` itself |
| **A refused caller cannot refuse anybody else** | 6 Security Invariants — ADR-0408 §5's requirement |
| **Fail-open is real and loud** | Tested against a store that refuses and one that hangs; both the `WARNING` and the alertable counter are asserted |

⛔ **Not verified, and named for that reason**: **behaviour under real
concurrent load**, and **the numeric budgets**, which ADR-0408 §15 refuses to
set until measured traffic exists.

---

## 6 · ⚠️ What a future change must not do

- ⛔ **Do not read `X-Forwarded-For`** until a trusted proxy strips and replaces
  it. **Today it is caller-controlled**, and trusting it hands every caller a
  free identity — a test exists to stop this arriving as a convenience.
- ⛔ **Do not key on a workspace claim.** The limiter runs *before*
  authorization; a limiter that reads tenancy has started deciding authorization
  in a component that runs before it ([ADR-0408](adr/0408-inbound-rate-limiting.md) §4).
- ⛔ **Do not add a per-process fallback when Redis is down.** ADR-0408 §12
  assessed and rejected one: it re-introduces the *n* × budget **exactly when
  the system is already degraded.**
- ⛔ **Do not let Alembic create Better Auth's `rateLimit` table.**
  `0005_auth_schema.py` creates the schema *"and nothing inside it"*, and two
  migration systems over one object is how an upgrade silently conflicts.
- ⛔ **Do not describe either limiter as protecting "the API".** Name the tier.
