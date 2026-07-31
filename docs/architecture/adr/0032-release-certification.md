# ADR-0032 — Release Certification: the evidence a version carries, not a sixth kind of test

> Status: **PROPOSED — 2026-07-31.** Recommended for ratification, with one scope change from the request that produced it.
> Deciders: Product Owner · Architecture Review Board
> Supersedes: nothing. Amends: nothing. Extends: [ADR-0027](0027-local-first-development.md) (local-first), [20-provider-simulation.md](../20-provider-simulation.md) (progressive assertion), CLAUDE.md §19 (Milestone Definition of Done).

## Context

The request: *"a release should represent substantially more than **all tests passed**."* That is right, and the gap it names is real. The mechanism proposed for it — a new end-to-end test tier — is not the cheapest way to close it, and two pieces of repository evidence say so.

### What the repository already proves

| Gate | Question it answers | Speaks for |
|---|---|---|
| Unit tests | Does this component do what it says? | the component |
| Integration tests | Does it do it against a real database and a real event bus? | the module |
| **`make smoke`** | Does the **built production image** start, migrate, authenticate, isolate tenants, relay events and run the pipeline? | the deployable artifact |
| Security Invariants (321) | Do the architectural guarantees still hold, each proven by removal? | the architecture |
| Mutation testing | Are the tests load-bearing, or decoration? | the test suite |
| Prompt evaluations | Can this model satisfy Signora's contract behind this prompt? | the model |
| import-linter (29) · mypy strict | Do the boundaries and types hold? | the structure |

**`make smoke` is already a production-conditions gate**, not a health check: 23 stages against the real `docker-compose.prod.yml` stack, including image hygiene, separate migration and runtime identities, a JWT minted by the real frontend path, RLS enforcement, and the pipeline end to end. A design that treats it as "just smoke tests" would be designing around something that already exists.

### Gap 1 — the scenario framework is ratified and under-built

[20-provider-simulation.md](../20-provider-simulation.md) already specifies exactly what is being asked for, under the heading **Progressive assertion**:

> *"Scenario assertions **extend at each milestone; regression datasets are never recreated.** A scenario authored in M2.0 accumulates layers as the pipeline is built, so **by M11 each of the ten scenarios is a full end-to-end regression test**."*

Ten scenarios, deepening per milestone, with a **seeded fault injector** that raises failures *"through the same error surface a real provider failure would take"* — which is the design for the failure-handling and recovery categories the request lists.

**One scenario exists.** `signora_platform/simulation/scenarios/baseline@1.json`, and it is what every golden dataset and every pipeline test is seeded from. The framework is built; the catalogue is at one tenth.

> **The correct response to "we need realistic customer workflows" is to build the nine missing scenarios in the framework that already owns them — not to introduce a second scenario concept beside it.** A parallel system would split the fault injector, the determinism guarantee and the provenance fields across two owners.

### Gap 2 — every gate is ephemeral, and this has already cost us

Each gate above passes in a terminal and **leaves nothing behind**. Nothing in the repository records that commit *X* satisfied guarantee *Y* on date *Z*.

This is not hypothetical. M9.5 Step A found the same defect one level down: `release.py` was written so that failing evaluations are recorded too, yet `--record` was opt-in and the harness recorder was in memory, so **ADR-0031's entire evidence base existed only as prose in documents and commit messages** until it was deliberately re-measured. A prompt that had been measured and found wanting was indistinguishable, to any tool, from one nobody had ever run.

The same is true today of the platform as a whole. `PROJECT_STATUS.md` states *"`make smoke` ✅ 23 stages, 106s"* — a hand-copied number, in a file a human edits, describing a run nobody can point to. **The dashboard is a claim, not a measurement.**

And the failure mode is demonstrated, not theoretical: during M9.5 Step A I verified with `-m "not integration"`, which silently deselected the suite that step had invalidated, and shipped a broken test. A green terminal is not evidence of what was green.

