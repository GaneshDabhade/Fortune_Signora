# 34 · Machine Credentials — *as built*

> **A third party authenticating INBOUND to Signora.**
>
> **Ratified by [ADR-0414](adr/0414-machine-credentials-bounded-context.md)** (ACCEPTED, product owner, 2026-08-13, ruling [C-1404](../LANE_COORDINATION.md) ⓐ). **Built by [TASK-1413](../BACKLOG.md), slice ⓐ, 2026-08-16.**

⚠️ **Slice ⓐ is the domain and its Security Invariants. There is no table, no repository, no endpoint and no application layer yet** — and the reason for stopping there is [C-1524](../LANE_COORDINATION.md), below.

---

## 1 · What this module is, in one line each

| | |
|---|---|
| ✅ **Owns** | **The inbound API-key credential lifecycle** — issuance · rotation · one-time display · revocation · per-call audit |
| ⛔ **Does not own** | **Outbound credentials** (`integrations`) · **webhook delivery** (the outbox/relay, [ADR-0011](adr/0011-background-processing-and-event-bus-transport.md), [TASK-1481](../BACKLOG.md)) · **the ownership anchors** (`workspace_tenancy` keeps the workspace, the member and machine-principal ownership) |

📁 **The near-miss is `integrations`, and it is worth knowing why it is wrong before you are tempted**: that module already publishes `Credential`, `ConnectedAccount` and `ExecutionContext` — **for the opposite direction.** 📁 [§13](../../CLAUDE.md) forbids exactly this reuse: *"a sign-in OAuth token must never be reused as an integration OAuth token."* ⚡ **An inbound machine credential placed in the module that owns outbound ones is that defect with new nouns.**

---

## 2 · The decision this slice took, and it is the one to read first

📁 **[TASK-1413](../BACKLOG.md)'s Security Invariant**: *"a key's scope is enforced by the same enforcer as a human's, never by a parallel check."*

🔴 **It is not directly expressible, and finding that out shaped the whole module.**

📁 **`Authorizer.is_allowed(role, workspace_id, resource, action)` — the subject term is a ROLE STRING.** ⛔ **A key has a scope, not a role.** ⛔ **And a per-key policy row cannot be written**: 📁 [ADR-0010](adr/0010-identity-and-access.md) makes `policy.csv` read-only at runtime — *"policy changes ship as code review."*

> ## ✅ **The GRANT is Casbin's alone. A scope can only SUBTRACT.**

⚡ **Expressed as a type rather than a convention**: `KeyScope.narrow` **requires** the enforcer's answer as a keyword argument with no default, and **there is no public method that answers without one.**

```python
def narrow(self, *, granted: bool, resource: Resource, action: Action) -> bool:
    return granted and (resource, action) in self.pairs
```

⛔ **A caller physically cannot ask a scope whether something is permitted.** ✅ **That is the difference between a filter and a second enforcer, placed where it cannot be forgotten** ([§2](../../CLAUDE.md), *types should make incorrect architecture impossible*).

⚠️ **A test asserts the PUBLIC SURFACE of `KeyScope`**, so a future method that answered alone would fail the suite rather than pass review:

```python
assert public == {"pairs", "of", "narrow", "within"}
```

---

## 3 · The invariants enumerate the product rather than sampling it

🔴 **`EVERY_PAIR = frozenset(product(Resource, Action))`** — read from the enums, never listed.

⛔ **A sampled version passes on the day somebody registers a new `Resource` and leaves it unguarded.** ✅ **This one grows with the product**: the day a `Resource` member is added, every test in `test_machine_credential_scope.py` covers it without anybody editing the file.

**159 assertions in slice ⓐ.** **Fire-tested, both ways:**

| Change | Result |
|---|---|
| `narrow` returns membership without `granted` | 🔴 **RED** — *"a scope widened a denial"* |
| the issuer-scope check is skipped | 🔴 **RED** — a key wider than its creator is issued |

---

## 4 · The key format, and the two things that decided it

**`sig_<public_id>_<secret>`**

| | |
|---|---|
| **`sig`** | ⚡ **A recognisable prefix so a leaked credential can be SCANNED for.** ⛔ Not `signora_`: in a customer's log that reads as the product, not as a credential |
| **`public_id`** | **6 bytes, HEX.** ⛔ **Not `token_urlsafe`** — see below |
| **`secret`** | **32 bytes, `token_urlsafe` (~256 bits).** ⚠️ **It MAY contain `_`, and that is fine**: it is the last field and `split_token` splits at most twice |

### ⚠️ The separator collided with the alphabet, and only a real token found it

🔴 **The first implementation used `token_urlsafe` for both halves and `token.split("_")`.** ⛔ **`token_urlsafe` emits `-` and `_`**, so a real token has more than three parts and `split_token` rejected it.

