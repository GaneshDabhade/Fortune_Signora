# Repository Architecture — Two Proposals

> Status: **PROPOSED — awaiting approval.** Nothing implemented.
> Scope: the architecture of the *repository*, not of the product.
> Date: 2026-07-30

**The filename is itself finding #1.** There is no correct place in this repository for a document about the repository — not `docs/architecture/`, which is the product's architecture; not the root, which is already crowded; not `adr/`, since this is a proposal rather than a decision. It went to `docs/` because nothing better exists. On approval it moves to its permanent home.

---

# Part 1 — Documentation Organization

## Reconstruction

| | |
|---|---|
| Tracked markdown documents | **66** |
| Total lines | **13,360** |
| Inter-document markdown links | **848** |
| Locations | root (7) · `docs/` (1) · `docs/architecture/` (30) · `docs/architecture/adr/` (28) |

Link density is the governing constraint. At 848 relative links across 66 files, **any move is a mechanical edit of dozens to hundreds of paths**, and there is currently nothing that would tell us if one broke.

## What is actually wrong

Four findings, in descending order of how much they cost.

### 1 — Nothing verifies that 848 links resolve

There is no check. A moved file, a renamed heading, a typo in a relative path — all silently produce a dead link, and dead links are discovered by a reader who then stops trusting the next one.

This is the largest gap in the documentation set, it exists *today* independent of any reorganization, and under the principle ratified yesterday — **the repository itself should always tell the truth** — a broken cross-reference is the same class of defect as a workflow that looks live. It is also the only finding here that is a *defect* rather than a matter of taste.

### 2 — The root is a landing zone

Seven markdown files sit at the repository root. Exactly two have to be there: `README.md` (GitHub renders it) and `CLAUDE.md` (the tool loads it from there). The other five — `PROJECT_STATUS.md`, `IMPLEMENTATION_ROADMAP.md`, `PRODUCT_ROADMAP.md`, `AI_MATURITY_ROADMAP.md`, `PRODUCT_DIFFERENTIATORS.md` — are planning documents that ended up at root because root was where the first one went.

The cost is real: someone opening this repository sees seven documents of equal apparent weight and no indication that two of them govern everything and five are planning artifacts.

### 3 — `docs/architecture/` holds three different kinds of document under one numbering scheme

| Files | What they are | Lifecycle |
|---|---|---|
| `01`–`21` | The architecture itself | Living, ratified, revised in place |
| `22`–`28` | Per-module design records | Written once per milestone, marked *as built*, then frozen |
| `ARCHITECTURE_VALIDATION_M1_2.md` | A dated validation record | Historical, never revised |
| `provider-qualification.md` | Reference data | Updated as providers qualify |

A single `01…28` sequence implies one document set read in order. It is not: `21-intelligence-pipeline.md` is the *first* thing a new reader should open, and `22`–`28` are milestone artifacts that will number ~40 by M15.

### 4 — There is no developer documentation, and Local-First just made that load-bearing

There is no setup guide, no "how to run the gates" document, no environment prerequisites beyond a table buried in `SESSION_HANDOFF.md` §1. That was survivable while CI encoded the setup in three workflow files that anyone could read. **ADR-0027 removed that.** The developer's machine is now the only place verification happens, and the instructions for standing one up exist nowhere.

This is the highest-value *new* document in this proposal, and it is a consequence of a decision made yesterday.

## Recommendation — and where I disagree with the brief

The brief anticipated seven directories: Architecture · ADRs · Milestones · Project Management · Developer Documentation · Validation · Reference. **I recommend four, and I want to argue against three of the seven.**

```
README.md                     root — GitHub convention
CLAUDE.md                     root — the tool loads it from here

docs/
  README.md                   the map: what exists, and which to read first
  architecture/               01–21, adr/, provider-qualification.md  ← UNCHANGED PATHS
    adr/                                                             ← UNCHANGED PATHS
    22-…-28-…                                                        ← UNCHANGED PATHS
  project/                    PROJECT_STATUS · SESSION_HANDOFF · the four roadmaps
                              · PRODUCT_DIFFERENTIATORS · ARCHITECTURE_VALIDATION_M1_2
  developing/                 setup · local verification · working in this repository
```

### Against a `milestones/` directory — the strongest objection

