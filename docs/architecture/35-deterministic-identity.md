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

> **Correction, 2026-07-31, made before planning any repair.** The table above reports the
> measurements correctly and **reads two of them wrongly.** `business_event_id` and `signal_id`
> dropping `entity_id` are **not correctness gaps**: a business event must cite ≥1 observation and a
> signal must cite ≥1 business event (both refused at construction), and an observation id already
> contains `entity_id`. **The entity is therefore transitively determined by the evidence**, so two
> entities can never share an evidence set and the collision the mutation implies is unreachable.
> Those two inputs are *redundant defence in depth*, not load-bearing — and no test can be written
> that fails when they are removed by observing the system, only by testing the function directly.
> **`observation_id`'s `provider` is genuinely different**, and §2.3 of the plan below traces why.
>
> The corrected count is **three of ten mutations exposing something real**, not five. Recording this
> rather than quietly restating it: the measurement was right, my reading of it was not.

**Five of ten mutations survive.** The pattern is consistent and diagnostic:

> **The identity tests assert what an id must *equal*. Almost nothing asserts what it must
> *distinguish*.**

Idempotency — *"the same situation computes the same id"* — is tested in two modules and is the
property the docstrings talk about. **Injectivity — *"a different situation computes a different
id"* — is tested in exactly one place** (`test_a_different_workspace_produces_a_different_identity`,
Observation Engine).

Every surviving mutation above is an unasserted injectivity property of the **derivation function**.
Per the correction, only three of them are also reachable defects in the **system**: the four
unpinned namespaces, `observation_id`'s `provider`, and `buying_score_id`'s lost `sorted()`.

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

---

# Part II — the engineering plan

**Added 2026-07-31**, converting the findings above into scheduled work. Written before T133; no
repair applied in the same session.

## 1 · The four questions, answered

### Finding 1 — namespace mutations survive. Registry, or discovery tests?

**The question contains a false alternative: a discovery test cannot exist without a registry.**
Discovery finds the namespaces that *are* in the tree; to fail, it must compare them against a
declared list of the ones that *should* be. The registry is what discovery discovers against.

**So: one file holding both, and the discovery half is the valuable half.** Pinning without discovery
protects exactly the modules someone remembered — which is how four of five came to be unprotected in
the first place. Discovery makes forgetting a build failure, which is the whole design of
`tenancy_policy.py`.

**One objection worth answering.** Pinning a constant in a test duplicates it, and *truth has exactly
one authoritative representation*. That principle is not violated here: the second copy exists **only
to detect divergence** and asserts nothing else — the same shape as `tenancy_policy.py` restating
table names that also exist in migrations, and as the prompt loader's recorded fingerprint. A
characterisation test is the one legitimate duplicate.

| | |
|---|---|
| Implementation change | ❌ None |
| Stronger tests | ✅ Yes — one file, three tests |
| Architectural document | ⚠️ One rule appended to the Knowledge Contract |
| Roadmap task | ✅ Small, named |
| Can wait until after M10 | ✅ **Yes** |

### Finding 2 — should stability, idempotency and injectivity be a repository-wide requirement?

**Yes, as a stated testing standard — and the three are genuinely distinct**, which is why naming all
three is worth more than naming one:

| Property | Question it answers | Failure mode if unasserted |
|---|---|---|
| **Stability** | Does the same input produce the same id **across processes and runs**? | An unordered set, a `dict`, or `hash()` in the canonical string — deterministic within a run, different after a restart. **`PYTHONHASHSEED` is the classic version of this** |
| **Idempotency** | Does recomputation **insert nothing**? | Replay duplicates the table |
| **Injectivity** | Does each declared input **independently change** the id? | Two different things silently become one |

Currently: stability is implied by `uuid5` and never asserted · idempotency is tested in **two of five**
modules · injectivity in **one place in the repository**.

**With the correction above applied, the standard's justification changes and should be stated
honestly.** Injectivity is a property of the *derivation function*, not always of the pipeline — for
`business_event_id` and `signal_id` the entity is transitively determined, so the test asserts *"this
input is deliberately part of the key"* rather than *"otherwise data collides"*. That is still worth
asserting, because it converts accidental redundancy into recorded intent. It is simply not urgent.

| | |
|---|---|
| Implementation change | ❌ None |
| Stronger tests | ✅ Yes — five small per-module sets |
| Architectural document | ✅ A testing standard, stated once |
| Roadmap task | ✅ Yes |
| Can wait until after M10 | ✅ **Yes** |

### Finding 3 — is `provider` genuinely required for correctness?

**Yes. Traced end to end through the code, not inferred — and it is the only finding here with a
product-visible consequence.**

1. `observation_id` keys on `workspace · entity · provider · attribute · kind · transition key`.
   **Nothing else in that key encodes the provider** — the transition key is values and timestamps.
2. Two providers reporting the same value change over the same period produce the **same** transition
   key. Without `provider`, they collapse into **one** observation row.
3. Detection rules run over **one provider's series at a time**, by contract:
   *"The series is always a single provider's, so no rule can combine two providers' values into a
   synthetic truth. Agreement between providers is counted afterwards."*
4. `Detection.providers` is `{observation.provider for observation in evidence}`, and the use case
   passes it straight to `BusinessEvent.corroborating_providers`.
5. `is_corroborated` reads that set. **M9's `SupportBasis` derives from *"≥2 distinct corroborating
   providers"*.**

**So a collapsed observation does not corrupt a value — it deletes a corroborating provider.** Two
providers independently agreeing would be reported to a customer as `LIMITED` support rather than
`CORROBORATED`. That inverts M4's ratified contract, *agreement is evidence*, and it does so silently:
every citation still resolves, every number is still right, and the conclusion is simply
under-supported.

