# ADR-0412 — The environment is machine-readable, and logging is secret-safe by default

| | |
|---|---|
| **Status** | ✅ **RATIFIED — product owner, 2026-08-12, as [C-298](../../LANE_COORDINATION.md)** |
| **Decision** | ✅ ***"Credentials and secrets must NEVER be written to logs in production or customer-facing environments… The implementation must NOT rely on developers remembering which environment they are in. The environment must be explicit and machine-readable."*** |

## 1 · The rule that makes this an ADR and not a lint fix

📁 **[§2](../../../CLAUDE.md): *a guard that cannot fail is not protection — it is documentation pretending to be code.*** ⚡ **A logging rule kept by developer memory is exactly that**, and the ruling says so in its own words: **the implementation must not rely on remembering.**

⛔ **So the environment is a value the code reads, never a fact the author is assumed to know.**

## 2 · One vocabulary, and only one

📁 **The defect [C-298](../../LANE_COORDINATION.md) recorded: the auth tier and the registry do not agree what an environment is called.** ⛔ **The ruling: *"Do not create a second environment taxonomy."***

- **`SIGNORA_ENVIRONMENT` is the single name, defined consistently across the application and the runtime.**
- **Frontend and backend semantics are identical** — ⚠️ **a value that means *production* in one tier and something else in the other is the same defect with a longer fuse.**
- ⛔ **The vocabulary is closed.** 📁 **[§2](../../../CLAUDE.md), *types should make incorrect architecture impossible* — an unrecognised environment value must be unrepresentable, never silently treated as development.**
- ⚡ **A missing value FAILS. It does not default.** 📁 **The precedent is already in the repository: `SIGNORA_REDIS_URL` refuses rather than defaulting to index 0, and `.env.example` records why** — *"it used to default in code, which made the allocation table advisory."*

## 3 · Secret-safe by default

| | |
|---|---|
| **Production and every customer-facing environment** | 🔴 **Redaction is ENFORCED. A credential value is never emitted, under any level, in any field, in any tier** |
| **Development and test** | ✅ **Diagnostic logging is permitted only where the value is redacted or non-secret** |
| **Every environment** | ⛔ **The default is safe.** ⚡ **A developer must opt *in* to verbosity, never opt out of redaction** |

📁 **[§16](../../../CLAUDE.md) already says *never log secrets, credentials, or raw PII without an explicit, approved policy.*** ✅ **This ADR is that policy, and it makes the guarantee enforceable rather than aspirational.**

## 4 · Enforcement, not convention

🔴 **This belongs in the Security Invariants suite** ([§11](../../../CLAUDE.md)), because a rule verified by review is a rule that lapses on the day nobody reviews.

**The invariant to state: a credential value cannot reach a log sink in a production configuration.** ⚡ **Fire-test it** — 📁 **the practice QE established: a check nobody has made fail proves nothing.**

⚠️ **And the second invariant, which is the one that would actually have caught [C-298](../../LANE_COORDINATION.md): the environment vocabulary agrees across tiers.** ⛔ **Two tiers disagreeing about a name is invisible until the day it matters.**

## 5 · What was latent, and why it stops being

📁 **[C-298](../../LANE_COORDINATION.md) recorded that nothing sets `SIGNORA_ENVIRONMENT` for the frontend, so every clone works today.** ⚠️ **That is the dangerous shape, not the safe one: the gap is invisible precisely because nothing fails.**

⛔ **Under §2 above it stops being latent** — an absent value fails rather than defaulting, so the gap surfaces the first time it is run rather than the first time it matters.

## 6 · Infrastructure Contract

✅ **Unchanged and reinforced.** 📁 **[§20b](../../../CLAUDE.md): every value through a typed `Settings` object owned by the module whose behaviour it governs, constructed only at the composition root; no module calls `os.environ`.** ⛔ **`SIGNORA_ENVIRONMENT` is no exception, and a second reader of it elsewhere is the second taxonomy this ruling forbids.**

## 7 · What this ADR deliberately does not decide

⛔ **The member names of the environment vocabulary · which logging library or processor performs redaction · the field-matching strategy · the `Settings` object's owning module · deployment configuration.**

✅ **All of it is Lane A's.** ⚠️ **Lane A proposes the vocabulary in its Slice Handoff; it becomes part of the ratified contract.**
