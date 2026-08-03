# 50 · Sales Engagement Intelligence — discovery

> **Assigned 2026-08-03 by the product owner, to Lane A, immediately after Lead Lifecycle was handed to QE.** *"If Lead Lifecycle answered how do I manage an opportunity, this should answer how do I turn that opportunity into a meaningful customer conversation?"*
>
> **No code was written before this document.** The repository was audited first, on the discipline that produced nine Lead Lifecycle slices without changing a domain once.

---

## 1 · The finding that decides the milestone

**Signora has no people, and their absence is a deliberate, documented, defensible design decision — not an oversight.**

```python
class EntityKind(StrEnum):
    """Person is deliberately absent: claims carry role changes but no person
    *identifier*, so there is no identity to resolve. Adding people now
    would mean inventing one."""
    COMPANY = "company"
    TECHNOLOGY = "technology"
```

And, stated even more directly in the buying committee:

> *"A committee is a **template of roles**, never a list of people. Person entities are deferred platform-wide… naming an individual would put **personal data in a module with no lawful basis declared for holding it** and no consumer able to use it."*

**The pipeline already detects `LEADERSHIP_APPOINTED` — *"Appointed a new VP of Engineering"* — and does not know who.** A `role_change` claim carries `title`, `seniority` and `direction`. There is no name, no email, no identifier, and nothing anywhere in the canonical vocabulary that could hold one.

### What *"Contact Sarah Johnson"* would actually require

| # | Prerequisite | Whose | Cost |
|---|---|---|---|
| **1** | **A lawful basis for holding personal data** — declared, with retention, subject access, erasure and a processing record | **Product owner and legal.** Not an engineering decision at all | The gate on everything below |
| **2** | `EntityKind.PERSON` + **identity resolution for people** | Knowledge Graph | **Harder than companies.** People share names, change employers, and a wrong merge attributes a stranger's job move to your buyer |
| **3** | Person fields in the **canonical claim vocabulary** | Provider Normalization | A reviewed artifact change; every provider adapter follows |
| **4** | **Contact providers**, and a route for their data to arrive | Provider Platform — **already blocked at [C-021](../LANE_COORDINATION.md)** | A new provider category on a dispatch path that does not run |
| **5** | PII in prompts, in the evidence set, in the timeline, in exports | AI Platform, Timeline, every downstream surface | Touches the entire pipeline |

> **Four bounded contexts and a legal decision.** This is not a slice, and it is not Lane A's to start. **It is a platform capability with a compliance precondition**, and the precondition is the product owner's.

---

## 2 · But the mission is larger than contacts, and most of it is composable today

**Re-read as written, the assignment asks for eleven things.** Only three of them need a person:

| The seller's question | Answerable now? | From what |
|---|---|---|
| **Why should I contact them?** | ✅ | Signals, business events, contributions |
| **Why now?** | ✅ **The strongest answer in the product** | `BuyingScore.trigger`, the score movement, the event that caused it |
| **What changed recently?** | ✅ | The account timeline |
| **Which business problem are they likely experiencing?** | ✅ | The leading hypothesis, its posture, its catalog definition |
| **Which evidence supports that message?** | ✅ | The evidence drawer, corroboration, citations |
| **Why does Signora believe this?** | ✅ | Contributions, the ledger, narration, validation |
| **What should I avoid mentioning?** | ✅ **Already computed and never surfaced** — validation records what a hypothesis *cannot* prove | `AccountValidation` |
| **Which *role* should receive it?** | ✅ **Declared by the customer and read by nobody** | The buying committee |
| **What should I ask them?** | ⚠️ Derivable — see §5 | Signals + committee part + what validation says is unproven |
| **Which *person*?** | ⛔ **Blocked** | §1 |
| **Which channel, which message to which inbox** | ⛔ Blocked, **and out of scope by the first principle** | §3 |

> **Eight of eleven are composable from capabilities that already exist**, and one of them — the buying committee — is a customer-authored declaration whose own docstring says **"nothing downstream reads it yet."**
>
> **That is the seventh time this pattern has appeared in two milestones.** Built, correct, and unreachable.

---

## 3 · The first principle, and what it rules out permanently

**The product owner's rule, adopted verbatim as the milestone's design constraint:**

> **Outreach tools optimise volume. Signora optimises relevance.**

**What that rules out — not for now, but by design:**

