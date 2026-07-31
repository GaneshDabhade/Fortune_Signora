# 35 — Deterministic identity: one rule, five implementations, no enforcement

**Status:** Analysis. **No repair applied**, per instruction.
**Date:** 2026-07-31 · **Repository position:** `19cec5f`, M10 T132 complete.
**Trigger:** a mutation that survived during T132.

> **Method.** Every claim below is a measured result. Each mutation was applied to a clean tree, the
> **full suite** was run (1608 tests), and the tree restored. No conclusion here rests on reading code.

---

## 1 · What was found

Changing a `uuid5` namespace constant — the value every derived primary key in a module is computed
from — **fails no test in four of five modules.**

The finding is real, and **it is the smaller half of the problem.** Testing the derivations themselves
showed that *most of their inputs are unprotected too*.

### Measured: namespace mutation, full suite each time

| Module | Constant | Result |
|---|---|---|
| Observation Engine | `OBSERVATION_NAMESPACE` | ⚠️ **1608 passed — survives** |
| Business Event Engine | `BUSINESS_EVENT_NAMESPACE` | ⚠️ **1608 passed — survives** |
| Signal Engine | `SIGNAL_NAMESPACE` | ⚠️ **1608 passed — survives** |
| Buying Score Engine | `BUYING_SCORE_NAMESPACE` | ⚠️ **1608 passed — survives** |
| AI Research Engine | `RESEARCH_FINDING_NAMESPACE` | ✅ 1 failed — pinned at T132 |

### Measured: dropping an input from the derivation

| Mutation | Result | What it would mean in production |
|---|---|---|
| `observation_id` drops `provider` | ⚠️ **survives** | Two providers reporting the same change to one attribute collapse into **one** observation |
| `business_event_id` drops `entity_id` | ⚠️ **survives** | Identity stops naming the account it concerns |
| `signal_id` drops `entity_id` | ⚠️ **survives** | Same |
| `buying_score_id` drops `sorted()` | ⚠️ **survives** | **Insertion order becomes a hidden input** — the defect class §2 of CLAUDE.md names outright |
| `buying_score_id` drops `basis_at` | ✅ 2 failed | — |

**Five of ten mutations survive.** The pattern is consistent and diagnostic:

> **The identity tests assert what an id must *equal*. Almost nothing asserts what it must
> *distinguish*.**

Idempotency — *"the same situation computes the same id"* — is tested in two modules and is the
property the docstrings talk about. **Injectivity — *"a different situation computes a different
id"* — is tested in exactly one place** (`test_a_different_workspace_produces_a_different_identity`,
Observation Engine). Every surviving mutation above is an injectivity failure.

---

## 2 · The answers

### 2.1 · How many deterministic identity implementations exist?

**Five `uuid5` implementations**, all in `domain/`, all module-owned:

| Object | Namespace | Keyed on |
|---|---|---|
| `Observation` | `OBSERVATION_NAMESPACE` | workspace · entity · **provider** · attribute · kind · transition key |
| `BusinessEvent` | `BUSINESS_EVENT_NAMESPACE` | workspace · entity · type · **sorted** observation ids |
| `Signal` | `SIGNAL_NAMESPACE` | workspace · entity · signal type · **sorted** event ids |
| `BuyingScore` | `BUYING_SCORE_NAMESPACE` | workspace · entity · model/artifact/profile versions · **sorted** signal ids · `basis_at` |
| `ResearchFinding` | `RESEARCH_FINDING_NAMESPACE` | workspace · subject · derivation@version · **sorted** citation tokens |

**Two further deterministic identities exist that are not `uuid5`**, and both are worth naming because
they bracket the problem:

- **`TECHNOLOGY_NAMESPACE`** (`knowledge_graph/application/relationships.py`) — the string
  `"canonical:technology"`, a canonical-key prefix rather than a hash seed. It is **the only one with
  a test that reads it** (`test_graph_pipeline.py:423`), and that test is self-referential in exactly
  the way T132's was: it compares the constant against itself.
