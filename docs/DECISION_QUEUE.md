# Product Owner Decision Queue

**The single place the product owner reviews when making rulings.** Established 2026-08-05 by product owner directive — *"Instead of spreading them across reports, maintain one continuously updated Product Owner Decision Queue."*

> **This document does not replace [`LANE_COORDINATION.md`](LANE_COORDINATION.md).** That register stays the authoritative record of every coordination item and its full reasoning. **This is the queue: which decisions to make, in what order, and what each one costs.** Every row links to the item that holds the argument.

## How this stays true

**Two kinds of column, and the difference is the whole reason this file is safe to keep.**

| | Column | Source |
|---|---|---|
| **Derived** | Status · Blocks · Lanes waiting | **Computed from [`LANE_COORDINATION.md`](LANE_COORDINATION.md), [`BACKLOG.md`](BACKLOG.md) and [`modules.toml`](coordination/modules.toml)** — never typed here |
| **Judgement** | Priority · Recommended option · Cost to decide | **Lane C's**, and only Lane C's |

> **A hand-maintained copy of a derived fact is the defect this repository keeps rediscovering** — [C-213](LANE_COORDINATION.md) stored an assignee beside a module, [C-412](LANE_COORDINATION.md) stored one beside a task, and **both went stale within a day while continuing to read as answers.** So the derived columns here are regenerated, not edited, and **`python3 infra/decision-queue.py --check` fails when this file and the register disagree.**

**A ruling is recorded in [`DECISION_REGISTER.md`](DECISION_REGISTER.md) and the item is closed in [`LANE_COORDINATION.md`](LANE_COORDINATION.md).** This file then drops the row on its next regeneration. **Nothing is decided here; this is where deciding is made cheap.**

---

# ⚡ P1 · Blocks work a lane is holding or about to start

**Seven decisions. Between them they hold two lanes' next slices, an entire epic, and the last step of PP-02.**

## 🥇 The two cheapest rulings in the repository — the answer is already written

> **C-206 and C-208 both block [TASK-904](BACKLOG.md), which is Lane A's next task**, and **TASK-904's own row already states the answer to each.** These are ratifications, not designs. **Ruling on them costs a sentence and returns a whole slice.**

### C-206 · Is an invitation Better Auth's or Signora's?

| | |
|---|---|
| **Summary** | `POST /members` takes a `user_id: UUID`, **nothing resolves an email to a user**, and every workspace is permanently whoever created it. **Better Auth's `organization` plugin is installed and unused** and ships the whole domain |
| **Impact** | **An organization cannot grow.** No customer can add a second seat |
| **Blocks** | **[TASK-904](BACKLOG.md)** — the *invitation* and *acceptance* thirds. **Not the members list** ([46 §7](architecture/46-team-management.md)) |
| **Lanes waiting** | **Lane A** — it is the `next` entry in [`lane-a.toml`](coordination/queues/lane-a.toml) |
| **Priority** | **P1** |
| **Cost to decide** | **Minutes.** Ratification |
| **Recommended** | ✅ **Signora owns the invitation**, as [TASK-904](BACKLOG.md)'s row already states. **§13 says auth is bought and never built, and this is the bounded exception**: migration `0005` revokes `signora_app` from the `auth` schema, so **membership held in the plugin's tables is membership the application cannot read.** Buying identity is not the same as buying tenancy. **An `invitation` table keyed by email, and [ADR-0010](architecture/adr/0010-identity-and-access.md) amended to say the plugin is deliberately unused for organizations** |

### C-208 · A tenant-scoped row whose only legitimate reader is outside the tenant