| | |
|---|---|
| **Message generation** | ⛔ *"Hi John, I hope you're doing well"* is what every assistant already produces. A generated paragraph is **believed, not checked** — and this platform's whole claim is that its output can be defended (`CLAUDE.md` §2) |
| **Sequences and cadences** | ⛔ A cadence is a volume instrument. It answers *how many times do I touch this* — a question relevance never asks |
| **Send, schedule, track opens** | ⛔ The seller's own mail client already does it, better, with their signature and their deliverability |
| **A contact table** | ⛔ *"I do not want a table of contacts. I want an experience"* — and a table would be a CRM feature bolted onto an intelligence platform |

**What it demands instead:** every sentence a seller reads traces to a recorded observation, from a named provider, at a stated time, that they can open. **The evidence drawer already does this**, and it is the model for everything here.

---

## 4 · The capability that is buildable now: the Approach Brief

**The composition, stated as one screen.** Nothing below needs a person, a new provider, or a legal decision.

```
  ┌─ Why this account, now ────────────────────────────────────────┐
  │  The leading hypothesis, its posture, and the event that       │
  │  moved the score — all already on the wire                     │
  ├─ Who has to agree ─────────────────────────────────────────────┤
  │  The customer's own committee, per product:                    │
  │    VP Engineering   champion    ← the one to start with, and   │
  │    CFO              economic buyer          why                │
  │    Security         gatekeeper                                 │
  │  Roles, never people. No person is named because none exists   │
  ├─ What has changed there ───────────────────────────────────────┤
  │  The account timeline, filtered to what a seller would open    │
  │  a conversation with                                           │
  ├─ What to ask ──────────────────────────────────────────────────┤
  │  Derived from the hypothesis and from what validation says is  │
  │  **not** proven — questions, never claims                      │
  ├─ What not to say ──────────────────────────────────────────────┤
  │  Validation's unproven assertions, surfaced as a caution       │
  └─ Every line opens its evidence ────────────────────────────────┘
```

**The one genuinely new idea is the last line of the middle block: *which committee role to start with, and why*.** Everything else is composition and surfacing.

### Why *that* is a real capability rather than a rearrangement

The customer has declared *"for Revenue Cloud, my champion is the VP of Engineering and my economic buyer is the CFO."* The pipeline has detected *"they appointed a new VP of Engineering three weeks ago"* and *"engineering headcount grew 42%"*.

> **Nothing in Signora joins those two facts**, and the join is the entire product: *the role you told us argues for you internally is the role that just changed at this company, and here is the evidence.*

**No person is named and the recommendation is still actionable** — a seller who knows *the newly-appointed VP Engineering is the one to approach, because they own the initiative your signal detected* has had most of the work done for them. **Finding that individual's name is the last mile, and it is the mile that needs the legal decision.**

---

## 5 · The models

### Stakeholder recommendation — roles ranked by evidence, never by declaration

**Input:** the committee (declared) × the account's business events (observed) × the leading hypothesis (derived).

**Ranking rule:** a role rises when **the evidence names it**. *"Appointed a new VP of Engineering"* raises the role whose title matches; *"Security review platform adopted"* raises the gatekeeper; a hiring surge in engineering raises the engineering roles.

| | |
|---|---|
| **Where it must live** | **Not Commercial Profile.** That module refuses evaluation by design — *"a committee is one plausible field away from becoming an influence model"* and a structural test enforces it. **The ranking belongs to a consumer, with evidence to reason from** |
| **What it must never become** | A stored influence score. It is **derived at read time from the live evidence**, exactly as `evidence_state` is |
| **Why not AI** | A title match against a declared role is deterministic. **If the platform already knows something, never ask a model to invent it again** (`CLAUDE.md` §2) |

### Conversation intelligence — questions, never claims

**A question is safe where an assertion is not.** *"Has the new VP set a platform budget yet?"* is useful whether or not Signora is right; *"They have a platform budget"* is a claim a seller would be embarrassed by.

**And validation already computes what is unproven.** `AccountValidation` records what a hypothesis asserts and cannot support — **the single best source of *what to ask* in the entire platform**, currently rendered only as a caution.

### Confidence — derived, and expressed in words

**Never a percentage.** The platform has refused invented precision everywhere: revenue is a band because *"inventing a point estimate from a range is exactly the kind of quiet fabrication"* this architecture rejects; `MatchStrength` refuses numeric conversion. **A confidence figure on a stakeholder recommendation would be the same fabrication.**

Derived from what is already measured: **how many providers corroborate · how recent · how directly the evidence names the role · whether the reading is contested.** Rendered as *strong · reasonable · thin*, each opening the evidence behind it.

### Explainability — the acceptance test for the whole milestone

