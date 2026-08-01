# 39 — Product Review Findings

> **A standing register, not a redesign.** Every user-visible feature gets reviewed here after it ships and before the next one starts, as the five people who would use it and as the designers whose products set the bar. Findings are **recorded and scheduled**, not acted on immediately — the goal is to evolve Signora deliberately rather than continuously redesigning it.
>
> Immediate implementation is permitted only when a finding **fixes a correctness bug**, **materially reduces cognitive load**, or **is essential to the current milestone**. Everything else carries a milestone and waits.
>
> Design *decisions* — the reasoning behind what was built — live in [38-product-design-principles.md](38-product-design-principles.md). This file is the **critique**.

---

## How this review was conducted, and its one honest limitation

Reviewed against the twelve-account Playground running the real pipeline: real scores, real ledgers, real identities, real model-authored narration.

**I could not open the browser UI.** Sign-in is OAuth-only by ratified decision ([ADR-0010](adr/0010-identity-and-access.md)) and no Google or Microsoft credentials are configured here, so `/opportunities` is unreachable without them. Instead every component was **rendered against the real API responses** and its output read in page order — which gives the true information architecture, wording, ordering and conditional behaviour, and gives **nothing about pixels**: spacing, contrast, weight, rhythm and how the page feels at a glance are unreviewed.

**Findings below marked 👁 are therefore provisional** and need a human with a browser. The standing rule the product owner set — *no frontend screen is complete until a human has reviewed it in the demo environment* — is not satisfied by this document.

*(Fixing that requires OAuth credentials in `frontend/.env.local`; `docs/RUNNING.md` now says so, having previously said the opposite.)*

---

# Review 1 — the attention list and the account brief *(2026-08-01, M12.2)*

Twelve accounts, real pipeline output. What the list actually said, top to bottom:

```
 50  Databricks, Inc.            current    why: New evidence arrived
 50  NVIDIA Corporation          current    why: New evidence arrived
 43  Snowflake Inc.              current    why: New evidence arrived
 39  Stripe, Inc.                current    CONTESTED
 33  7c33ed38 (unnamed)          current    why: New evidence arrived
 33  Atlassian Corporation       current    why: New evidence arrived
 20  HubSpot, Inc.               cooling    why: Evidence aged out
 10  MongoDB, Inc.               stale      why: Evidence aged out
 10  Salesforce, Inc.            current    why: New evidence arrived
 10  Adobe Systems Incorporated  cooling    DISPUTED-NAME
  5  Datadog, Inc.               stale      why: New evidence arrived
  1  Twilio Inc.                 current    why: Evidence aged out
```

---

## R1-01 · The *"why now"* line says the same thing eleven times 🔴

**Observation.** Across twelve rows there are **two distinct reasons**: *"New evidence arrived"* (7×) and *"Evidence aged out"* (5×). The line I described in code as *"the single most important line on the row"* is very nearly a constant.

**Why it matters.** `ScoreTrigger` records **why the score was last recomputed** — a pipeline event. A seller reads that line asking **why this company matters today** — a commercial question. The two are not the same question, and the enum can only answer the first. The list currently spends its most valuable horizontal space on a field that does not discriminate between any two rows.

**User impact.** *(AE)* "Every row says the same thing, so I stopped reading that column by the fourth row." Once a column is ignored it is worse than absent — it costs width and attention and returns nothing.

**Suggested future improvement.** The commercially meaningful *why* already exists one layer down: the **highest-contributing signal's title** — *"Active evaluation"*, *"Displacement opportunity"*, *"Contraction risk"* — which differs across nine of these twelve rows. Show that; keep the trigger for the brief, where *"why did this number move"* is a question somebody is actually asking. **Do not invent new wording** — the Signal Catalog owns those titles.

**Priority:** High. **Milestone:** M12.3, with the list's other hierarchy work (D20).

---

## R1-02 · Trigger and evidence state contradict each other on the same row 🔴

**Observation.** Datadog: `stale` · *"New evidence arrived"*. Twilio: `current` · *"Evidence aged out"*. Both are literally correct and both read as errors.

**Why it matters.** The trigger describes the **last recomputation**; the evidence state describes **now**. Side by side with no visual separation, a reader assumes they describe one moment and concludes the product is confused.

