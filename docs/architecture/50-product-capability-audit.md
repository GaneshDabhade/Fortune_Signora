# 50 — Product Capability Audit

> **A record, dated 2026-08-03, by Lane B**, against the Revenue Intelligence Platform vision supplied by the product owner.
>
> **This is analysis, not implementation.** Nothing here was built. Every claim about what exists was measured from the repository, and every claim about what does not exist was checked before it was written.
>
> **The vision document is a reference, not an authority.** Where Signora's architecture already answers a need better, that is recorded as a challenge rather than a gap.

---

## 1 · What was measured

| | |
|---|---|
| **Modules built** | **15**, ~38,000 lines |
| **API paths exposed** | **24** |
| **Domain events catalogued** | **82** ([`06-events.md`](06-events.md)) |
| **Architecture documents** | 52 · **ADRs** 43 |
| **Frontend routes a customer can reach** | **5** |

### The headline, and it reframes every priority below

> **Signora has fifteen modules, eighty-two events and twenty-four endpoints behind five screens.**

**The platform is not short of capability. It is short of surface.** The audit below repeatedly finds the same shape: a capability the vision document lists as a module already exists as a *computed fact in the database with no route to a customer*. That is a far better problem than the opposite, and it changes what the roadmap should optimise for.

**Two ratified modules are not built** — Recommendation Engine and Revenue Intelligence Platform, both in [`04-modules.md`](04-modules.md), both absent from `backend/modules/`. **And one built module is not ratified**: `integrations` has 22 files and no entry in the module registry. That is a documentation defect worth fixing in the same pass as anything else touching that file.

---

## 2 · The eighteen modules, audited

**Categories, as instructed:** ✅ built · 🔄 built differently · 🧱 foundation ready · 🟡 partial · ❌ missing.

### 1 · Company Intelligence — 🔄 **built differently, and better**

**Exists as `knowledge_graph` + `provider_normalization`.** The vision asks for a company database with stored fields. Signora **does not store a company record**; it stores **claims**:

```
claim(provider, attribute, value, observed_at, raw_record_id,
      mapper_version, payload_provenance, subject_external_id)
```

**Every attribute carries its source, its observation time, and a pointer to the raw payload it came from.** The vision document lists this under *"Platform Capabilities Often Overlooked"* — source attribution, data lineage, historical snapshots, confidence scoring — as things products miss at enterprise scale.

> **Signora built them first and derived the company record from them.** *"Employee count 2024 → 350, 2025 → 500"* is not a feature to add; it is a `SELECT` over claims ordered by `observed_at`, and it is already there for every attribute of every entity.

**Ours is superior and should not be changed.** What is missing is the **read surface**: no screen or endpoint answers *"show me this company's history"*.

**Gap:** a company profile view. **Not a module — a read model over existing claims.**

### 2 · Contact Intelligence — 🟡 **partial, and the largest genuine gap**

`knowledge_graph` resolves entities of any `kind`, and `identity_binding` / `resolution_decision` already do person-grade identity work. **`commercial_profile.committee` models buying-committee *roles* — job titles, deliberately not names.**

**What does not exist:** people as records. No email, no phone, no seniority, no tenure, no reporting hierarchy, no relationship graph.

> **This is the gap a seller notices first** — *"who do I call?"* — and [`PRODUCT_EXPERIENCE.md`](../PRODUCT_EXPERIENCE.md) records every persona asking it. It is a **new bounded context**, and the audit's clearest *build this* finding.

**Challenge to the vision:** it proposes AI should *"automatically identify Champion, Economic Buyer, Blocker"*. **That must be deterministic in Signora, not inferred.** A champion is a conclusion drawn from observed engagement, and §10's rule applies — *if the system knows something deterministically, never ask a model to invent it.* AI may **explain** why somebody looks like a champion; the classification is a derivation.

### 3 · Intent Intelligence — 🔄 **built differently, and the vision is thinner**

**`observation_engine` → `business_event_engine` → `signal_engine` is exactly this**, and it is a stronger design than a weighted list of sources. The vision proposes ~25 intent sources each with *weight, confidence, recency, strength*, combined into an intent score.

Signora already has: providers behind a port, observations derived from claims, **business events** interpreted from observations, and **signals** with a catalog that records each one's limitations.