**Every recommendation answers all of these from recorded facts, or it is not shipped:**

| Question | Source |
|---|---|
| **Why this role?** | The declaration says it, the evidence names it |
| **Why not another?** | The evidence does not name it — **said out loud, not left as silence** |
| **Why now?** | The event that moved the score |
| **Why this topic?** | The leading hypothesis and its posture |
| **Why this confidence?** | Corroboration, recency, directness, contest |
| **Why this account before another?** | The attention ranking, already the list's order |
| **What might be wrong?** | Validation's unproven assertions |

---

## 6 · Repository reuse audit

| Capability | Exists? | Verdict |
|---|---|---|
| **Buying committee** | ✅ Declared, versioned, per product — **read by nobody** | **Surface and consume.** The single largest reuse in this milestone |
| **Signals and the catalog** | ✅ Named hypotheses with definitions and postures | Compose |
| **Business events** | ✅ Eleven types incl. `LEADERSHIP_APPOINTED` with `title` and `seniority` | Compose — **and `title` is what joins an event to a committee role** |
| **Evidence and corroboration** | ✅ Drawer, citations, provider agreement | Reuse verbatim |
| **Validation** | ✅ What a hypothesis cannot prove | **Reuse for *what to ask* and *what not to say*** |
| **Narration** | ✅ AI prose beside its evidence | Reuse |
| **Score contributions** | ✅ Ledger, per event | Reuse |
| **Timeline** | ✅ What changed, by day | Reuse |
| **Attention ranking** | ✅ Which account first | Reuse |
| **Ownership and workflow** | ✅ Lead Lifecycle | Reuse — an approach brief belongs to whoever holds the account |
| **`EntityName`, evidence drawer, badges, empty states** | ✅ | Reuse |
| **People** | ❌ | **Blocked — §1** |
| **Contact providers** | ❌ | **Blocked — §1, and C-021** |
| **Relationship strength, influence over time, promotions** | ❌ | All are person-shaped. **Blocked by the same gate** |

> **Nothing in §4 requires a new module.** It requires a consumer of five existing ones — which is a real architectural question (§8), but a far smaller one than a new bounded context.

---

## 7 · Missing capability audit

| | Missing | Blocked by |
|---|---|---|
| **People** | Every person-shaped feature in the assignment: named contact, relationship strength, promotions, job changes, conference appearances, shared investors | **The lawful-basis decision** (§1) |
| **Role → evidence join** | Nothing connects a declared committee role to an observed leadership event | ✅ **Buildable now.** The core of §4 |
| **A consumer for the committee** | It is declared and read by nothing | ✅ **Buildable now** |
| **Question generation** | Validation knows what is unproven; nothing turns that into what to ask | ✅ **Buildable now** |
| **Per-product context** | The committee is per product; the score is per account. **Which product is this opportunity about?** | ⚠️ **Unanswered anywhere.** See §9 |
| **Historical wins informing recommendations** | No outcome-to-evidence feedback exists | ⚠️ Needs closed-won volume that does not exist yet |

---

## 8 · The architectural question this milestone must answer first

**Where does an approach brief live?**

It reads the committee (Commercial Profile), signals (Signal Engine), business events, validation, narration (AI Reasoning) and the opportunity (Lead Lifecycle). **No existing module may read all of those** — and the module that could would be reaching across most of the pipeline.

| Option | |
|---|---|
| **A** | **A new module, `sales_engagement`.** Clean ownership, a real bounded context, and the dependency graph gains one node reading six. **Honest, and the largest change** |
| **B** | **Extend the Opportunity Engine.** ⛔ **Wrong, and the module's own contract says so**: *it answers what is the state of the work, never what is true about the company* (49 §19), and its import contract forbids reaching the Signal Engine at all |
| **C** | **A read-model composition in the API layer**, like the account brief already is. **Smallest**, and it puts commercial reasoning in a composition root, which is where reasoning goes to become invisible |
| **D** | **Extend AI Reasoning Engine.** ⛔ The ranking is **deterministic**, and putting it behind a model would be exactly the mistake `CLAUDE.md` §2 names: *if the system already knows something deterministically, never ask a model to invent it again* |

**Recommendation: A**, and it needs an ADR before any code. **The composition is the product**, and a product capability that lives in a composition root has no owner, no tests of its own, and no boundary.

---

## 9 · Product owner decisions required