### What is therefore actually missing

Not a test tier. Three things:

1. **Scenario breadth** — nine scenarios the architecture already commissioned, including the failure and recovery narratives nothing exercises end to end today.
2. **A durable, dated record** that a specific commit satisfied specific guarantees under specific conditions.
3. **A definition of the conditions**, so that a record means something later: which rendering protocol, which prompt releases, which migration head, which image.

## The challenge to the framing

**There is no release.** [ADR-0027](0027-local-first-development.md) removed release automation, publishing, tagging and deployment; cloud infrastructure is deferred to M14.5. Making certification a *release* gate today gates an event that does not occur, and ADR-0027 states the ordering it would violate: **architecture first · implementation second · automation third · deployment last**, with *"automate for demonstrated need, never anticipated need."*

The gate that genuinely exists is the **Milestone Definition of Done** (CLAUDE.md §19).

**So certification should bind to the milestone now and to the release at M14.5** — one concept, two attachment points, and the second costs nothing to add once releases exist.

### The reframing

> **The first-class concept is the Certification Record — the evidence a version carries — not the suite that produces it.**

This is the pattern the repository already proved with prompts, and it should be reused rather than reinvented:

| Prompts (shipped, M8–M9.5) | Platform (proposed) |
|---|---|
| `Evaluation` — a recorded measurement, facts only, no verdict | `CertificationRun` — one scenario's recorded outcome |
| `passed` — **derived** from the facts | `satisfied` — derived from the outcomes |
| `earns_release` — derived, **and bound to the conditions** (model, protocol) | `is_certified` — derived, and bound to the conditions (commit, protocol, prompt releases, migration head) |
| manifest — append-only, refusals recorded too | certification manifest — append-only, failed runs recorded too |
| *"nothing in the system can mark a prompt released"* | **nothing can mark a version certified** |

`PromptVersion` deliberately has no `status` field, because *"a declared status could say released while no evaluation supported it — a field that can lie about the thing beside it."* A `CERTIFIED.md` a human edits would be exactly that field, at repository scale.

## Decision

Adopt **Release Certification** as a first-class concept, with three parts:

**1. The Certification Record** — an append-only, machine-written manifest plus a rendered report, holding one entry per certification run: the commit, the date, every scenario's outcome, and the conditions in force. Certification is **derived** from it and can never be declared.

**2. The scenarios live in the Provider Simulation Framework**, extending the ratified catalogue of ten. Certification *executes* them and *records* the outcome; it does not own a second scenario concept.

**3. `make certify` is its own command**, orchestrating the production stack, and is **not** part of `pytest`.

### Where it lives

```
backend/tests/certification/          # the scenarios, as pytest cases
  conftest.py                         #   the certified environment fixture
  test_research_lifecycle.py          #   one file per certification area
  test_failure_and_recovery.py
  test_determinism.py
  reporting.py                        #   the plugin that writes the record
backend/certification/                # the durable artifacts
  manifest.json                       #   append-only; failed runs recorded too
  reports/<commit>.md                 #   the rendered report per run
infra/certify.sh                      # stack up → run → record → tear down
```

**`tests/certification/` sits beside `tests/security_invariants/`, and for the same reason.** Both are repository-level suites asserting properties no single module owns; neither can live inside a module without a module claiming authority over the platform. The precedent is established and the shape is proven.

**The record is committed.** It is repository state, like the prompt manifests, and for the same reason: *the repository should always tell the truth*, and a record only a CI server holds is one a reader cannot check.

### Responsibilities, stated so no layer duplicates another

| Layer | Asks | Speaks for | Leaves behind |
|---|---|---|---|
| Unit / integration | Is this component correct? | the component | nothing |
| Security Invariants | Does this guarantee still hold? | the architecture | nothing |
| Mutation testing | Are those tests load-bearing? | the test suite | a finding |
| Prompt evaluation | Can this model satisfy the contract? | the model | **an `Evaluation`** |
| `make smoke` | Does the built artifact deploy and function? | the deployable | nothing |
| **`make certify`** | **Does a customer's whole journey produce the right business outcome — including when things go wrong?** | **the customer** | **a Certification Record** |