> **The vision's model is a bag of weighted sources. Signora's is a chain of interpretations, each of which can be shown to a customer.** That is why the product can say *"what this cannot tell you"* — a weighted-sum model has nothing to say there.

**Gap:** more *sources*, not a different architecture. Every new one is a provider adapter behind the existing port. **The abstraction is the finished part.**

### 4 · ICP Builder — 🟡 **partial, and a real philosophical fork**

`commercial_profile` has `icp`, `segment`, `icp_segment_version`, `icp_segment_state` — **versioned, state-tracked ICP declarations in the customer's own words.**

The vision asks for a **visual query builder** — `Company Size > 500 AND AWS = true AND Hiring contains "AI Engineer"` with a live preview.

**These are different products and the difference is deliberate.** [`40-commercial-profile.md`](40-commercial-profile.md) and the screen itself say it: *"Signora records what you say here; it does not grade anyone against it."*

> **The fork: is an ICP a description or a filter?** Today it is a description, and the scoring engine does not consume it — which is precisely [PX-314](../PRODUCT_EXPERIENCE.md): *Your business* claims Signora needs this before it can judge anyone, then scores twelve accounts without it. **One of those two positions has to give, and it is a product-owner decision, not an implementation one.**

**Recorded as [C-322](../LANE_COORDINATION.md).** A query builder is buildable on the existing claim model — `claim(attribute, value)` is already the shape a filter needs.

### 5 · Account Scoring Engine — 🔄 **built differently; the vision's ten scores are wrong for Signora**

`buying_score_engine` computes one attention score with a **full contribution ledger** — every point traceable to a signal, a relevance, a freshness band and an evidence reading.

The vision proposes **ten parallel scores** (Fit, Intent, Engagement, Relationship, Expansion, Competitive Risk, Renewal Risk, Champion, Coverage, Revenue Potential) combined into a weighted Revenue Score.

**Challenged, on evidence from the review.** The product already shows *"75"* and *"90 of 120 points"* on one screen and a customer cannot reconcile two numbers ([PX-302](../PRODUCT_EXPERIENCE.md)). **Ten scores is ten times that problem.**

> **What a seller needs is not more scores — it is the same score decomposed along more axes.** Signora's ledger already does this: the score *is* its contributions. Adding *Expansion* and *Renewal Risk* as separate models duplicates the machinery; adding them as **postures within the existing decomposition** reuses it.

**One genuine gap:** every score today is about **opportunity**. Nothing models **risk** — churn, renewal, a champion leaving. That is real, and it belongs as a **new signal family and posture**, not a new engine.

### 6 · Buying Committee Mapping — 🟡 **partial** · roles yes, people no. Blocked on module 2.

### 7 · Territory Management — ❌ **missing, and questionable at this stage**

Ownership exists (`opportunity_state` records who took an account). Regions, capacity planning and round-robin do not.

**Challenge:** territory management is an *administrative* capability that matters at 50 sellers and is invisible at 5. **It is a GA-scale concern, not a product-differentiation one**, and building it before search and filters would be optimising for a customer Signora does not have yet.

### 8 · Sales Workspace — 🔄 **built, and it is the best screen in the product**

**The attention list is this module**, and the review measured it as the strongest screen: 169 words, 13 actions, **no paragraph over 25 words**.

**Gaps** from the vision's list: meetings, tasks, emails and calls — **all of which Signora does not do and arguably should not.** *Deals at risk* needs module 5's risk postures. *Pipeline movement* needs Timeline mounted, which is [C-024](../LANE_COORDINATION.md).

### 9 · AI Copilot — 🧱 **foundation ready, surface absent**

`ai_platform` (5,380 lines) has the provider abstraction, the Prompt Registry, the release rule, the evaluation harness and `ai_inference` provenance. `ai_reasoning_engine` produces the Decision Package. `ai_research_engine` (4,027 lines) does agentic multi-step research.

**Everything a copilot needs exists except a place to type.**

> **Challenge, and it is the most important one in this audit.** The vision lists *"Generate email · Write LinkedIn message · Write cold call script · Proposal generation · ROI calculation"*. **Signora's AI philosophy permits explanation, summary, synthesis, personalisation and communication — and these are communication, so they qualify.** But *"Suggest next actions"*, *"Risk analysis"* and *"Find competitors"* are **conclusions**, and those are deterministic reasoning's. **Adopting the vision's copilot list literally would put a model in the decision path**, which every ADR in `docs/architecture/adr/` since 0012 exists to prevent.
>
> **The adaptation: a copilot that can *say* anything and *decide* nothing.**