| | Decision | Why it matters | Recommendation |
|---|---|---|---|
| **D-1** | **Is Signora going to hold personal data?** Lawful basis, retention, erasure, subject access | **The gate on every person-shaped feature in the assignment.** It is a legal and product decision; no engineering answer exists | **Not yet.** §4 delivers most of the value without it, and taking it later costs nothing that taking it now would save |
| **D-2** | **Does an approach brief get its own module?** (§8) | Determines whether this milestone starts with an ADR or a slice | **Yes — a new module, with an ADR first** |
| **D-3** | **Which product is an opportunity about?** The committee is per product; opportunities have no product | **Blocks role ranking**, because *which committee* is unanswerable. It is also a Commercial Profile ↔ Lead Lifecycle boundary question | **Ask the seller**, once, at the moment they take the account on — one field on a decision they are already making |
| **D-4** | **Is *what to ask* generated or derived?** | Derived is checkable and cheap; generated is fluent and must be evaluated | **Derived first.** If a customer finds it stilted, that is the evidence for a prompt |

---

## 10 · Future pressure — recorded, not designed

| Trigger | Pressure | Direction |
|---|---|---|
| **100 contacts at one account** | Only once D-1 is answered. The committee has `MAX_ROLES = 16`; **an org chart is not a committee** | Rank roles, never list people |
| **10,000 contacts** | Identity resolution for people, at provider scale | The company resolver's problem, harder |
| **Matrix organisations · multiple business units** | One committee per product is already the right shape; **one committee per *unit* is not** | Scope the declaration, not the model |
| **Mergers and acquisitions** | Two committees, one company | Knowledge Graph's identity problem again |
| **Existing-customer expansion · cross-sell · upsell** | The committee that bought is not the committee that expands | **A second declaration**, not a second model |
| **Partner and channel selling** | The buyer is not the customer | Same ADR that partner *ownership* needs (49 §28) |
| **Government and enterprise procurement** | The gatekeeper becomes the longest part of the deal | `GATEKEEPER` already exists and is unranked — **the model is ready** |
| **AI agents acting for sellers** | An agent contacting a person is a different legal act from a person doing it | **D-1 with a much higher bar** |

---

## 11 · Premium experience — what would make this feel like an experienced AE

| | |
|---|---|
| **One screen, no navigation** | *"How many clicks before a seller knows who to contact?"* — **zero.** It belongs on the brief they already open |
| **Disagreement is a first-class act** | A seller who thinks the champion is wrong should be able to say so, with a reason — **the same shape as every decision in Lead Lifecycle**, and it is the only feedback the ranking would ever get |
| **Comparison, not just ranking** | *Why this role and not that one* is more convincing than a ranked list, and the evidence is already per-role |
| **Nothing generated that cannot be opened** | Every line traces to a provider, a date and a claim |
| **Silence when there is nothing to say** | An account with no committee declared, or no events naming a role, **says so** rather than inventing a recommendation — the rule the attention list and the decided section both follow |

---

## 12 · Proposed roadmap, in the order value arrives

| | Slice | Blocked? |
|---|---|---|
| **SE-01** | **ADR — the approach brief's home** (§8, D-2) | Product owner |
| **SE-02** | **Which product is this opportunity about?** (D-3) | Product owner |
| **SE-03** | **The committee, surfaced on the account brief** — read-only, roles, no ranking. *The customer's own declaration reaching a screen for the first time* | ✅ Buildable after SE-01 |
| **SE-04** | **Role ranked by evidence** — the leadership-event ↔ declared-title join, with *why this one* and *why not that one* | After SE-03 |
| **SE-05** | **What to ask** — derived from validation's unproven assertions | After SE-03 |
| **SE-06** | **What not to say** — the same source, as a caution | With SE-05 |
| **SE-07** | **Disagree with a recommendation**, with a reason | After SE-04 |
| **SE-08+** | **Everything person-shaped** | ⛔ **D-1** |

**Browser journeys** (with Lane B, specified not written): open a strong account → know which role to approach and why → open the evidence → disagree with it → find what to ask → find what not to claim.

---

## 13 · The honest summary

**The assignment as written cannot be delivered**, because its central noun — a person — does not exist in this platform and cannot be created without a decision that is not an engineering one.

**Most of its value can be delivered anyway**, because the platform already knows *why this account*, *why now*, *what changed*, *what is unproven*, and — declared by the customer and read by nobody — ***which role has to agree***.

> **The last mile is the name. Everything before it is composition, and it is not built.**

---

# Part II · The design, after the product owner's refinement, 2026-08-03

