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