**User impact.** *(RevOps)* "One of these two fields is wrong and I don't know which, so I don't trust either." This is the most direct trust cost on the screen — worse than a missing feature, because it looks like a defect in the intelligence rather than a gap in it.

**Suggested future improvement.** Resolved for free by R1-01: a signal title and an evidence state do not appear to contradict. If the trigger stays, it needs to be visibly about the past — *"last moved when evidence aged out"*.

**Priority:** High. **Milestone:** M12.3, same change as R1-01.

---

## R1-03 · A screen reader could announce a score the screen never showed 🔴 **FIXED**

**Observation.** `ScoreArithmetic` rendered `<sr-only>Attention score </sr-only>{score}` in one element and `{points} of {ceiling} points` in the next. For Twilio — score 1, points 2 — the accessible text was `Attention score 12 of 120 points`.

**Why it matters.** Not a formatting nitpick: **assistive technology reported a different number, confidently.** The one thing this product cannot do is state a figure it did not compute.

**User impact.** A screen-reader user triaging by score works from wrong values, with nothing to indicate it.

**Implemented immediately** — a correctness bug. The number and the arithmetic are `aria-hidden` and replaced by one sentence: *"Attention score 1 out of 100, from 2 of 120 points."* Regression test asserts no `score 12` string can be announced.

**Priority:** — **Milestone:** done, M12.2.

---

## R1-04 · The brief never mentions that an account is cooling 🟠

**Observation.** Adobe and HubSpot show a **cooling** badge on the list. Open either brief and the word never appears — the brief renders `is_current`, which is `true`, so it says *"Exactly correct until Sep 20, 2026."*

**Why it matters.** **Two screens disagree about the same account.** The list says *"this is going off the boil"*; the brief says *"this reading is fine"*. Both are true of different facts — `evidence_state` is opportunity-derived, `is_current` is score-derived — and no reader will ever reconstruct that.

**User impact.** *(Sales Manager)* "The list flagged it, the detail page didn't, so I assumed the list was noisy." The brief is where a seller goes to confirm what the list told them; a brief that silently drops the flag teaches them the list is unreliable.

**Suggested future improvement.** The brief already receives `evidence` on the opportunity response and ignores it. Surface it beside the momentum line, where *"opened at 35, −15 since"* and *"cooling"* are the same story told twice — which is the point.

**Priority:** High. **Milestone:** M12.3 — smallest of the three high findings and the most obviously wrong.

---

## R1-05 · Six of twelve accounts tie, and nothing breaks the tie visibly 🟠

**Observation.** 50/50, 33/33, 10/10/10. Half the list shares a score with another row, and their relative order is decided by a rule the screen never shows (contested first, then keyset order).

**Why it matters.** A ranked list whose ranking is invisible at the top half looks arbitrary exactly where attention is highest.

**User impact.** *(SDR)* "Why is Databricks above NVIDIA? They're both 50." No answer on screen.

**Suggested future improvement.** Once R1-01 lands, the signal title differentiates them. Failing that, the tiebreak should be *stated* rather than merely applied.

**Priority:** Medium. **Milestone:** M12.3.

---

## R1-06 · The workflow line is identical on all twelve briefs 🟡

**Observation.** *"Signora is tracking this · nobody has taken it yet"*, twelve times.

**Why it matters.** It is true, it is the principle made visible, and after the first account it is furniture. A line that is constant across every instance carries no information at that instance.

**User impact.** Low — mild noise under the account name, in the position of highest attention on the page.

**Suggested future improvement.** It becomes informative the moment assignment exists, because it will then differ. **Leave it.** This is a finding about the demo's uniformity more than about the design, and it resolves itself in M12.3.

**Priority:** Low. **Milestone:** M12.3, no action needed.

---

## R1-07 · An account worth 1 point gets the same page as one worth 50 🟠

**Observation.** Twilio: score 1, one contextual signal at 60% weight, a full brief with score card, momentum, validity, posture split and ledger.

**Why it matters.** Restates D20 from the brief's side. The product has an opinion about the difference between these accounts and declines to express it anywhere.