**Should protecting it be a mandatory repository invariant?** **Yes — but as the specific property,
not as a rule about identity fields.** The invariant worth stating is *"corroboration is never
under-reported"*, asserted by deriving the same change from two providers and requiring two
observations and two corroborating providers. A rule phrased as *"provider must appear in
`observation_id`"* would protect today's implementation rather than the property, and would pass while
step 3, 4 or 5 broke instead.

**No test in the repository derives one attribute change from two providers.** That is why the
mutation survives — the M9 lesson exactly: *a property a fixture cannot vary is a property the fixture
cannot test.*

| | |
|---|---|
| Implementation change | ❌ None — the code is correct |
| Stronger tests | ✅ Yes — **one test, one module** |
| Architectural document | ⚠️ Worth a line in `24-business-event-engine.md` |
| Roadmap task | ✅ Yes, and the **only one I would not defer** |
| Can wait until after M10 | ⚠️ **It can, but it should not.** It is roughly twenty lines and it guards shipped behaviour |

### Finding 4 — would a shared `uuid5` helper improve correctness?

**No. It would move the safe part and leave the dangerous part where it is.**

What a helper could centralise is *canonical joining and sorting* — three lines, correct in all five
implementations, and not the source of a single finding here. What it cannot centralise is **which
inputs belong in the key**, which is the whole of the risk and is irreducibly domain knowledge: why
`Signal` excludes its profile version, why `BuyingScore` includes three versions, why an observation
may not key on claim ids. **A helper would make five modules import a shared derivation while every
decision that could be wrong stayed exactly where it is.**

It also breaks two stated rules. *Identity is owned by the owning module's `domain/`*
([34](34-knowledge-contract.md), Rule 3) — a shared deriver relocates it to a substrate. And
`signora_platform/` is frozen (§20a); *"a module finding the platform inconvenient is not a defect."*

**The honest counter-argument, recorded:** five modules repeat a pipe-join and a `sorted()`, and one
of them (`buying_score_id`) already survived losing its `sorted()`. That is real duplication. But the
answer to *"the same mistake is possible in five places"* is **the shared standard proposed in Finding
2 — a test every implementation must pass — not a shared implementation.** Sameness of *rule* does not
require sameness of *code*, and this repository has made that call before: three modules each write
their own repository rather than sharing a generic one.

**Verdict: no shared helper. The registry (Finding 1) and the standard (Finding 2) address the same
risk without relocating ownership.**

## 2 · The plan

### Immediate — before or alongside T133

**Nothing is required.** The AI Research Engine's own identity is already pinned and
injectivity-tested, T133 creates no new namespace, and none of the findings is a defect in shipped
behaviour — they are unasserted properties of code that is correct.

**One item recommended immediately after T133:** Finding 3's two-provider test. It is the only finding
with a product-visible failure mode, it is one test in one module, and every milestone that ships
before it makes the eventual regression harder to attribute.

### After M10

| Work | Size | Why it waits |
|---|---|---|
| Identity registry + discovery test (Finding 1) | ~1 file | No new namespace arrives until a sixth derived-identity module does, and none is planned before M11 |
| Injectivity sets for the four earlier modules (Finding 2) | 4 small tests | Records intent; guards no reachable defect, per the correction |
| Idempotency for the three modules lacking it | 3 small tests | Same |

### Roadmap additions

Two tasks, deliberately **not** a milestone. Both are repository maintenance, and neither changes
architecture — no roadmap category applies ([§5c](../../IMPLEMENTATION_ROADMAP.md)).

- **`T-ID1` — Corroboration is never under-reported.** One Observation Engine test deriving one
  attribute change from two providers, asserting two observations and two corroborating providers.
  *Recommended immediately after T133.*
- **`T-ID2` — Deterministic identity registry and testing standard.** The registry file, the three
  registry tests, and the stability/idempotency/injectivity sets for the four pre-M10 modules.
  *After M10.*

### Architectural documentation

1. **[34-knowledge-contract.md](34-knowledge-contract.md) — one new rule**, alongside Rules 1–3, which
   say *when* identity is content-derived but never what one is made of. Proposed wording:

   > **RULE 24 — A content-derived identity is `uuid5` over a fixed, module-owned namespace and a
   > canonical string of its declared inputs, with the workspace first and every multi-valued input
   > sorted. The namespace is repository state: it may change only with a migration, and never
   > silently.**

   Consistent with that document's method — generalising what already operates five times, not
   inventing a sixth thing.

2. **[24-business-event-engine.md](24-business-event-engine.md)** — a line recording that
   corroboration depends on per-provider observation identity, so the chain from
   `observation_id` to `SupportBasis` is discoverable from either end.

3. **This document** — already corrected above.

### Repository-wide testing standards that should now exist

One addition to **CLAUDE.md §11**, proposed for ratification rather than applied, since that file is
the constitution:

> **Every deterministic identity proves three properties: stability** (the same inputs produce the
> same id across processes, so no unordered or hash-seeded value enters the canonical string),
> **idempotency** (recomputation inserts nothing), and **injectivity** (each declared input
> independently changes the id). **A namespace constant is pinned to its literal value by a test.**
> These are asserted per module, never through a shared helper — identity belongs to the module that
> owns the object.

## 3 · Is any of this Category 1?

**No.** No milestone moves, no dependency edge changes, no architecture changes. The identity
functions are correct today; what is missing is assertion and a written rule. **T133 proceeds.**