### 10 · Pipeline Intelligence — ❌ **missing, because there is no pipeline**

Signora models **opportunities before they are deals** — qualification, not stages. No amount, no close date, no forecast category. **Deal health presupposes a deal**, and that data lives in a CRM.

**This is where [MC-4 · CRM write-back](../PRODUCT_EXPERIENCE.md) becomes structural rather than convenient**: pipeline intelligence requires reading the CRM's pipeline. `integrations` has the connection model and no OAuth flow.

### 11 · Forecasting — ❌ **missing**, and downstream of 10. Not addressable until pipeline data exists.

### 12 · Marketing Intelligence — ❌ **missing, and I would challenge whether it belongs**

Campaign attribution needs campaigns, and Signora has no marketing surface at all. **Adding attribution would mean owning campaigns**, which is a different product. **Recommend: out of scope until a customer asks.**

### 13 · Customer Expansion — 🟡 **partial, and cheaper than it looks**

`opportunity_engine` already qualifies **Expansion opportunity** as a posture — it was on screen in every review. What is missing is the **customer** side: knowing which accounts are already customers. That is one boolean from a CRM ([MC-4](../PRODUCT_EXPERIENCE.md)) plus the risk postures from module 5.

### 14 · Competitive Intelligence — 🧱 **foundation ready**

`provider_platform` can watch any subject; `business_event_engine` can interpret any change. **Competitor monitoring is a target list and an event taxonomy, not an engine.** The taxonomy is the work.

### 15 · Conversation Intelligence — ❌ **missing, and it is a company-sized decision**

Recording, transcription, storage, retention, consent, and per-region compliance. **This is Gong's entire product.** `integrations` lists Slack, Teams and calendars as connectors. **Recommend: explicitly out of scope, and say so in the roadmap** — leaving it unmentioned invites somebody to start it.

### 16 · Workflow Automation — 🧱 **foundation ready, and it is the strongest leverage in this audit**

**Signora already has the whole substrate**: 82 catalogued events, a transactional outbox, ARQ workers, idempotent handlers, dead-lettering and replay. The vision asks for a Zapier-like builder over exactly these primitives.

> **`IF Bombora score increases AND funding announced AND pricing page visited THEN …` is a subscription over three existing events.** The engine exists; what is missing is **a way for a customer to express a rule**, and a **safe action set** for it to trigger.

**Challenge:** the vision's actions include *"Generate email · Start outreach"* — Signora sends nothing. **The honest first version triggers what Signora already does**: watch an account, raise its posture, notify a person, record a decision.

### 17 · Analytics — ❌ **missing**, and correctly deprioritised. Nothing to analyse until there is more than one workspace's worth of history.

### 18 · Admin Platform — 🟡 **partial**

**Exists:** RBAC (Casbin), multi-tenancy (RLS, forced, with a Security Invariants suite proving it), audit-grade immutable history, and per-tier database identities.

**Missing:** SSO/SCIM, API keys, webhooks, retention policy, GDPR/CCPA tooling, rate limits, custom objects, field mapping.

> **This is the *"procurement reviewer"* persona from [`PRODUCT_EXPERIENCE.md`](../PRODUCT_EXPERIENCE.md), and it is the category most likely to lose an enterprise deal after the product has already won the evaluation.**

---

## 3 · Where Signora is ahead of the vision document

**Recorded deliberately, because these are the parts a competitor cannot copy in a quarter.**

| Vision lists as *"often overlooked"* | Signora |
|---|---|
| Source attribution for every field | **`claim.provider`, on every attribute** |
| Data lineage — where it came from, when | **`raw_record_id` · `mapper_version` · `payload_provenance` · `observed_at`** |
| Historical snapshots and time travel | **Claims are immutable and timestamped. History is a query, not a feature** |
| Entity resolution across providers | **`identity_binding` + `resolution_decision`, with the decision recorded** |
| AI explainability — *why* this recommendation | **The contribution ledger. Every point traceable to a provider reading with a date** |

**And one the vision does not list at all:** *"what this cannot tell you"* — a per-signal statement of limitations, authored by a domain expert in a reviewed catalog rather than by a model. **No competitor ships this**, and it is the reason a sceptical evaluator keeps reading.

---

