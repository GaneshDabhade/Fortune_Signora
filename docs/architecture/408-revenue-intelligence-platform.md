# 408 — Revenue Intelligence Platform — implementation preparation

> **Prepared by Lane C — Product Office. No code was written and none should be.** **Every claim verified against source on 2026-08-04.**
>
> **This package is short because its finding is short.** Most of RIP should not be built, and the remainder is already built. **A longer document would not reduce implementation uncertainty; it would only look like more preparation.**

---

## 1 · The finding

**RIP is planned as the seventeenth module. Its job is already done, by a layer that exists and was designed deliberately.**

> **`04-modules.md`:** *"The outward-facing composition domain that **aggregates** buying score, opportunity, AI research/reasoning, recommendation and timeline data into the workspace-level views and APIs… **Owns:** cross-module composition/aggregation for presentation, workspace-level prioritization and reporting logic, **the primary read APIs consumed by the frontend**. **Does Not Own:** any of the underlying domain logic of the modules it composes."*

**`backend/apps/api/composition/` is exactly that, and it is twelve files:** `accounts` · `evidence` · `integrations` · `narration` · `opportunities` · `products` · `research` · `scores` · `timeline` · `validation` · `workflow` · `__init__`.

**Its own docstring explains why it has that shape, and the reason forecloses the module:**

> *"**The composition boundary, and the only place that may see two modules' infrastructure at once.**… **Split per module, and the split is not cosmetic.** A single shared module here was the first shape tried, and **import-linter refused it**: a router importing it inherits *every* import it makes, so `knowledge_graph`'s router acquired a transitive dependency on `opportunity_engine` — **an upstream module reaching downstream, which is a cycle waiting to happen.** One file per read surface means a router depends only on what it actually composes."*

> **The single-composition-point shape was tried, and the repository's own dependency rules rejected it.** **`modules/revenue_intelligence_platform/` is that shape with a module wrapper around it** — one place that sees every module's infrastructure, which is what import-linter refused.

---

## 2 · The test it fails, and why the test is not "is it composition?"

**The obvious argument is [C-025](../LANE_COORDINATION.md)'s** — *"M13 is a capability delivered across consuming modules, not a fifteenth bounded context."* **That argument is not sufficient here, because it lost.** `modules/integrations/` **was** built, and correctly: its `public/__init__.py` records the 2026-08-02 ruling — *"a Connected Account is a business relationship that exists **before, during and after** any synchronization"*, so it owns an aggregate with a lifecycle nothing else reproduces.

**So the test that actually decides a bounded context in this repository is:** **does it own an aggregate with a lifecycle and invariants of its own?**

| | Integrations | **RIP** |
|---|---|---|
| **Aggregate** | `ConnectedAccount` · `IntegrationGrant` | **None.** Core Concepts are *Workspace Intelligence View · Prioritized Opportunity List · Revenue Intelligence Report* — **three views** |
| **Lifecycle** | `ConnectionState`, independent of sync runs | **None.** A view has no states |
| **Invariants** | *"connection state and run state are different lifecycles"* | **None stated anywhere** |
| **State it owns** | Tables, migrations, an encrypted secret store | **`05-module-dependencies.md`:** *"they own none of what they display"* |
| **Publishes** | Yes | **`04-modules.md`: none — *"top of the pipeline; product-facing"*** |

> **Integrations passed this test. RIP fails every row of it.** A module that owns no aggregate, no lifecycle, no invariant, no state and publishes no event **is a composition layer**, and the repository already has one.

---

## 3 · What is genuinely missing — and it is not a module

**Two of RIP's three Core Concepts are already served.** The *Prioritized Opportunity List* is the attention list, shipped on Product Surface. The *Workspace Intelligence View* is the account brief and the accounts list, shipped.

**The third — *Revenue Intelligence Report* — has no owner and no definition anywhere.** No screen, no endpoint, no spec, no acceptance criterion. **It is a name in a registry entry.**

