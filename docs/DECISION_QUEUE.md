# Product Owner Decision Queue

**The single place the product owner reviews when making rulings.** Established 2026-08-05 by product owner directive.

> ## ⛔ Six of the 31 items on this page hold a named row. The other 25 hold nothing, and that is the number worth reading.
>
> **Re-measured 2026-08-09 against `BACKLOG.md`, not asserted.** ⚡ **An item is listed as blocking only when a task row's own `Status` names it** — ⛔ **not when it sounds important, and not because it was blocking last week.**
>
> | | Blocks | What it is |
> |---|---|---|
> | 🔴 **[C-1405](#-c-1405--the-entry-coverage-review-recommends-four-documents-and-three-of-them-block-work-already-released)** | **[TASK-1401](BACKLOG.md) · [1421](BACKLOG.md) · [1423](BACKLOG.md) · [1426](BACKLOG.md)** | **Commission three design documents.** ⚡ **The single highest-value decision on this page — it is four of the six** |
> | 🟠 **[C-338](#c-338)** | **[TASK-003](BACKLOG.md)** | Customer labels in the file that builds the prompt |
> | 🟠 **[C-1404](#-c-1404--where-do-machine-credentials-live)** | **[TASK-1413](BACKLOG.md)** | Where machine credentials live — three options, written |
> | ⏱️ **[C-334](#-c-334--the-hosted-evaluation-credential--ruled-not-yet-provided)** | **[TASK-202](BACKLOG.md) · [459](BACKLOG.md)** | ⚡ **Ruled and unprovided — one credential, and release is automatic on configuration.** Nothing to decide |
> | 🟡 **[C-003](#c-003)** · **[C-009](#c-009)** | **[TASK-454](BACKLOG.md)** | Both land on one row |
>
> ⚠️ **[C-306](#-c-306--the-one-that-argues-against-work-and-it-collides-with-d-128) is still the interesting one, and still blocks nothing.** **It argues *against* rebuilding a screen** — *"would discard fourteen findings from real product review"* — **and it predates [D-128](DECISION_REGISTER.md), which made the design the authority.** **It becomes P1 the moment a refinement slice reaches that screen.**
>
> ✅ **[C-421](#-c-421--a-lane-cannot-read-the-design-it-is-implementing-against--external) and [C-229](#-c-229--opportunity-intelligence-needs-a-door-and-d38-closed-that-one-deliberately) were the two items this banner named as blocking, and both closed on 2026-08-06/07** — **C-421 by [D-137](DECISION_REGISTER.md) §2 (the design was readable the whole time), C-229 by [D-141](DECISION_REGISTER.md) ① (the finalized design already contained the answer).** ⛔ **The banner went on naming them for two days, which is the defect this page exists to prevent, sitting at the top of the page.** ⚡ **It is now derived from the register and the backlog on each cycle rather than carried forward.**
>
> **This is the healthy state, not an empty document.** *"Our objective is not to close the maximum number of governance items. Our objective is to maximize engineering throughput."*
## 🟠 C-250 · When entry is unremarkable, what does the diagnostic code say? *(point ③ of three)*

> ⚡ **Found by Lane A BUILDING the entry engine, not by reading the design** — the third of three disagreements it reported, and **the only one that is a product question.**

📁 **The design tints rule 24 `HOME` and calls it *"the default and the most common outcome"*.** ⛔ **It cannot fire**: its condition is *"no other rule matched"*, and gate 3 always produces a reason.

> ## **When a person lands on Home with nothing remarkable about their entry, should the code read `HOME` — or the resolution code that chose the workspace, `SOLE_WORKSPACE` · `LAST_USED` · `FELL_THROUGH`?**

⚡ **It matters because the code is customer-facing infrastructure, not a log line.** 📁 **The design puts it *"in the support diagnostics bundle"* — whichever answer is right, support reads it, and changing it later invalidates every bundle already collected.**

✅ **Shipped meanwhile: the resolution code wins, and rule 24 is KEPT as the totality guard rather than deleted** — it is what makes `resolveEntry` total, and a router handed `undefined` fails far from the cause. ⛔ **Nothing is blocked.**

## 🟠 C-1404 · Where do machine credentials live?

> ⚡ **Found decomposing Settings under [D-204](DECISION_REGISTER.md) §4 — hidden work behind a visible screen.**

📁 **The design specifies API keys and webhooks: *"Scoped, rotatable, and logged per call"*, *"shown once at creation and never again"*, *"failed deliveries retry with backoff for 24 hours, then park with the payload retained."*** ⛔ **None of it exists, and no module owns machine credentials.**

🔴 **It is already load-bearing**: **[TASK-1407](BACKLOG.md) widens the entry engine to admit a non-human principal**, and this is where non-human principals would come from.

| Option | |
|---|---|
| ⓐ **A new `machine_identity` module** | ✅ **Honest** — a service principal is not a member. ⛔ **Needs an ADR** |
| ⓑ **Inside `workspace_tenancy`** | ✅ **Smallest change.** ⛔ **Least honest** — it already owns membership, and a key is not a person |
| ⓒ **Inside `platform_foundation`** | ⚠️ **It owns `infra/` and no runtime surface today** |

⛔ **Nothing is blocked** — **[TASK-1413](BACKLOG.md) is sequenced behind this and Lane A has 24 other startable rows.**


## 🔴 C-1411 · An audit stream: the reliable shape needs the frozen platform, the cheap shape is lossy

> ⚡ **Found by Lane A BUILDING the security stream, and it built everything that did not need you first** — 📁 **the table, the domain type, the repository and the `public/` contract are on `main`, green, with 401 Security Invariants passing.** ⛔ **Only the producers wait.**

🔴 **Four authentication journeys are on `main` today and NOTHING RECORDS THEM.** 📁 **[493](architecture/493-security-platform-architecture.md) names Workflow 1 as the producer and says nothing about how a fact born in the Better Auth tier reaches a table Python owns.**

| | How | The cost |
|---|---|---|
| ⓐ **The client reports it** | Next.js calls a new endpoint after Better Auth mints the token | ⛔ **Lossy by construction** — **it drops events exactly when something went wrong**, which is the population an audit stream exists for |
| ⓑ **The server records it** | The API records on first verification of a new session | ✅ **Reliable.** ⛔ **Needs `signora_platform/auth/`, which [§20a](../CLAUDE.md) freezes** — **product owner + ADR** |

⚪ **Recommended: ⓑ, under §20a's FIRST exemption rather than its third.** 📁 **The list opens with *"a tenancy, authentication, authorization, or secrets defect. Fix it, and add a Security Invariant proving it stays fixed"*** — ⚡ **and an authentication tier that produces no audit record is an authentication gap, not the platform being inconvenient.**

⚠️ **This office states that as a recommendation and declines to act on it.** 🔴 **Reading a gap as a security defect in order to reach an exemption is exactly the reasoning §20a exists to constrain, and the office that wants the answer should not be the one giving it.**

⛔ **Nothing else waits.** ✅ **Lane A has 18 other startable rows and the stream's foundation is already shipped.**

## ⚡ Design Clarifications — for the Design Authority, not for a product ruling

> **[D-207](DECISION_REGISTER.md) §2 · [D-208](DECISION_REGISTER.md) §6.** ⛔ **These are questions, not recommendations.** ⚡ **Each states the observed behaviour, the evidence and the impact — and deliberately does NOT propose which interpretation should win.** ⚠️ **Listed here because the queue is where a human looks; the OWNER is the Design Authority, and answering one as a product preference would be the conflation [D-207](DECISION_REGISTER.md) §2 corrects.**

| | Clarification | Classification | Impact if it changes | Blocks |
|---|---|---|---|---|
| 🔴 | **[C-1407](LANE_COORDINATION.md) — rule 24 `HOME` cannot fire**, while the same document tints it *"the default and the most common outcome"* | **CONTRADICTORY DESIGN** | 🟢 **LOW in code** — one rule's reason string. 🔴 **HIGH in support**: the code goes in the diagnostics bundle, so **changing it after launch invalidates every bundle already collected** | ✅ **Nothing** |
| 🟠 | **[C-1408](LANE_COORDINATION.md) — rule precedence.** Read flat, rules 18–24 are unreachable; §02's gate ladder is a second reading in the same document | **INCOMPLETE DESIGN** | 🟠 **MODERATE, contained** — `RULES` is a data table walked in order, so a precedence change is a reordering plus fixtures. **What it invalidates is every code already emitted** | ✅ **Nothing directly** |
| 🟠 | **[C-1410](LANE_COORDINATION.md) — rule 04's landing with no intent** is not stated anywhere | **MISSING DESIGN** | 🟢 **LOW as code** — one route. 🟠 **MODERATE as experience**: it is where a person lands when their session dies and they were not going anywhere in particular | ⏸️ **[TASK-1426](BACKLOG.md)** — **the only row held by a clarification** |
| 🟠 | **[C-1409](LANE_COORDINATION.md) — rule 23's start-page preference** *"wins"*, with no rule for when the page becomes unreachable | **INCOMPLETE DESIGN** | 🟢 **LOW** — [TASK-1422](BACKLOG.md) is already building the same clearing mechanism for *last-used*, so the answer costs a call site rather than a design | ✅ **Nothing** |
| 🔴 | **[C-258](LANE_COORDINATION.md) — the scope ladder has no page-scope failure state**, and no way to say a region failure interrupted something. **Raised by Lane A holding [TASK-1428](BACKLOG.md)**, by measuring thirteen call sites before composing | **INCOMPLETE DESIGN** | 🟠 **MODERATE** — ⚡ **[TASK-1409](BACKLOG.md)'s own row predicted this in advance**: *"if its region scope will not carry `StatedAbsence`'s sentence, that is a finding against the ladder, not a licence to keep two."* ✅ **The lane took it at its word** | ⏸️ **Five of [TASK-1428](BACKLOG.md)'s thirteen call sites.** ✅ **The other eight compose cleanly and are being built** |

> ## ✅ **Five clarifications, and between them they hold one row and five call sites.** ⛔ **23 of 24 entry rows continue.** ⛔ **Exactly one waits, and its backlog row declares WHY — which clarification, why it matters, and what assumption it would otherwise have to invent** ([D-208](DECISION_REGISTER.md) §3).

⚡ **What shipped meanwhile is stated as fact rather than as a proposal**: the resolution code is emitted, rule 24 is retained as the totality guard, and **a test asserts it cannot currently fire** — ✅ **so whichever way Design answers, the assumption is visible and the test fails if the answer differs.**

## 🔴 C-1405 · Commission four design documents — the Entry Coverage Review's own priority order

> ## ✅ **Governance reviewed the document adversarially and ADOPTS it.** ⚡ **The architecture is sound and the four-document recommendation is better than the eleven the brief implied.** ⛔ **What is asked here is a commissioning decision, which is not this office's** ([§21](../CLAUDE.md)).

| | Document | The review's argument | What it unblocks here |
|---|---|---|---|
| **①** | **Session Continuity** | 📁 *"the only genuinely cross-cutting gap"* — **five shipped documents already promise behaviour only this specifies** | [TASK-1426](BACKLOG.md), and rule 04's half of [TASK-1423](BACKLOG.md) |
| **②** | **Home** *(expand Executive Dashboard)* | **Rule 24 is the most travelled path and three of four outcomes are undrawn** | [TASK-1424](BACKLOG.md), [TASK-1425](BACKLOG.md) |
| **③** | **Workspace Chooser** | 📁 *"the single largest hole… no document draws it"* | 🔴 **[TASK-1421](BACKLOG.md) entirely** |
| **④** | **Security Gates** | **A challenge raised against somebody mid-sentence has no owner** | [TASK-1410](BACKLOG.md)'s screen, rule 05 |
| **⑤** | **Workspace Lifecycle States** | **One mechanic split across three documents, which is why none is complete** | rules 15–17 |

⚡ **Two things need no commissioning and this office recommends them TODAY:** ✅ **the four textual contradictions** (Executive Dashboard breadcrumb and route · App Shell rail · App Shell's *lands on Home* sentence · Design Review's screen count) and ✅ **the *Specified in* column on the Entry rules table.** 📁 **The review's own argument for putting them first: *"Every day they wait, more code is written against the wrong model."*** ⛔ **Both are edits to the upstream snapshot, which [D-138](DECISION_REGISTER.md) makes the authority — the product owner's to make, not this office's to patch locally.**

⚠️ **This office's error, recorded rather than absorbed**: **[TASK-1421](BACKLOG.md) and [TASK-1423](BACKLOG.md) were released to Lane A as *cheap* two hours before this review was read.** ✅ **Both are now `BLOCKED` on this item.** ⛔ **The finding that produced them is unaffected — `/workspaces` still does not exist, so [TASK-1401](BACKLOG.md) still must not be wired.**

## 🟠 C-1406 · The review says the engine has no routing defect; the lane that built it found three

> 📁 **The review, four times: *"Do not change: any rule"* · *"The audit found no routing defect"* · *"the engine survives this review unaltered"* · scorecard *"0 changes needed to Entry's routing logic"*.**

⛔ **Lane A found three by building the table** ([C-250](LANE_COORDINATION.md)) — **rule 24 cannot fire while the same document calls it *"the most common outcome"*; seven rules are dead read flat; rule 04's route is `(intent preserved)` with nowhere to land when there is no intent.**

🔴 **The review classifies rule 24 as *B · expand Home* and never notices it cannot fire.** ⚡ **A completeness audit that reads the table without executing it cannot find this class** — ✅ **that is the honest limit of the method, not sloppiness.** ⛔ **But *"no routing defect"* is stated without that qualification, and a reader will take it as verified.**

✅ **Recommendation: adopt the coverage findings in full; treat *no routing defect* as UNTESTED rather than false.** **Nothing is blocked** — the engine ships with all three handled, and [C-250](LANE_COORDINATION.md) ③ is the product decision that remains.

## 🔴 C-1401 · `CLAUDE.md` tells every lane to read four queue fields that were deleted

> ## ⛔ **One word of approval. The replacement text is written and nothing else is needed.**
>
> 📁 **[`CLAUDE.md`](../CLAUDE.md) §20e still instructs: *"Read your queue first — `current`, then `next`, then `future`, in that order"* and *"takes `current`, and starts."*** ⛔ **[D-199](DECISION_REGISTER.md) deleted all four fields.**

⚡ **This is the dispatcher model [D-198](DECISION_REGISTER.md) removed, surviving in the one document that outranks the ruling that removed it.**

| | |
|---|---|
| **Lines** | **946, 1031, 1035** — and **946 · 1187** still say `lane-<a\|b>.toml`, and **Lane B was closed by [D-165](DECISION_REGISTER.md)** |
| **Blocks today** | ⚠️ **Nothing — by luck.** **Lane A read [`BACKLOG.md`](BACKLOG.md) instead and claimed [TASK-1400](BACKLOG.md) correctly.** ⛔ **A lane obeying the constitution literally reads `current` and finds nothing** |
| **Whose fault** | ⛔ **This office's.** **D-198 was implemented in the data, the projection, the queues and four instruments — and the document lanes read first was never checked** |
| **What is asked** | ✅ **Approval to apply the four replacements in [C-1401](LANE_COORDINATION.md).** ⛔ **Both previous Lane C edits to `CLAUDE.md` were instructed ([D-170](DECISION_REGISTER.md) §2, [D-195](DECISION_REGISTER.md) §8); this office will not make a third undirected** |

✅ **Everything generated is already correct** — `coordination.py` emits `backlog`, `state-check.py` **refuses** a queue carrying a retired field, and both dashboards read the new shape.

## 🟠 C-246 · Does the customer read *Workspace* or *Organization*?

> 📁 **The onboarding design labels a step *Workspace*; [ADR-0034](architecture/adr/) says a customer reads *Organization*.** ⛔ **Two approved sources name one thing differently, and Workflow 8 renders whichever a lane reads first.**

⚠️ **Blocks nothing.** **What it changes is what the Workflow 8 review is shown** — ⛔ **and a reviewer holding the design will read a word the ADR forbids, then file it as a defect against a lane that followed the design.**

✅ **Whichever you rule, one of the two documents is corrected** rather than the screen deviating from both. ⚡ **[`vocabulary.toml`](coordination/vocabulary.toml) is where the answer lands, so the next screen cannot rediscover it.**

## 🔴 C-245 · May an invitation link alone reveal a company's name, headcount, employee and role?

> ## ⛔ **The one blocking decision. It is why [Workflow 7](coordination/workflows.toml) is `blocked`, and it reached this queue the cycle QE integrated it — as promised.**
>
> 📁 **Screen `13 Accept invitation` shows six facts to a reader who has not entered the tenant.** ⛔ **No endpoint could serve them: `workspace_tenancy`'s four invitation routes are all workspace-scoped and require membership or admin.**

⚡ **Lane A found it by reading the routes rather than the screen, and stopped rather than inventing an endpoint.** ✅ **The accept path already ships at `/join/[workspaceId]`, so nothing customer-facing regressed.**

### The question, at its smallest

> ## **An invitation link is a bearer token.** ⛔ **Whatever screen `13` shows, a forwarded link shows to a stranger.**

| | | |
|---|---|---|
| ⚡ **"Show all six"** | **The design as drawn** | ✅ **Warmest experience.** ⛔ **Accepts that a forwarded invitation discloses headcount and an employee's name and role to anyone** |
| **"Show a reduced set"** | **Workspace name and inviter only** | ✅ **Enough to answer *am I in the right place*.** ⚠️ **Departs from the approved design, so the SNAPSHOT is corrected rather than the row deviating** |
| **"Show nothing until accepted"** | ⛔ **Safest** | **Makes screen `13` largely pointless** |

⛔ **Either of the last two needs a new unauthenticated, invitation-token-scoped endpoint** — ⚡ **a real capability with a real security boundary, belonging to `workspace_tenancy` rather than to the screen.**

✅ **Whichever you rule, this office writes the endpoint's contract before Lane A returns to Workflow 7.**

## 🟠 C-247 · Is a theme preference per person, or per organization?

> ⚡ **Workflow 9 · User Profile, found by Lane A building against the design.** ⛔ **Does not block: the screen ships without the contested behaviour rather than guessing it.**

⚡ **[TASK-470](BACKLOG.md) already flagged this shape: it is the first row whose data is ACCOUNT-scoped rather than workspace-scoped, and the answer decides its `tenancy_policy.py` class.**

## 🟠 C-248 · Four profile fields are locked as *"Managed by"*, and no directory sync exists

> ⛔ **Four profile fields render locked, which asserts a directory-sync capability the platform does not have.** ⚠️ **Split out of C-247's row on 2026-08-09** — ⛔ **two items under one heading is one item nobody can route to, which is exactly what `decision-queue --check` had been reporting.**

📁 **Better Auth's `sso` plugin has the capability and is unregistered ([TASK-493](BACKLOG.md)).** ⛔ **Until it is, the lock is a false affordance — the class this lane has now refused six times.**

## 🟠 C-249 · Two rows on the AI screen are policies, not preferences

> 📁 **The AI-preferences screen offers two controls that read as personal settings and are actually workspace POLICY.** ⛔ **A person toggling their own copy of a policy either does nothing or silently changes it for everybody, and both are worse than the control not existing.**

⚡ **Related to [496](architecture/496-security-architecture-blueprint.md)'s quota primitive: *"may spend up to here"* is authorization, not preference** — ✅ **which is the architectural reason this cannot be a per-person toggle.**


## ✅ The Authenticated Entry reconciliation — what it found, and the work it became

> ## ⚡ **The audit ran, the findings were concrete, and every one is now a row.** ✅ **Kept here as the record of what was found and where it went — not as something waiting on you.**

### ① 🔴 The entry decision already exists — hardcoded, in a module, racing another mechanism

📁 **`frontend/app/(auth)/sign-in/sign-in-form.tsx:148` — `router.push('/')`.** ⛔ **That IS the entry decision, made by a module, and the specification forbids exactly it**: ***"no module performs its own entry redirect."***

⚠️ **And the file's own comment records a second problem this office had not seen:** ***"Auth navigates to its own `callbackURL` and beats this push"*** — **so there are TWO redirect mechanisms racing, and which wins is timing.**

✅ **Six files perform redirects today**: `sign-in-form`, `sign-up-form`, `reset-password-form`, `join/[workspaceId]`, `(app)/layout`, `accounts/[accountId]`. ⚡ **Under the spec, the first five are entry decisions that belong to one engine.**

### ② 🔴 Two rows Lane A HOLDS RIGHT NOW have the defect the spec names

📁 **Contradiction ④, verbatim: *"Onboarding completes and lands somewhere unspecified; workspace creation success also lands somewhere unspecified. Two flows with no defined exit."*** ✅ **Resolution: *"Both exit through the routing engine with `intent=null`… Neither flow chooses a destination itself."***

⛔ **[TASK-468](BACKLOG.md) and [TASK-469](BACKLOG.md) are both `CLAIMED` and neither said anything about its exit.** ✅ **Both now carry the constraint, and — because a queue file reaches a lane only through `integration` — it also went out on the notice channel, which does not wait for QE.**

### ③ ⚠️ Two contradictions are between documents in our own snapshot

⛔ **The Executive Dashboard's breadcrumb *Home › Executive Dashboard*, and the navigation rail listing Home with the dashboard unlisted.** ⚡ **Both are superseded by *Home is one route with four compositions* — so two approved design documents now disagree with a third, inside the authority [D-138](DECISION_REGISTER.md) makes authoritative.** ✅ **Neither is built, so the cost is zero if the snapshot is corrected at the next refresh; it is a defect only if a lane implements the older one first.**

### ✅ What remains compliant

**Workflows 1, 2, 3 and 4 are on `main` and none is contradicted** — ⚡ **they end *at* the entry decision rather than making one, except for the single `router.push('/')` above.** ✅ **Workflow 7 is `blocked` for unrelated reasons and its invitation routing is rule 12's, which the spec now defines.**

### ✅ RESOLVED 2026-08-08 — the block was extended and the work exists

✅ **[D-195](DECISION_REGISTER.md) §8 extended Lane C to `1400`+ and every finding above is now a row.** ⚡ **[TASK-1401](BACKLOG.md) repairs the five module-owned redirects; [TASK-1400](BACKLOG.md)–[1407](BACKLOG.md) are the engine that replaces them.** ⛔ **The two snapshot contradictions remain a *refresh* action rather than a row, and [TASK-468](BACKLOG.md)/[469](BACKLOG.md) carry their exit constraint.** **Nothing here is waiting on the product owner.**


## ⚠️ One blocking decision is not queued yet — it is still on Lane A's branch

> 🔴 **May an invitation link alone reveal a company's name, headcount, employee and role?** ⛔ **It is why [Workflow 7](coordination/workflows.toml) is `blocked`, and it is the product owner's.** *(Lane A filed it; the id is theirs and is deliberately not repeated in a heading here, because a heading is what makes this a queue row.)*
>
> ⚠️ **Raised by Lane A and still on `lane-a-product-surface`.** ⛔ **This office will not write a queue row against an item that does not exist on this branch — that is a reference to nothing, and the check refuses it correctly.** ✅ **It enters this queue the cycle QE integrates, with the three options and this office's recommendation prepared.**

## 🟠 C-244 · Should a password reset actually sign other devices out?

> 📁 **Screen `09` says it does. Nothing does it.** ✅ **Lane A shipped screens `09` and `10` WITHOUT the claim rather than printing an untrue one — the fifth false affordance this lane has refused.**

⚡ **Better Auth's `multi-session` plugin is installed and unregistered** ([TASK-493](BACKLOG.md)), **so the capability is bought and one line away.** ⛔ **Whether it SHOULD happen is a security behaviour and yours.**

| | |
|---|---|
| ⚡ **"Yes"** | ✅ **The design becomes true; the screen's sentence returns.** **One line in [TASK-493](BACKLOG.md), which is already prepared** |
| **"No"** | ✅ **Zero work — the copy is already absent.** ⚠️ **The snapshot is corrected at the next refresh so the next lane does not re-raise it** |

⛔ **Blocking nothing either way.** ⚡ **Listed because leaving a design and an implementation disagreeing is how the next lane re-discovers it, which is [C-241](LANE_COORDINATION.md)'s exact shape.**


## 🟠 D-191 · Workflow-level certification — the premise does not hold, and the cost is elsewhere

> ## ⛔ **Recommendation: keep certification as it is. Neither Option A nor Option B addresses what is actually consuming cycles.**
>
> ⚡ **You asked to be challenged rather than agreed with. The measurement disagrees with the premise, and that is the most useful thing this package can say.**

### ① The premise, tested — only 37% of cycles certify a slice

**120 certification cycles on `main`, classified by what each one actually promoted:**

| | | |
|---|---|---|
| **Governance / other** | **53** | **44%** |
| ⚡ **Slice certification** | **45** | **37%** |
| 🔴 **QE's own corrections** | **18** | **15%** |
| **Planning-only** | **4** | **3%** |

> ## ⛔ **Batching slice certification per workflow addresses 37% of the cycles.** ⚡ **59% are governance and QE repairing its own defects — and that is where the overhead lives.**

### ② The batching you want is already the rule, and already happening

📁 **[§20e](../CLAUDE.md), verbatim: *"Every slice at `IN VALIDATION` is taken at once — never held because more are expected in the same implementation area."*** ⚡ **QE certifies a *snapshot*, not a slice.** **Measured: 20 of 45 slice cycles carried more than one row; the mean is 1.7.**

⛔ **So the model already permits what Option B asks for.** ⚠️ **What it does not permit is deferring *promotion*, and that is the part that would break something.**

### ③ 🔴 The evidence that decides it — certification has never cost throughput

**Searched the backlog, the coordination register and the bug register for a lane blocked on QE.** ✅ **Zero instances.** 📁 **[§20e](../CLAUDE.md)'s *Continuous execution* is why: *"the moment a lane sets `IN VALIDATION`, it returns to `BACKLOG.md` and claims the next `READY` task."*** **Lane A's own reports confirm it every cycle.**

**What has actually idled Lane A, from the record:**

| | |
|---|---|
| 🔴 **Planning depth** | **136 consecutive idle cycles** |
| 🔴 **Synchronization** | **[C-435](LANE_COORDINATION.md), five instances in two days, one of which shipped a test asserting the opposite of a ruling** |
| 🔴 **Missing capability** | **[C-245](LANE_COORDINATION.md), [B-214](BUGS.md) — Workflow 7 blocked on both** |
| ✅ **Certification** | **Never** |

> ## ⚡ **Certification frequency costs QE's time. It has never cost Lane A's, and Lane A is the constraint.** ⛔ **Optimising a non-constraint moves nothing.**

### ④ ⚠️ What Option B would break, in the repository's own words

📁 ***"Every commit on `main` was itself certified, by the repository-wide certification process, before it was promoted."*** 📁 ***`promoted commit SHA == certified commit SHA`.***

⛔ **Certifying once per workflow means either promoting commits that were never certified — which voids the central release guarantee — or not promoting until the workflow ends, which is the large-batch anti-pattern you correctly rejected.** ⚡ **There is no third reading: [§20e](../CLAUDE.md) binds promotion to certification by SHA equality.**

🔴 **And there is direct counter-evidence for deeper batches.** 📁 **QE's own dashboard: *"QE certified and promoted four Timeline slices without noticing. Every gate was green because a composition root is the one file no module's own suite covers."*** ⚠️ **A defect already survived four slices. A workflow-deep batch is ten to fifteen — ⛔ the failure this model has already had, made three times deeper.**

### ⑤ ✅ Option D — the recommendation

| | |
|---|---|
| **Certification** | ⛔ **Unchanged.** **Per snapshot, taking every `IN VALIDATION` slice at once — which is already the rule** |
| ⚡ **Attack the 59%** | 📁 **[§20e](../CLAUDE.md) already says *"A cycle is warranted by executable change, not by movement"* — and 44% of cycles are governance.** 🔴 **The rule exists and is not being applied.** ✅ **`make certified ARGS="--next-cycle"` already answers *does anything here change what the software does* — the mechanism is built and unused** |
| ⚡ **The 15% is closing** | **QE's own corrections are the [B-411](BUGS.md)/[B-412](BUGS.md) class — scripted edits damaging registers.** ✅ **`_structural_findings` now refuses an unannounced row deletion, and the same discipline applies to QE's tooling** |
| ✅ **The customer milestone you want already exists** | ⚡ **[D-169](DECISION_REGISTER.md) made Product Owner review a *checkpoint per workflow*, not per slice.** ⛔ **You are describing a **review cadence**, and it is already once-per-journey.** **Certification is a quality gate; the milestone is the review** |

> ## ⚡ **The distinction worth keeping: certify continuously because it is cheap and catches defects next to the code that caused them; review per workflow because that is where a customer journey becomes meaningful.** ✅ **Signora already does both.**

### ⑥ What would change my recommendation

⚠️ **Stated so this is falsifiable rather than a defence of the status quo:**

⛔ **If a cycle's wall-clock ever delays a promotion twice — measured, not felt — [TASK-413](BACKLOG.md) already exists for exactly that trigger and this recommendation reverses.** ⚡ **Today `make smoke` runs ~200s and no promotion has been recorded as delayed by it.**

⛔ **Or if slice cycles rise above ~60% of the total, batching starts to matter.** **They are 37%.**


## What the ruling released

| | |
|---|---|
| ⚡ **[TASK-901](BACKLOG.md)** | **Seven independently certifiable slices** — [ADR-0404](architecture/adr/0404-platform-composition.md) ratified [435](architecture/435-platform-composition-rfc.md) whole |
| **[TASK-904](BACKLOG.md)** | Team Management — C-206 and C-208 both ruled |
| **[TASK-003](BACKLOG.md)** | Attribute vocabulary — C-018 ruled |
| **[TASK-406](BACKLOG.md)** | ICP measurement — C-328 ruled, at changed scope |
| **[TASK-201](BACKLOG.md)** | Epic C — C-221 ruled, at narrowed scope |
| **[TASK-400](BACKLOG.md)** | A6 — C-321 ruled |
| **[TASK-418](BACKLOG.md)** | `signora_platform/` has a permanent owner — **C-416 ruled** ([D-073](DECISION_REGISTER.md)) |
| **Lane A's resolution route** | The authorization `Resource` — **C-224 ruled**, and `CLAUDE.md` §20a's carve-out now names it |
| **The vocabulary** | `Owner` and `Match` — **C-420 ruled** ([D-087](DECISION_REGISTER.md)). **Qualified, not renamed** |

**Eight tasks and seven slices, from two sittings.** **A ruled item leaves this file the same day** — its record is [LANE_COORDINATION.md](LANE_COORDINATION.md)'s, and its ruling is [DECISION_REGISTER.md](DECISION_REGISTER.md)'s.

## How this stays true

**Two kinds of column.** **Derived** — status, blocks, lanes waiting — computed from [`LANE_COORDINATION.md`](LANE_COORDINATION.md), [`BACKLOG.md`](BACKLOG.md) and [`modules.toml`](coordination/modules.toml). **Judgement** — priority, recommendation, cost — Lane C's.

> **`python3 infra/decision-queue.py --check` fails when this file and the register disagree.** It reported every ruled row still sitting here within a minute of the ruling, which is how this rewrite got scoped.

> ⚠️ **And on 2026-08-06 it caught the other direction, which is the one that cannot be seen from inside this document.** **Five items were `OPEN`, owned by the product owner, and had no row here** — so this page claimed to be the single place to review decisions and was not. **They are added below.**
>
> ⚡ **Four *more* would have been escalated and should not have been.** **`C-201`, `C-334`, `C-412` and `C-025` each carried a ruling in a blockquote directly above a `Status` field that still read `OPEN` or `READY FOR PRODUCT DECISION`.** ⛔ **That is this tool's *"most misleading failure"* by its own docstring — attention spent on something already decided.** **All four fields are corrected in the register.** **The lesson is the one [C-213](LANE_COORDINATION.md) taught: a fact stated in prose beside a field is a fact no instrument reads.**

---

## ✅ Recommendation — **contextual, reached by drilling. Not a first-class destination.**

⚡ **[D-139](DECISION_REGISTER.md) ① asked for a navigation model rather than a question, and the finalized design answers it directly.** **Measured from [`design-snapshot/screens/Fortune Signora Opportunity Intelligence.dc.html`](../design-snapshot/screens/), which this office could not read when the item was raised.**

| Evidence | |
|---|---|
| ⚡ **The breadcrumb the design draws** | **`Deals / EMEA enterprise / Vantage renewal — Q4 FY26`** — ⛔ **three levels deep, and the screen is the leaf** |
| **Every label is singular** | *Opportunity summary · Update deal · Deal health · Competitive position · Next best action · Add to forecast call* — ⛔ **not one list affordance on the page** |
| **It is a record page** | **The same shape as Account 360**, which also has no navigation entry and is reached by opening an account |

> ## **The design does not draw a destination. It draws a leaf, and a leaf is reached by drilling.**

**So the five options resolve like this:**

| Option | |
|---|---|
| ⛔ **First-class navigation destination** | **Refused by the design itself** — the breadcrumb places it under two parents, and D38's bar (*"adding one back is a claim that needs defending"*) is not met by a page with no list |
| ✅ **Contextual from Account 360** | **Recommended, primary.** The account brief already carries the opportunity; opening it is the customer's existing motion |
| ✅ **Contextual from the attention list** | **Recommended, and it is the journey that already ships** — *"which accounts should I work on today?"* → open the one that moved |
| ✅ **Accessible through Search** | **Recommended, and already designed** — the App Shell specifies **`08 Global search`** and **`09 Command palette`**, which is how a named deal is reached without a list |
| ⛔ **Intentionally not exposed** | **Refused** — three entrances is exposure; the screen is reachable, just not from the rail |

⛔ **What this does *not* claim.** **The App Shell design binds its navigation items from data (`{{ n.label }}`), so this office cannot read the rail's item list and does not assert what is on it.** ⚡ **The recommendation rests on where the *screen* places itself, which the design states in full.**

✅ **If ruled as recommended, [TASK-441](BACKLOG.md) needs no navigation work at all** — **the entrances are Account 360, the attention list and search, and all three exist.** ⛔ **[D38](architecture/39-product-review-findings.md) is not reversed and needs no amendment.**

## 📌 C-331 · TASK-003 changes what the model is shown, which un-releases the narration prompt

| | |
|---|---|
| **The problem** | **[TASK-003](BACKLOG.md) is `IN PROGRESS` and the change is small and understood** — **but changing what the model is shown un-releases the prompt** (§10: *a released version is immutable; a change is a new version*), **and re-releasing needs an evaluation run this workstation cannot perform** |
| **Blocks** | **Three rows, consolidated rather than raised three times** |
| **Priority** | **P2 — and it collapses into [C-334](#-c-334--the-hosted-evaluation-credential--ruled-not-yet-provided) the moment the credential lands** |
| **Recommended** | ✅ **Take no separate action.** ⚡ **This is not an independent decision** — the credential [D-111](DECISION_REGISTER.md) already approved is the whole of what it needs. **Listed so it is visibly accounted for rather than quietly assumed** |

## 📌 C-335 · Epic C's next stage is four deep, and two of the four are nobody's to take

| | |
|---|---|
| **The problem** | **[TASK-428](BACKLOG.md)'s S3 sits behind four dependencies; ① is Lane C's and ③ is yours.** ✅ **② and ④ resolve themselves once those move** |
| **Blocks** | **[TASK-428](BACKLOG.md)'s S3 entirely** — ⛔ **not its `commercial_profile` half**, which the lane is building |
| **Priority** | **P3 — the lane is not idle on it** |
| **Recommended** | ✅ **Answer ③ when convenient.** ⚠️ **Recorded here because a chain four deep with two unowned links is how a stage becomes permanently *next*** — and nothing on the board makes that visible |

---

## ✅ TASK-427 · RESOLVED — Lane B took it, and this entry is stale

> ⛔ **Removed as a question 2026-08-07.** **`TASK-427` is `IN FLIGHT` with Lane B.** ⚡ **The placement question answered itself when a lane claimed it, and this page went on asking for a decision that no longer existed** — **which costs the one thing this page exists to protect, your attention.** ⚠️ **`decision-queue.py --check` did not catch it: it compares `C-` items against the register and does not look at `TASK-` rows.** **Recorded rather than fixed in the instrument — [D-155](DECISION_REGISTER.md) ② forbids expanding tooling while Workflow 1 is unimplemented.**

<details><summary>The original entry, kept because a dated record is not rewritten (§2)</summary>

### TASK-427 · The People domain's trigger has fired, and placing it is yours

**Not a `C-` item and deliberately** — **nothing is undecided.** [D-074](DECISION_REGISTER.md) ruled the direction; **what is left is a position in the queue, which is a priority act and not Lane C's.**

| | |
|---|---|
| **Summary** | **[TASK-427](BACKLOG.md) · M-D · the People domain** is `SEQUENCED` with the trigger *"the first dependent customer-facing capability enters implementation."* ⚠️ **Measured 2026-08-05: fired.** **[TASK-202](BACKLOG.md) is `READY` and its own row says *"phase 4 needs Epic C"*** |
| **Why it is here rather than in the `READY` queue** | **Your instruction**: *"do not assign implementation immediately… make it part of the planned execution sequence so implementation begins at the correct time."* **The row is prepared and unplaced.** A lane may not insert a `READY` task and Lane C may not reprioritize — **so one move by you is the whole remaining step** |
| **Impact** | **Four screens across waves 1–4.** Account 360 has already shipped two ⬜ stated absences; **AI Copilot is the next one to pay** |
| **Blocked tasks** | **[TASK-428](BACKLOG.md) entirely.** TASK-429 and TASK-430 have their own, later triggers |
| **Lanes waiting** | **None yet, and that is the argument for placing it now rather than the argument against.** ⚠️ ~~Epic C is assigned to **Lane A**~~ — **wrong, corrected 2026-08-06; see below** |

> ## ⚠️ **Corrected 2026-08-06 — this entry named the wrong lane, and the row's real blocker is narrower than *"placement."***
>
> **Measured, not recalled:** **[`modules.toml`](coordination/modules.toml) gives `knowledge_graph` and `commercial_profile` to Lane B · [`queues/lane-b.toml`](coordination/queues/lane-b.toml) is the only queue naming `TASK-201` · and this entry said Lane A.** **Two governance documents named different lanes for one epic** — **[C-213](LANE_COORDINATION.md)'s class exactly, in a document this office wrote.**
>
> ⚡ **And the sharper finding: `modules.toml` has no `people` row at all.** **[TASK-427](BACKLOG.md)'s own Module cell says so — *"`modules.toml` gains a row when this is placed, not before."***

| | |
|---|---|
| ⚡ **So the ask is one line, not a priority act** | **A `[people]` row in [`modules.toml`](coordination/modules.toml) naming an owner.** ⛔ **Module ownership is never Lane C's** (§20e, *what Lane C never does*), so this office cannot write it however obvious the answer looks |
| ✅ **The answer does look obvious, and that is offered as input** | **Lane B holds `knowledge_graph`, `commercial_profile` and the `TASK-201` parent row.** §20e's precedence — **① product architecture · ② bounded context · ③ long-term maintenance** — points the same way |
| ⚠️ **Why `READY` alone would not have worked** | **Setting it `READY` is this office's** (§20e — *fitness, not priority*), **and a `READY` row in a module no lane owns is unclaimable** — the [C-412](LANE_COORDINATION.md) defect. **So this row is the one place where fitness genuinely is not enough** |
| 🟢 **What it is not** | **Not a ruling.** [D-074](DECISION_REGISTER.md) approved the domain; [ADR-0400](architecture/adr/0400-person-as-an-entity.md) is ratified; [441](architecture/441-people-roadmap.md) is the plan; the trigger fired on 2026-08-05. **One registry line and a queue position** |
| **Priority** | **P1 — it is in front of a wave that is claimable today** |
| **Recommended** | ✅ **Place [TASK-427](BACKLOG.md) in `READY` above [TASK-202](BACKLOG.md).** **Nothing gates it** — no ruling, no provider, no missing module. **Alternative, if wave 2 should not wait**: place it immediately *below* TASK-202 and accept that AI Copilot's phase 4 stalls where phases 1–3 do not |

</details>

## ✅ TASK-434 · RESOLVED — `PROMOTED`, and this entry is stale

> ⛔ **Removed as a question 2026-08-07.** **`TASK-434` reads `PROMOTED` in [`BACKLOG.md`](BACKLOG.md) — it is on `main`.** ⚡ **It was correctly flagged as the only time-critical row on this page, the sequencing argument was made, and it shipped.** ⚠️ **Same class as TASK-427 above: a resolved row still asking for a ruling.**

<details><summary>The original entry, kept because a dated record is not rewritten (§2)</summary>

### TASK-434 · The only time-critical row on this page

**Not a shape question — you asked Product Office to determine the architectural home and [443](architecture/443-account-matching-capability.md) determines it, at 🟠 with no ADR and no new dependency edge.** **What is yours is *when*.**

| | |
|---|---|
| **Why now** | **[TASK-406](BACKLOG.md) is `IN PROGRESS` with Lane B**, and its acceptance criterion is *"**the backtest reports both cohorts, never in-ICP alone**"* — **which requires a predicate deciding which an account is.** **Measured on `integration`: no matching code has landed.** The window is open **by days** |
| **Impact if it closes** | **Sixteen consumers** inherit whichever interpretation TASK-406's backtest happened to need — including **Workflow rule conditions**, **Epic E1's CRM arrival** and **AI Research cohorts**, none of which was on any list |
| **The ownership answer** | **`commercial_profile`, and explicitly *not* because TASK-406 needs it first** — **the criterion vocabulary is defined there and evaluating elsewhere means a second copy of it.** **The move that makes it fit: the contract forbids that module from *reading* the pipeline and does not forbid it from being *given* facts.** **`evaluate(criteria, attributes)` is pure** — zero new edges, `lint-imports` unchanged |
| **⚠️ The finding that makes it foundational** | **The two sides do not speak the same language.** A customer types `SaaS`; a provider reports `Computer Software`; **string equality returns `False` and the account silently drops out of its own ICP.** **`unmeasured` must be a value in the type, never `false`** |
| **Blocked tasks** | **None today.** **This is the argument for acting, not against it** |
| **Lanes waiting** | **None.** Lane B is building TASK-406 and would consume this rather than wait for it |
| **Priority** | **P0 on timing · P3 on difficulty.** Two small slices |
| **Recommended** | ✅ **Sequence [TASK-434](BACKLOG.md) ahead of TASK-406's backtest slice.** ⚠️ **First slice is a prerequisite regardless of any of this**: **`commercial_profile/public/` publishes thirteen views and *not one is the ICP* — no module can read the criteria at all today**, and every one of the sixteen consumers is blocked on that one missing read port. **[ADR-0403](architecture/adr/0403-signal-engine-reads-a-declaration.md) is the ratified precedent for exactly this shape** |

</details>

## 📌 C-338 · TASK-003 as you ruled it would change evidence identity — Lane B stopped rather than shipped it

⚡ **[C-018](LANE_COORDINATION.md) is `RULED` and Lane B holds [TASK-003](BACKLOG.md).** ⛔ **Implementing the ruling as written would put customer-facing labels into the file that builds the evidence digest — which changes what an evidence identity *is*.** **Lane B raised it and wrote no code**, which is the correct order and worth saying so.

| | |
|---|---|
| **State** | **`READY FOR PRODUCT DECISION`** — ⚡ **the analysis and the alternatives are already in the row.** ⛔ **Lane B did not mark it `READY FOR IMPLEMENTATION`**: that is yours on a ruling |
| **What it holds** | **[TASK-003](BACKLOG.md)**, `IN PROGRESS` with **nothing written** |
| ⚡ **The question, at its smallest** | **Did [C-018](LANE_COORDINATION.md)'s ruling mean the label reaches the digest, or only the surface?** ⛔ **§2 — *determinism outranks convenience*, and evidence identity is the repository's most load-bearing derived value** |

</details>

## 🟡 C-433 · §19 names a command flag that does not exist

✅ **Nothing is blocked and this needs one sentence, not a decision.** ⚡ **Lane A ran the command §19 tells it to run, and reported the gap rather than quietly skipping the gate.**

| | |
|---|---|
| **The measurement** | **§19: *"`python3 infra/certification-guard.py --journeys` names which specs the change selects."*** ⛔ **`error: unrecognized arguments: --journeys`.** ⚠️ **Checked further before reporting, because a missing flag and a renamed one are different defects: `--plan` exists and lists sixteen gates and zero Playwright specs.** **It is not renamed; it does not exist** |
| ✅ **Recommended — correct §19** | **One sentence: say the selection is the lane's judgement, or point at `--plan`, which exists.** ⚡ **[D-156](DECISION_REGISTER.md) ⑦ defers building it — Lane A demonstrated the flag is not needed by writing its journey without it** |
| ⚡ **§19 already contains the argument** | **Three paragraphs away, about the headed-execution policy: *"a rule stated before the mechanism exists is the defect this file warns about, so the row exists rather than the claim."*** |
| ⛔ **Why this office neither built it nor edited §19** | **Building it is deferred work; editing §19 is your file.** **Both would have been the wrong shape** |

## ✅ C-431 · TWO OF THREE ANSWERED BY D-156 — one narrow question left

> ⚡ **[D-156](DECISION_REGISTER.md) settled this without a separate ruling, and both answers came out of its own text rather than out of a judgement here.**
>
> ⛔ **The attempt counter** — *"3 attempts left before the account locks"* — **is out of Workflow 1 by ⑤'s own parenthetical: *lock or rate-limit messaging (where backed by implemented capability)*, and there is none.**
>
> ⛔ **`Use single sign-on` is out on ④ rather than on scope.** **Domain→IdP routing is an authorization semantic, not an infrastructure boundary** — ⑥ permits simulating a missing *data source*, and ④ forbids substituting an *authorization* one.
>
> ## ⚠️ **What is left is one question, and it may not be a question at all:** **`Keep me signed in for 30 days`.**
>
> **Raised as *no capability*; under ① it may be a *real* implementation.** **Better Auth owns session lifetime and `server.ts:86` merely fixes `expiresIn` at seven days.** ⛔ **This office has no `node_modules` and did not open the package, so it asserts nothing** ([D-137](DECISION_REGISTER.md)). ✅ **Lane A verifies by opening it. If Better Auth exposes it, it is ordinary work and needs nothing from you. If it does not, it defers with the other two.**
>
> ⚡ **So: no action expected. It is listed only so that a question raised to you is visibly closed rather than quietly dropped.**

<details><summary>The original entry, kept because a dated record is not rewritten (§2)</summary>

### C-431 · Three controls on the approved sign-in card have no backing capability

⛔ **Raised because [D-153](DECISION_REGISTER.md) ⑦ requires it rather than because Lane A is stuck.** ***"No lane may simplify the design. No lane may reinterpret the design. If something in the design is unclear: STOP."*** ✅ **Workflow 1 is buildable today and this changes what the review gate is shown, not what gets built first.**

| | |
|---|---|
| ⚡ **The measurement** | **The design's sign-in card draws three controls with nothing behind them.** **`Use single sign-on`** — [418 §1](architecture/418-platform-foundation-assessment.md) lists **domain→IdP routing** and **per-workspace SSO enforcement** among Authentication's named absences. **`Keep me signed in for 30 days`** — `frontend/lib/auth/server.ts:86` fixes `expiresIn` at **seven days**, and it is not electable. **The attempt counter** — *"3 attempts left before the account locks for 15 minutes"*: **`rateLimit`, `lockout`, `maxAttempts` and `failedAttempts` return zero across the whole repository** |
| **Owner** | **Yours.** ⛔ **The middle one is an authentication *semantic*, and [D-151](DECISION_REGISTER.md) ④ is explicit — *"Only the infrastructure boundary may change."* Session lifetime is not the infrastructure boundary** |
| ✅ **Recommended — option C** | **Workflow 1 delivers every element of screens `02`, `03` and `15` whose capability exists; these three become rows behind Login.** ⚡ **Not a simplification — the same distinction [TASK-467](BACKLOG.md) already drew with your approval when it put magic link, MFA, SSO enforcement, domain→IdP routing and session-expiry state out of scope by name** |
| ⛔ **Why not the alternatives** | **A — build all three inside Workflow 1**: three backend capabilities with no rows, and Workflow 1 stops being a presentation-layer replacement, which is the one thing D-153 says it is. **B — render them and route them somewhere**: a control that does not do what it says is worse than an absent one, and the attempt counter would be a fiction about our own product |
| ⚠️ **What you should know going in** | **Under C you review a login screen with no SSO entry point and no *keep me signed in*.** **Better discovered here than at the gate** |

</details>

## ⚙️ C-337 · SSH to GitHub is intercepted here — and the obvious fix is the dangerous one

⛔ **Not a repository defect and not blocking.** **The remote is HTTPS and pushes cleanly.** ⚡ **It is here because the remediation every lane will reach for — `ssh-keygen -R github.com` — is precisely what converts a *caught* interception into a *successful* one.**

| | |
|---|---|
| ✅ **Measured twice, independently** | **Lane B raised it; Lane C hit the same failure in the same window and measured before reading the row.** **Both found a single 2048-bit RSA key, `SHA256:7zYnlSpxx6z0t477lR5vNYfelxewzWwu8N1X6v+wsZA`, with no ed25519 or ecdsa offered**, against the three genuine fingerprints in `known_hosts`. ⚡ **Two lanes, one answer — not a transient** |
| **Owner** | **Yours** — ⛔ **the network this workstation is on, never the repository** (§20e; [B-011](BUGS.md) is the worked example of that distinction) |
| ⚠️ **What it costs, and when** | **Nothing today.** ⛔ **The moment any remote is switched back to SSH, every lane's fetch fails — or worse, somebody clears the key and it stops failing** |

## 🔴 The Action Batch needs an owner — one registry line, brought with the decomposition

✅ **[D-126](DECISION_REGISTER.md) is ruled and executed**: [ADR-0405](architecture/adr/0405-an-action-is-approved-before-it-is-effective.md) is drafted, and **[TASK-461](BACKLOG.md)–[TASK-466](BACKLOG.md)** are the six slices. ⛔ **One thing remains and it is not mine: the new bounded context has no owner, and module ownership is never Lane C's** (§20e).

> ⚡ **Brought *with* the decomposition rather than discovered after it.** **[TASK-427](BACKLOG.md) sat shut for two days because its row said *"`modules.toml` gains a row when this is placed, not before"* while `READY` needed an owner — [D-103](DECISION_REGISTER.md) broke that deadlock, and this is the lesson applied rather than re-learned.**

| | |
|---|---|
| ✅ **Lane C recommends** | **Lane B** |
| **§20e's precedence, and it points one way** | **① product architecture** — the first consumer is **Companies bulk**, whose backend is `opportunity_engine` · **② bounded context** — Lane B holds `opportunity_engine`, `commercial_profile` and `people` · **③ long-term maintenance** — four of the five blocked screens read Lane B's modules · **④ continuity** — Lane B raised and closed [C-334](LANE_COORDINATION.md), [C-332](LANE_COORDINATION.md) and the `TASK-428` boundary, all in this area |
| ⚖️ **And the load argument, stated separately because it is weaker** | **Lane A holds 11 eligible rows at shortfall 0; Lane B holds 4.** ⛔ **Capacity is not a precedence criterion** — §20e: *ownership optimises for cohesion, never for arithmetic* — **so it is offered as a tiebreak that was not needed, not as the reason** |
| ⬜ **Also unnamed, and deliberately** | **The context's own name.** ⛔ **[ADR-0405](architecture/adr/0405-an-action-is-approved-before-it-is-effective.md) refuses to coin one**: a name is [ADR-0034](architecture/adr/0034-ubiquitous-language.md)'s test — *would a salesperson use this word unprompted?* — **and it is worth one deliberate pass rather than a placeholder that ships** |

**On confirmation: the `modules.toml` row is written, [TASK-461](BACKLOG.md) goes `READY`, and the five remaining slices sequence behind it. Nothing else waits.**

## 📌 TASK-431 · Six screens assert one guarantee, and the repository has no word for it

**Not a `C-` item — no lane is blocked and nothing is undecided about *whether*.** **The question is the shape**, and it is 🔴, so it is yours.

| | |
|---|---|
| **Summary** | **[442 §F1](architecture/442-product-led-domain-discovery.md).** *"Approved before it writes, reversible after it does"* · *"nothing sends without your approval, reversible for 24 hours"* · *"reversible for 24 hours as a single named batch"* · *"attributed, reversible, in the audit log"* · **AI Copilot's 17 surfaces: *"proposes rather than commits… attributable and reversible"***. **Five screens in the design project's own words, plus every AI surface** |
| **The finding** | **The AI contract and the bulk-edit contract are the same contract**, and that is invisible screen-by-screen — one reads as AI governance, the other as a table feature. **They are one concept: a change that waits for a human, is recorded as one named thing with an author, and can be taken back inside a window** |
| **Already built** | **More than half.** `Recommendation` proposes · **`MACHINE_AUTHORED = frozenset({Stage.TRACKING})` — *"Intelligence suggests. Humans commit."*** · `actor_id` in **37 files** · **reversal-as-supersession, five times** (`observation` · `signal` · `entity` · `business_event` · opportunity stage) |
| **Genuinely absent** | **A named unit of change · a window · and the verbs.** The `Action` enum is `read · update · add · remove` — **there is no `approve` and no `withdraw`, so the guarantee cannot currently be *authorized*, let alone recorded** |
| **Impact** | **Six screens.** **AI Copilot is wave 2 and is the first to need it** |
| **Blocked tasks** | **[TASK-431](BACKLOG.md).** Nothing is blocked today — **the cost is paid later, and paid five times** |
| **Lanes waiting** | **None.** This is why it is cheap to rule now |
| **Priority** | **P1 — the only 🔴 in [442](architecture/442-product-led-domain-discovery.md) with no decision behind it** |
| **Recommended** | ✅ **(b) — a domain concept in one owning context, consumed through `public/`.** **The reason is the reuse gate, not taste**: *"a port belongs to the module that owns the language it represents"* (§6), and **approval is a language the whole product speaks** — which is exactly what distinguishes it from the five existing supersessions, each of which is one module's own vocabulary. **(a)** puts a shared concept in frozen substrate; **(c)** is the five-implementations outcome, and it is unpickable afterwards because each copy will be load-bearing for its own screen |

## 📌 TASK-433 · `Segment` already means something else

| | |
|---|---|
| **Summary** | **[442 §F2](architecture/442-product-led-domain-discovery.md).** The App Shell applies global scope *"before a module renders"* and **all 16 screens inherit it**; **Companies** needs *"saved views and segments"*; **Global Search** needs *"saved and monitored searches"*. **`saved_view`, `saved search`, `monitored` — zero matches repository-wide** |
| **The collision** | **`commercial_profile` owns `Segment`** — a named ICP segment with its own state machine, meaning ***who buys***. **Companies' "segment" is a saved filter over a list of accounts.** **Two concepts, one word, and the word is already in the ubiquitous language** — §4: *"never repurpose a term from one module inside another"* |
| **What this does *not* ask** | ⛔ **[O3](DECISION_REGISTER.md) stays deferred.** O3 asked **where shell services live**; this asks **whether a saved view is a domain concept, and what it is called.** *"No further preparation"* is respected — no placement is proposed here |
| **Impact** | **Five screens**, and the shell inherits into all sixteen |
| **Lanes waiting** | **None** |
| **Priority** | **P2 — trivial now, a rename across a bounded context later** |
| **Recommended** | ✅ **Rule the name before the second one is built.** **Lane C's suggestion is `SavedView` for the filter and `Segment` unchanged for the ICP concept** — the customer says *"my saved view"* and *"my segment"* about different things already, so [ADR-0034](architecture/adr/0034-ubiquitous-language.md)'s test is satisfied without inventing anything |

## ⬜ Open, and none of these blocks a lane today

> ⚠️ **These twelve were never on this page, and the reason is worth recording: they were *masked*.** **`decision-queue.py` treats a bold `**C-nnn**` anywhere in a section as a listing, so each of them counted as present because a section about something else mentioned it.** ⛔ **Removing seven decided sections on 2026-08-06 revealed all twelve at once** — **the page had been under-reporting by twelve for as long as those sections existed.**
>
> ✅ **Listed compactly rather than as twelve sections, deliberately.** **None blocks a lane today, and giving each a full page of analysis would bury [C-421](#-c-421--a-lane-cannot-read-the-design-it-is-implementing-against--external) and [C-229](#-c-229--opportunity-intelligence-needs-a-door-and-d38-closed-that-one-deliberately), which do.** ⚡ **A queue that presents everything equally has stopped prioritising.**

| | The decision | Why it is here rather than higher |
|---|---|---|
| **[C-211](LANE_COORDINATION.md)** | 🔴 **Where does an approach brief live?** **It reads the buying committee, signals, business events, validation, narration and the opportunity — and *no existing module may read all six*** | ⚡ **The most architectural of the twelve.** **A new bounded context or a widened contract; both are 🔴** |
| **[C-212](LANE_COORDINATION.md)** | 🟠 **Which product is an opportunity about?** **The buying committee is declared *per product*; an opportunity has no product** | ⛔ ***"Which committee applies to this account?"* is unanswerable, so role ranking cannot start** |
| **[C-203](LANE_COORDINATION.md)** | **Nothing in the product can render a person's name** | **Narrowed 2026-08-02. Grouped with People Intelligence** |
| **[C-223](LANE_COORDINATION.md)** | **`competitor_entry` across the current dependency graph** | **Only the *detection* half of Epic D phase 1** — the declaration, its API and its screen all shipped |
| **[C-009](LANE_COORDINATION.md)** | **An internal fault reaches a customer as a `422`** | **Blocks nothing today. It blocks *doing this properly* in any module that splits its errors** |
| **[C-003](LANE_COORDINATION.md)** | **Three wire codes for one condition** | ⚠️ **Blocks nothing — *"but it gets worse with every slice"*.** **[TASK-454](BACKLOG.md) is the slice that fixes it and is `READY`** |
| **[C-017](LANE_COORDINATION.md)** | **The onboarding honesty principle has no permanent home** | ⚡ **The text is written and ready to paste. Lane B may not place it** — **this is one paste, not a project** |
| **[C-007](LANE_COORDINATION.md)** | **The guided first run is a two-lane build** | ⚡ **Becomes live with [TASK-469](BACKLOG.md) Onboarding**, which is sequenced behind [C-421](#-c-421--a-lane-cannot-read-the-design-it-is-implementing-against--external) |
| **[C-014](LANE_COORDINATION.md)** | **Accessibility and performance testing are QE's, and neither exists** | ⚠️ **QE owns it and recorded the absence rather than stubbing a framework.** ⛔ **[D-131](DECISION_REGISTER.md) ② makes this a *product readiness* item — accessibility is what an enterprise buyer asks about** |
| **[C-210](LANE_COORDINATION.md)** | **Will Signora hold personal data?** | ⏸️ **Already `DEFERRED` by you on 2026-08-05** — *"keep grouped with future People Intelligence work"* |
| **[C-307](LANE_COORDINATION.md)** | **Signora cannot say who anybody is** | ⚡ **The customer framing is the useful part**: not *"I want to edit my name"* but ***"the product cannot tell me who my colleagues are."*** **Grouped with [C-203](LANE_COORDINATION.md) and [C-210](LANE_COORDINATION.md)** |
| **[C-305](LANE_COORDINATION.md)** | **Two principles that outgrew the ADR that found them** | **`CLAUDE.md` is yours.** ⚡ ***"A version is something the customer intentionally published. Not something they typed."*** — **a sentence worth promoting or discarding, not leaving in an ADR's margin** |
| **[C-304](LANE_COORDINATION.md)** | **A standing review question that has already paid for itself** | ⚡ **Not a blocker and not closeable.** **It asks that a rejection state whether it rejects the *whole* option or only one instance of it** — ⛔ **and this office has made that exact error twice this week** |

## 📌 C-423 · Architecture document numbers can still collide — the cheap half of a decision you already took

| | |
|---|---|
| **The question** | **Do numbered architecture documents get a prefixed allocation block, the way `B-`, `C-` and `TASK-` ids did at [D-112](DECISION_REGISTER.md)?** |
| **Blocks** | ⛔ **Nothing.** **[TASK-477](BACKLOG.md) fixes today's three collisions either way; this decides whether a fourth can occur** |
| **Priority** | **P3 — one sentence, and it can wait indefinitely without cost** |
| ⚡ **Why it is here at all** | **[D-112](DECISION_REGISTER.md)'s bar was general: *"repository growth should remove collision risk completely rather than reducing it probabilistically."*** **Architecture documents fail it today** — six files landed on one day, three numbers each naming two documents, **and `state-check` has reported it every cycle since.** **Detection working as designed; prevention absent** |
| **Recommended** | ✅ **Extend the existing block table prospectively — Lane A `2xx`, Lane B `3xx`, Lane C `4xx`.** ⚡ **That is what already happened by accident**: every `4xx` document in the tree is Product Office's. ⛔ **Do not retro-fit across the forty existing documents** — they are dated records (§2), and rewriting forty identities to prevent a defect that has occurred once is the wrong trade |

### ⚠️ C-306 · The one that argues *against* work, and it collides with D-128

| | |
|---|---|
| **The claim** | ⛔ ***"Rebuilding this experience would discard fourteen findings from real product review."*** **The Opportunities & Signals experience already exists and Lane A owns how it evolved** |
| **Why it needs you rather than me** | ⚡ **[D-128](DECISION_REGISTER.md) says the 26 finalized designs are the canonical UI specification — *"existing code is not the authority. Historical UI is not the authority."*** **C-306 is the strongest recorded counter-argument to applying that on one screen**, and it predates the ruling |
| **What is *not* in tension** | ✅ **D-128's authority is not in doubt.** **The question is narrower: whether fourteen product-review findings should be carried *into* the conformance work as inputs, or whether the design already accounts for them** |
| **Priority** | **P2 — nothing is blocked today.** ⚠️ **It becomes P1 the moment a refinement slice reaches this screen**, and [TASK-467](BACKLOG.md)–[471](BACKLOG.md) are that work |
| **Recommended** | ✅ **Rule that the design is authoritative *and* that the fourteen findings are inputs to the gap analysis** — ⛔ **not a veto over it.** ⚡ **[D-129](DECISION_REGISTER.md) already permits exactly this artifact: a measurable gap analysis is one of the three, and *"the design already handles this"* is a legitimate finding for each of the fourteen** |

## Closed on 2026-08-09

### ✅ C-254 · WITHDRAWN FROM THIS QUEUE — [CLAUDE.md](../CLAUDE.md) already answered it

> ⚡ **This office queued a 🔴 Change Budget grant that the product owner had already granted, in writing, eight days earlier.** ✅ **Withdrawn 2026-08-09 under [D-212](DECISION_REGISTER.md) §7's gate — *"can this be answered by an existing finalized design document?"* — which this office applied to itself and should have applied before queueing.**
>
> 📁 **[CLAUDE.md](../CLAUDE.md) line 429, ruled by the product owner in [D-153](DECISION_REGISTER.md), [D-154](DECISION_REGISTER.md) and [D-161](DECISION_REGISTER.md):** ***"The UI Migration Program is a standing approved architectural change… Replacing the design tokens, the shells and the shared components to match the finalized Signora Design System is the programme, not a breach of the freeze."***
>
> ⚡ **And the distinguishing test is drawn in the next line: *"the direction of the change: toward the finalized design is the migration; away from it, to suit one caller, is the defect."*** ✅ **[TASK-1429](BACKLOG.md) converges four improvised surfaces ONTO the Design System's ladder and removes a live `1.3.1` violation — it is the migration by that test, not an exception to it.**
>
> ✅ **Measured, not argued: the shell has been edited twice under this exemption already** — `f4fb9594` and `a165ed1a`, both [TASK-1408](BACKLOG.md), both on `main`. **A grant the repository has been exercising is not a grant to ask for.**
>
> ✅ **[TASK-1429](BACKLOG.md) released `READY` the same day.** ⛔ **Nothing is asked of you.**

⚠️ **What this cost, recorded because it is the second instance.** **Lane A did the right thing** — §20e says touching a file outside your budget is a finding to raise — **and this office converted a correct finding into a product-owner decision instead of answering it from the file that governs it.** ⚡ **[D-210](DECISION_REGISTER.md) produced the same defect (two capabilities reported absent that were fully specified), and D-212 §7 exists because of it. This is the gate failing to fire, not a missing gate.**

## Closed on 2026-08-06

> ✅ **[C-424](LANE_COORDINATION.md) closed 2026-08-07, [D-141](DECISION_REGISTER.md) ③ — by measurement, not by ruling.** **All four rail entries exist and none of them is a screen**: `Home`, `Forecast` and `Pipeline` are the Executive Dashboard and two of its sections; `Deals` and `Conversations` are entity types the design declares through Global Search's `entityPages`. ⛔ **Nothing was missing.**

## 📌 C-424 · Four rail entries, no design — **one pointer answers it**

| | |
|---|---|
| **The question** | **The App Shell rail specifies `Forecast`, `Pipeline`, `Deals`, `Conversations`. No design in the set defines them.** ⚡ **Is each one: ① a design I have not found · ② out of scope for this wave · or ③ still to be designed?** |
| **Blocks** | ⛔ **Nothing today** — every screen in flight is one the set contains |
| **Priority** | **P2 — it becomes P1 the moment a lane renders the rail**, which is [TASK-447](BACKLOG.md), currently `CLAIMED` |
| **What was exhausted** | **All 26 designs · the App Shell's own `navItems` definition · the related screens · the ADRs · [D38](architecture/39-product-review-findings.md) · `frontend/app/`.** ⚡ **`Deals` is confirmed real — Opportunity Intelligence's breadcrumb reads `Deals / EMEA enterprise / Vantage renewal`. The other three appear nowhere else** |
| ⚠️ **Why guessing is dangerous here** | **`Accounts` maps to the *Companies* design — proven by its `8,412`, the exact row count [TASK-440](BACKLOG.md) cites.** ⛔ **No filename would have suggested that mapping.** **Three of the remaining four may map similarly, and one wrong guess in four is a screen nobody designed** |
| **Recommended** | ⚪ **None offered — this needs design intent, not a judgement.** ⚡ **Answerable by pointing: a filename, "out of scope", or "not yet designed", per name** |

> ✅ **[C-229](LANE_COORDINATION.md) closed 2026-08-07, [D-141](DECISION_REGISTER.md) ①** — **the finalized App Shell defines the navigation rail, so the decision was already made.** ⛔ **It stayed on this page for two days after the design became readable, which is what ① exists to stop.**

## ✅ C-229 · Opportunity Intelligence's door — **answered by the design, and my first recommendation was wrong**

⛔ **Corrected 2026-08-06, within the hour.** **The recommendation published earlier today said *"contextual, not a destination"* and rested on a caveat that was false: that the App Shell binds its navigation items from data this office cannot read.** ⚡ **The data is in the file.** **I read the templates and not the definitions**, and [D-140](DECISION_REGISTER.md)'s *exhaust the evidence first* is what found it.

### The finalized navigation rail, read from the design

**`Home · Forecast · Pipeline · Accounts (8,412) · Deals · Conversations · Signals (14) · Reports`**, with **`Enterprise (312)`** and **`Mid-market (1,140)`** as sub-items of Accounts, and **`Settings`** in the utility rail.

| | |
|---|---|
| ✅ **Opportunity Intelligence is *not* a rail entry** | **That half of the earlier recommendation holds.** Its breadcrumb is `Deals / EMEA enterprise / Vantage renewal — Q4 FY26` and every label on it is singular — **a record page, like Account 360** |
| ⛔ **But its parent `Deals` *is* a rail entry** | **So the entrance exists and it is a first-class destination — one level up.** **The screen is reached by drilling *from a list that the rail links*** |
| ⚡ **And `Accounts` carries `8,412`** | **The exact row count [TASK-440](BACKLOG.md) Companies cites.** ⛔ **Companies *is* a first-class navigation destination in the finalized design** |

### ⚠️ What this means for D38

**[D38](architecture/39-product-review-findings.md) reduced navigation to two entries plus Settings, reasoning that *"none of the six customer journeys is show me all the companies."*** ⛔ **The finalized design has eight primary entries plus two sub-items plus Settings, and `Accounts` is one of them.**

> ## **The design supersedes D38 on this point, and [D-128](DECISION_REGISTER.md) already says so: the design is the authority, and historical UI is not.**

✅ **So C-229 needs no ruling.** **The question was *"does it get a navigation entry, reversing D38?"*** — **the design answers it, and the answer arrived when the design became readable.** ⛔ **Escalating it further would be asking the product owner to re-decide something the approved design already states.**

⚡ **[TASK-441](BACKLOG.md) is unblocked**: its entrance is `Deals`, which the rail provides.

> ✅ **[C-204](LANE_COORDINATION.md) closed 2026-08-06, [D-139](DECISION_REGISTER.md) ⑦** — **evaluated against the finalized designs rather than in the abstract.** **The Signal Center design puts *"Why this matters"* on the signal itself; no catalog page exists in any of the twenty-six.**

> ⚙️ **[C-334](LANE_COORDINATION.md) left this page 2026-08-06, reclassified `OPERATIONAL` by [D-139](DECISION_REGISTER.md) ②** — *"no longer a Product Owner decision… an operational environment dependency."* **Tracked in the register; release is automatic on configuration.**
> ⏸️ **[C-302](LANE_COORDINATION.md) removed from the open tier** — held until [ADR-0040](architecture/adr/0040-notifications.md) by [D-139](DECISION_REGISTER.md) ⑤, **with Lane C as trigger steward.**

## ⏱️ C-334 · The hosted evaluation credential — ✅ ruled, not yet provided

| | |
|---|---|
| **Status** | ✅ **`RULED` — [D-111](DECISION_REGISTER.md)**: *"I will provide the hosted evaluation credential."* ⛔ **Listed here because it is not yet configured, never because it is undecided** |
| **Blocks** | **[TASK-003](BACKLOG.md) · [TASK-202](BACKLOG.md)'s prompt release · [C-222](LANE_COORDINATION.md) · [C-331](LANE_COORDINATION.md)** |
| **Priority** | **P1 — one credential converts four rows** |
| ✅ **No action needed beyond configuring it** | **Release is automatic**; nothing waits on further instruction. ⚠️ **[TASK-202](BACKLOG.md) is `READY` today and stays `READY`** — the credential gates its *prompt release*, never its start |


> ✅ **[C-421](LANE_COORDINATION.md) left this page 2026-08-06.** **It was never an access problem** — the design was readable throughout and [`docs/design-snapshot/`](design-snapshot/MANIFEST.md) now holds it locally ([D-138](DECISION_REGISTER.md)). ⛔ **It blocked three prepared slices for two days on a call nobody made.**

## ⛔ C-421 · A lane cannot read the design it is implementing against — EXTERNAL

| | |
|---|---|
| **The ask** | ⚡ **Nothing to decide. Something to provide.** **That Lane A can open the canonical design set** — the location registered in [410](architecture/410-approved-ui-specification.md) |
| **Blocks** | **[TASK-467](BACKLOG.md) · [TASK-468](BACKLOG.md) · [TASK-471](BACKLOG.md)** — **every slice whose first act is a gap analysis against the design.** ✅ **[TASK-469](BACKLOG.md) and [TASK-470](BACKLOG.md) carry backend work that is not blocked** |
| **Priority** | **P1 — three prepared slices, sequenced, and none can begin** |
| ⛔ **Why it is an item and not a note** | **The workaround was proposed and refused.** **This office suggested extracting the design's states into a conformance checklist a row could reference; [D-129](DECISION_REGISTER.md) ruled against it** — *"the only acceptable derived artifacts are implementation tasks, measurable gap analyses, and test cases. The design itself must remain the single source of truth."* ⚡ **So the slices reference the design directly and the access gap is raised rather than absorbed — the difference between a dependency and a silent assumption** |
| **Recommended** | ✅ **Grant read access to the registered design location.** ⛔ **Not a copy, not an export into the repository, not a checklist** — all three are what D-129 forbids |



> **Seven rows left this page because they were decided, not because they were dropped.** **[D-131](DECISION_REGISTER.md) ①**: *"a decision recorded only in prose is effectively invisible to the repository"* — **so each item's `Status` field and its index row were written in the same change as this removal, and `decision-queue.py --check` is what proves it.**

⚠️ **All seven had been ruled on 2026-08-06 and were still presenting themselves as open questions.** **Three of them — [C-417](LANE_COORDINATION.md), [C-418](LANE_COORDINATION.md), [C-419](LANE_COORDINATION.md) — were nearly escalated for a second ruling.**

## C-332 · The predicate landed and TASK-406 still cannot call it

⚠️ **Raised by Lane B, and it falsifies a claim this office published.** **[443](architecture/443-account-matching-capability.md) and [TASK-406](BACKLOG.md)'s row both say *"the per-criterion lift half is unaffected and needs nothing new."* Lane B measured that and it is wrong.**

| | |
|---|---|
| **The problem** | **`evaluate(icp, observed)` shipped and is correct. Nothing in the repository constructs an `ObservedAttributes`, and the module ruled to do the measuring is forbidden from every module that could** |
| **Why this office missed it** | ⚡ **[443](architecture/443-account-matching-capability.md) made the function pure *specifically* to avoid the import contract — *"the facts are handed to it"* — and never asked **who hands them.** **The same class as [ADR-0404](architecture/adr/0404-platform-composition.md)'s §Validation, which checked that `apps/worker` had an owner and never checked who owned the trees the capability reached.** **Twice now: a boundary designed without asking who stands on the other side** |
| **What is verified** | `ClaimReader.for_subjects` keys on `SubjectRef`, a *provider* identity. **The `entity_id → SubjectRef[]` binding lives only in `knowledge_graph`.** ⛔ **`pyproject.toml` forbids `opportunity_engine → knowledge_graph` in full.** ⛔ **The score carries *"no name, no domain, no industry"*, deliberately.** ⛔ **And [C-328](LANE_COORDINATION.md) already ruled the opposite direction shut** |
| **Impact** | **[TASK-406](BACKLOG.md) whole — both halves.** Lane B returned it to `BLOCKED` and wrote no code, correctly |
| **Priority** | **P1 — a promoted capability with no reachable caller** |
| **Proposal** | ⚡ **[462](architecture/462-observed-attributes-proposal.md), prepared 2026-08-06 on your instruction — and it changed its own recommendation while being written.** **`GraphQueries` and `ClaimSet` are *already published*, so the first reading — *"there is no reader"* — was wrong.** **The real argument is that `ClaimSet` publishes *evidence* where a resolved *fact* is needed: it hands a caller three providers disagreeing about an industry and no rule for settling it, and a consumer projecting that is a second resolver — which this repository has refused in writing twice.** **With eight consumers of R-00, *"the caller projects it"* means up to eight rules for what an account's industry is, and the disagreements would be invisible** |
| **Recommended** | ✅ **`knowledge_graph` publishes an `AccountAttributesReader` in its `public/`** — canonical `industry`, `country`, `employee_count` per entity — **and `opportunity_engine` gains a `public/`-only edge.** ⚡ **[ADR-0403](architecture/adr/0403-signal-engine-reads-a-declaration.md) is the exact precedent for a different pair**: a new edge to `public/` alone, the reader shaped as the module's existing `View · Reader` triple, no inner layer reached. **A new cross-module edge is 🔴 and needs an ADR; the shape does not need inventing** |
| **Alternative, if the edge is refused** | **The projection travels as an event.** ⚠️ **More machinery, and it makes a measurement depend on delivery** — recorded so the cheaper option is a choice rather than an assumption |

## C-419 · The six verbs have no representation, and *17 surfaces, one contract* is undecided

**Found by [445](architecture/445-ai-copilot-traceability-audit.md) — the first Screen-by-Screen Domain Traceability Audit, on the screen wave 2 reaches next.**

| | |
|---|---|
| **Two halves** | **[410](architecture/410-approved-ui-specification.md) asserts *"**six verbs and no others**"* and *"17 surfaces, one contract."*** ⛔ **No verb taxonomy exists in any `domain/` layer** — six values the design calls closed, and nothing closes them. **And seventeen endpoints is seventeen chances for one of the five guarantees to differ, with no way to check that it did not** |
| **What already argues one way** | ✅ **The guarantees are already single** — `GroundedOutput`, `EvidenceRef`, `SupportBasis` and the never-repairing validator are one implementation each. **The contract is a platform capability in substance today** |
| **Impact** | **Nothing blocked.** [TASK-202](BACKLOG.md) waits on C-222 for unrelated reasons |
| **Lanes waiting** | **None** |
| **Priority** | **P2 — free now, and it decides a module's published language** |
| **Recommended** | ✅ **The verb taxonomy and surface identifier go in `ai_reasoning_engine`'s `public/`; the 17 surfaces are consumers, not variants.** **§6's rule, not preference**: *"a port belongs to the module that owns the language it represents."* **Put it in the frontend and the closed set stops being closed the first time a screen wants a seventh.** **Trade-off stated: one parameterised route reads less obviously than seventeen named ones** — and the repository took that trade before, deliberately: the provider registry *"exposes `for_model(model)` and no vendor-keyed lookup, so business code that cannot name a vendor cannot branch on one"* |
| ⚠️ **A separate, cheaper finding** | **There is no `Resource` for reasoning.** `Resource.RESEARCH` exists because *"reading an account is free and asking for research spends a model call… without it every reader becomes a spender."* **AI Copilot is 17 surfaces on pages every member already reads** — mounted without the same separation, **it grants every member the ability to spend, on every page.** **One `Resource` and two policy lines**, which [C-224](LANE_COORDINATION.md) already makes a lane's to register |

## C-418 · Does Signora forecast revenue?

**Found by [444](architecture/444-executive-dashboard-domain-assessment.md), assessing the Executive Dashboard to its domain — not by implementation reaching it.**

| | |
|---|---|
| **The conflict, in two quotations** | **[410](architecture/410-approved-ui-specification.md) describes the screen as *"CEO/CRO homepage — **forecast**, risk, ageing, movements."*** **`buying_score_engine` says, twice, in its own code: *"**No probability, no likelihood, no prediction.** A buying score prioritizes commercial attention; **it does not forecast a purchase**."*** **The approved UI's first word contradicts a ratified principle, in the module the forecast would come from** |
| **Four absences, one question** | **`Opportunity` has no amount, no currency and no close date · `quota`/`target_amount`/`forecast` return nothing · `fiscal` returns zero · there is no `Team`, no `manager_id`, no `reports_to`.** **Answer the question and all four follow, or none do** |
| **Impact** | **None today.** **[TASK-438](BACKLOG.md) delivers five of the screen's sections without it** — conversion, ageing, movement, roll-up by owner, and ICP coverage |
| **Lanes waiting** | **None** |
| **Priority** | **P2 — cheap now, and it decides four things at once** |
| **Recommended** | ✅ **B for now — pipeline health — and A only behind Epic E1**, stated as a sequence rather than a refusal. **A forecast needs a deal value, and the value must come from the customer's CRM rather than a text box** ([ADR-0036](architecture/adr/0036-target-account-contract.md): *"asking them would be asking a customer to do resolution"*). **A forecast built before [TASK-402](BACKLOG.md) lands is a forecast over numbers nobody entered.** ⚠️ **[417](architecture/417-executable-slice-audit.md) reached the same split independently** — *"the AI projection is BLOCKED BY PRODUCT"* |
| **The consequence nobody has hit** | **Every grant today is workspace-wide.** **A roll-up by owner is everybody's performance on one page**, and this is **the first approved screen whose data is sensitive between colleagues rather than between tenants.** **Recorded, not proposed — it becomes real only on answer A** |

## C-417 · ADR-0404 approved three platform capabilities, and its owner may not finish two of them

**Found by running [ADR-0404](architecture/adr/0404-platform-composition.md) §Validation before the first slice — which is what that section is for.** **The ADR is Lane C's own, so this is this office's error surfacing exactly where it was designed to surface.**

| | |
|---|---|
| **Summary** | **The platform edit is Lane C's. The proof it worked is five files in `backend/modules/`, and §20e forbids Lane C from touching that tree** — ⚫ *refactor a module you are not assigned* |
| **Why the halves cannot be split** | **`mypy strict = true` implies `warn_unused_ignores`.** The moment `PublishableEvent`'s members become read-only, the five `# type: ignore[arg-type]` go unused and **the gate fails.** **Platform change and five one-line deletions are one atomic change whether anybody likes it or not.** Capability ① is the same shape — the two `EventHandler` implementations are in `modules/` |
| **What the modules already said** | **`observation_engine/application/record.py:120`, in the code, before this item existed:** *"the platform's `PublishableEvent` Protocol declares settable members, which frozen domain events cannot satisfy. **Raised as a finding, not fixed here.**"* **Three modules carry that comment. They declined to cross the boundary, correctly — and ADR-0404 is the fix they were waiting for** |
| **Impact** | **[TASK-418](BACKLOG.md) ① and ②, and [TASK-901](BACKLOG.md)'s seven slices behind them.** ⚠️ **TASK-901's slices are the only prepared work left for Lane A, whose queue is 0 of 5** |
| **Lanes waiting** | **Lane C now. Lane A when its two in-flight rows land** |
| **Priority** | **P1 — it is in front of seven slices and a starving lane** |
| **Recommended** | ✅ **A bounded, named exception**: *the slice may delete `# type: ignore[arg-type]` comments at publish sites and may change no other line in `backend/modules/`*. **Five deleted comments, provably behaviour-free, and a reviewer can verify the bound from the diff alone** — the same standard §20a's carve-out already uses for a `Resource` member. **The alternative that bends no rule delivers the capability never**: those comments have sat there for weeks precisely because no slice makes anybody touch them |
| ⚠️ **Two corrections to the ADR, same validation** | **It says *"all eight"* ignores; there are **five** at publish sites** — the other three are `provider_normalization` (×2) and `ai_research_engine` and none is at a publish site. **And §Validation checks that `apps/worker/` has an owner but never checks that the *modules* the change reaches have one** — which is the check that would have caught this at ratification |

## C-104 · May a request handler call a vendor synchronously, when the answer *is* the request?

🟢 **Nothing is blocked** — [TASK-407](BACKLOG.md) is promoted and passes every gate. **This decides whether it becomes precedent**, and **`/check` is the only synchronous outbound vendor call in any `interface/` layer** — so it is a precedent being *set*, not one being discovered.

> ⚡ **Two ratified texts disagree, and reading the source settles it.**
>
> **[02-principles.md §13](architecture/02-principles.md)** governs *"work **not required to complete within the request/response cycle**"* and enumerates **provider polling, normalization, the observation→signal→opportunity chain, AI reasoning, recommendations** — **every one a pipeline stage.** **A liveness probe's answer *is* the response**, so the principle's own precondition is never met.
>
> **`CLAUDE.md` §7 paraphrased it and widened it**: ***provider polling*** **became** ***provider calls***. **§20e predicted exactly this** — *"a rule written in two places is a rule that will eventually contradict itself."*

**Lane C recommends: permit it, bounded by a stated test rather than case-by-case judgement** — ① the call's result **is** the response · ② nothing about the customer's data is read into the pipeline, stored or normalized · ③ an explicit timeout · ④ the vendor is reached only through a module-owned port.

⛔ **What it must not become**: *"synchronous vendor calls are fine if they are quick."* **①+② are load-bearing** — a stage that ingests one record fails ② however fast it is.

🔴 **The second half is yours alone**: if the ruling is *permit*, **`CLAUDE.md` §7 says something the architecture does not**, and the honest repair narrows *"provider calls"* to *"provider polling"*. **Lane C drafts `CLAUDE.md` only on instruction.**

⚠️ **Raised by QE on 2026-08-04 and it drifted for two days.** **Not because it lacked a `Status` row** — QE inferred that from a false positive in this office's own checker, which knew `Status` and not `State`. **It drifted because `OPEN` means *nobody has looked* and somebody had.** **Moving it to a decidable state is Lane C's under §20e, and this office did not.**

## C-225 · Wave 1's technology stack section has no route

✅ **Answered by delivery.** Wave 1 shipped **ten sections, not eleven** — [414](architecture/414-wave-1-account-360.md) was corrected before anything was built, and **Lane A built the ten.** **The product owner's half of this item — *does wave 1 ship the subset or wait* — is answered by the subset having shipped.** What remains is **Lane B's**: whether `knowledge_graph` gets a route for `USES_TECHNOLOGY`, which is a capability with no customer-facing edge. **No decision needed from you.**

## C-329 · Lane B had nothing claimable, and the row that said otherwise

✅ **Substance addressed 2026-08-05.** Both halves were acted on: **[C-412](LANE_COORDINATION.md) was corrected** — it named the wrong lane on *both* pairs — and **`lane-c-product-office` was measured and holds nothing** *(59 ahead, 268 behind, zero files newer)*. **Closure is Lane B's**, which raised it. **No decision needed from you.**


---

# ⏸️ Deferred by you — do not work these

**Recorded so nobody re-raises them, and so the trigger is written down rather than remembered.**

| ID | Summary | Trigger |
|---|---|---|
| **C-320** | No environment can complete a sign-up | **Highest of this group. After the current engineering wave** |
| **C-322** + **C-002** | *Is an ICP a description or a filter?* · customer-language anticorruption | **When Epic B1 begins. Grouped, not split** |
| **C-210** + **C-203** | Personal data · rendering a person's name | **[TASK-429](BACKLOG.md) — M-E · Provider Enrichment**, which is now the row that carries them. *(Was *"with future People Intelligence work"*; [D-074](DECISION_REGISTER.md) split that into four milestones and **these two belong to exactly one of them** — no person's name exists to render before M-E, and none of M-D or M-I S3 produces one)* |
| **C-020** | M7 scope | **Explicitly deferred.** ⚠️ Half stale — Timeline has a design, and [C-215](LANE_COORDINATION.md) is queued to Lane B as buildable work |
| **C-025** | M13 is not a module | Deferred |
| **C-005** | Who owns the signal-profile write path | **When implementation reaches the feature** |

> ⚠️ **[C-002](LANE_COORDINATION.md) is deferred and still load-bearing.** It is the live scope bound on **[TASK-903](BACKLOG.md)**: *display the declarations, assert no match.* **Deferred does not mean inert.**

# 📎 Standing — blocks nothing being built

> ✅ **C-011 left this list 2026-08-05, closed by delivery.** It was *"a contraction risk reads like a small opportunity"*, and **[TASK-905](BACKLOG.md) is that item built** — shipped by Lane A the same day. **`--check` reported it as ruled-and-still-queued within the hour**, which is the queue doing its job: **an item that resolves by delivery leaves no ruling behind**, so nothing but the checker would have noticed.

**C-003** three wire codes for one condition · **C-006** which lane owns `test_api_<module>.py` *(16 files)* · **C-007** the guided first run is a two-lane build · **C-009** an internal fault reaches a customer as a `422` · **C-014** accessibility and performance testing · **C-017** the onboarding honesty principle · **C-204** the catalog explains nine words to nobody · **C-211** where an approach brief lives · **C-212** which product an opportunity is about · **C-223** `competitor_entry` across a boundary *(**resolved in principle by C-328's ruling** — same shape, same answer)*

> **No action, by ruling:** *"Continue collecting evidence. Do not spend engineering effort on these until implementation naturally reaches them."*

# 🔧 Open, and not yours

| | Owner | |
|---|---|---|
| **C-214** | **Lane B** *(joined from `modules.toml`)* | Its own text says *"Implementation impact. Blocks nothing"* |
| **C-215** | **Lane B** | **Not a decision — a finished specification.** Queued as [TASK-902](BACKLOG.md) |
| **C-216** | **QE** | Same defect as [B-105](BUGS.md), open in two registers |
| **[436](architecture/436-execution-isolation.md) ③b and ④** | **QE** | The `conftest.py` guard and certification asserting its own isolation. **Designed in full; scheduled by QE** |

---

## Closed on 2026-08-05

**C-019** the claim protocol already implements it · **C-008** ruled 2026-08-03, stage 1 shipped · **C-205** **responsive web is officially part of Signora**; native mobile is a future roadmap item · **C-200** deferral confirmed · **C-012 · C-013 · C-021 · C-207** — **all four by [ADR-0404](architecture/adr/0404-platform-composition.md)**