Moving `22`–`28` out of `architecture/` is the change that looks most obviously right and is the one I recommend against.

Moving them **coherently** requires renumbering: a directory containing `22`–`28` and nothing else is a sequence with a missing start, and the next reader will look for `01`–`21` inside it. But renumbering is destructive in a way this project has explicitly refused elsewhere — those numbers are cited in `01-overview.md`'s map, in `SESSION_HANDOFF.md` §6, in `PROJECT_STATUS.md`, in seven commit messages, and in each other. **Commit messages cannot be updated.** Renaming `26-buying-score-engine.md` makes `ed7f9e9`'s message point at nothing.

So: moving requires renumbering; renumbering falsifies existing references; therefore **do not move them.** Make the distinction visible instead — a short `docs/architecture/README.md` stating that `01`–`21` are the living architecture and `22`+ are per-milestone design records — which costs one file and breaks nothing.

If the ~40-files-by-M15 concern later becomes real, the honest fix at that point is a `records/` subdirectory *with a redirect stub left at each old path*. Cheap then, unnecessary now.

### Against `validation/` and `reference/`

One document each. **A directory holding one file is a directory that stays at one file**, and it makes the tree look more organized than the content actually is. `ARCHITECTURE_VALIDATION_M1_2.md` is a milestone artifact and belongs with the project records; `provider-qualification.md` is architecture reference and is already linked from `20-provider-simulation.md`, where it belongs.

This is the same YAGNI reasoning the roadmap applies to ports: structure arrives with its second occupant, not in anticipation of one.

### What I do recommend, and why it is safe

The recommendation moves **7 files and 0 directories**, and leaves the 58 highest-linked documents on their existing paths. `docs/architecture/` and `docs/architecture/adr/` — the two most-referenced paths in the repository (`12-scalability.md` alone is linked 38 times) — do not move at all.

## Sequencing — the test comes first

1. **Build the link-integrity check and prove it passes on today's layout.** It must find nothing, because nothing is currently broken. A checker introduced *with* a move cannot distinguish "the move broke this" from "the checker is wrong."
2. **Move the seven files**, rewriting affected links mechanically (~150 edits, all relative-path arithmetic).
3. **Re-run the check.** A green run is the proof that nothing broke — and is the reason this reorganization is safe at all.
4. **Write `docs/README.md` and `docs/developing/`.**