## 4 · Policy challenges — with evidence, as instructed

**Three, and only three. Each names the assumption that changed.**

### 4a · `04-modules.md` does not describe the system — 🔴 **documentation defect**

**Evidence:** `integrations` is built (22 files, 1,923 lines, three endpoints) and **absent from the module registry**. Recommendation Engine and Revenue Intelligence Platform are **in the registry and absent from the code.**

**What changed:** the registry was written before M13 and has not been reconciled since. **Under lane rotation this is the document a cold lane trusts first** (§12), and it is currently wrong in both directions.

**Proposed:** reconcile in one pass. Add Integrations; mark Recommendation Engine and RIP as ratified-unbuilt with their milestone.

> **Not corrected by this lane.** `docs/architecture/01`–`21` is 🔴 in the Change Budget — product owner and an ADR (§20e). **The defect is reported with the evidence rather than fixed quietly**, which is the same call this lane made on [B-312](../BUGS.md), [B-313](../BUGS.md), [B-314](../BUGS.md) and [B-315](../BUGS.md).

### 4b · The ICP is declared and consumed by nothing — 🟠 **architectural contradiction**

**Evidence:** [PX-314](../PRODUCT_EXPERIENCE.md). *Your business* states Signora needs the catalogue *"before it can tell you anything useful about anyone else's company"*; a freshly seeded organization has **no products and twelve scored accounts**.

**What changed:** `commercial_profile` shipped its declaration surface (M12.5) before `buying_score_engine` had a reason to read it. **Neither module is wrong; the seam between them is unbuilt**, and the screens now contradict each other.

**Proposed:** [C-322](../LANE_COORDINATION.md) — decide whether relevance is scored against the declared ICP. **This is the highest-value architectural decision in the audit**, because it is what makes the whole commercial-profile module load-bearing rather than decorative.

### 4c · Nothing in the product records *when Signora last looked* — 🟠

**Evidence:** searched `app/` and `components/` — no *"as of"*, no *"last synced"*. `provider_watermark` and `provider_sync` **hold this fact already**.

**What changed:** freshness became customer-visible the moment evidence started ageing out on screen (*"Evidence expired"*, *"Cooling"*). **The data exists; the contract to expose it does not.**

**Proposed:** a `last_observed_at` on the account read model. **Small, and it is the difference between *"nothing happened"* and *"nothing was collected"*.**

> **Nothing else in `CLAUDE.md`, the ADRs or the Engineering Laws obstructed a single capability in this audit.** Where a capability was hard, it was hard because it is genuinely large — not because a policy forbade it. **That is worth stating explicitly**, because an audit that challenged nothing would be suspicious and one that challenged everything would be cheap.

---

## 5 · The implementation roadmap

**Ordered by what unblocks the most, not by what the vision lists first.** Sizes are S/M/L/XL. Lanes are suggestions.

### Epic A — Make the existing intelligence reachable

> **Fifteen modules behind five screens.** Every slice here exposes something already computed. **Highest value per unit of work in the repository.**

| # | Slice | Module | Depends on | Size | Lane |
|---|---|---|---|---|---|
| **A1** | **Account search** — find by name | Product Surface · `knowledge_graph` | — | **M** | Product Surface |
| **A2** | **The accounts list** — all of them, filtered by score, posture, owner, freshness | Product Surface · `opportunity_engine` | A1 | **L** | Product Surface |
| **A3** | **Mount Timeline** — account history on the brief | Product Surface | [C-024](../LANE_COORDINATION.md) | **S** | Product Surface |
| **A4** | **Freshness** — *"as of"* on every account | `provider_platform` → read model | 4c | **S** | Provider Platform |
| **A5** | **Company profile** — attribute history from claims | Product Surface · `knowledge_graph` | A1 | **M** | Product Surface |
| **A6** | **`Needs identity` queue** — unnamed records leave the working list | `knowledge_graph` · Product Surface | [C-321](../LANE_COORDINATION.md) | **M** | Knowledge Graph |

### Epic B — Close the contradictions

| # | Slice | Module | Depends on | Size | Lane |
|---|---|---|---|---|---|
| **B1** | **ICP consumed by scoring** — relevance measured against the declaration | `buying_score_engine` · `commercial_profile` | [C-322](../LANE_COORDINATION.md) | **L** | Commercial Profile |
| **B2** | **A first-run path** — sign-up to first account, guided | Product Surface | [C-320](../LANE_COORDINATION.md) | **M** | Product Surface |
| **B3** | **Email transport** — a customer can verify their own address | Deployment | [C-320](../LANE_COORDINATION.md) | **S** | QE / M14.5 |