- **The prompt fingerprint** (SHA-256 over prompt text) — **and this one is genuinely enforced.** The
  loader refuses to start when a file disagrees with its recorded fingerprint. It is the repository's
  own proof that an identity constant *can* be enforced rather than described.

### 2.2 · Do they already follow one common rule?

**Yes — an unusually strict one, followed identically five times out of five, and never written down.**

> `uuid5(<MODULE>_NAMESPACE, "<field>|<field>|…|<sorted multi-valued input>")`

with six consistent sub-rules:

1. **One fixed namespace per object type**, declared `Final` in that module's `domain/`.
2. **Workspace identifier first**, always — tenant separation is part of identity, not a filter over it.
3. **A pipe-joined canonical string**, never a tuple, dict or `hash()`.
4. **Multi-valued inputs are sorted**, so insertion order cannot be an input.
5. **Keyed on observed facts, not allocated ids** — except where the referenced id is *itself* derived,
   which is why a score may key on signal ids and an observation may not key on claim ids.
6. **A version participates iff a version change can change the value.** `Signal` deliberately excludes
   its profile version; `BuyingScore` includes three versions; `ResearchFinding` includes
   `derivation_version`. Each docstring gives the reason.

**This is not five conventions that happen to agree. It is one rule, applied five times by different
milestones, each restating its justification in nearly identical words.** That is the signature of a
real invariant — and precisely the kind [34-knowledge-contract.md](34-knowledge-contract.md) exists to
make explicit. Rule 1 of that contract already states *when* identity is content-derived; **it does not
state what a content-derived identity must be made of.**

### 2.3 · Is namespace part of repository identity?

**Yes, unambiguously.** The namespace is an input to every derived primary key, those keys are stored,
and the rows are immutable. It is therefore **not a code constant that happens to live in code** — it
is a value that stored history was computed under, in the same category as an Alembic revision
identifier or an event's `PAYLOAD_VERSION`.

The practical test settles it: change the namespace, and the next pipeline run does not update
existing rows. It **inserts a complete duplicate of the table** under new ids, while every foreign key,
citation and evidence reference in the system continues to point at the old ones. Nothing raises.

### 2.4 · Should namespace be immutable repository state?

**Yes — and it already is; the repository simply has no way to say so.** Five docstrings say *"Never
change it"*, which is documentation asserting a guarantee nothing enforces. That is the exact defect
shape CLAUDE.md §2 names:

> **A guard that cannot fail is not protection — it is documentation pretending to be code.**

Here it is one step worse than a decorative guard, because there is no guard at all: only a comment
claiming a property, in a repository whose stated principle is that **everything committed is read by
someone who has no way to check it against anything but itself.**

### 2.5 · Should changing a namespace always fail tests?

**Yes, and the reason is not that the change is forbidden — it is that it must never be *silent*.**

A namespace could legitimately need to change once: a genuine collision, or a deliberate,
migration-backed re-identification. **Both are decisions with a data migration attached.** What must be
impossible is the accidental case — a copy-paste while adding a sixth module, a merge resolution, a
find-and-replace across UUID literals — where every gate stays green and the damage appears only when
production data already exists.

**A failing test is not a prohibition. It is a demand that the change be deliberate**, in the same
spirit as `tenancy_policy.py`: adding a table is allowed, adding one *without classifying it* is not.

### 2.6 · Is this a Category-1 architectural change?

**No — and it is not Category 3 either.** Against the roadmap's own definitions
([IMPLEMENTATION_ROADMAP.md §5c](../../IMPLEMENTATION_ROADMAP.md)):

| Category | Applies? |
|---|---|
| **1 — Sequencing** | ❌ No milestone moves |
| **2 — Dependency correction** | ❌ The dependency graph is untouched |
| **3 — Architectural change** | ❌ **Nothing about the architecture changes.** No new module, bounded context, responsibility, or derivation |

