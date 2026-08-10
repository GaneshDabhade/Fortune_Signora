# ADR-0408 · Inbound rate limiting — a limiter at the edge, backed by Redis

**Status: ACCEPTED — product owner, 2026-08-10, [D-232](../../DECISION_REGISTER.md) §4. Drafted by Lane C.**
**Unblocks [TASK-1430](../../BACKLOG.md), which reads `SEQUENCED` with *"needs the ADR before it is claimable"* — and that ADR is this office's to draft. The row has waited on work only Lane C could do.**

> ⛔ **This is a draft. Nothing in the repository behaves as though it were ratified, and `signora_platform/` stays frozen until it is** ([§20a](../../../CLAUDE.md)).

---

## 0 · Why this needs an ADR at all

📁 **[§20a](../../../CLAUDE.md) freezes `signora_platform/`.** A limiter at the edge is platform substrate by definition — it sits in front of every route, before any module sees a request. ⛔ **So it cannot be added as a module's slice**, and the freeze's third exemption is *"explicitly approved architectural changes — raised through the RFC process and approved before implementation."*

⚡ **That is the whole reason `TASK-1430` is `SEQUENCED` rather than `READY`**, and it is why this document exists before any code.

---

## 1 · 🔴 The measurement, and the first version of the probe got it backwards

| | |
|---|---|
| **Inbound limiting on Signora's own API** | ⛔ **None.** `git grep add_middleware backend/apps` returns nothing — **there is no middleware layer at all** |
| **`429` anywhere in the API layer** | ⛔ **Zero occurrences** in `signora_platform/api/` |
| **Outbound limiting** | ✅ **Present and healthy** — `ai_platform`, `integrations` and the provider pools all limit calls **they make to vendors** |

> ## ⚠️ **38 files rate-limit OUTBOUND traffic, and that is the opposite concern.**

⛔ **A repository search for *"rate limit"* looks reassuring and is measuring the wrong direction.** ⚡ **Protecting HubSpot from Signora is not protecting Signora from the internet**, and the sign-in route is the one that matters: **nothing stands between a credential-stuffing script and Better Auth.**

---

## The decision

> ## ✅ **A limiter runs as ASGI middleware at the API edge, keyed per route and per identity, with its counters in Redis.**
>
> ⛔ **Buy the mechanism; own the policy.** The counting algorithm is a commodity ([§3](../../../CLAUDE.md), principle 15); **which routes are limited, at what cost, and what a refusal says are Signora's.**

---

## 2 · ⚡ Why Redis rather than in-process, and it is not about scale

📁 **[§20b](../../../CLAUDE.md) requires stateless services**: *"no process holds state another needs; scaling to n replicas changes throughput only."*

🔴 **An in-memory limiter violates that directly.** With *n* replicas a per-process counter gives an attacker **n × the budget**, and — worse — **the limit silently loosens every time the service scales**, which is the failure nobody notices because nothing breaks.

✅ **Redis is already a backing service** (ARQ, the outbox relay), attached by URL, so this adds a **use** of existing infrastructure rather than a new datastore ([§8](../../../CLAUDE.md) — one PostgreSQL database, and Redis is not a system of record here: **a lost counter fails open for one window and is not data**).

---

## 3 · ⛔ What a refusal must not say

📁 **The sign-in card's copy already follows the account-enumeration rule**, and a limiter is the easiest place to break it:

| ⛔ Never | ✅ Instead |
|---|---|
| *"Too many attempts for this account"* | **A response identical whether or not the address exists** |
| A different status, delay or body for a known address | **One `429`, one shape, one `Retry-After`** |

⚡ **This is [§7](../../../CLAUDE.md)'s `404`-not-`403` reasoning applied to timing and volume**: a limiter that answers faster for unknown addresses is an enumeration oracle wearing a security control's clothes.

---

## 4 · ✅ Where it sits, and what it must not become

| | |
|---|---|
| **Layer** | **ASGI middleware in `signora_platform/api/`** — before routing, before authorization, before any module |
| **Ordering** | **After correlation-id assignment** — a refused request must still be traceable ([§16](../../../CLAUDE.md)) |
| **Configuration** | **A typed `Settings` object owned by the platform**, injected at the composition root ([§6](../../../CLAUDE.md)). ⛔ **No module reads it and no module configures it** |
| **Scope** | ⚡ **Authentication routes first** — `/sign-in`, `/register`, password reset. **Per route, never one global number** |

⛔ **What it must not become**: **a second authorization layer.** Casbin decides *who may*; this decides *how often anyone may*. **A limiter that inspects a workspace claim to choose a limit has started making authorization decisions** in a component that runs before authorization.

---

## 5 · ⚠️ The failure mode this must be tested for, and it is not the happy path

> ## 🔴 **A limiter is a denial-of-service vector pointed at your own customers if the key is attacker-controlled.**