> **That is the honest gap, and it is a product question rather than an architectural one:** *what is a revenue intelligence report, who reads it, and what decision does it change?* **Until that is answered it cannot be scoped, and a module built to hold it would be a module built around a name.**

**Two smaller things RIP's registry entry points at that are real:**

- **`recommendation.created` and `recommendation.status_changed` list RIP as a consumer.** With RIP unbuilt, **[M11](407-m11-recommendation.md) ships to one of its two intended consumers** — Timeline. **Sufficient, and it should be a choice** ([407](407-m11-recommendation.md) ❓1).
- **`05-module-dependencies.md:118`** — *"RIP → Timeline: synchronous query when composing a workspace intelligence view."* **`composition/timeline.py` already does this.**

---

## 4 · Recommendation

> **Do not build `modules/revenue_intelligence_platform/`. Retire it from the module registry, and keep composition where it is.**

| | |
|---|---|
| **Retire** | The module from `04-modules.md`, `05-module-dependencies.md` and README's *"Not started"* row — **replaced by a note naming `apps/api/composition/` as the composition boundary** |
| **Keep** | Every read surface it would have owned, **exactly where it is** |
| **Reassign** | `recommendation.*`'s second consumer → **Timeline only**, until something needs more |
| **Escalate** | ***Revenue Intelligence Report*** — **a product definition, not an architecture task** ([C-411](../LANE_COORDINATION.md)) |

**Why retiring beats leaving it listed.** A registry entry for an unbuilt module is a standing instruction to build it. **The next lane that reads `04-modules.md` sees seventeen modules and one missing**, and the cheapest moment to prevent that is before somebody starts. **This repository has already paid for the inverse mistake** — [C-025](../LANE_COORDINATION.md) argued Integrations was not a module, and the correct answer was that it was; **the cost was an investigation, not a rebuild, because it happened before the code.**

**What Lane C is not recommending:** removing the *capability*. **Composition, workspace-level reads and reporting all continue** — the question is only whether they need a bounded context, and the evidence says they have one already and it is called `apps/api/composition/`.

---

## 5 · A naming collision worth ten seconds of somebody's time

**`apps/api/composition/workflow.py` already exists**, and it means *"composing the **Opportunity Engine's write surface**"* — *"progressing an opportunity needs the workflow tables and a membership check, and nothing else at all."*

> **[Epic F](402-epic-f-workflow.md) proposes `modules/workflow/`.** Two different meanings of *workflow*, one repository. **Not a blocker and not worth an ADR — but a lane building Epic F will meet this file, and knowing in advance costs nothing.** ADR-0034 owns naming if it turns out to matter.

---

## 6 · Cross-cutting, risks, and what remains open

**[405](405-cross-cutting-concerns.md) applies unchanged and adds nothing here** — a package recommending that a module not be built has no observability, deployment or testing surface of its own.

| Class | Risk | Mitigation |
|---|---|---|
| **Architectural** 🟠 | **A module is built because a registry lists it** | §4 — retire the entry |
| **Architectural** 🟠 | A single composition point reintroduces the cycle import-linter refused | §1 — **the constraint is enforced, not advisory** |
| **Product** 🟡 | *Revenue Intelligence Report* is quietly dropped rather than decided | §3 — escalated as [C-411](../LANE_COORDINATION.md) |

> **🟡 Upcoming — the one decision here: is `modules/revenue_intelligence_platform/` retired?** **Lane C recommends yes**, on the evidence in §2. **Retiring a planned module is a roadmap scope change and is the product owner's alone.**

> **🟢 Background — what is a *Revenue Intelligence Report*?** **Unanswerable from repository evidence** — nothing defines it. Needed before anything is built for it; **nothing waits on it today.**

**Maturity: this package is complete.** It is not `READY` and never will be, because **its conclusion is that there is nothing to implement.**