**It is not a roadmap change at all.** Two things are proposed, and neither alters behaviour: *writing
down a rule the repository already follows*, and *adding tests that fail when it is broken*. The
identity functions themselves are correct today — that is exactly why the mutations were survivable
rather than catastrophic.

**The one thing that would be Category 3** is changing how identity is derived, or introducing a shared
identity abstraction that five modules depend on. §3 recommends against both.

### 2.7 · Would a repository-wide identity verification strategy improve safety?

**Yes, on the evidence — five of ten mutations survived, across four modules and three milestones.**
This is not one module's oversight; it is a gap that has been reproduced by every module that has ever
derived an identity, which is the definition of a systemic one.

**With one important qualification.** *Verification* should be repository-wide; the *implementation*
should not become a shared abstraction. Five identity functions have five different signatures, and a
generic helper that could call all of them would need to know each module's domain types — which would
pull five modules' vocabulary into one place and buy nothing. **The repository already has the right
pattern for this, and it is a registry, not a base class.**

---

## 3 · The smallest repository-consistent solution

**Not proposed for this session** — recorded so the decision is available. Two parts, deliberately
different in shape, because they are different problems.

### Part A — an identity registry, in the shape of `tenancy_policy.py`

`tenancy_policy.py` is the precedent and it is exact. It declares every table's classification in one
file, and `test_every_table_is_classified` fails when a new table appears in neither list — so the
failure mode of forgetting is a **build failure, not a silent exemption**.

The same three tests, one file, no module touched:

1. **Every declared namespace still equals its pinned value.** Changing one fails, naming the module
   and the consequence.
2. **Every namespace in `modules/` is declared** — discovered by scanning for `uuid5(` call sites and
   `*_NAMESPACE` constants. **This is the test that matters**, and the one a per-module pinning test
   would not give: without it, the sixth module repeats the gap, exactly as the fifth did.
3. **No two namespaces collide.** One assertion, currently true.

*Estimated: one file, ~60 lines, no production code changed.*

### Part B — injectivity, per module, **not** shared

Each identity function asserts that **each of its inputs independently changes the id** — the shape
T132 already uses (`test_every_input_independently_changes_identity`), which is what kills the five
surviving mutations in §1.

**Deliberately five small tests rather than one clever one.** Each module's identity has different
inputs with different meanings; a shared parametrisation would have to construct valid domain values
for five modules, which is a shared abstraction over five vocabularies — worse than the duplication it
removes, and against the module-ownership rule.

**And it is the more valuable half.** A wrong namespace re-identifies everything *visibly and at once*;
a missing input in a derivation makes two genuinely different things silently become one — which is
[the M9 lesson restated](30-m9-retrospective.md): *a property a fixture cannot vary is a property the
fixture cannot test.* The Observation Engine's `provider` field is the sharpest case: no test in the
repository derives the same attribute change from two providers, so nothing can see the collision.

### What is deliberately not proposed

- **No shared identity helper or base class.** Identity is owned by the owning module's domain
  ([34](34-knowledge-contract.md), Rule 3). A shared deriver would move it to a substrate.
- **No change to any namespace value.** Every one is correct; only unprotected.
- **No migration.** Nothing about stored data changes.
- **No new principle.** The rule in §2.2 is a *finding*, and belongs in the Knowledge Contract next to
  Rules 1–3 — as generalisation of what already operates, which is that document's stated method.

---

## 4 · Recommendation

**Part A is worth doing before the next module derives an identity** — which, on the current plan, is
T133. It is one file, changes no production code, and the discovery test is what stops the sixth
module from repeating the gap.

**Part B is worth doing per module, opportunistically**, when a milestone next touches each module's
domain — with **one exception worth raising now: `observation_id`'s `provider` field.** Multi-provider
contradiction is a shipped product behaviour that nothing currently protects at the identity level, and
it is the one surviving mutation whose production consequence is data loss rather than confusion.

**Neither blocks T133.** The Research Engine's own identity is already pinned and injectivity-tested;
this is about the four modules built before it.
