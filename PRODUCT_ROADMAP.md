# PRODUCT_ROADMAP.md

> **Owner:** Product Engineering Lead / CPO · **Audience:** Exec, GTM, Board, Engineering
> **Status:** Living document — revised at each milestone boundary
> **Anchors:** [`PRODUCT_DIFFERENTIATORS.md`](PRODUCT_DIFFERENTIATORS.md) (strategy) · [`IMPLEMENTATION_ROADMAP.md`](IMPLEMENTATION_ROADMAP.md) (engineering sequence)
>
> This document translates engineering milestones into **customer-visible value**. Every milestone here maps to a phase in the implementation roadmap; nothing is promised that engineering has not sequenced.

---

## How to Read This Document

Signora's pipeline is a strict dependency chain, which creates an uncomfortable but important property: **the first several milestones produce infrastructure with no demoable customer value.** Pretending otherwise would produce a roadmap that misleads GTM.

So each milestone below is explicitly labelled:

- 🏗️ **Foundation** — real engineering value, *no* customer-facing artifact. Do not demo.
- 🔍 **Internal Value** — demoable to a design partner as evidence of progress; not sellable.
- 💰 **Customer Value** — a customer would pay for this.

The first genuinely sellable moment is **M6**. That is a fact about the architecture, not a scheduling failure, and GTM planning should be built on it rather than around it.

---