Two axes distinguish certification from everything above it: **it speaks for the customer rather than the component**, and **it is the only gate that leaves durable evidence.**

**Certification does not re-assert what a lower layer proves.** It must not re-test grounding rules, boundary contracts or citation parsing — those are unit tests and Security Invariants, and duplicating them buys a slower suite and two places to update. Where a guarantee is already proven elsewhere, certification **cites the result in its record** rather than re-deriving it.

## Consequences

### `make certify`, not `pytest -m certification`

Four reasons, one of which is precedent: **`make eval` is already deliberately excluded from `make test`**, because a gate that needs a GPU is a gate people learn to skip.

- It needs the production stack up and torn down — orchestration, not collection.
- It must **write a record**, and a test runner that mutates repository state on every run is a bad default.
- Folding it into `pytest` means it runs on every save until someone adds `-m "not certification"` — and then it never runs.
- It must capture provenance the test process does not have: image digests, migration head, `git rev-parse HEAD`, dirty-tree status.

**But pytest remains the executor.** `certify.sh` brings up the stack, invokes `pytest tests/certification` with a reporting plugin, and writes the record. No second test framework — ADR-0023 is not reopened.

### Definition of "Release Certified"

A version is **Release Certified** when a Certification Record exists whose:

- **commit** is the exact tree certified, and the tree was **clean** — a certification of uncommitted work certifies nothing anyone can retrieve;
- **every scenario in the catalogue** ran and satisfied its business outcome, with skips counted as failures;
- **conditions** match the ones now in force — rendering protocol version, every prompt release the pipeline requests, migration head, and image digest;
- **lower gates are recorded as passing** at that commit: `pytest --cov`, `mypy --strict`, `lint-imports`, Security Invariants, `make smoke`.

**Certification is derived from those facts, never stored.** A record whose conditions have since moved reads as *awaiting re-certification* — the same derivation, and the same wording, that `earns_release` already uses for prompts. **A protocol bump or a prompt re-release therefore invalidates a certification automatically**, exactly as Step C withdrew three prompt releases without anyone editing a manifest.

### Reporting

The record is data; the report is rendered from it. The report answers, at a glance: *what was certified · under what conditions · which scenarios ran · what failed · what is no longer current*. `PROJECT_STATUS.md` stops hand-copying gate numbers and **cites the latest record instead** — closing the "dashboard is a claim" gap directly.

### It stays local

`certify.sh` is a local command, like `smoke.sh`. **No CI, no scheduled run, no remote execution** — ADR-0027 is untouched, and nothing here is a step toward reopening it.

### What this does not solve

**Certification measures a system with zero production traffic.** It is evidence of discipline, not of field reliability, and the record should say so in the same words `PROJECT_STATUS.md` already uses. A green certification means the workflows we thought to write still work — never that the platform is correct.

## Priority — ordered by what would fail undetected today

Deliberately **not** the order the request listed, because several categories are already well covered and re-testing them would add runtime and no evidence.