**Key on what the attacker cannot forge.** ⛔ **Keying sign-in solely on a submitted email address lets anybody lock any customer out** by spending their budget for them — **the control becomes the attack.**

✅ **The Security Invariant this needs** ([§11](../../../CLAUDE.md)): **a refused caller must never be able to cause the refusal of a caller they do not control.**

---

## 6 · Scope — what this does not decide

⛔ **Not decided here, deliberately**: the specific library, the numeric budgets, per-tenant quotas, WAF or CDN-layer protection, or outbound limiting (**which exists and is untouched**).

⚡ **The library is Lane A's [L-1](../../../ENGINEERING_LAWS.md) audit to run against what is already installed**, and the budgets are a product judgement that wants real traffic. ⛔ **Deciding either here would be inventing detail this office cannot measure** ([§21](../../../CLAUDE.md)).

---

## 7 · What the product owner is being asked

> **① Approve a `signora_platform/` exemption under [§20a](../../../CLAUDE.md) for an edge limiter.**
> **② Confirm Redis-backed rather than in-process**, on the stateless-service argument in §2.
> **③ Confirm authentication routes first**, rather than a global limit.

✅ **On approval, `TASK-1430` becomes `READY`** and the remaining choices are ordinary implementation.


---

## 8 · ⚡ The five categories — [D-231](../../DECISION_REGISTER.md) §1

