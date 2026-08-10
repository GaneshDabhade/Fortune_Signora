# ADR-0408 · Inbound rate limiting — a limiter at the edge, backed by Redis

**Status: DRAFT — Lane C, 2026-08-10. Awaiting the product owner.**
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
