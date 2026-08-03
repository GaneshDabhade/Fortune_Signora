# The Product Review Platform — design

> **Status: design, 2026-08-03. Stages 1–5 are built and on `main`; everything below the fold is proposed.**
>
> **An environment runs software. A review platform produces evidence.** The distinction is the product owner's, and it is the reason this document exists before any of the demonstration is code: a guided tour asserts what the product *means*, and that is not a thing to discover halfway through writing a launcher.

---

## 1 · What exists, and what it proved

`make review` is on `main` at `f034364`. It validates the workstation, seeds twelve accounts through the real pipeline, starts both tiers, waits until each answers, opens the browser, and records the session. `make review-end` closes it.

**Building it produced one finding that shapes everything below.** The first version asked *"is `HEAD` certified?"* — wrong on `main` every single time, because a Closeout commit can never be certified. It now walks to the nearest certified ancestor and **verifies** each intervening commit changes nothing executable.

> **The lesson generalises: a review platform's job is to make claims that are true.** Every stage proposed below is judged by whether it produces something a reader six months later can rely on — not by whether it runs.

---

## 2 · The lifecycle

The product owner's eleven stages, with each marked by what it costs and what blocks it. **Cleanup is last, and that ordering is the whole point: evidence outlives the environment.**

| # | Stage | State | Notes |
|---|---|---|---|
| 1 | **Prepare** | ✅ built | Resolves the `review` profile; no literal port exists in `infra/review.py` |
| 2 | **Validate repository** | ⚠️ **partial** | The certified-ancestor walk answers *"is this build measured?"*. It does **not** yet refuse to review an uncertified tree — see §6 |
| 3 | **Validate environment** | ✅ built | Ports, containers by name, database reachability, required configuration |
| 4 | **Seed dataset** | ✅ built | `playground@2`, recorded by identity so a second dataset changes no mechanics |
| 5 | **Launch product** | ✅ built | Both tiers, health-gated, browser opened |
| 6 | **Execute demonstration** | 🔵 **designed below** | The subject of this document |
| 7 | **Capture evidence** | 🔵 proposed | §5 |
| 8 | **Reviewer notes** | ✅ built | `make review-end ARGS='--note "…"'` |
| 9 | **Summarize session** | ✅ built | `summary.md` beside the record |
| 10 | **Archive review** | 🔵 **unblocked 2026-08-03** | D-2 ruled: summary committed, binaries external, hashes in the manifest |
| 11 | **Cleanup** | ✅ built | Ports released, and **verified** before the claim is printed |

**Smoke validation is deliberately absent and cannot be added.** The production stack binds the same two ports a review holds. The certification record answers the same question from a run that measured the real thing, so the session **cites** it. Ratified by the product owner: *"Review should reference certification, not recreate certification."*

---

## 3 · The demonstration is not navigation

**A demonstration and a test share an environment and share nothing else.**

| | **Test** | **Demonstration** |
|---|---|---|
| **Asserts** | The product is correct | Nothing |
| **Fails when** | Behaviour is wrong | It cannot reach the next beat of the story |
| **Audience** | The suite | A person, of a stated kind |
| **Success** | Green | **The audience understood why the product matters** |
| **Owned by** | The lane that built the behaviour | **The product owner** — see below |

> **QE must not author the narrative.** A story about why Signora matters to a CRO is a product claim. QE can build the mechanism that executes a story faithfully, records what it showed, and refuses to claim it showed something it did not. **It cannot write the story**, and burying one inside a launcher would hide the authorship — which is precisely how a demo starts asserting things nobody agreed.

**So the architecture separates them completely:** the playbook is data, authored by the product owner; the runner is code, owned by QE.

---

## 4 · Playbook architecture

### One product, several stories

The product owner named six audiences — investor, CTO, VP Sales, CRO, product manager, design lead, customer — and the key constraint: **the product does not change, only the narrative does.**

That constraint is what makes this tractable. A playbook is therefore **a sequence of beats over the same seeded dataset**, never a variant build, never a feature flag, never a mock.

