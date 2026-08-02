# ADR-0037: Failure categories — who caused it, and what they can do about it

## Status

**Proposed** — 2026-08-02. Raised by Lane A while assigned to `opportunity_engine`, as coordination item [`C-009`](../../LANE_COORDINATION.md#c-009--an-internal-fault-reaches-a-customer-as-a-422). **The direction is agreed by the product owner; implementation is not scheduled.**

**Nothing here is implemented and nothing should be until this ADR is Accepted.** It is recorded in ADR form rather than left in the coordination register because a decision that outlives the question belongs in the architecture — the register is for questions in flight.

Would amend [19-api-conventions.md](../19-api-conventions.md) (two new response codes, one new handler) and touch `signora_platform/api/errors.py`, which is frozen under CLAUDE.md §20a. Supersedes nothing.

## Context

**One exception class is serving two purposes, and `ERROR_MAPPING` cannot tell them apart.**

`OpportunityError → 422 transition_refused` is correct for *"a won deal does not reopen"*. It is applied identically to *"an opportunity cannot record a negative score at creation"* — which no customer caused and no customer can act on. The same shape exists in `ai_research_engine` (`ResearchRequestError`), and it will exist in every module that follows the pattern in front of it.

This is the failure-attribution rule, in the API layer:

> **Failure attribution must be truthful** (ratified 2026-07-30). *An error must never name a component that was not involved… an incorrect attribution is worse than none, because it misdirects the investigation.*

A support engineer reading `transition_refused` on a bug report will look at the transition table. **The transition table is fine.**

**Found by a repository-wide scan**, not by a report: R4-03 described one message with a UUID in it; asserting the rule as a scan (`tests/security_invariants/test_customer_facing_messages.py`) found seven across two modules, and the four it added were all of the second kind.

### Why it could not be fixed in the slice that found it

`signora_platform/api/errors.py` **registers no catch-all `Exception` handler**, so an unmapped exception bypasses `ErrorResponse` entirely and returns a bare framework `500` — no `code`, no `correlation_id`, no `error` object. Every client parses that envelope, Signora's own included.

Splitting a module's hierarchy today would therefore trade a **wrong code** for a **missing envelope**, which is worse: `correlation_id` is the only thread between a customer's report and the log line that explains it.

## Decision (proposed)


### 1 · The hierarchy

Four categories, and the test that separates them is **who caused it and what they can do about it** — not where the code lives:

```
SignoraError                      (platform, abstract — never raised)
├── CustomerError                 the caller did something the domain refuses
│   ├── BusinessRuleViolation     a rule about their data said no
│   ├── ValidationError           the request itself was malformed
│   └── NotFoundError             the thing named is not visible to them
└── PlatformError                 nobody outside caused this
    ├── InvariantViolation        a stored fact contradicts itself
    └── InfrastructureError       a dependency failed — database, queue, provider
```

**`CustomerError` is the only branch whose message is customer copy.** That single sentence is the whole proposal; everything else follows from it.

**Modules keep their own exception types** and inherit from one of the five leaves. `OpportunityError` becomes a `BusinessRuleViolation`; the four construction-time refusals in `OpportunityState.__post_init__` and `ResearchRequestState.__post_init__` become `InvariantViolation`. **No module names an HTTP status**, exactly as today.

**Why `NotFoundError` is a customer error and not its own branch.** *"That account has no opportunity in this workspace"* is actionable — and 404-not-403 is already a deliberate security property (a non-member and a non-existent resource must be indistinguishable). Splitting it out would invite somebody to make the two differ.

### 2 · What a customer sees

| Category | Status | Message | Envelope |
|---|---|---|---|
| `BusinessRuleViolation` | `422` | **The domain's own words** | Full |
| `ValidationError` | `422` | The domain's own words | Full, with `details` |
| `NotFoundError` | `404` | The domain's own words | Full |
| `InvariantViolation` | **`500`** | **Fixed string. Never `str(exc)`** | Full |
| `InfrastructureError` | **`503`** | **Fixed string. Never `str(exc)`** | Full |

**`PlatformError` messages must never be translated into customer-facing business errors.** That is the rule this item exists to establish. A customer told *"an opportunity cannot record a negative score at creation"* learns nothing, can do nothing, and is being told about a bug in a sentence that sounds like their fault.

**`503` rather than `500` for infrastructure** because it is the one platform failure a client can act on: retry. `500` says *do not retry*, and telling a client to give up on a transient database blip is a wrong answer with a cost.

**The full envelope in every case, including `500`.** That is the point of the change — today an unmapped exception bypasses `ErrorResponse` entirely and a customer reporting a fault has no `correlation_id` to quote.

### 3 · Envelope, logging and correlation

**Envelope — unchanged in shape.** `{ error: { code, message, details?, correlation_id } }`, which is already ratified in [19-api-conventions.md](architecture/19-api-conventions.md). What changes is that **nothing escapes it**.

Two new stable codes: `internal_error` and `service_unavailable`. Module codes are untouched.

**Logging, and this is the half that makes the fixed message acceptable:**

| Category | Level | What is logged |
|---|---|---|
| `CustomerError` | `INFO` | Code, `workspace_id`, `correlation_id`. **Not an error** — the platform behaved correctly |
| `InvariantViolation` | `ERROR` | Full `str(exc)`, traceback, every identifier the message ever carried |
| `InfrastructureError` | `ERROR` | Full `str(exc)`, traceback, the dependency that failed |

**A `CustomerError` logged at `ERROR` is how an error dashboard becomes noise nobody reads.** A seller trying an illegal transition is the product working.

**Correlation id — the requirement that makes this worth doing.** Every response carries it, `500` included; every log line for that request carries the same one; it is generated once per request and already stored on `request.state`. **It is the only thread between *"it broke and said something about an internal error"* and the line that explains why**, and today that thread is cut exactly where it matters most.

Identifiers therefore move **out of messages and into log fields** rather than being deleted — `logger.error(..., extra={"opportunity_id": ...})`. This slice removed them from the messages; the proposal is what gives them a proper home.

### 4 · What changes in `signora_platform/api/errors.py`

**Four changes, all additive. No existing behaviour is altered.**

1. **A catch-all `Exception` handler**, registered last, returning the envelope with `internal_error`, a fixed message and the correlation id. **This alone fixes the regression that blocks the split** and is independently worth having: any unhandled bug today escapes the contract.
2. **Two platform base classes** (`CustomerError`, `PlatformError`) exported for modules to inherit — or, if the product owner prefers zero new platform vocabulary, a second mapping `PLATFORM_ERROR_TYPES` and no base classes at all. **The first is stronger** because it makes the category a type rather than a registration somebody can forget.
3. **`_domain_handler` stops calling `str(exc)` unconditionally** — customer copy for `CustomerError`, the fixed string otherwise.
4. **Logging inside the handlers**, at the levels above. There is none today, so an error's only record is whatever the raising code happened to log.

**Estimated size: under a hundred lines, no migration, no API path change, no client change.** The risk is not size — it is that `signora_platform/` is frozen (§20a) and this is a change to how *every* module's errors surface, which is precisely why it is here rather than in a lane's commit.

### 5 · What this unlocks, and what it costs

**Unlocks:** each module splits its own hierarchy inside its own budget · the invariant added in `e1a34a6` narrows from *"no mapped message may name an identifier"* to *"no **customer** message may"*, which is stronger, because a `PlatformError` would then be free to say everything an engineer needs · error dashboards separate *customers being refused* from *Signora being wrong*, which are currently one number.

**Costs:** every module reclassifies its exceptions once — mechanical, and the invariant will find any that are missed · two new response codes for clients to know about, both already implied by the status codes · QE gains a real assertion it cannot make today: **no `5xx` response may contain a domain sentence.**