**User impact.** *(CRO)* "If everything gets the same treatment, the ranking isn't a judgement — it's a sort." That is the difference between a product with a point of view and a spreadsheet with a header.

**Suggested future improvement.** Needs a seller, not a designer — see D20. Candidates: a threshold below which the list collapses, a visual break between *worth your morning* and *worth knowing*, or grouping by reason.

**Priority:** Medium. **Milestone:** M12.3.

---

## The five roles, in their own words

**SDR.** *First look:* the top three names. *Confusing:* every row saying "New evidence arrived". *Delight:* the account nobody has named still appears, with its real identifier rather than a blank — "it didn't hide the one it knows least about". *Ignored:* the evidence badges. *Trust:* the score is a division I can check. *Doubt:* nothing tells me what to **do**, so I still open the CRM to decide.

**Account Executive.** *First look:* the brief for the account I already had a meeting about. *Confusing:* "Opened at 35, 5 weeks ago · −15 since" — good, but where did the 15 go? The ledger shows the current lines and never the ones that expired. *Delight:* the zero-point line with its reason. "It told me why something I could see didn't count." *Doubt:* NVIDIA claiming two identical expansion lines at 30 points each (**F-10**).

**Sales Manager.** *First look:* how many accounts are stale. *Confusing:* a stale account can outrank a current one — MongoDB at 10 `stale` sits above Salesforce at 10 `current`. *Trust:* the contested account shows both sides and marks the minority. *Doubt:* eight of twelve say "unchanged since", which reads as a system that has not run recently rather than a book that has not moved (**D22**).

**RevOps.** *First look:* whether the numbers reconcile. They do: points ÷ ceiling reproduces every score. *Delight:* provenance on the narration — model, prompt version, date, on the page. *Doubt:* R1-02, and no page states when it was loaded.

**CRO.** *First look:* the top of the list, for thirty seconds. *Confusing:* nothing. *Ignored:* everything below the third row. *Trust:* "the model chose the words, not the facts." *Doubt:* "It tells me what is true. It does not tell me what we are doing about it, and that is the meeting I actually run."

**The common thread across all five:** every role reached *"and then what?"* within a minute, and the product has no answer. That is D3 and D15, now confirmed by five independent readings rather than one.

---

## The staff-designer pass

**Apple — does every element earn its place?** Five cards on the brief, all the same border, padding and weight. **A page where everything is a panel has said nothing about what matters.** The score card should be the subject; the rest should recede. *(👁 provisional — this is a visual judgement made from structure, not from pixels.)* **Priority:** Medium · **M12.3.**

**Stripe — would a developer trust this?** They already would; the arithmetic is the best thing here. But it is set at `text-sm` muted beside a `text-4xl` number — **the check is whispered and the claim is shouted, which is backwards for a product whose differentiator is that the claim can be checked.** Also: no page states when it was loaded, and a stale browser tab is indistinguishable from stale data. **Priority:** Medium · **M12.3.** 👁

**Linear — is it fast, and does it work without a mouse?** Three sequential requests and no prefetch on row hover. No `j`/`k` through the list, no `Esc` back, no "4 of 12", no next/previous. **A product for people who live in it all day should not require the mouse**, and today it does. **Priority:** Medium · **M12.4 or a dedicated interaction slice.**

**Notion — does it read as a document?** Since narration landed, **yes** — this is the finding that changed. The remaining flaw is structural: *"What contributed"* is the only heading on the page. The score card and momentum have none. **Either everything is titled or nothing is.** **Priority:** Low · **M12.3.**

**OpenAI — is the AI honest about itself?** Yes, and this is the strongest part of the screen. Provenance in words on the page; a fact count on every sentence; one line stating exactly what the model did and did not choose. **The bar to hold, not raise.** What is missing: nothing says the narration can be *absent*, so a seller comparing two accounts cannot tell "not yet narrated" from "nothing to say".

**Perplexity — can every claim be followed?** **No, and this is the largest remaining gap.** Each ledger line carries `signal_id` and `business_event_id`; each narration sentence shows "3 facts". Neither can be opened. **The page's whole argument is *you can check this*, and the check stops one level short.** **Priority:** High · **M12.3**, and it should be the first thing built there.