✅ **Every hand-written fixture passed. The test that issued a REAL key failed.** ⚡ **That is the shape a fixture-only suite never finds**, and it is why the round-trip test exists at all.

### ⚠️ SHA-256, and not a password hash — stated because it looks wrong

⛔ **bcrypt and argon2 exist to make GUESSING expensive**, and they buy that by being slow. ⚡ **There is nothing to guess here**: the secret is 256 bits of CSPRNG. **A slow hash would add its cost to every API call rather than to an attacker.**

✅ **What matters instead:** **the comparison is `hmac.compare_digest`**, and **the lookup does not need the secret** — the public id finds the row, and only then is one digest compared. ⛔ **Without a public id, verification would mean hashing the candidate against every key in the workspace** — slow, and a timing oracle for how many keys exist.

---

## 5 · The secret exists in exactly one moment

📁 **The design: *"A key is shown once at creation and never again."***

⛔ **A rule in prose is a rule somebody breaks by writing a helpful `get_key()`.** ✅ **So the plaintext is `IssuedSecret`, returned by `issue()` and by nothing else** — **there is no field of that type on `ApiKey`**, so a repository has nowhere to persist it even if a column were added.

⚡ **`__str__` and `__repr__` are overridden to redact.** **A credential reaches a log through an f-string far more often than through a deliberate write**, and 📁 `workspace_tenancy`'s `SecurityEvent` contract already refuses a `detail` key carrying one — **this closes the accidental path as well as the deliberate one.**

---

## 6 · Three states, and no `EXPIRED`

| | |
|---|---|
| `ACTIVE` | |
| `SUPERSEDED` | ⚡ **Still usable, and that is the point.** 📁 *"Rotation with an overlap window"* — a rotation that ended the old key immediately is one nobody can perform without downtime |
| `REVOKED` | **Terminal. Revoking twice is not an error and keeps the FIRST time**, which is the fact an audit needs |

⛔ **Expiry is a PREDICATE over `expires_at`, never a stored state** — 📁 [§2](../../CLAUDE.md), *truth has exactly one authoritative representation*. ⚠️ **A stored `EXPIRED` needs a job to write it, and between the deadline and that job the row says a dead key is live.**

⚠️ **`expires_at = None` means *no deadline*, which is a different fact from *not yet expired*.**

---

## 7 · 🔴 What blocks the rest, and it is not this module's to fix

📁 **[C-1524](../LANE_COORDINATION.md).** **`AuthenticatedPrincipal` in `signora_platform/auth/principal.py` is human-only** — `user_id · session_id · email · email_verified · active_workspace_id · token_id`.

📁 **[495](495-principal-and-identity-boundary.md) already measured this in its own words** — *"every field is human, and every non-human caller in [D-176](../DECISION_REGISTER.md) §1 is unrepresentable"* — **and ratified the repair: one principal type with `kind`, `subject_id`, `workspace_id`, `owner_user_id`.** ⚠️ **It has not been built, and `signora_platform/**` is 🔴.**

⛔ **So a key-authenticated request has nowhere to say it is not a person.**

⚡ **The asymmetry is the argument for ruling it soon**: 📁 `frontend/lib/entry/principal.ts` already admits non-human principals, widened by [TASK-1407](../BACKLOG.md) *while `resolveEntry` had zero callers*. **`AuthenticatedPrincipal` has more than zero — its own docstring says it is *"the ONLY representation of caller identity in the system"*** — **so the cost of the widening only rises.**

### ✅ What is above that boundary and therefore proceeds

**The credential lifecycle · hashing · one-time display · the per-call record · the scope model.** ⛔ **What waits: authentication itself, and the endpoints that would use it.**

---

## 8 · What a lane picking this up next needs to know

| | |
|---|---|
| **Slice ⓑ** | **The table, the repository and the endpoints.** ⚠️ **The table is 🟠 and needs its `tenancy_policy.py` registration in the same change** ([§8](../../CLAUDE.md)) |
| **`workspace_id`** | 🔴 **Non-nullable.** 📁 [495](495-principal-and-identity-boundary.md): *"a machine identity that is not workspace-scoped is a cross-tenant credential."* |
| **`owner_user_id`** | 🔴 **Non-nullable.** 📁 *"Every machine principal is owned by a human… what makes revocation on offboarding tractable and audit attributable."* ⚠️ **Which implies a cascade when the owner leaves the workspace, and slice ⓐ does not build it** |
| **The per-call audit** | ✅ **Reuse `workspace_tenancy`'s `SecurityEventWriter`** — 📁 [TASK-1413](../BACKLOG.md) says so and the port already refuses a `detail` key carrying a credential. ⛔ **Never a second audit log** |
| ⛔ **Do not** | **Add a public method to `KeyScope` that answers without the enforcer's verdict.** **A test will fail, and it is failing on purpose** |