| # | Area | Why here | Marginal value |
|---|---|---|---|
| **1** | **Failure and recovery** — worker crash mid-pipeline, restart, resume, duplicate suppression, exactly-once completion | Nothing exercises these end to end. The fault injector exists and is unused by any scenario. **This is the whole of the gap** | **highest** |
| **2** | **Determinism across runs** — same scenario twice yields identical finding identities, identical derivations, no duplicate rows | Asserted in unit tests over pure functions; never across a full run against a real database | **high** |
| **3** | **The nine missing scenarios** — displacement, hiring surge, quiet account, contested account, thin evidence | The architecture commissioned ten; one exists, so every golden dataset has *variety 1*, already recorded as the main caveat on M8's passing run | **high** |
| **4** | **Research lifecycle, happy path** | Already proven by smoke stage 14k and `test_pipeline.py` | low — **fold into 1–3 rather than writing separately** |
| **5** | **Prompt infrastructure and protocol compatibility** | M9.5 made this structural and enforced at the point of use | **none as scenarios** — record them as *conditions* in the record |
| **6** | **Grounding rules** | Unit-tested exhaustively, mutation-verified | **none** — do not duplicate |
| **7** | **Architectural guarantees** | The 321 Security Invariants own these, permanently | **none** — cite the count in the record |

**Items 5–7 are the ones worth arguing about**, and the argument is the same each time: a certification suite that re-asserts what a faster gate already proves trains people to read a long green log without looking at it.

## Phases

| Phase | Scope | Ends when |
|---|---|---|
| **1 — the record** | `certification/manifest.json`, the derived `is_certified`, the reporting plugin, `infra/certify.sh`, and **one** scenario: the research lifecycle, promoted from smoke 14k | `make certify` produces a committed record for the current commit, and `PROJECT_STATUS.md` cites it instead of hand-copied numbers |
| **2 — failure and recovery** | Priority 1 and 2. Fault injection wired into a scenario for the first time; crash/restart/resume; determinism across repeated runs | A killed worker mid-pipeline provably resumes to the same findings, with no duplicates |
| **3 — the catalogue** | The nine missing scenarios, each layered to current pipeline depth per *Progressive assertion* | Ten scenarios certify; golden-set *variety* stops being 1 |

**Phase 1 is small and is the one that matters** — it converts every existing gate from ephemeral to durable without writing a single new assertion.

## Migration from today's repository

**Nothing is duplicated and nothing is thrown away.**

- **`make smoke` narrows to what it is uniquely good at**: build, image hygiene, migrations, identities, health, readiness, auth, JWT, RLS, relay, teardown — *deployability*. Its stages `14b`–`14k` currently shell out to `pytest tests/<module>`, which makes them workflow checks living in a deployment gate. Those move to certification, where they belong, as scenarios rather than as re-runs of module suites.
- **The simulation framework gains scenarios**, not concepts.
- **The Security Invariants suite is untouched** and remains permanent.
- **`PROJECT_STATUS.md` §4 changes from transcription to citation.**

The one-way door is the record format; it should be versioned from the first write, for the reason M9.5 established — **a measurement whose conditions cannot be stated is not reproducible.**

## Alternatives considered

| | Alternative | Why not |
|---|---|---|
| **A** | **More end-to-end tests, no record** | Closes the scenario gap and leaves the evidence gap wide open. The repository would still have no way to say what was true at a commit — the defect M9.5 Step A just spent a milestone correcting one level down |
| **B** | **A new scenario framework for certification** | Splits the fault injector, determinism guarantee and provenance fields across two owners, against a ratified design that already covers them |
| **C** | **Make it a release gate now** | There are no releases (ADR-0027). Automation for anticipated need, and the ordering ADR-0027 states forbids it |
| **D** | **A `CERTIFIED.md` a human updates** | The `status` field `PromptVersion` deliberately refused, at repository scale: *"a field that can lie about the thing beside it"* |
| **E** | **Do nothing; the gates are good** | They are good, and they are ephemeral, single-narrative, and happy-path. Three specific failures — a crashed worker resuming, a duplicate completion, a re-run producing different finding identities — would not be caught by any gate that exists |

## Naming collision, resolved

*"Certified model"* already means something narrow and shipped: the `(model, dataset)` pairing a prompt has passed. This ADR's terms are **Certification Record** and **Release Certified**, which describe the platform. The two must not be conflated in code: nothing in `modules/ai_platform/` may take a dependency on the certification concept, and the certification record refers to prompt releases only by citing them.