> **Implementation sequencing note (2026-07-28).** Two enablement milestones now precede product work: **M1.5 Frontend Foundation** (the frontend platform — shell, design system, routing, session, query layer; no business screens) and **M2.0 Provider Simulation Framework**. Neither appears below, because neither delivers customer-visible value on its own.
>
> **Product milestone order is unchanged.** Two consequences worth knowing:
>
> - **Business screens are deferred until realistic provider data exists.** Company, opportunity, signal, timeline, AI-recommendation, and analytics pages are built against real domain models, never mocked JSON — so they arrive from M2 onward rather than being sketched earlier.
> - **Cloud infrastructure is deferred to Production Readiness**, immediately before GA. Until then there is no externally reachable environment: a demo is a local stack or a screen share. This is a deliberate, accepted cost — see [IMPLEMENTATION_ROADMAP.md §5b](IMPLEMENTATION_ROADMAP.md#5b-updated-implementation-order).
>
> M0's *first sellable moment* (M6, Qualified Opportunities) and every milestone's customer promise are unaffected.

## Milestone Map

| Milestone | Phase | Label | Headline |
|---|---|---|---|
| M0 | 0 ✅ | 🏗️ | Secure multi-tenant foundation |
| M1 | 1 | 🏗️ | Runtime spine + first login |
| M2 | 2 | 🔍 | Company data flowing in |
| M3 | 2 | 🔍 | The Knowledge Graph — one truth per company |
| M4 | 3 | 🔍 | Business events detected |
| M5 | 3 | 💰 | Buying signals and scores |
| M6 | 3–4 | 💰 | **Qualified opportunities — first sellable moment** |
| M7 | 4 | 💰 | AI reasoning with evidence |
| M8 | 4 | 💰 | Deep AI research |
| M9 | 4 | 💰 | Actionable recommendations |
| M10 | 5 | 💰 | Timeline — the account narrative |
| M11 | 5 | 💰 | Revenue Intelligence Platform |
| M12 | 6 | 💰 | Workflow integration (CRM, Slack) |
| M13 | 6 | 💰 | Enterprise readiness |

---

## M0 — Secure Multi-Tenant Foundation 🏗️ ✅ COMPLETE

**User value:** None directly. This is the substrate everything else stands on.

**Business value:** Two risks retired that are ruinous to retrofit: **tenant data isolation** and **the authentication boundary**. A cross-tenant leak is an extinction-level event for a B2B intelligence platform; building isolation into the database layer now, with adversarial tests proving it, is the cheapest it will ever be. Enterprise security reviews in M13 will draw directly on this work.

**Demo scenario:** Internal only — show the RLS regression suite failing against pre-fix policies and passing after. Demonstrates that isolation is *proven*, not asserted.

**Customer outcome:** Nothing yet.

**Success metrics:** ✅ 116 tests passing · ✅ tenant isolation verified under adversarial conditions · ✅ zero boundary violations.

---

## M1 — Runtime Spine + First Login 🏗️

**User value:** A user can create an account, sign in with Google or Microsoft, and create a workspace. That is the entire user-visible surface — and it is genuinely necessary.

**Business value:** Unblocks *everything*. Two hard blockers clear here: the event bus relay (which 13 modules wait on) and the Better Auth issuer (without which no human can access Signora at all). Also the first deployed environment, which makes progress visible to non-engineers for the first time.

**Demo scenario:** Sign in with Google → create "Acme Revenue" workspace → invite a colleague → they see the workspace, and provably cannot see anyone else's.

**Customer outcome:** Design partners can be onboarded into a real environment, which starts the feedback loop months before the product is useful.

**Success metrics:** Sign-in success rate >99% · event relayed end-to-end with traceable `correlation_id` · deployed environment reachable.

---

## M2 — Company Data Flowing In 🔍

**User value:** Signora begins watching the companies a customer cares about. Nothing is *shown* yet — the system is accumulating.

**Business value:** Proves the multi-provider thesis technically. Five providers (Apollo, CoreSignal, BuiltWith, Similarweb, NeverBounce) across five distinct data categories, behind one abstraction — the foundation of the "Multi-Provider Fusion" differentiator, and the thing that removes the "GTM engineer maintaining pipelines" burden that plagues Clay's user base.

**Demo scenario:** Add a target account list → watch provider ingestion populate raw records with full provenance → show the same company enriched by three providers simultaneously.

**Customer outcome:** "Signora is watching my accounts" — a credible progress signal for design partners, not yet a workflow.

**Success metrics:** 5 providers integrated · ingestion success rate >98% · provenance recorded on 100% of records · per-provider cost tracked.

---

## M3 — The Knowledge Graph 🔍

**User value:** One canonical record per company, reconciled across every provider. Duplicates and contradictions resolved.

**Business value:** **This is moat #1** ([PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md) §Product Moats). Entity resolution quality compounds: the longer Signora runs, the better it gets, and the harder it becomes for an entrant to catch up. Every downstream stage inherits its quality — a weak graph makes every signal, score, and recommendation weak.

**Demo scenario:** Show "Acme Corp," "Acme Corporation Inc.," and a differently-named legal entity resolving into one record — then the merge history explaining exactly why.

**Customer outcome:** "Signora knows my market better than my CRM does."

**Success metrics:** Entity resolution precision/recall on a labelled set (targets set after the M3 spike) · duplicate rate <2% · merge decisions fully auditable.

---

## M4 — Business Events Detected 🔍

**User value:** Signora recognises *what happened*: funding rounds, executive hires, hiring surges, technology adoption, expansion.

**Business value:** The first genuinely proprietary interpretation layer — where Signora stops being a data pipeline and starts having a point of view. The taxonomy is domain IP no vendor sells off the shelf.

**Demo scenario:** Timeline of detected events for a real account, each one expandable to the exact observations that produced it — provenance visible from the first interpretive layer onward.

**Customer outcome:** "Signora noticed my account raised a Series B before my rep did."

**Success metrics:** Detection precision >85% on a labelled set · false-positive rate tracked per event type · median detection latency from source publication.

---

## M5 — Buying Signals and Scores 💰

**User value:** Accounts ranked by a single, explainable **Buying Score** — with the evidence behind it one click away.

**Business value:** The direct answer to the loudest complaint about 6sense and Demandbase: opaque scoring that reps distrust and quietly ignore. Signora's score is explainable by construction, and the Buying Score Engine is a named differentiator.

**Demo scenario:** Prioritized account list. Click the top score → see contributing signals → drill to business events → drill to source observations. Then show the *inverse*: an account explicitly deprioritized, with reasoning. **Almost no competitor demos that second half**, and it is the cheapest differentiation available to us.

**Customer outcome:** "I finally know which of my 200 accounts to call this morning, and I can defend the choice to my manager."

**Success metrics:** Score-to-conversion correlation (baseline established here) · % of scores a rep rates "makes sense" >80% · **rep-time reclaimed from deprioritized accounts**.

---

## M6 — Qualified Opportunities 💰 **FIRST SELLABLE MOMENT**

**User value:** Signora surfaces qualified opportunities: *this account, right now, because of this*.

**Business value:** **The commercial inflection point.** From here, Signora answers three of its four founding questions (*which companies · why now · what changed*) with evidence. This is the earliest defensible point for design-partner contracts and the first credible pricing conversation.

**Demo scenario:** The full chain, live: provider data → observation → business event → signal → buying score → qualified opportunity, with an unbroken evidence trail end to end. This is the demo that wins the category argument against both the data vendors and the signal-alert tools.

**Customer outcome:** "Signora generates my pipeline list. I stopped building it by hand."

**Success metrics:** Opportunities per workspace per week · **rep acceptance rate >60%** · time-to-first-opportunity after onboarding · design-partner contracts signed.

---

## M7 — AI Reasoning With Evidence 💰

**User value:** Every opportunity comes with an AI-written explanation — *why this matters, why now, what the angle is* — citing its evidence.

**Business value:** The core AI differentiation, and where "AI Revenue Intelligence" stops being a label and becomes the product. Critically, the **evaluation harness ships before the engine**, so reasoning quality is measurable from day one rather than assessed by vibes.

**Demo scenario:** Opportunity → AI explanation with inline evidence citations → expand any citation to the source observation. Then show a low-confidence case where Signora says so plainly instead of overclaiming.

**Customer outcome:** "I walk into calls prepared, with an angle I trust enough to use."

**Success metrics:** **Reasoning factual accuracy >90%** on golden sets · evidence-completeness 100% (release gate) · reasoning latency P95 · cost per reasoning call.

---

## M8 — Deep AI Research 💰

**User value:** On-demand deep research on any account — a genuine analyst brief in minutes instead of hours.

**Business value:** The differentiator most likely to be undervalued today and decisive in three years. No competitor in the comparison set has agentic, multi-step account research. It is also the clearest "wow" moment in the sales cycle.

**Demo scenario:** "Research this account before tomorrow's call" → multi-step agentic research runs → structured brief with sources. Show the fallback too: reasoning still completes if research times out, degrading gracefully rather than blocking.

**Customer outcome:** "I stopped spending Sunday evenings researching accounts."

**Success metrics:** Research completion rate within SLA · **rep-rated usefulness >4/5** · hours saved per rep per week · cost per research task (governed by the M13 spend controls).

---

## M9 — Actionable Recommendations 💰

**User value:** Not just "this account is hot" — *reach out to this person, reference this event, this week, via this channel*.

**Business value:** Closes the fourth founding question (*what should we do next*) and completes the loop that powers the flywheel: `recommendation.status_changed` feeds back into Signal Engine, so the system learns from what reps actually acted on. **This is where compounding starts.**

**Demo scenario:** Recommendation with a specific action, contact, timing, and rationale → rep acts → outcome recorded → show that outcome becoming an input to future scoring.

**Customer outcome:** "Signora tells me what to do, not just what to look at."

**Success metrics:** **Recommendation acceptance rate** (primary leading indicator) · pipeline generated per recommendation acted on (the North Star) · win rate on Signora-sourced opportunities vs. baseline.

---

## M10 — Timeline: The Account Narrative 💰

**User value:** A chronological story for every account — everything Signora has observed, interpreted, and recommended, searchable.

**Business value:** A retention and expansion feature disproportionate to its build cost. It answers "what changed since I last looked," which is what turns Signora from a research tool into a daily habit. It also collapses new-rep onboarding: territory context transfers instantly instead of over weeks.

**Demo scenario:** New rep inherits a territory → opens Timeline → has the full account history in minutes. Then: "what changed this week across my book."

**Customer outcome:** "Onboarding a rep onto a territory takes an afternoon, not a month."

**Success metrics:** Weekly active usage of Timeline · time-to-productivity for new reps · search usage per session.

---

## M11 — Revenue Intelligence Platform 💰

**User value:** The composed product surface — prioritized opportunities, evidence, recommendations, and reporting in one place.

**Business value:** The thing customers actually buy. Also the first surface that serves the *economic buyer* (RevOps/CRO) rather than only the end user — which is what makes renewal and expansion conversations possible.

**Demo scenario:** The full daily workflow: open Signora → prioritized list → evidence → act → outcome tracked. Plus the RevOps view: is the motion working, at the signal level.

**Customer outcome:** "Signora is the first thing my team opens each morning."

**Success metrics:** DAU/WAU · % of pipeline attributable to Signora · **renewal-intent signal from design partners**.

---

## M12 — Workflow Integration 💰

**User value:** Signora's intelligence appears in Salesforce, HubSpot, Pipedrive, Zoho, Slack, and Teams — no new tab required.

**Business value:** Directly serves the "Workflow Over Reporting" principle and removes the biggest adoption risk in this category: another tool reps forget to open. Also a competitive wedge — pushing *into* a customer's existing ABM/CRM spend makes Signora the reasoning layer above their stack rather than another thing to rip out.

**Demo scenario:** Opportunity appears in Salesforce with evidence attached; recommendation lands in the rep's Slack channel; rep acts without leaving either.

**Customer outcome:** "Signora works inside my existing stack."

**Success metrics:** % of workspaces with ≥1 integration active · action rate on in-CRM/in-Slack recommendations vs. in-app · integration reliability >99%.

---

## M13 — Enterprise Readiness 💰

**User value:** Invisible to end users. Decisive for their security teams.

**Business value:** Unblocks enterprise deals. Every deal lost to "you're too new/unproven" before this lands is a preventable loss. Covers SOC 2 readiness, PII/retention policy, AI spend governance, and validated scale.

**Demo scenario:** Security-review walkthrough — tenant isolation, least-privilege database access, secrets management, audit trails, AI vendor data-handling terms.

**Customer outcome:** "Our security team approved Signora."

**Success metrics:** Security reviews passed · SOC 2 readiness assessment cleared · load-tested at target scale · AI spend within per-workspace budget 100% of the time.

---

## Cross-Milestone Success Metrics

Tracked continuously from the milestone at which each becomes measurable. Aligned to [PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md) §North Star Metrics.

| Metric | Type | From |
|---|---|---|
| **Qualified pipeline generated per recommendation acted on** | 🎯 North Star | M9 |
| Recommendation acceptance rate | Leading indicator of trust | M9 |
| Signal-to-noise precision (rep-rated relevance) | Guards against alert fatigue | M5 |
| Time-to-first-recommendation after onboarding | Time-to-value | M9 |
| Win rate vs. baseline on Signora-sourced opportunities | Customer outcome | M9 + 1 sales cycle |
| Sales cycle length vs. baseline | Customer outcome | M9 + 1 sales cycle |
| Rep hours reclaimed per week | Customer outcome | M8 |
| Reasoning factual accuracy on golden sets | AI quality | M7 |
| Evidence-completeness rate | AI quality (release gate) | M7 |
| AI cost per recommendation | Unit economics | M7 |

**Deliberately not tracked as success:** signals detected, accounts scored, dashboard views, time-in-app. These measure system activity, not customer value, and optimising for them would corrupt the product exactly as it has corrupted several ABM vendors' public metrics ([PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md) Principle 8).

---

## GTM Sequencing Guidance

| Stage | Milestone | Motion |
|---|---|---|
| **Design partners** | M1 | Recruit now. Onboard into a real environment early; their data shapes the graph and the taxonomy. |
| **First value delivery** | M5 | Buying scores are the first thing worth a partner's attention. |
| **First contracts** | M6 | Earliest defensible commercial conversation. |
| **First pricing test** | M9 | Recommendations are what pricing should anchor on — that is where the value is. |
| **Broad launch** | M11 | Full product surface. |
| **Enterprise motion** | M13 | Do not start enterprise cycles before this; security review will stall them. |

**One recommendation I would push on:** recruit design partners at **M1**, not M6. The Knowledge Graph and Business Event taxonomy both improve with real customer data and real feedback, and the flywheel in [PRODUCT_DIFFERENTIATORS.md](PRODUCT_DIFFERENTIATORS.md) only starts turning once real accounts are flowing. Waiting until there is something impressive to show costs months of compounding.