> **The direction changed on three points, and each made the feature stronger.** The absence of people is an **implementation boundary, not a stopping point** · the module owns **commercial synthesis**, which is why it deserves a bounded context · and **AI belongs in the design after all** — not in the reasoning, in the explanation.

## 14 · The reasoning graph

**Deterministic, end to end. No model is called anywhere in this section.**

```
  ICP ─────────┐
  Portfolio ───┤
  Committee ───┤
               ├──▶  which product, which roles have to agree
  Signals ─────┤
  Events ──────┤──▶  which roles the evidence names, and how strongly
  Intent ──────┤
  Research ────┤
  Validation ──┤──▶  what is asserted and unproven      → questions
  Corroboration┤──▶  what one provider says alone       → risks
  Timeline ────┤──▶  what changed, and when             → why now
  Score ───────┘──▶  how much, and what moved it
                     │
                     ▼
            a closed, cited evidence set
```

**Every edge already exists as a published contract.** Nothing here is a new pipeline stage; it is the first module permitted to read across them.

### Role ranking — the join nothing performs today

| Step | Deterministic rule |
|---|---|
| **1** | Take the committee declared for the likely product |
| **2** | For each role, find business events whose `title` names it — `LEADERSHIP_APPOINTED` carries `title` and `seniority` today |
| **3** | Add signals whose posture bears on that role's part — an expansion hypothesis bears on a champion; a contraction one on a gatekeeper |
| **4** | Rank by **how directly the evidence names the role**, never by the declaration's order |
| **5** | State **why not** for every role that did not rank — *"no evidence names your CFO"* is more useful than silence |

**Step 4 is the whole discipline.** The customer's order is a preference; the evidence is a fact, and **a declaration must never become a ranking input** — Commercial Profile refuses to hold one and a structural test enforces it.

### Unknowns — absences, computed

**The section the product owner called magical, and it is the cheapest one to build**, because an absence is a set difference:

| Unknown | Computed as |
|---|---|
| *Budget owner not identified* | A committee part with **no supporting evidence** |
| *Which product line owns this* | Two products' ICPs match **equally well** |
| *Existing cloud partner* | An attribute **no provider reported** |
| *Security review timeline* | A `GATEKEEPER` declared and **never named by any event** |

> **Signora already knows what it does not know.** It has a closed evidence set, a declared committee and a canonical attribute vocabulary — **the gaps are computable, and nothing has ever computed them.**

### Risks — contradiction, thinness, inference

| Risk | Computed from |
|---|---|
| **Contradiction** | Two providers, one attribute, different values. **`IdentityState.AMBIGUOUS` and the corroboration count already record this** |
| **Thin** | One provider, no corroboration |
| **Stale** | The evidence behind the score has expired — `evidence_state` says so today |
| **Inferred** | The link between evidence and role is indirect. **Stated as an assumption, not hidden** |

**None is a confidence figure in different clothes.** A risk names *what could be wrong and why*; confidence bands *how much to lean on it*. **Two questions, two answers.**

## 15 · Where AI belongs, and the fence around it

**The product owner's distinction, adopted exactly: the reasoning graph is deterministic; the explanation layer is AI.**

| | Layer 1 — reasoning | Layer 2 — synthesis |
|---|---|---|
| **Produces** | Ranked roles · unknowns · risks · questions · citations | The paragraphs a seller reads in seconds |
| **Verified against** | Fakes and fixtures. **Never calls a model** | A real model, prompt-evaluated, `REFUSED` a legitimate outcome |
| **May invent** | Nothing | **Nothing.** Its input is a closed set |
| **If it fails** | The brief cannot be shown | **The brief is shown without prose.** Degrades to the facts |

**The enforcement is the closed evidence set, not a review.** A synthesis naming a role the graph did not rank, or a risk it did not find, **fails validation and is refused** — the same mechanism that already refuses a citation to evidence outside the set.

> **Delete the synthesis and a seller still gets ranked roles with their evidence. Delete the graph and there is nothing to synthesise.** That asymmetry is the fence.

## 16 · Which product — likely, never certain

**The product owner's correction to C-212, and it is better than asking.**

```
  Portfolio ──▶ products A · B · C
  ICP that matched this company ──▶ B
  Signals mostly map to ─────────▶ B
  Intent aligns with ────────────▶ B
  Research aligns with ──────────▶ B
                                   │
                            Likely product B
                            Seller may override
```

**Four weak agreements make one strong inference**, which is the same shape as corroboration across providers — a mechanism this platform already has, applied to a new question.