**Cursor — what would make this feel alive?** Nothing on either screen changes, updates, or responds. Scores move on a schedule and the UI has no way to say so. Not a defect at this stage; recorded so it is a decision later rather than an omission. **Priority:** Low · **unassigned.**

---

## What this review changed today

**One thing: R1-03**, a correctness bug where assistive technology could announce a score the screen never showed. Fixed, with a regression test.

**Everything else is recorded and scheduled.** Three high findings (R1-01, R1-02, R1-04) plus Perplexity's citation gap all land in **M12.3**, and they are closely related: the list needs a *why* that discriminates, the brief needs to agree with the list, and both need a citation that opens. That is one coherent slice, not four.

**The most valuable thing the review produced is not a finding.** It is that all five roles reached *"and then what?"* within a minute. Signora currently answers *which accounts* and *why* extremely well, and **does not yet participate in the decision that follows** — which is what M12.3 owns and what makes it the right next milestone.

---

# Review 2 — "Before you act" *(2026-08-01, M12.3)*

The first surface in Signora that is about **what a seller should do** rather than what is true. Reviewed against the twelve-account Playground; same limitation as Review 1 — **the browser UI could not be opened** (OAuth-only sign-in, no credentials configured), so components were rendered against real API responses. Findings resting on visual judgement are marked 👁.

What the real data produced:

```
NVIDIA (75)      Expansion opportunity [primary]
                   — Check which functions the recent hiring is in…
                   — Ask on a first call which division the investment sits in…
                   (3 limitations)

Stripe (39)      Active evaluation [primary]
                   — Confirm which function the research came from…
                   — Look for a public RFP or tender, which is a decision rather than an interest.
                 Contraction risk [contextual]
                   — Check whether the decline is company-wide or confined to one division.
                   — Look for a divestiture announcement that would explain the figures…

11 of 12 accounts have something live to validate.
```

---

## R2-01 · Two accounts get identical guidance, and that is correct but reads as a bug 🟠

**Observation.** NVIDIA and Databricks both score 75, both hold `expansion_opportunity`, and both show **word-for-word the same two checks**.

**Why it matters.** The guidance is a property of the *hypothesis type* — that is the design, and it is what keeps this from being a recommendation. But a seller reading two accounts in a row sees the same paragraph twice and concludes the product is generic.

**User impact.** *(AE)* "It gave me the same advice for two different companies, so I assumed it wasn't really looking at either."

**Suggested future improvement.** The check is generic; **the evidence it points at is not.** *"Check which functions the recent hiring is in"* could name the hiring the pipeline actually observed — *"NVIDIA added 5,000 people and 500 open roles in 38 days; which functions?"*. That is composition of two things already stored, not new inference. It becomes possible the moment citation resolution lands, because the business event is then reachable from the check.

**Priority:** Medium. **Milestone:** M12.3, immediately after citation resolution — it is the same join.

---

## R2-02 · "What it cannot tell you" is the strongest thing on the page and the least visible 🟠 👁

**Observation.** The limitations are behind a disclosure, closed by default, at `text-xs`.

**Why it matters.** I collapsed them deliberately — twelve caveats across four hypotheses reads as a product that does not believe itself. **That reasoning still holds and it may have gone one step too far.** No competitor tells a seller what their signal *cannot* prove. It is the most differentiating sentence on the screen and it is the smallest text on it, behind a click.

**User impact.** *(Sales Manager)* "This is the bit I'd want my reps to read, and it's the bit they'll never open."

**Suggested future improvement.** Show **one** limitation inline — the first, which the catalog already orders — and keep the rest behind the disclosure. One caveat is calibration; twelve is hedging.

**Priority:** Medium. **Milestone:** M12.3, cheap and self-contained.

---

## R2-03 · An account with nothing live says nothing at all 🟡

**Observation.** One of twelve renders no "Before you act" section, because the block returns `null` on an empty list.

**Why it matters.** Consistent with how narration is handled, and here it may be wrong. *"Nothing is currently held about this account"* is **actionable information** on a page whose subject is an open opportunity — it means the commitment is running on evidence that has expired.

**User impact.** *(RevOps)* "The section just isn't there, so I can't tell if there's nothing to check or if the feature didn't load."