| | |
|---|---|
| **Summary** | **An invitation is workspace-owned data and its addressee is, by definition, not in the workspace yet.** `CurrentWorkspace` refuses them correctly; every RLS policy is `workspace_id = current_setting('app.workspace_id')` and **no user-scoped session setting exists** |
| **Impact** | **The row addressed to somebody is invisible to them.** The first time the tenancy model has met this shape, and **it recurs for anything a person receives before they belong** |
| **Blocks** | **[TASK-904](BACKLOG.md)** — acceptance |
| **Lanes waiting** | **Lane A** |
| **Priority** | **P1** |
| **Cost to decide** | **Minutes to rule; the shape is already drafted** |
| **Recommended** | ✅ **Acceptance matches a pending row against the `email` claim in the already-verified JWT** — [TASK-904](BACKLOG.md)'s row. **The reader is authenticated but not a member**, which is a third state the model does not currently have. **Rule the state into existence explicitly** rather than letting an endpoint discover it: a named, single-purpose read path, not a general weakening of RLS. ⚠️ **`signora_platform/db/` is frozen (§20a), so this needs your approval regardless of how small it looks** |

---

## The five that need a real decision

### C-018 · Nobody owns the customer-facing name of an attribute

| | |
|---|---|
| **Summary** | A seller reads `employee_count` where they would say *headcount*. **Every available home contradicts something already written down** — `knowledge_graph` publishing labels contradicts AC-28 and ADR-0034; the frontend translating contradicts R11-06's own instruction |
| **Impact** | The product speaks engineering's vocabulary to customers, everywhere, permanently |
| **Blocks** | **[TASK-003](BACKLOG.md)** — *"cannot be implemented without the answer"* |
| **Lanes waiting** | **Lane B** — carried in its `blocked` array |
| **Priority** | **P1** |
| **Cost to decide** | **Moderate** — it picks a home and one existing document gets amended either way |
| **Recommended** | **`explanation.py`, per R11-06's own words** — *"the fix belongs upstream where the pipeline chooses its words."* It keeps ADR-0034's rule that translation never travels inward into `knowledge_graph`, and it puts the label where the sentence is already being composed. **Accept that R11-06 wins and AC-28 is untouched** |

### C-328 · `commercial_profile` cannot measure its own ICP

| | |
|---|---|
| **Summary** | **The ICP is declarable and nothing tells a customer whether it is any good** — and measuring that needs outcomes the declaring module is **architecturally forbidden** to see. The refusal is deliberate and carries its reasoning in `pyproject.toml`: *"declaration would quietly become declaration informed by our own conclusions"* |
| **Impact** | A customer declares an ICP and never learns it is wrong |
| **Blocks** | **[TASK-406](BACKLOG.md)** — A-iv only; every other `commercial_profile` slice is unaffected |
| **Lanes waiting** | **Lane B** |
| **Priority** | **P1** |
| **Cost to decide** | **Moderate** — a bounded-context question, which is yours by definition |
| **Recommended** | **Do not open the edge.** The contract is right and Lane B was right to stop at it. **The measurement belongs to whichever module already sees outcomes** — `opportunity_engine` — **reading the declaration through `commercial_profile.public`, which is the direction the dependency graph already permits.** ICP quality becomes a scored output, not a field on the declaration |

### C-321 · What should Signora do with a company it cannot name?

| | |
|---|---|
| **Summary** | **Identity and significance are different axes and the attention list multiplies them into one number.** A record with four weeks of elevated research and no name is offered *"I'm working this"* |
| **Impact** | **Genuinely interesting and genuinely not actionable intelligence is presented as actionable** |
| **Blocks** | **[TASK-400](BACKLOG.md)'s A6 half** (via [C-219](LANE_COORDINATION.md)), plus PX-301 and PX-316. **A7 is unaffected and is queued** |
| **Lanes waiting** | **Lane A** — carried as `held`, not idling on it |
| **Priority** | **P1** |
| **Cost to decide** | **Higher** — six sub-questions, and it is product philosophy rather than a screen fix |
| **Recommended** | ✅ **Adopt Lane B's six recommendations as written.** They are internally consistent: appear **yes** · working list **no** · contribute to a score **yes** · become an opportunity **no** · workable **never** · **and it becomes `Needs identity`, a queue with its own workflow.** The one thing to confirm deliberately is the last: **a new queue is new surface area**, and it is the half of the recommendation that costs building |