**Ties are not resolved.** Two products matching equally well is an **unknown**, surfaced as one, and the seller answers it. **Guessing between them would be the platform inventing a commercial decision.**

## 17 · Tracking is an explicit commercial decision

**Recorded because it changes assumptions elsewhere.**

```
  ICP ──▶ discovery proposes ──▶ customer decides: Track · Ignore · Dismiss · Watch later
                                          │
                                    tracking begins, permanently
```

| Consequence | Why it matters here |
|---|---|
| **Signora never crawls the world** | Every tracked company was chosen. **Evidence density is high by construction**, which is what makes role ranking viable at all |
| **Intelligence accumulates forever** | An approach brief is **better at six months than on day one**, and that improvement is free — it is the same graph over a longer evidence set |
| **Historical reasoning becomes possible** | *"This company looked like this before it bought"* needs history the platform will have and does not yet |
| **`Ignore` and `Watch later` are new states** | ⚠️ **Neither exists.** Not this module's, and **not a stage on an opportunity** — a company that was never tracked has no opportunity to put a stage on |

## 18 · Ten hard questions, answered before any code

| | Answer |
|---|---|
| **Five providers disagree** | **A risk, surfaced, never resolved.** Corroboration counts and `IdentityState.AMBIGUOUS` already record it; the reasoning refuses to pick a winner |
| **The declared champion contradicts observed leadership** | **Both are shown, and the contradiction is the finding.** *"You declared the CFO; the evidence names the VP Engineering"* is the most useful sentence the module can produce |
| **Two products match equally well** | An **unknown**, and the seller decides (§16) |
| **No committee exists** | The brief says so and offers the declaration screen. **It ranks nothing** — a recommendation with no declared committee would be Signora inventing the customer's sales process |
| **No strong signals** | **Silence, with a reason.** *"Nothing has happened here that names a role"* — the rule the attention list and the decided section already follow |
| **Only weak evidence** | Shown, banded `thin`, with the risk named. **Never suppressed** — a seller deciding on thin evidence should know it is thin, not be left with nothing |
| **Signals are six months old** | `evidence_state` reads `stale` today. **The brief leads with the staleness**, because a six-month-old reason to call is a reason not to |
| **A provider disappears** | Corroboration drops, risks rise, ranking changes. **Nothing breaks**, because nothing was stored |
| **AI suggests something unsupported** | **Refused by validation before a customer sees it**, and the brief degrades to its facts (§15) |
| **Fifty companies become urgent on one day** | The attention ranking already orders them. **This module adds no urgency of its own** — and *"everything is urgent"* is a signal-profile problem, not a synthesis one |

## 19 · Where the market stops, and where Signora goes further

**Studied for where sellers still have to think, not for features.**

| | What they expose | Where they stop |
|---|---|---|
| **ZoomInfo · Apollo · LinkedIn Sales Navigator** | Contacts, titles, filters | **Data, not reasoning.** The seller decides what any of it means |
| **Clay** | Composable enrichment | **A workbench.** Powerful, and it presumes the seller already knows the question |
| **6sense · Demandbase** | Account intent scores, buying stage | **A score with a black box behind it.** *Why* is a vendor model, not evidence a customer can open |
| **Common Room · UserGems · Warmly** | Signals from communities and job changes | **Alerts.** *A person moved* is delivered; *what it means for your committee* is not |
| **Gong · People.ai** | What happened **in** conversations | **After first contact.** They are strongest exactly where this capability ends |
| **Salesforce · HubSpot** | Records, stages, fields | **The seller supplies all reasoning.** The CRM stores it |

> **Every one of them either hands the seller data or hands them a number. None hands them a defensible argument.**
>
> **Signora's difference, stated as the acceptance test:** every sentence in the brief opens the observation, the provider and the date behind it — and the product says **what it does not know** as clearly as what it does. *"This product understands my account better than my CRM"* is not a claim about volume of data; it is what a reader concludes when nothing on the screen is unexplained.

## 20 · The Approach Brief — the experience

**On the account brief a seller already opens. Zero navigation.**

```
  Why this account matters today
     hiring up 47% in 60 days · engineering leadership changed · intent
     around cloud modernisation rose        ← every line opens its evidence

  What changed, and why the score moved
     Medium → High because: hiring acceleration · new leadership · research
                                            ← already computed, never shown together

  Who has to agree                          ← the customer's declaration, first consumer
     Champion       VP Engineering    strong    recently appointed · org growing
     Economic buyer CFO               —         no evidence names this role
     Gatekeeper     Security          thin      one provider

  What Signora does not know                ← absences, computed
     Budget owner · which product line owns modernisation · existing cloud partner

  What could be wrong                       ← contradictions and thin links
     Provider A says Azure, provider B says AWS
     Champion inferred from an appointment, not from a stated reporting line

  What to ask                               ← from validation's unproven assertions
     Has the new VP set a platform budget? · Who signs off on security?

  ── and the seller can disagree, with a reason ──
```