**Suggested future improvement.** For an account whose evidence is `stale`, say so here rather than saying nothing. Overlaps R1-04.

**Priority:** Low. **Milestone:** M12.3, with R1-04.

---

## The five roles

**SDR.** *Delight:* "It told me what to ask on the call. Nothing else has ever done that." *Doubt:* the same two lines on two accounts (R2-01).

**AE.** *First look:* straight to "Before you act", past the score. **That is the finding** — given something actionable, the arithmetic became reference material rather than the destination. *Confusing:* nothing. *Ignored:* the posture split.

**Sales Manager.** *Trust:* "It says what it can't prove. I'd put that in onboarding." *Doubt:* R2-02 — the best part is hidden.

**RevOps.** *Delight:* no model involved, so nothing to govern, evaluate or budget. *Doubt:* R2-03.

**CRO.** *First look:* Stripe, because "contested" plus a risk hypothesis is the only account that looks like a decision. *Trust:* "It gave me the counter-argument without me asking." *Doubt:* "Still nothing I can *do* in the product — I can read what to check and then I leave."

**The common thread has moved.** In Review 1 every role reached *"and then what?"* within a minute. Now four of five reach *"and I still can't do it here"* — which is a different and much better complaint. The product now says what to do; it cannot yet record that you did it. **That is exactly what the rest of M12.3 owns.**

---

## The staff-designer pass

**Apple.** The brief now has six sections and still no hierarchy between them — five cards of equal weight plus a heading. **This finding was Medium in Review 1 and is now the largest visual problem on the page**, because there is more to order. 👁 **Medium · M12.3.**

**Stripe.** The guidance carries no provenance. The narration says which model and prompt wrote it; this says nothing about where it came from — and it came from a *versioned, reviewed artifact*, which is a stronger claim than the AI's. **One line — "from your signal catalog, v1" — would make it checkable.** **Medium · M12.3.**

**Linear.** Every hypothesis is a disclosure the mouse must find. No way to expand all, no keyboard path between them. **Low · interaction slice.**

**Notion.** *"Before you act"* is the best heading on the page — a verb, addressed to the reader. **The others are nouns.** *"What contributed"* should probably be *"Why this score"*. **Low · M12.3.**

**Cursor.** Nothing here changes when the account changes, and the checks are the one thing a user might want to keep state on — *I already asked that*. **Recorded, not built:** it needs per-user storage, which is a real schema decision. **Low · unassigned.**

**Perplexity.** **Unchanged and now sharper.** The checks point at evidence — *"the recent hiring"* — that is one click away in the ledger and cannot be reached. **High · M12.3, next.**

**OpenAI.** *"No model produced any of this"* is true and unstated. The narration announces its provenance; this is more trustworthy and announces nothing. Same as Stripe's point, from the opposite direction. **Medium · M12.3.**

---

## Rejected ideas

**Bolting the guidance onto the score response.** One fewer request, and it merges *how the number was computed* with *what to do about it* — two questions asked at different moments. Rejected. *May return* if the account page's measured latency justifies aggregation, which is the trigger `37-product-surface.md` already set for revisiting the BFF question.

**Keying the guidance to the score's ledger rather than to live signals.** It would tie the advice to what actually drove the number. Rejected: the Buying Score Engine is downstream of the Signal Engine, and asking it for catalog prose puts the score in the business of explaining hypotheses it only weighs. **A hypothesis worth validating is one that is current, not one that happens to carry points.** *Unlikely to return* — the boundary argument does not weaken.

**Checkboxes on the checks.** They look exactly like a checklist. Rejected because nothing owns per-user state and **a control that forgets is worse than no control**. *Returns* when M12.3's workflow actions introduce somewhere to store it — Cursor's point above.

**Showing the guidance on the attention list.** Twelve accounts × three limitations is a wall. Rejected; it belongs where somebody has already chosen to concentrate. *Will not return.*

**A confidence figure.** Considered because "how sure are you" is the obvious next question. Rejected: **nothing computes it.** The catalog knows what a hypothesis cannot prove and not how likely this one is, and a number here would be an inference wearing the catalog's clothes. *Returns only with the Recommendation Engine, and as its output rather than as a decoration.*
