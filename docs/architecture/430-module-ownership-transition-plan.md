# 430 — Module Ownership Transition Plan

> **Lane C — Product Office, 2026-08-04.** **PREPARED — READY FOR PRODUCT OWNER.** Prepared on the directive: *"Do not immediately redistribute modules… prepare a Module Ownership Transition Plan… The objective is that no module changes ownership while implementation is in flight."*
>
> **Nothing here moves a module.** Module assignment is the product owner's ([D-057](../DECISION_REGISTER.md)), and this plan is a recommendation with its evidence.

## 1 · The three states a module has, and they are deliberately distinct

**Conflating any two of these is how a transition plan becomes an ownership change.**

| | |
|---|---|
| **Interim owner** | **Who holds it today.** **Lane B, every production module** — [D-058](../DECISION_REGISTER.md). ✅ **On `integration`, and the *"not yet"* that stood here is cleared 2026-08-05** — [B-205](../BUGS.md)'s class, caught by the guard that item produced. ⚠️ **And the fact itself has moved on**: [D-065](../DECISION_REGISTER.md) transitioned six modules to Lane A. **[`modules.toml`](../coordination/modules.toml) is authoritative; this row is a dated record** |
| **Recommended steady-state owner** | **Who should prepare and build it once both Product Development lanes are running.** A recommendation, ruled by nobody yet |
| **Transition point** | **The event after which the move is safe.** Never a date |

> **No module moves on this document.** **Eleven of seventeen recommend Lane A, which is `PAUSED`** — so **the plan executes nothing until the product owner resumes Lane A**, and until then today's assignment is also the correct assignment. **That is the controlled sequence the product owner recommended**, and it falls out of the plan rather than being imposed on it.

## 2 · What determines ownership — corrected 2026-08-04

> ⚠️ **The first version of this section made recent `git` history the primary basis. The product owner corrected it, and the correction is the more important half of this document.**
>
> **"Git history is evidence. It is not governance."**

**Ownership is determined in this precedence, and a lower rung is consulted only when the ones above it do not decide:**

| | Rung | What it asks |
|---|---|---|
| **1** | **Product architecture** | Where does this sit in the system the product owner is building? |
| **2** | **Bounded context** | Which ubiquitous language does it speak? [04-modules.md](04-modules.md) is authoritative |
| **3** | **Long-term maintenance responsibility** | Who will still be answering for this in six months? |
| **4** | **Repository continuity** | Who holds the context that would otherwise be rebuilt? |
| **5** | **Historical implementation evidence** | Who last worked here — read from `git log`, attributed by identifier block |

**Why the correction matters rather than being a wording change.** **Recent commits describe who was *available*, not who should be *responsible*.** A module can be touched last by whichever lane happened to be free, and **promoting that accident to governance would make ownership a function of scheduling** — which is precisely the confusion between *a lane is temporary* and *a module is permanent* that §20e exists to prevent.

> **The product owner's worked example:** *"if `workspace_tenancy` becomes a foundational platform module used across the product, you may eventually decide it belongs with Platform or another lane regardless of who committed there recently."* **That row now carries the flag rather than the inference**, and rung 1 will decide it.

**The registry records both.** [`docs/coordination/modules.toml`](../coordination/modules.toml) carries `last_work` as evidence at rung 5 and **never as the reason for an assignment on its own.**

## 3 · The plan

**Transition-point classes:** **T0** immediate, nothing in flight · **T1** on promotion of named work now with QE · **T2** on completion of named claimed work · **T3** on a ruling that does not exist yet.