**Refusals that keep it premium:** no message · no send · no cadence · no contact table · **no percentage anywhere** · nothing shown that cannot be opened · **silence when there is nothing to say.**

## 21 · Implementation roadmap

| | Slice | Depends on |
|---|---|---|
| **SE-01** | **ADR-0200 ratified** | Product owner |
| **SE-02** | The module skeleton, its public contract and the reasoning graph's **deterministic core**, against fakes | SE-01 |
| **SE-03** | **The committee reaches a screen** — read-only, per product, its first consumer ever | SE-02 |
| **SE-04** | **Likely product**, inferred and overridable (§16) | SE-03 |
| **SE-05** | **Roles ranked by evidence**, with *why* and *why not* | SE-04 |
| **SE-06** | **Unknowns** — computed absences | SE-05 |
| **SE-07** | **Risks** — contradiction, thinness, inference | SE-05 |
| **SE-08** | **Questions** — from validation | SE-05 |
| **SE-09** | **AI synthesis**, refused when unsupported | SE-06…08 |
| **SE-10** | **Disagree with a recommendation** | SE-05 |
| **SE-11+** | Person Intelligence | ⛔ [C-210](../LANE_COORDINATION.md) |

**Browser journeys** (specified, with Lane B): open a strong account → know which role to approach and why → open the evidence behind it → read what Signora does not know → disagree, with a reason → find what to ask.

---

## 22 · SE-02b — the recommendation, and the value of saying *wait*

**The framing moved up a level on the product owner's direction**: the Signora Customer is not paying for role ranking, they are paying for an answer to *"if I spend the next fifteen minutes on this Target Account, what should I do?"*

### Why *wait* is the value, not the fallback

**A module that can only say *approach* has a recommendation carrying no information.** Restraint is what makes the positive case believable — a seller told to wait once, correctly, believes the next approach; a seller told to approach everything learns to ignore all of it.

**And the type enforces the honest form:** a recommendation to wait **names nobody**. Naming somebody while advising against contact is an invitation dressed as caution, and a reader takes the name and ignores the advice.

### The most valuable rule is the one that prevents an embarrassment

> **The same evidence that would rank a role highest is the evidence that means nobody is there.**

`LEADERSHIP_DEPARTED` naming your declared champion is *stronger* evidence than an appointment — and it inverts the conclusion completely. **Approaching a departed executive is the single most embarrassing thing this module could cause a seller to do**, and reasoning that read only `leadership_*` would have caused it.

**The sequence decides, not the set**, and both directions are pinned by tests: joined-then-left is a vacancy, left-then-replaced is not.

### A kind that nothing could produce

`RiskKind.CONTRADICTION` was in the first draft and **no code path emitted it** — protection in appearance, nothing in fact. It is now produced by an appointment and a departure for the same title, and **a test asserts every `RiskKind` is reachable**, so the next one added cannot arrive decorative.

### Title canonicalization — recorded, not built

Token comparison handles *VP Engineering* ↔ *VP of Engineering* and will **not** handle *CTO* ↔ *Chief Technology Officer*, which share no token.

**Three independent consumers justify extracting shared infrastructure; there is one.** The trigger is stated in [ADR-0200](adr/0200-sales-engagement.md): a second module needing to match a job title, or a customer reporting a missed match.

### What this deliberately did not become

| | |
|---|---|
| **A score for the recommendation** | ⛔ Three values a seller can act on beat a number they would have to interpret |
| **A model choosing the action** | ⛔ Every rule is a comparison over recorded facts |
| **A stored recommendation** | ⛔ Derived at read time. Its inputs move daily and a stored copy would disagree within a week |
| **An urgency of its own** | ⛔ The attention list already orders accounts. *"Everything is urgent"* is a signal-profile problem, not a synthesis one |

---

## 23 · SE-04 — Commercial Fit Reasoning, and the honest dimension count

**Which of the Signora Customer's products is this Target Account about?** A Buying Committee is declared *per product*; an Opportunity has no product; so nothing could answer it and role ranking could not start.

### One dimension today, and saying so is the discipline