### Epic C — People

| # | Slice | Module | Depends on | Size | Lane |
|---|---|---|---|---|---|
| **C1** | **Person as an entity** — the bounded context | **new: `people`** | ADR | **XL** | dedicated |
| **C2** | **Committee members** — roles become names | `commercial_profile` · `people` | C1 | **L** | Commercial Profile |
| **C3** | **Deterministic committee roles** — champion, blocker, economic buyer, derived | `people` · `observation_engine` | C2 | **L** | dedicated |

### Epic D — Risk, the missing half of the score

| # | Slice | Module | Depends on | Size | Lane |
|---|---|---|---|---|---|
| **D1** | **Risk signal family** — champion departure, usage decline, competitor entry | `signal_engine` | catalog work | **L** | Signal Engine |
| **D2** | **Risk postures** in the existing decomposition — **not a second score** | `buying_score_engine` | D1 | **M** | Buying Score |
| **D3** | **Customer flag** — which accounts we already sell to | `integrations` | E1 | **S** | Integrations |

### Epic E — The enterprise gate

| # | Slice | Module | Depends on | Size | Lane |
|---|---|---|---|---|---|
| **E1** | **CRM OAuth + read** — Salesforce, HubSpot | `integrations` | credentials | **XL** | Integrations |
| **E2** | **CRM write-back** | `integrations` | E1 | **L** | Integrations |
| **E3** | **SSO / SCIM** | auth tier | ADR | **L** | QE |
| **E4** | **Audit log · retention · API keys · webhooks** | platform | RFC (§20a) | **L** | QE |

### Epic F — Workflow automation

| # | Slice | Module | Depends on | Size | Lane |
|---|---|---|---|---|---|
| **F1** | **Rule model** — conditions over catalogued events | **new: `workflow`** | ADR | **L** | dedicated |
| **F2** | **Safe action set** — watch, re-post, notify, record. **Nothing that sends** | `workflow` | F1 | **M** | dedicated |
| **F3** | **Rule builder** | Product Surface | F1, A2 | **L** | Product Surface |

### Epic G — Copilot

| # | Slice | Module | Depends on | Size | Lane |
|---|---|---|---|---|---|
| **G1** | **Ask about this account** — explanation only, grounded in the ledger | `ai_reasoning_engine` | prompt release | **L** | AI |
| **G2** | **Draft an approach** — communication, never conclusion | `ai_reasoning_engine` | G1, C2 | **L** | AI |

### Suggested order

```
A4 · A3 · A1  ──▶  A2 · A5      surface what exists          weeks 1–4
B3 · B2                          a customer can get in        weeks 2–3
C-322 ──▶ B1                     stop contradicting ourselves weeks 3–6
C-321 ──▶ A6                     the unnamed record           weeks 5–7
E1 ──▶ E2 · D3                   the enterprise gate          weeks 6–12
D1 ──▶ D2                        risk                          weeks 8–12
C1 ──▶ C2 ──▶ C3                 people                        weeks 10–18
F1 ──▶ F2 ──▶ F3                 workflow                      weeks 14–20
G1 ──▶ G2                        copilot                       weeks 16–22
E3 · E4                          procurement                   before GA
```

**A4 is first deliberately** — it is a small slice, it closes a contradiction, and it is the cheapest thing in the repository that changes how the product *feels*.

---

## 6 · Dependency graph

```
                    ┌─ A1 search ─┬─ A2 accounts list ─┬─ F3 rule builder
                    │             └─ A5 company profile │
  existing modules ─┤                                   │
                    ├─ A3 timeline (C-024)              │
                    ├─ A4 freshness ────────────────────┘
                    └─ A6 needs-identity (C-321)

  C-322 ──▶ B1 ICP consumed by scoring
  C-320 ──▶ B3 email transport ──▶ B2 first-run path

  E1 CRM oauth ──┬──▶ E2 write-back
                 └──▶ D3 customer flag ──┐
                                          ├──▶ D2 risk postures
  D1 risk signals ────────────────────────┘

  C1 people ──▶ C2 committee members ──▶ C3 derived roles ──▶ G2 draft approach
  F1 rule model ──▶ F2 safe actions ──▶ F3
  G1 ask ──▶ G2
```