The check itself: a test that parses every tracked `.md`, resolves every relative link (and every `#anchor` against the target's headings), and fails naming each unresolved one. It is a **local gate**, run with the suite, per ADR-0027.

## Trade-offs

| | We gain | We give up |
|---|---|---|
| Move 5 planning docs off root | A root that says *"read the README, then CLAUDE.md"* | Muscle memory; `PROJECT_STATUS.md` is no longer at a path people have typed for weeks |
| Link-integrity test | The repository proves its own references — the truth principle applied to documentation | One more thing that can fail the build (correctly) |
| `docs/developing/` | Setup instructions exist at all, now that they are the only ones | A document that must be maintained as tooling changes |
| Keeping `architecture/` intact | Zero churn on the highest-value set; every commit message stays accurate | The `01`–`28` sequence keeps mixing two lifecycles, mitigated by a README |

## Effort

~1–1.5 ew. The link checker is the only real work; the moves are mechanical once it exists.

---

# Part 2 — Business Scenario Tests

## Reconstruction — the harness already exists

This is the finding that should shape the whole design.

**`backend/tests/pipeline.py` (426 lines) is already a full pipeline composition root.** Its own docstring:

> *"Each stage is driven by the **events actually published to the outbox**, read back the way the relay reads them. Calling handlers with hand-built envelopes would prove the handlers work while proving nothing about the contract between the modules."*

It exposes `normalize_all` · `resolve_all` · `observe_all` · `detect_all` · `signal_all` · `score_all` · `sweep_stale` · `set_opportunity_policy` · `qualify_all`, plus a read-port accessor per stage. Every module's `test_<module>_pipeline.py` already drives the real pipeline through it, and `make smoke` stages 14b–14h re-run those same suites against the live production stack.

So the honest statement of the gap is narrower and more interesting than "we have no end-to-end tests":

> **The machinery to run a complete customer workflow exists and is proven. What does not exist is a set of assertions written in business language, owned as a specification, that no milestone may break.**

Today every assertion belongs to a module and is phrased in that module's vocabulary. Nothing in the repository says *"a hiring surge at a company this workspace cares about ends up as an opportunity a seller can act on, with an explanation naming the hiring surge."* That sentence is the product, and nothing asserts it.

**Recommendation: do not build a second harness.** Build the assertion layer on `tests/pipeline.py`.

## Existing test layers, and where this one fits

| Layer | Question it answers | Vocabulary |
|---|---|---|
| Unit | Is this function correct? | Code |
| Module pipeline (`test_*_pipeline.py`) | Does this stage produce the right output from real upstream events? | The module's domain |
| Integration | Do the platform mechanics work against a real database? | Infrastructure |
| Security Invariants | Does a guarantee the architecture depends on still hold? | Architectural |
| `make smoke` | Does the deployed stack work, end to end, from production images? | Operational |
| **Business Scenario** ← new | **Can Signora perform this complete customer workflow?** | **The customer's** |

The distinction that justifies a sixth layer: every existing layer is phrased in *our* language. A scenario is phrased in the customer's, and it is the only layer that would notice if all eight modules passed their own tests while the product stopped working.

## Design

### Location and shape

```
backend/tests/scenarios/
  conftest.py                                    scenario fixtures, controllable clock
  test_hiring_surge_becomes_a_tracked_opportunity.py
  test_conflicting_evidence_stays_contested.py
  test_an_expiring_score_does_not_close_an_opportunity.py
```

One file per scenario, named as the sentence it proves. Each reads as a narrative — `given_…` (evidence arrives from providers) · the pipeline runs · `then_…` (business outcomes).

### The rule that keeps them a specification

> **A scenario may read only through `public/` read ports.** Never a repository, never a table, never a domain object, never a module's `application/` layer.

This is the whole discipline. A scenario that reaches into a repository has become a slow integration test, and within a year it will be asserting implementation details that make refactoring expensive — the exact decay this project has avoided everywhere else.

It is also **machine-enforceable**, and should be: an import-linter contract forbidding `tests.scenarios` from importing any module's `domain`, `application`, or `infrastructure`. If a business outcome cannot be observed through `public/`, that is a finding — it means the capability is not actually exposed to a customer, and the scenario has discovered a real gap rather than needing an exemption.

### Assert outcomes, not counts

Not *"three signals were generated."* That is implementation.

> The account appears in what a seller should track · the opportunity's explanation names the hiring surge · the number that qualified it traces to the provider payload that caused it · a human, and only a human, can progress it.

### Scenarios author their own evidence

Each scenario states its own preconditions explicitly rather than inheriting a shared fixture. That is better specification practice — a specification that says *"given a company that raised a Series B six weeks ago"* is readable; one that says *"given the baseline scenario"* is not — and it has a useful side effect: **it decouples the suite from the four scheduled M2.0 simulation items.** Those remain needed for *demonstrations*, which must look real; a scenario needs only to be precise.

### Time must be controllable

Signal expiry and buying-score decay are wall-clock dependent. `signora_platform/simulation/clock.py` already exists and scenarios must use it exclusively. A scenario reading the system clock passes in January and fails in March — and the person who inherits that failure will delete the scenario, which is how a regression suite dies.

### When AI enters, in M8

The brief's example chain ends in *AI Narration → user-visible explanation*. When that exists, a scenario must assert **only the deterministic half**: that the narration is grounded, that every claim carries a resolving citation, and that the hiring surge is among the facts cited. **Never the prose.** This falls straight out of M8's two-tier guarantee — deterministic correctness is assertable, probabilistic quality belongs in the evaluation harness — and it is the reason the scenario suite and `make eval` stay separate things.

## The first three, and why not eleven

The brief lists eleven candidate scenarios. I recommend **three**, chosen because they exercise disjoint machinery:

| Scenario | What only it covers |
|---|---|
| **Hiring surge → tracked opportunity** | The golden path, all eight stages, the full explanation chain intact |
| **Conflicting evidence stays contested** | Contradiction preserved rather than netted; a contested account still qualifies |
| **An expiring score does not close an opportunity** | The time dimension: step decay, staleness sweep, and *opportunities outlive their score* |

Funding, technology adoption, leadership change, expansion and contraction are the *same* path with a different business event type — already covered by the taxonomy's own tests, and eight near-identical scenarios would be eight files to maintain for one file's worth of coverage. They arrive when one of them stops being a variation.

## When they run — with one addition to the brief

Agreed: **not on every commit, not in `make smoke`.** They are `make scenarios`, marked `scenario`, and deselected by default so a bare `pytest` never picks them up.

The brief proposes: after milestone completion · before milestone acceptance · before releases. I recommend one addition:

> **Also at the *start* of a milestone**, as a baseline.

Run only at the end, a red scenario means *"something in the last three weeks broke this."* Run at both ends, it means *"this milestone broke it"* — and the difference between those two sentences is usually a day of bisecting. The run is cheap and the attribution is the whole value.

So: **milestone start (baseline) · milestone acceptance (Definition of Done) · before any release.**

## What this becomes

Every milestone adds scenarios and breaks none. When M9 lands, the M8 scenarios still pass; when M10 lands, all of them do. The suite becomes the executable specification — and, unlike a written one, it cannot drift from the product without failing.

## Risks

| Risk | Mitigation |
|---|---|
| **Scenarios decay into integration tests.** The most likely failure, and it happens one convenient assertion at a time. | The `public/`-only rule, enforced by an import-linter contract rather than by review. |
| **They become slow enough to be skipped.** | Three scenarios, not eleven. If the suite exceeds a few minutes, that is a signal to prune, not to parallelise. |
| **A scenario is written to match current behaviour rather than intended behaviour.** | Each scenario names the architectural contract it protects, from `SESSION_HANDOFF.md` §2. A scenario that protects nothing named there is describing an accident. |
| **Wall-clock flakiness.** | Controllable clock, mandatory. |
| **The suite drifts from the demonstrations in `make smoke`.** | Deliberate overlap is intended, per CLAUDE.md §11. Smoke proves the *stack* works; scenarios prove the *product* does. |

## Effort

~3–5 ew for the three scenarios, the marker, the `make scenarios` target, and the import-linter contract. Lower than it would otherwise be, entirely because `tests/pipeline.py` already exists.

---

# Sequencing — my recommendation

| | When | Why |
|---|---|---|
| **Link-integrity test** | Now, before anything moves | It is a defect fix, not a reorganization, and it is what makes step 2 safe |
| **Documentation reorganization** | Now | Cheap, low-risk, and it improves every session that follows |
| **`docs/developing/`** | Now | ADR-0027 made it load-bearing yesterday |
| **The three scenarios** | **Now, before M8** | ← the judgement call |
| **AI narration assertions** | Inside M8, extending the first scenario | The scenario exists to be extended |

**Why scenarios before M8 rather than after.** The suite's entire purpose is to be the thing a new milestone must not break. Building it *after* M8 means M8 — the milestone that introduces the first non-deterministic component into a deterministic pipeline — is the one milestone that ships without the net. The harness already exists, so the cost of doing it first is small, and the alternative buys nothing.

The counter-argument, recorded: it delays M8 by roughly a week, and the eight built stages already have per-module pipeline tests plus twenty-one smoke stages behind them, so the net is thinner than it looks rather than absent. If M8 should start immediately, the honest fallback is to write the three scenarios as the **first task of M8**, before the AI work begins — not after it.

---

## Open questions requiring a ruling

| # | Question | Recommendation |
|---|---|---|
| 1 | Four directories or the seven in the brief? | **Four.** `milestones/` requires renumbering, which falsifies commit messages; `validation/` and `reference/` would each hold one file. |
| 2 | Do `22`–`28` move? | **No.** Make the distinction visible with a README instead. |
| 3 | Scenarios before M8, or as M8's first task? | **Before**, so M8 ships with a net. Either is defensible; shipping M8 without one is not. |
| 4 | Three scenarios or eleven? | **Three**, chosen for disjoint machinery. The rest arrive when they stop being variations. |
| 5 | Is the `public/`-only rule enforced by machine? | **Yes** — an import-linter contract. Every other boundary in this repository is machine-enforced; this one is more fragile than most. |

*Nothing in this document has been implemented.*