| Module | Interim owner | Implementation status | Active tasks | QE status | Blockers | **Recommended** | **Transition point** | **Why it is safe** |
|---|---|---|---|---|---|---|---|---|
| `integrations` | Lane B | Epic E1 built; **nothing customer-visible** | TASK-402 | **`VERIFIED`** | [C-300](../LANE_COORDINATION.md) | **Lane B** | **T0** | **No move.** Lane B built S01/S02/S09 and holds it now — **the only rows where interim and steady state already agree carry no risk at all** |
| `provider_normalization` | Lane B | Canonical shape for E1; TASK-301 shipped | TASK-402 · TASK-301 | `IN VALIDATION` | — | **Lane B** | **T0** | **No move** |
| `knowledge_graph` | Lane B | Global Search shipped | TASK-301 | `IN VALIDATION` | — | **Lane B** | **T0** | **No move.** Lane B's most recent work, and **11 backlog references — the most of any module**, so continuity is worth most here |
| `observation_engine` | Lane B | A5 backend — 13 fields computed since M4 | — | — | — | **Lane B** | **T0** | **No move** |
| `timeline` | Lane B | M7 S01–S04a shipped | TASK-902 `READY` | — | [C-215](../LANE_COORDINATION.md) | **Lane B** | **T0** | **No move.** C-215 travels with the module, as [D-057](../DECISION_REGISTER.md) requires |
| `business_event_engine` | Lane B | M12.3-era; no post-lane work | — | — | — | ⏸️ **undecided** | **Review at first implementation** | **Deliberately unassigned** *(product owner, 2026-08-04)*. Its **inputs** are `observation_engine` and `knowledge_graph`, both Lane B; its **output** feeds `signal_engine`, future Lane A. **It sits exactly on the seam, and rather than guess, ownership is decided when implementation reaches it** — **evidence over prediction** |
| `ai_platform` | Lane B | M12.3-era; no post-lane work | — | — | [C-214](../LANE_COORDINATION.md) | ⏸️ **undecided** | **Review at first implementation** | **Deliberately unassigned** *(product owner, 2026-08-04)*. Cohesion argues Lane A — its only consumers are `ai_reasoning_engine` and `ai_research_engine` — **but no evidence exists yet and prediction is not required.** **C-214 already names its owner as *"whoever is assigned `ai_platform`"*** — the derived form [428](428-lane-coordination-model.md) argues for, and **it needs no edit whichever way this is eventually ruled** |
| `ai_reasoning_engine` | Lane B | A-i shipped — Signora's conclusion reaches a customer | TASK-204 · TASK-202 | `IN VALIDATION` | — | **Lane A** | **T1 → T3** | **TASK-204 must promote first**, then Lane A must resume. **Two gates, both external to this plan** |
| `ai_research_engine` | Lane B | R4-02/03 shipped | — | — | — | **Lane A** | **T3 — Lane A resumes** | **Nothing in flight.** The move is safe the moment Lane A exists |
| `opportunity_engine` | Lane B | **Lead Lifecycle feature-complete for v1** — 9 slices | Lead lifecycle | `IN VALIDATION` | — | **Lane A** | **T1 → T3** | **§19–§29 of its design doc are an explicit handover package** — *what the module owns, its ten invariants, its contracts, five user walks, eighteen journeys*. **This is the module best prepared to change hands**, and it was written that way deliberately |
| `signal_engine` | Lane B | Epic D phase 1 — competitor entry | **TASK-405 `READY`** | — | — | **Lane A** | **T2 → T3** | ⚠️ **TASK-405 is `READY` and claimable now.** **If Lane B claims it, the transition point moves to that task's completion** — which is the rule working, not a conflict |
| `commercial_profile` | Lane B | ICP, buying committee, business priorities | **TASK-406 `READY`** · TASK-903 | — | ADR-0041 unratified | **Lane A** | **T2 → T3** | **Same shape as `signal_engine`.** **ADR-0041's ratification is the product owner's and travels with the module either way** |
| `buying_score_engine` | Lane B | Epic D contribution | TASK-905 `READY` | — | — | **Lane A** | **T3 — Lane A resumes** | Nothing in flight |
| `sales_engagement` | Lane B | SE-09d shipped; **A-ii unbuilt** | **TASK-205 `READY`** | — | ~~C-213~~ **closed** | **Lane A** | **T2 → T3** | ⚠️ **Highest-risk row.** TASK-205 was **unblocked by consolidating it with `commercial_profile`**, and **the recommended split separates them again.** **See §4** |
| `provider_platform` | Lane B | PP-01/02/04/05/06 built; PP-03 suspended; A7 shipped | **TASK-400 `CHANGES REQUESTED`** | **returned** | [C-021](../LANE_COORDINATION.md) · [B-107](../BUGS.md) | **Lane A** | **T2 → T3** | **Returned work is addressed before anything else** (§20e). **B-107's ten never-passing tests are in the A7 slice Lane A wrote** — **transferring a returned slice to a lane that did not write it is the most expensive transfer available**, and this plan does not do it |
| `workspace_tenancy` | Lane B | TM-06 shipped | TASK-904 `READY` | — | [C-206](../LANE_COORDINATION.md) · [C-207](../LANE_COORDINATION.md) | **Lane A** | **T3 — Lane A resumes** | Nothing in flight. **Team Management is buildable now** — the blockers were withdrawn by the lane that raised them |
| **Product Surface** | Lane B | CX-07 shipped; PS-01…08 · CX-01…03 | TASK-400 (A6) · TASK-200 | `IN VALIDATION` | [C-025](../LANE_COORDINATION.md) · [C-008](../LANE_COORDINATION.md) | **Lane A** | **T1 → T3** | **Every approved screen lands here.** Lane A built the shell, the design system usage and eleven routes — **this is the largest continuity cost in the table if it moves wrongly** |