```
  playbook (data, product owner)          runner (code, QE)
  ──────────────────────────────          ─────────────────
  beat 1  where to be                ──▶  navigate, wait for the real thing
  beat 2  what a customer sees       ──▶  capture, and assert it is present
  beat 3  why it matters             ──▶  narrate; assert nothing
                                          record what was actually shown
```

### The shape of a beat

Four fields, and the fourth is what stops a demonstration lying:

| Field | Whose | What |
|---|---|---|
| **`where`** | Product owner | A customer-vocabulary destination — *"the account Northwind"*, never `/accounts/:id` |
| **`say`** | Product owner | The narration. **In the customer's language** (ADR-0034), because it becomes the caption on a screenshot |
| **`show`** | Product owner | What the audience should be looking at |
| **`present`** | Product owner, **checked by the runner** | **A condition that must hold before the beat is claimed.** *"An opportunity with a reason"*, *"evidence with a citation"* |

> **`present` is the whole design.** Without it a demonstration is a slideshow that navigates: it would happily narrate *"here is why this account is moving"* over an empty state, capture the screenshot, and file it as evidence. **With it, a beat that cannot be shown is a recorded failure rather than a silent one** — and that is the difference between a review record and a marketing asset.

### Why a playbook is not a Playwright spec

**They will share the driver and must not share the file.** A spec asserts correctness and fails the build; a playbook tells a story and fails the *demonstration*. Merging them produces the worst of both: a test suite the product owner edits, and a narrative that blocks a promotion.

**The runner reuses Playwright as a browser driver.** It is already an approved dependency (ADR-0023), it produces traces and video, and building a second driver would be the duplication `CLAUDE.md` §20 forbids.

### The six playbooks, and the order to write them

**None now.** The mechanism first, then **one** playbook — and the first should be the one the repository can already satisfy.

| | Needs | Ready? |
|---|---|---|
| **Product Capability** | The screens that exist today | ✅ **Write this one first** |
| **Sales** | The attention list, an account, evidence, a brief | ✅ mostly |
| **AI Explainability** | Prompt versions and reasoning surfaced to a screen | ⚠️ partially |
| **Executive · Technical Architecture · Customer Success** | Product surface that is not built | ❌ |

> **A playbook for a story the product cannot yet tell is a specification for a demo, not a demonstration.** Writing all six now would produce four documents describing screens nobody can open — and the gap would be discovered by a reviewer, in front of an audience.

---

## 5 · The evidence package

The product owner's target list, with what each costs and what it is worth. **Cheap and truthful first.**

| Artifact | Cost | Verdict |
|---|---|---|
| Commit · certification · dataset · accounts · known defects · duration · notes | — | ✅ **built** |
| **Screenshots, one per beat, captioned with `say`** | **S** | **First.** The single highest-value addition — it is what *"exactly what did we show?"* actually means |
| **Playwright trace and video** | **S** | Free once the runner drives Playwright |
| **Backend logs and browser console for the window** | **S** | Already written to the session directory; needs scoping to the run |
| **Beat outcomes** — which were shown, which could not be | **S** | **The record that makes the rest trustworthy** |
| **Prompt versions in play** | **M** | Reads the prompt manifest; sound, and worth it — a demonstration of AI output that cannot name its prompt version is not evidence |
| **Timing per beat** | **S** | Free |
| **Reasoning-graph and commercial-brief fingerprints** | **L** | ⚠️ **Deferred, and challenged.** No fingerprint exists to read. Building one *for a demo* would put a demonstration concern inside the pipeline — the exact inversion `CLAUDE.md` §20a exists to prevent. **Revisit when the pipeline has a reason of its own to fingerprint** |

### Two properties the package must have

**Every artifact is produced by the run, never entered by hand.** The same rule as the certification manifest: there is no flag that marks a beat as shown.

**A failed beat is recorded as faithfully as a shown one.** A package holding only successes describes a demonstration that never stumbled — a different claim from the true one, and a more flattering one.

---

## 6 · Two decisions this needs