### C-221 · Epic C — no person's name enters the platform anywhere

| | |
|---|---|
| **Summary** | [ADR-0400](architecture/adr/0400-person-as-an-entity.md) said *"check this before writing any code."* **It was checked. The answer is no.** No mapper reads a name, `RoleChangeValue` has no field to carry one, the simulator models none, and **no `person_name`, `contact_name`, `full_name` or `first_name` exists anywhere outside tests** |
| **Impact** | **People Intelligence has no people.** The epic's premise is not met by any data the platform ingests |
| **Blocks** | **[TASK-201](BACKLOG.md) — all of Epic C's phases 1–3**, claimed and blocked |
| **Lanes waiting** | **Lane B** |
| **Priority** | **P1 — and it is the largest single block by scope** |
| **Cost to decide** | **High.** It is a product-scope decision, possibly a vendor one |
| **Recommended** | **Do not specify around it.** Two honest options and they differ in cost by an order of magnitude: **① acquire a provider capability that carries names** — a real vendor decision with a real cost — or **② narrow Epic C to role changes without identity**, which is buildable today from what the platform already ingests. **Lane C recommends ②** and holds the specification half; **say which and the specification follows within a slice** |

### C-021 · An event handler cannot reach a provider adapter

| | |
|---|---|
| **Summary** | Everything a lane may build is built — delta rule, version ordering, state table, repository, use case, handler, **17 unit tests.** What remains is **how the handler starts a sync**, and `signora_platform/event_bus/queue.py` is the relay's and frozen |
| **Impact** | **Nothing yet reads a company a customer declared** |
| **Blocks** | **The last step of PP-02 and the whole of PP-03** |
| **Lanes waiting** | **Lane A** (`provider_platform`) |
| **Priority** | **P1** |
| **Cost to decide** | ✅ **None as a separate ruling — see below** |
| **Recommended** | **Do not rule on this in isolation. It is one of the four capabilities in [TASK-900](BACKLOG.md)'s RFC**, which Lane C now owns and is writing. **Ruling piecemeal here would decide the substrate one accident at a time**, which is what §20a exists to prevent |

---

# 🧩 Collapsed — four decisions, one RFC

**[TASK-900](BACKLOG.md) closes [C-012](LANE_COORDINATION.md), [C-013](LANE_COORDINATION.md), [C-021](LANE_COORDINATION.md) and [C-207](LANE_COORDINATION.md).** Approved to Lane C on 2026-08-05.

> **This is the highest-leverage item in the repository on both sides at once.** It removes **four decisions** from this queue, and **[TASK-901](BACKLOG.md) — seven independently certifiable slices — is blocked on it.** One approval, four rulings retired and seven slices released.

**You will see it as a single RFC to approve rather than as four questions.** That is the entire point.

---

# P2 · Blocks a milestone, no lane waiting today

| ID | Summary | Blocks | Priority | Recommended |
|---|---|---|---|---|
| **C-320** | **No environment can complete a sign-up**, so nobody has reviewed the product's first hour | The most commercially important hour in the product | **P2 — high** | **Rule the deployment question**; this blocks *review*, which is how everything else gets found |
| **C-322** | **Is an ICP a description, or a filter?** The product contradicts itself on screen | Epic B1 | **P2** | Pairs with **C-328**. **Rule them together** — one is the definition, the other is who measures it |
| **C-025** | M13 is not a module, and its consumers do not exist | M13's credential half | **P2** | Defer explicitly rather than leaving open |
| **C-020** | M7 has no scope, Timeline has no design | M7 entirely — [TASK-902](BACKLOG.md), `WAITING` | **P2** | Defer explicitly; Timeline ships value without it |
| **C-200** | M14b is three concerns in one roadmap row | All of M14b — [TASK-906](BACKLOG.md), `WAITING` | **P2** | **Already deferred by D-029.** Confirm and close |
| **C-023** | M13 is ratified architecture, not an executable milestone | Lane A taking M13 as an assignment | **P2** | Confirm; it is bookkeeping |
| **C-203** | Nothing in the product can render a person's name | Narrowed 2026-08-02 | **P2** | **Rule with C-221** — same root fact |
| **C-005** | Who owns the signal-profile write path | The first customer-editable relevance profile | **P2** | — |
| **C-205** | **Is Signora expected to work on a phone?** | [B-019](BUGS.md) and every responsive decision | **P2** | **Yes or no, once.** It is being answered by default today |