**`infra/` · `Makefile` · repository process · `signora_platform/simulation` are Lane C's and are not production modules.** **No transition, and none is proposed** ([D-022](../DECISION_REGISTER.md)).

## 4 · The one row that needs a ruling rather than a rule

> ⚠️ **`sales_engagement` and `commercial_profile` are recommended to different lanes, and that re-creates C-213.**

**The consolidation closed C-213 by putting the export (`commercial_profile.public`) and its only consumer (`sales_engagement`'s `AssembleApproach`) in one lane.** **The evidence-based split separates them again** — `sales_engagement` and `commercial_profile` both recommend Lane A, so **in the recommended steady state they are together and the risk does not arise.**

**It arises only if the product owner splits them differently.** **Stated here so the decision is made knowingly**: the two modules have a **published-but-unbuilt contract between them**, and **a boundary drawn between them costs a coordination item on day one.**

> **The general rule this yields, and it is worth keeping:** **do not draw a lane boundary across an unbuilt contract.** A boundary across a *built* contract is ordinary; across one that still has to be designed, it is C-213 by construction.

## 5 · What the split would look like, and it is not balanced

| | Modules | Count |
|---|---|---|
| **Lane A — intelligence and the product surface** | `ai_platform`* · `ai_reasoning_engine` · `ai_research_engine` · `buying_score_engine` · `commercial_profile` · `opportunity_engine` · `provider_platform` · `sales_engagement` · `signal_engine` · `workspace_tenancy` · **Product Surface** | **11** |
| **Lane B — ingestion and the data platform** | `business_event_engine`* · `integrations` · `knowledge_graph` · `observation_engine` · `provider_normalization` · `timeline` | **6** |

**\* placed by cohesion; no post-lane work exists to attribute.**

> **This is reported rather than corrected.** **The imbalance is real and it is historical**: Lane A held the intelligence pipeline and the entire Product Surface while Lane B held ingestion. **Rebalancing by moving modules to even the count would discard the continuity that is the whole argument for the split** — and continuity, not headcount, is what the directive optimises for.
>
> **If capacity rather than continuity is the concern, the lever is which lane resumes on which epic, not which lane holds which module.**

## 6 · Recommended sequence

**The product owner's own sequence, and this plan agrees with it on the evidence:**

| | Step | Why here |
|---|---|---|
| **1** | **`lane-c-sync` reaches `integration`** | **Nothing above is actionable until it does** — the consolidation itself is not yet on `integration`, so today's *recorded* owners are still the morning's split |
| **2** | **Governance lands** | The three new lifecycle states must exist before a package can enter `PREPARING` |
| **3** | **This plan is ruled** | Steady-state owners fixed while nothing is moving |
| **4** | **Lane A resumes** under the new model | **11 of 17 rows are gated on this and on nothing else** |
| **5** | **T1/T2 modules transition** as their named work promotes | Per module, event-driven, never dated |

> **Steps 1–3 move no module, and step 4 is the only one that does.** **That is the property the directive asked for** — *no module changes ownership while implementation is in flight* — and it holds because **every T1 and T2 row names the specific work that must finish first.**

## 7 · Recommendation

| | |
|---|---|
| **The plan** | ✅ **Adopt as the target state.** Derived from the repository, not from the historical split |
| **Timing** | ⏸️ **Execute nothing until Lane A resumes.** Six rows are `T0` and already correct; eleven wait |
| **The two arguable rows** | **`ai_platform` and `business_event_engine`** — placed by cohesion, **flagged rather than smuggled** |
| **The one real risk** | **Do not draw a lane boundary between `sales_engagement` and `commercial_profile`.** The recommendation keeps them together; a different split re-opens C-213 |