### D-1 · May a review run on an uncertified tree? — **RULED 2026-08-03, product owner**

> **An uncertified review is allowed. It is simply non-evidential.**
>
> *"Internal development review: allowed. Customer-facing evidence: requires certification. Those are different use cases."*

**Option C, ratified.** PR-5 implements it: a session started from a tree with no certified ancestor — or with executable commits above one — records itself as **non-evidential**, and the marking is in the record rather than in somebody's memory of which kind of session it was.

The positions considered:

| | | |
|---|---|---|
| **A** | Start, report honestly | Today. A lane can review its own work in progress |
| **B** | **Refuse unless the tree is certified or a certified ancestor is clean** | The strongest evidence guarantee — every record describes measured software |
| **C** | Start, but **mark the record as non-evidential** | **Recommended.** Keeps a lane's ability to look at its own work, and stops an uncertified session becoming a citable artifact |

**C was ratified**, because the failure it prevents is specific: a record produced from a working tree, filed indistinguishably from one produced from a certified build, cited months later.

### D-2 · Where does review evidence live? — **RULED 2026-08-03, product owner**

> **The repository stores the summary. Binary evidence remains external.**
>
> *"We should avoid committing hundreds of megabytes of binary data simply because a review occurred."*

**Option B, ratified**, and specified more precisely than QE proposed it:

| **Committed — the record** | **External — the evidence** |
|---|---|
| review metadata · summary · findings · reviewer notes | screenshots · videos |
| certification reference · dataset version · **playbook version** | Playwright traces · HAR files |
| **screenshots manifest · hashes · fingerprints** | browser recordings · logs |

**The hashes are the part that makes this work.** A committed manifest naming each screenshot and its hash means the repository can prove *which* image was shown even when the image itself is elsewhere — and can detect one that has been replaced. **The record stays lightweight and stays checkable**, which a bare file list would not.

Two consequences to implement:

1. **`--audit-main` learns a `review/` path class**, bounded to `.json` and `.md` — a Closeout-style allowance, and the binary exclusion is enforced by the path rule rather than by care.
2. **[`REPOSITORY_RESILIENCE.md`](REPOSITORY_RESILIENCE.md) R-4 is unblocked**, and its §5 decision table is now answered.

---

## 7 · What QE proposes to build next

| | | Blocked by | Size |
|---|---|---|---|
| **PR-1** | **The beat runner** — executes a playbook, captures a screenshot per beat, checks `present`, records outcomes | Nothing | **M** |
| **PR-2** | **The Product Capability playbook** — the first, written **by the product owner**, over screens that exist | PR-1, and the product owner's authorship | **S** |
| **PR-3** | **Evidence package** — screenshots, trace, video, beat outcomes, timings into the session directory, **with a hashed manifest** (D-2) | PR-1 | **S** |
| **PR-4** | **Prompt versions in the record** | PR-3 | **M** |
| **PR-5** | **Non-evidential marking** | ~~D-1~~ **ruled** | **S** |

> **PR-1 before PR-2, deliberately.** A playbook written before a runner exists is a guess about what the runner will accept. **A runner built with no playbook is testable against a two-beat example**, which is how the `present` condition gets exercised before anybody has written a story worth losing.

**Lane B is building Playwright infrastructure right now** — page objects, an auth setup, a golden-journey spec, none of it yet on `main`. **PR-1 must reuse it rather than grow a parallel one** (L-1), and that is a coordination item to open before PR-1 starts, not a discovery to make during it.

---

## 8 · The long-term target, restated

```
clone → validate → restore → seed → launch → demonstrate → capture → archive → summarize
```

**One command. One deterministic review. One evidence package. No manual setup.**

Five of those nine are built. `restore` belongs to [`REPOSITORY_RESILIENCE.md`](REPOSITORY_RESILIENCE.md) R-5, `archive` is blocked on D-2, and `demonstrate` and `capture` are §7.

> **The measure of this platform is not that it launches.** It is that a year from now, *"what exactly did we demonstrate to that customer, against which data, on which certified build, and what did they see?"* is answered from a folder rather than from memory.