**Three items block the most and are all decisions rather than code:** [C-320](../LANE_COORDINATION.md), [C-321](../LANE_COORDINATION.md), [C-322](../LANE_COORDINATION.md).

---

## 7 · TODOs

**Proposed, not inserted.** A lane may not add `READY` work to [`BACKLOG.md`](../BACKLOG.md) (§20e) — these are offered for the product owner to admit, with ids left unallocated so the block rules are not pre-empted.

Each is written to be claimable without asking a question. **Two are given in full as the pattern; the remaining twenty follow the same shape in §5's tables.**

### TODO-A4 · The product says when it last looked · **S**

| | |
|---|---|
| **Objective** | Every account shows when its evidence was last collected |
| **Customer value** | A seller cannot currently distinguish *"nothing has happened here"* from *"nothing has been collected since Tuesday."* **The product's entire promise is *here is what changed*** |
| **Modules** | `provider_platform` (owns `provider_watermark`, `provider_sync`) → the account read model → Product Surface |
| **Dependencies** | None. **The fact already exists and is stored** |
| **Architecture** | A derived field, not a stored one — §2, *truth has one authoritative representation*. Read from the watermark at query time |
| **UX** | One line near the score. **Not a new section** — the brief already measures 619 words ([PRODUCT_EXPERIENCE.md](../PRODUCT_EXPERIENCE.md)) |
| **AI** | None |
| **Risks** | *Last looked* is per provider; the screen needs one number. **Recommend the oldest**, because that is what bounds the claim |
| **Extensibility** | The same field drives a staleness badge and, later, a re-sync control |

### TODO-C1 · Person becomes an entity · **XL**

| | |
|---|---|
| **Objective** | A new bounded context owning people: identity, attributes, employment, and the relationships between them |
| **Customer value** | *"Who do I call?"* — **asked by every persona in the review and answerable by nothing today.** The buying committee is job titles with no members |
| **Modules** | **New `people`.** Consumes `provider_normalization`; consumed by `commercial_profile`, `ai_reasoning_engine` |
| **Dependencies** | An ADR: new bounded context (🔴, §20e). Provider coverage for contact data |
| **Architecture** | **Reuse the claim model rather than inventing a second one.** `identity_binding` and `resolution_decision` already do exactly this work for organizations; a person is a different `entity.kind`, not a different mechanism. **Whether it is a module or a `kind` is the ADR's central question** — and the audit's recommendation is a module, because people carry PII, consent and retention obligations that organizations do not |
| **UX** | A committee that names people; a person view reachable from an account |
| **AI** | **Roles are derived, never inferred** (§10). AI explains why somebody looks like a champion; the classification is deterministic |
| **Risks** | **PII is the whole risk.** GDPR, retention, right-to-erasure — and erasure conflicts with §2's immutability rule for claims. **That conflict must be resolved in the ADR, not discovered during implementation** |
| **Extensibility** | Relationship graph · reporting hierarchy · tenure and job-change signals (a champion leaving is the highest-value risk signal in D1) |

---

## 8 · Risks and long-term observations

| | |
|---|---|
| **The surface deficit compounds** | Every module shipped without a screen widens the gap between what Signora can do and what anybody can see it do. **Five screens over fifteen modules is the defining fact of the repository**, and Epic A exists to close it before more is built underneath |
| **PII changes the architecture's shape** | Epic C introduces the first data a customer can demand be erased. **Immutable claims and right-to-erasure are in direct tension**, and that is an ADR before it is a module |
| **CRM integration is the commercial gate** | Pipeline intelligence, forecasting, expansion and customer risk **all sit behind E1**. It is one integration and it unblocks four vision modules |
| **The copilot is where the AI philosophy will be tested** | Every pressure will be to let it decide. **The line — say anything, decide nothing — must be in an ADR before G1 starts**, not defended slice by slice |
| **Two ratified modules are unbuilt** | Recommendation Engine and Revenue Intelligence Platform. **Much of what they were to do now lives in Product Surface**, and the registry should either reflect that or the modules should be built |
| **What was deliberately not proposed** | Conversation intelligence, marketing attribution, territory management, forecasting. **Each is a product, not a feature**, and recommending them here would have been listing rather than auditing |