| | |
|---|---|
| **What the repository PROVES** | ⛔ **Zero `add_middleware` in `backend/apps` — there is no middleware layer at all.** ⛔ **Zero `429` in `signora_platform/api/`.** ✅ **38 files rate-limit OUTBOUND vendor calls.** ⚡ **Redis is already a backing service** (ARQ, the outbox relay), attached by URL |
| **What the SECURITY REQUIREMENT requires** | **A limiter in front of authentication, and a refusal that does not disclose whether an address exists.** ⛔ **Not a number** — no security requirement in this repository specifies one |
| **An ARCHITECTURAL choice** *(yours)* | **① the §20a exemption · ② Redis-backed versus in-process · ③ authentication-first versus global** |
| **An IMPLEMENTATION detail** *(Lane A's)* | **The library** — an [L-1](../../../ENGINEERING_LAWS.md) reuse audit against what is installed · **the algorithm** (fixed window, sliding, token bucket) · **where the middleware is registered** · **the `Retry-After` shape** |
| **CONFIGURATION, deferred by evidence** | **Every numeric threshold.** ⛔ **Not decided here and not decided by Lane A** — **set from measured traffic, and until traffic exists a conservative default that is changed without a code change** ([§6](../../../CLAUDE.md): configuration is a typed Settings object) |

## 9 · 🔴 Redis versus in-process, assessed rather than preferred

| Axis | In-process | Redis-backed |
|---|---|---|
| **Multiple replicas** | ⛔ **An attacker gets *n* × the budget** | ✅ **One budget, whatever *n* is** |
| **Horizontal scaling** | 🔴 **The limit LOOSENS as you scale — silently, with nothing failing** | ✅ **Unchanged by scaling** |
| **Failover** | ⛔ **Counters die with the process; a restart resets an attacker's budget** | ✅ **Survives a replica restart** |
| **Budget consistency** | ⛔ **Per-process, so the effective limit is unknowable** | ✅ **Stated limit is the real limit** |
| **Operational dependency** | ✅ **None** | ⚠️ **Redis becomes a dependency of sign-in** |
| **If Redis is unavailable** | — | 🔴 **THE MATERIAL DOWNSIDE. Fail-open leaves you unprotected during an outage; fail-closed makes a Redis outage an authentication outage.** ⛔ **Neither is free, and this ADR does not choose — it names it as the one thing that needs an explicit answer** |
| **Abuse resistance** | ⛔ **Defeated by distributing across replicas** | ✅ **Holds** |
| **Do auth endpoints need stricter protection?** | ​ | ✅ **Yes — they are the only routes where an attacker's goal is achieved by VOLUME rather than by a single request** |

> ## ✅ **The evidence supports the direction stated in [D-231](../../DECISION_REGISTER.md) §1**, and the honest downside is availability coupling, not complexity. ⚠️ **An in-process limiter in a horizontally scaled system does not provide equivalent protection — it provides a number that is wrong by a factor of *n* and looks right.**

## 10 · ✅ Route scope — the candidates, named

| Route | Candidate? | Why |
|---|---|---|
| **`/signin`** | ✅ **Yes** | Credential stuffing. **The one everybody names** |
| **`/register`** | ✅ **Yes** | ⛔ **Account-creation flooding, and it writes rows** |
| **Password reset request** | ✅ **Yes** | 🔴 **Email amplification — an unlimited endpoint that SENDS MAIL to an address the attacker chooses** |
| **Verification resend** | ✅ **Yes** | Same amplification shape |
| **SSO initiation** | ⚠️ **Assess** | Redirects rather than verifies; lower value, non-zero cost |

> ⛔ **There is no reason to protect only `/signin`.** ⚡ **Reset-request and resend are arguably worse: they make Signora send mail on an attacker's command**, and neither needs a valid credential to invoke.

## 11 · ✅ The §20a exemption — exactly what it permits

**The security risk justifies it: an unprotected authentication surface is [§13](../../../CLAUDE.md)'s subject, and no module can fix it because no module owns the edge.**

| ✅ **The exemption permits** | ⛔ **It does not permit** |
|---|---|
| **One ASGI middleware in `signora_platform/api/`**, its typed `Settings`, and its Security Invariant | **Any other platform change.** **Any authorization logic** — Casbin decides *who may*; this decides *how often anyone may*, and a limiter reading a workspace claim has started deciding authorization before authorization runs |


---

## 12 · 🔴 Redis degradation — the behaviour, not the preference

> ## ⛔ **This is the one thing the ADR must not leave implicit.** ⚡ **A limiter's failure mode is a product decision, not a library setting.**

| Redis state | Fail-OPEN | Fail-CLOSED |
|---|---|---|
| **Unavailable** | ⛔ **Authentication protection disappears silently.** An attacker who can degrade Redis has removed the control | 🔴 **Authentication becomes unavailable.** A Redis outage becomes a sign-in outage for every customer |
| **Slow** | ⚠️ **Latency added to every sign-in** unless bounded | ⚠️ **Same, plus refusals under load** |

### ✅ The ruling, and it is deliberately asymmetric

> **Fail-OPEN on the limiter, and make the failure LOUD.**

⛔ **The alternative trades a defence against a determined attacker for an outage affecting every legitimate customer**, and an authentication outage is the larger harm. ⚡ **But fail-open is only acceptable because it is observable** — a silent fail-open is the [§2](../../../CLAUDE.md) *decorative guard*, protection that has stopped protecting with nothing saying so.

| | |
|---|---|
| **Timeout** | **A short, explicit bound owned by the module** — ⛔ **never the client default.** A limiter that adds unbounded latency to sign-in has become the outage it was avoiding |
| **On timeout or error** | ✅ **Allow the request, increment a failure counter, and emit a WARN** carrying `correlation_id` ([§16](../../../CLAUDE.md)) |
| **Observability** | 🔴 **The degraded state must be alertable.** ⛔ *"Rate limiting is currently not enforced"* is an operational condition somebody must be able to see — **it is not a log line nobody reads** |
| **Local emergency fallback** | ⚠️ **Assessed and NOT recommended as a first slice.** ⛔ **A per-process fallback re-introduces the *n* × budget this ADR exists to avoid, and it does so exactly when the system is already degraded** — **the worst moment for a control that silently weakens.** ✅ **If it is added later it is a separate, measured decision** |

## 13 · ⚡ Two policies, not one — [D-232](../../DECISION_REGISTER.md) §4

| | |
|---|---|
| ✅ **Authentication abuse protection** *(this ADR)* | **Unauthenticated, credential-sensitive routes.** **The attacker's goal is achieved by VOLUME**, and the cost of a refusal is one retry |
| ⛔ **General API throttling** *(NOT this ADR)* | **Authenticated routes, capacity protection, fair use.** **A different policy, a different key, a different failure posture** — and it does not belong in the same slice |

## 14 · ✅ Identity and key strategy — the property that matters more than the number

> ## 🔴 **Key on what an attacker cannot choose on somebody else's behalf.**

⛔ **Keying sign-in solely on the submitted address lets anybody lock any customer out by spending their budget** — **the control becomes the attack.** ✅ **The Security Invariant** ([§11](../../../CLAUDE.md)): **a refused caller must never be able to cause the refusal of a caller they do not control.**

## 15 · ✅ Configuration model — and why no number appears in this ADR

**Every threshold is configuration** in the module's own typed `Settings` ([§6](../../../CLAUDE.md)), **changed without a code change.** ⛔ **This ADR states no production number**, because none is derivable: **there is no traffic to measure and no security requirement in this repository specifying one.** ✅ **A conservative default ships, and tuning follows measurement.**

## 16 · ✅ The §20a exemption, stated exactly

| | |
|---|---|
| **What is added** | **One ASGI middleware in `signora_platform/api/`, a typed `Settings`, and a Security Invariant** |
| **Why security-critical** | ⛔ **Nothing stands between a credential-stuffing script and `/signin`**, and no module can fix it because **no module owns the edge** |
| **Which boundary it crosses** | **The [§20a](../../../CLAUDE.md) platform freeze** — the substrate every module imports |
| **Why delay is unacceptable** | **The exposure is live on every deployed environment**, and it grows with each authentication route added |
| ⛔ **What is explicitly NOT changed** | **No other platform internals · no authorization logic · no module contract · no existing endpoint's behaviour when under the limit.** ⚡ **The exemption is one middleware and its configuration — it is not a licence to expand the platform** |