The product owner's list of fit dimensions is long and right: ICP match, portfolio fit, technology overlap, intent topics, hiring trends, business events, strategic initiatives, competitor technologies, existing-customer patterns, historical conversions, declared priorities, product capabilities.

**Every one of them needs a declaration or a record the repository does not hold.** A `Product` is an id, a name and a description. Nothing links a product to a technology, and nothing records which ICP discovered a Target Account.

> **So one dimension is implemented — committee overlap — and the enum has one value.** A `FitDimension` nothing could emit would be exactly the Decorative Logic found and fixed in `reasoning.py` an hour earlier, and adding five hopeful values would be that defect five times over.

**And it reuses the SE-02 join rather than repeating it.** A product fits to the degree its declared committee is named by what happened at the Target Account — the same question, asked per product. Two implementations of one join disagree the first time either changes.

### The dimensions that are not built, with their triggers

| Dimension | What it needs first | Trigger category |
|---|---|---|
| **ICP match** | A record of *which ICP discovered this Target Account*. Discovery is not built | **Repository** |
| **Technology overlap** | A product declaring the technologies it relates to. **A new Commercial Profile declaration**, and that module's decision | **Repository** |
| **Intent topics** | `INTENT_TOPIC_SURGE` exists as a claim; **mapping a topic to a product is a declaration nobody has made** | **Repository** |
| **Historical conversions** | Closed-won volume this platform does not have yet | **Operational** |
| **Strategic initiatives · competitor technology** | Neither is modelled anywhere | **Repository** |
| **Existing-customer patterns** | Requires customers, plural, and their outcomes | **Operational** |

**Three trigger categories, distinguished on the product owner's direction**, because they are different kinds of pressure and arrive from different places:

| | |
|---|---|
| **Repository trigger** | A declaration or record must exist first. *Somebody must build it* |
| **Customer trigger** | A Signora Customer reports a wrong or missed inference. *Somebody must feel it* |
| **Operational trigger** | Enough history has accumulated. *Time must pass* |

**Title canonicalization now carries all three**: a repository trigger (**a third deterministic module needing title normalization** — Person Intelligence would be the second), a customer trigger (a missed match caused by abbreviation), and no operational one.

### A tie is a question, and the seller still gets a screen

`likely` returns `None` when two products fit equally — **guessing would be the platform inventing a commercial decision it has no evidence for**, the same refusal that stops it resolving a provider disagreement.

**But the reasoning still runs**, against the best-fitting committee, and the tie is added as an unknown: *"Is this Revenue Cloud or Secure Edge? The evidence fits both equally."* **The open question is *which product*, not *whether anything is happening***, and a seller staring at an empty screen while they decide would be the product punishing them for its own uncertainty.

### An override is an answer, not a hint

When the seller has said which product, **the portfolio is not read at all** and no fit ranking is returned. Re-checking a person's decision against a guess is how a product starts arguing with its own customer — and showing a ranking beside their answer invites them to re-litigate a decision they already made.

## 24 · What today's model does not prevent

**Recorded on the product owner's direction: today's shapes must not foreclose tomorrow's.**

| Tomorrow | Does today's model allow it? |
|---|---|
| **A richer recommendation taxonomy** — *watch · escalate · re-evaluate after next signal · engage partner · expand the committee · pause pursuit* | ✅ `NextAction` is an enum on a `Recommendation` that carries a reason and an optional role. **A new value is a new rule and a new sentence**, not a new shape |
| **Richer contradictions** — intent says expanding, news says layoffs; hiring says growth, financials say decline | ✅ `Risk` is a kind plus a detail, and `contradictions()` is a function over the evidence set. **A cross-domain contradiction is another function**, not another model |
| **Cumulative reasoning** — the same Target Account reads better at six months | ✅ **Already true, and free.** Nothing is stored, so every conclusion is the same graph over whatever evidence exists *now*. Density grows; the reasoning improves without retraining or tuning |
| **Commercial memory** — *six months ago we thought Product A; today Product B; here is what changed* | ⚠️ **Not prevented, and not free.** It needs materialized reasoning with a supersession chain — the shape `ai_inference` and the prompt registry already use. **The `Approach` value is a complete snapshot**, which is exactly what such a record would hold |
| **Person Intelligence** | ✅ A ranked role is a **slot**. Nothing derived changes shape when a name arrives |
| **AI synthesis** | ✅ `Approach` is the closed set. **Layer 2 reads it and adds nothing** |

> **The one thing that would foreclose all of it is storing a conclusion.** Today the module stores nothing, and every future capability above is a function over the same facts.