# P3 · Standing ambiguity, blocks nothing being built

> **None of these stops a slice today.** Several *"get worse with every slice"* (C-003) or affect *"every AE and SDR, every day"* (C-008) — **real, and not urgent in the queue sense.** Listed so the queue is complete and so `--check` can prove it is. **Lane C is not asking for rulings on these this week.**

| ID | Summary | Blocks | Recommended |
|---|---|---|---|
| **C-207** | **Casbin cannot express an action on yourself** | Leaving an organization, **and every self-directed operation Signora will ever have** | ✅ **Collapses into [TASK-900](BACKLOG.md)'s RFC** — capability 4. **Do not rule separately** |
| **C-219** | TASK-400's two halves are not equally buildable | Nothing directly — **it is the item that narrowed A7 from A6** | **No ruling needed.** A6 is C-321; A7's render waits on a join proposal **Lane A owes Lane C**, not on you |
| **C-223** | `competitor_entry` cannot be implemented across the current boundary | **Only Epic D phase 1's detection half** — declaration, API and screen ship | **Rule with C-328.** Same shape: a module asked to read across a boundary that refuses on purpose |
| **C-008** | **Sellers cannot see what their company sells** | Nothing being built — **affects every AE and SDR, every day** | **The highest-value P3 by customer impact.** Promote to P2 the moment a lane has capacity |
| **C-002** | Customer language has no anticorruption layer | Nothing in M12.5 — **must be answered before anything matches an account against an ICP** | **Rule with C-322**; both are what an ICP *means* |
| **C-003** | Three wire codes for one condition | Nothing — **"but it gets worse with every slice"** | Cheap to fix, cheaper the sooner |
| **C-009** | An internal fault reaches a customer as a `422` | Nothing today | — |
| **C-017** | The onboarding honesty principle has no permanent home | Every future onboarding flow, wizard and assistant | **Pairs with C-320** — both are the first hour |
| **C-007** | The guided first run is a two-lane build | Nothing until M12.5 slice 5 | **Pairs with C-320** |
| **C-019** | A claim is invisible to the step meant to arbitrate it | Nothing — **"it has already happened once and will happen again"** | **Repository integrity.** Lane C can automate this; no ruling needed |
| **C-006** | Which lane owns `test_api_<module>.py` | Nothing. **A standing ambiguity every feature lane hits** | **One sentence closes it permanently** |
| **C-204** | The catalog explains nine words to nobody | R5-04 only | — |

---

## Summary

| | |
|---|---|
| **Open items owned by the product owner** | **28** — every one has a row here, and `--check` proves it |
| **P1 — a lane is waiting** | **7** |
| **…of which ratification only** | **2** (C-206, C-208) — **and they return Lane A's next slice** |
| **…of which collapse into TASK-900's RFC** | **1** (C-021), plus C-207 from P3 |
| **P2** | **9** |
| **P3 — blocks nothing today** | **12** |
| **Highest single unblock** | **[TASK-900](BACKLOG.md)'s RFC — 4 decisions retired, 7 slices released** |
| **Cheapest** | **C-206 + C-208 — two sentences, one whole slice** |
