# Product Quality — the reuse audit, and what it says to build

> **The question this framework exists to answer:** *"If we shipped tomorrow, would customers actually love using it?"* — which is a different question from *"do the tests pass?"*
>
> **Owned by QE.** `CLAUDE.md` governs how work moves · [`ENGINEERING_LAWS.md`](../ENGINEERING_LAWS.md) how it is built · [`RELEASE_ENGINEERING.md`](RELEASE_ENGINEERING.md) how it is released · **this, whether it is fit for a customer.**

**Audited against `main` at `7e43841`, 2026-08-03.**

---

## 1 · The audit result, and it changes the assignment

**Thirty product quality gates were proposed. The repository already implements twelve of them, and nobody had named them as a suite.**

**`frontend/tests/components/` holds 34 test files, and they are not component tests.** They assert product properties:

| Proposed gate | Already exists | What it asserts |
|---|---|---|
| **No Empty Dead Ends** | `dead-ends.test.tsx` | *"an address that does not lead anywhere"* · *"a render that failed outside the shell"* |
| **Onboarding Quality** | `first-run.test.tsx` | *"a signed-in reader who belongs to no organization"* · *"an empty list says why it is empty"* |
| **Permission Clarity** | `viewer-role.test.tsx` | *"the signed-in role is read, not assumed"* · *"unknown is distinct from none"* |
| **Microcopy · Consistency** | `vocabulary.test.tsx` | *"the platform vocabulary never reaches a customer"* — ADR-0034 enforced |
| **Workflow Continuity** | `workflow.test.tsx` | *"the moves offered are the ones the domain allows"* · *"every decision carries a sentence"* |
| **Trust Indicators** | `entity-name.test.tsx` | *"the row does not rewrite itself under the reader"* |
| **Accessibility (focus)** | `focus.test.tsx` | focus behaviour on declared and undeclared states |
| **Consistency (theme)** | `design-tokens.test.tsx` | *"theme switching requires no component change"* |
| **No fabricated data** | `no-mock-data.test.tsx` | *"no mock business data"* · *"empty states are first-class"* |
| **Feedback Quality** | `validation.test.tsx` | *"the checks are what a seller acts on"* |
| **AI Explainability** | `narration.test.tsx` · `corroboration.test.tsx` | narration is grounded in cited evidence |
| **Feature Reachability** | [`43-customer-experience.md`](architecture/43-customer-experience.md) | **31 endpoints · 5 screens · 2 reachable by a member** — a repeatable census |

**And four are already Engineering Laws**, enforced at slice level rather than as a separate suite: **L-4** independent slice · **L-5** capability expansion · **L-6** customer journey integrity · **L-7** production path first.

> **So the honest deliverable is not a framework. It is a name, a runner, and the gaps.** Building a parallel Product Quality system beside 34 existing tests and four laws would be the duplication [L-1](../ENGINEERING_LAWS.md) forbids — and the bureaucracy the assignment explicitly warned against.

---

## 2 · What is genuinely missing

**Four gaps, each with evidence that it matters. Everything else on the proposed list is either covered above or not yet warranted.**

| Gap | Why it is real | Cost |
|---|---|---|
| **PQ-01 · The suite is not named or measured** | Twelve product properties are asserted and **nothing reports them as product quality.** A lane deleting `dead-ends.test.tsx` would see a test count drop by two, not a gate disappear | **S** |
| **PQ-02 · Reachability is measured by hand** | The 31-endpoints-against-5-screens census is a document a lane wrote once. **It was already stale within a cycle** (CX-01/02/03 changed it), and only a re-read catches that. It is the single highest-value check to automate — it is how [B-301](BUGS.md) and the doorless Connection Center were both found | **M** |
| **PQ-03 · No returning-user or time-to-first-value check** | Every existing test asserts a *screen*. None asserts a **journey across screens**, which is where R6, R7 and R10 findings all lived | **M** |
| **PQ-04 · Product regressions are found by a human using the product** | `CLAUDE.md` records it plainly: **2046 tests found none of R4-01, R6-01–04, R7-01–03, R10-01 or R12-01.** That has not changed | **L** |

**Deliberately not proposed:** cognitive load, task completion rate, enterprise readiness, searchability, undo coverage. **Not because they do not matter** — because none has a defect behind it in this repository, and inventing a metric that sounds impressive is the failure mode the assignment named.

---

## 3 · Customer Readiness Certification — the concept, not the build

**Two independent questions, and today the pipeline answers one.**

```
  Engineering Ready?          Customer Ready?
  ─────────────────           ───────────────
  make certify                ← does not exist
  gates are the decision      would need PQ-01…PQ-04 first
```

**The shape it should take, and the reason:** *Customer Ready* must be **derived, never declared** — the same rule as prompt release and `evidence_state`. A checkbox a human ticks would be a certification nobody can defend, and the repository already refuses that pattern everywhere else.

**The minimum honest version** is `make product-certify` reporting: reachability census (PQ-02) · the named product suite (PQ-01) · journey checks (PQ-03) · **and the count of findings a human found that the suite did not** — because that last number is the only measure of whether the first three are working.

> **It should not be built yet.** PQ-02 and PQ-03 do not exist, so a certification today would certify twelve tests and a hand-written document. **A gate that cannot fail is documentation pretending to be code** (§2).

---

## 4 · Which regressions would pass today's pipeline

**Asked adversarially, answered from the repository's own history rather than imagination.**

| Regression | Caught today? | Evidence |
|---|---|---|
| A capability ships with no route to it | **No** | The Connection Center was linked from nowhere for weeks |
| A worker never consumes what a module projects | **Yes, now** | `make runtime-composition` — but it was **No** through four certified promotions |
| A screen renders an empty state forever because nothing populates it | **No** | Timeline's feed was mounted and empty; only reading `apps/` found it |
| Copy promises a capability the system lacks | **No** | [B-027](BUGS.md) — *"you can disconnect at any time"*, and no endpoint existed |
| An authorization grant exists for an operation with no implementation | **No** | `policy.csv:5` grants `member remove`; there is no use case |
| A journey works screen-by-screen and not end to end | **No** | Nothing asserts across screens |

**Five of six are still invisible**, and every one has already happened here. **That is the case for PQ-02 and PQ-03**, and it is stronger than any metric list.

---

## 5 · Priority

**In value order, and deliberately short.**

1. **PQ-01** — name and report the suite. Small, and it makes the other three measurable.
2. **PQ-02** — automate the reachability census. **The highest-value check in this document**: it is how the two worst defects of the last month were both found, by hand.
3. **PQ-03** — one journey check, end to end, as a proof of shape.
4. **PQ-04** — the human pass stays. **It should not be automated away**; it should become the measure of the others.

> **Not started, deliberately.** [`DECISION_PACKS.md`](DECISION_PACKS.md) holds five decisions blocking both implementation lanes, and **four consecutive cycles have shipped no customer value.** Building product quality tooling while the product itself is stalled would repeat the mistake this assignment was written to correct — one level up.
