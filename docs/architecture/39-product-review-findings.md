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

---

# Review 3 — the citation that opens *(2026-08-01, M12.3)*

**J3, "prove it".** The click that is the whole argument for Signora rather than a summary. Same limitation as Reviews 1 and 2 — the browser UI could not be opened (OAuth-only sign-in, no credentials configured) — so components were rendered against real API responses. Findings resting on visual judgement are marked 👁.

What the real data produced, opening NVIDIA's largest ledger line:

```
Hiring surge — 5,000 people and 500 open roles in 38 days
Reported by coresignal and apollo · 25 Jul

  employee count   29,000 → 34,000        coresignal · 25 Jul
  open roles       400 → 900              apollo · 25 Jul

Across sixteen business events in the Playground, exactly one names two providers.
```

---

## R3-01 · Corroboration is the most valuable thing in the drawer and the rarest 🟠

**Observation.** Fifteen of sixteen events read *"Reported by coresignal"*. One reads *"Reported by coresignal and apollo"*, and it sits on the top-ranked account.

**Why it matters.** The line is doing real work — *"reported by CoreSignal"* and *"reported by CoreSignal and Apollo"* are different claims, and the second is stronger. But a reader who opens four citations and sees one provider each time will stop reading the line, and then miss it on the one that matters.

**User impact.** *(RevOps)* "I'd want to know when two sources agree. I'd also stop looking after the third single-source event."

**Suggested future improvement.** Say something when corroboration is **absent**, not only when it is present — *"only CoreSignal has reported this"* is a fact a reader should have, and it makes the corroborated case legible by contrast. Cheap: the same field, the other branch.

**Priority:** Medium. **Milestone:** M12.4, with the drawer's second pass.

---

## R3-02 · The drawer shows what a provider said and never what Signora did with it 🟡

**Observation.** The readings appear as `29,000 → 34,000`. The ledger line that opened them says *"Expansion opportunity · primary relevance · fresh evidence (100%) — 30 points"*. Nothing connects the two: the drawer never says which rule turned this movement into that conclusion.

**Why it matters.** It is one level short of the full chain. A reader can now check that the *fact* is real; they still cannot check that the *inference* was reasonable.

**User impact.** *(Sales Manager)* "I believe the numbers. I still don't know why 5,000 hires is worth 30 points and not 10."

**Suggested future improvement.** The business event carries its `type_key`, and the Business Event taxonomy carries the rule that detected it. Naming the rule — *"detected by sustained-growth over 38 days"* — closes the last gap. **Not new inference; a lookup in an artifact already loaded.**

**Priority:** Medium. **Milestone:** M12.4.

---

## R3-03 · Nothing on the page said the citation could be opened until it could 🟢 **Deliberate**

**Observation.** The ledger rendered its reasons as flat text through M12.2 and now renders them as buttons. No transitional affordance ever existed.

**Why it matters.** Recorded as a *confirmation*, not a defect. **A control that looks clickable and goes nowhere costs more trust than the missing feature does**, and the test that enforces it (`draws no affordance at all without a handler`) is now permanent. Worth stating in the register because the same pressure will arrive with the Decision Package.

**Priority:** — **Milestone:** none. The bar to hold.

---

## The five roles

**SDR.** *Delight:* "It showed me the actual numbers. I could put that in an email." *Ignored:* the provider names — "I don't know which of those is good."

**AE.** *First look:* straight to the biggest ledger line, then the drawer. *Trust:* "The before-value is what makes it real. A current number alone I'd have to take on faith."

**Sales Manager.** *Doubt:* R3-02 — the fact is checkable and the judgement is not.

**RevOps.** *Delight:* "Two providers named, not 'multiple sources'." *Doubt:* R3-01.

**CRO.** *First look:* did not open a citation at all. **That is the finding, and it is correct** — the drawer exists so the claim *survives* the click, not so every reader makes it.

---

## The staff-designer pass

**Apple.** The drawer is the cleanest surface in the product — one subject, one table, nothing decorative. **The rest of the brief should look more like this.** 👁 **—**

**Stripe.** Values are rendered exactly as received, including `34000` without a thousands separator. **Correct and slightly hostile.** Formatting here would be Signora editing a provider's claim inside the one view that exists to show it unedited — so the answer is probably a monospace column and better alignment rather than a changed number. 👁 **Low · M12.4.**

**Linear.** Escape closes it and focus is trapped, both free from the native `<dialog>`. **No way to move between citations without closing and re-opening.** **Low · interaction slice.**

**Notion.** The title is the event summary and the subtitle names the sources. **Right hierarchy — Signora's sentence on top, the evidence beneath.**

**Perplexity.** **The finding that has been High since Review 1 is closed.** Every ledger citation resolves to a record. *"Narration sentences still show a fact count and cannot be opened"* replaces it. **High · M12.4.**

**OpenAI.** No model touched anything in this drawer and it does not say so. Same gap as R2's, now on the surface where it matters most: **this is the least AI-generated screen in the product and the one a sceptic would most want that stated on.** **Medium · M12.4.**

---

# Review 4 — recording a decision *(2026-08-01, M12.3)*

**J4.** The first write in the product. Reviewed against the twelve-account Playground, with one real decision recorded through the real HTTP path.

What the real data produced:

```
NVIDIA Corporation      Signora is tracking this · nobody has taken it yet
                        [ I'm working this ] [ Lost ] [ Not a real opportunity ]

  → "I'm working this"
    This account will be assigned to you.
    Why are you taking this on? ______________________________
    Recorded against this account permanently, with your name and the date.

  after:
  NVIDIA Corporation    Being worked · you hold this
                        [ Won ] [ Lost ] [ Not a real opportunity ]

    27 Jun  tracking   Signora: Commercial attention reached 75, which your
                       qualification policy (v1) treats as worth tracking.
    01 Aug  engaged    a person: Their VP of Data replied to my note; call
                       booked for Thursday.
```

---

## R4-01 · The moves arrived alphabetically, so "Lost" led and "I'm working this" came last 🔴 **FIXED**

**Observation.** `allowed_next` was sorted by stage *value*, producing `closed_lost, dismissed, engaged` — and the client renders the first as the emphasised action. Every tracked account offered **[Lost] [Not a real opportunity] [I'm working this]**.

**Why it matters.** Not cosmetic. The emphasised control on every account was the one a seller almost never wants, and the milestone's entire purpose — *making the next decision easier* — was inverted by a sort key chosen for determinism alone.

**User impact.** *(SDR)* "The big button was 'Lost'. I assumed the product expected me to give up."

**Implemented immediately** — it defeats the milestone's goal, and the correct order was already in the domain. Sorted by the `Stage` enum's own declaration, which runs `tracking → engaged → won → lost → dismissed`: the order work actually moves in. Still deterministic, and now derived from something meaningful rather than from the alphabet.

**Found by rendering the real screen, not by a test.** Every assertion passed with the wrong order, because the tests asserted *which* moves and never *which first*. One now asserts the order and says why.

**Priority:** — **Milestone:** done, M12.3.

---

## R4-02 · "Lost" is offered on an account nobody ever worked 🟠

**Observation.** From `tracking`, the legal moves are `engaged`, `closed_lost`, `dismissed`. A seller who never engaged can record a loss.

**Why it matters.** The domain is defensible — a deal you knew about, did not chase, and that closed elsewhere *is* a loss. But on screen, beside *"nobody has taken it yet"*, **"Lost" reads as a mistake in the product** rather than as a distinct outcome from "Not a real opportunity".

**User impact.** *(AE)* "What's the difference between Lost and Not a real opportunity if I never touched it?" — which is exactly the distinction the module was built to protect, now unreadable at the point of use.

**Suggested future improvement.** Word it for the state it is offered from: *"Lost without pursuing"* from `tracking`, *"Lost"* from `engaged`. The wording map is already keyed by target stage; keying it by `(from, to)` is the same table with one more dimension. **Do not change the domain** — the stage set is right and this is a labelling problem.

**Priority:** Medium. **Milestone:** M12.4.

---

## R4-03 · A refusal shows the customer an internal identifier 🟡

**Observation.** Recording a decision that changes nothing returns *"opportunity 6d1510af-4468-4ddc-924a-543c66975c28 is already engaged with the same owner."* — and the dialog shows that sentence verbatim, on purpose.

**Why it matters.** Passing the domain's own words through is the right call and it was made without checking what those words contain. **The explanation is excellent; the UUID in front of it is noise the reader cannot use.** Reachable in practice from two open tabs.

**User impact.** *(RevOps)* "It looks like a stack trace leaked into the UI."

**Suggested future improvement.** The domain messages were written for logs and are now customer copy. Either the id moves out of the message (it is already on the row, the log line and the correlation id) or the interface strips it. **The first is better** — a message that needs sanitising before display is a message that will be shown unsanitised somewhere else.

**Priority:** Medium. **Milestone:** M12.4.

---

## R4-04 · A dismissed account is unreachable once you navigate away 🟠

**Observation.** Dismissing an account removes it from the attention list — correctly, because the list is open work. Its brief still exists and still offers reopening, and **there is no path back to it from anywhere in the product.**

**Why it matters.** Being able to undo a dismissal is what makes dismissing safe. Today it is undoable for as long as you stay on the page and permanent the moment you leave.

**User impact.** *(Sales Manager)* "I'd tell my reps not to dismiss anything, which defeats the point of asking them."

**Suggested future improvement.** A filter on the list — *closed and dismissed* — which is list work and belongs with R1-01, R1-05 and D20. **The brief itself is already correct**: it was made to survive closure in this slice precisely because this was foreseeable.

**Priority:** Medium. **Milestone:** the list slice.

---

## R4-05 · Every account offers the same three moves 🟢 **Correct, recorded so it is not "fixed"**

**Observation.** Twelve identical action rows, exactly like R1-06's workflow line.

**Why it matters.** Unlike a *description*, identical **options** carry no penalty: you can do the same things to any tracked account, and a product that varied its verbs by score would be inventing a judgement it never computed. **Recorded so a future reviewer does not read it as R1-06 repeating.**

**Priority:** — **Milestone:** none.

---

## The five roles

**SDR.** *Delight:* "I clicked one button and it was mine." *Doubt:* R4-02.

**AE.** *First look:* the action row, before the score. **Second milestone running where the actionable thing outranks the arithmetic** — the brief is becoming reference material behind a decision, which is the right direction. *Confusing:* nothing.

**Sales Manager.** *Trust:* "Every change names who and why, and I can't edit it. That is a manager's dream and a rep's least favourite feature." *Doubt:* R4-04, strongly.

**RevOps.** *Delight:* "The dismissal reason is a feedback loop into qualification quality. Nothing else we own has one." *Doubt:* R4-03.

**CRO.** *First look:* the history, not the buttons. *Trust:* "Two lines: what the machine suggested, what the human decided. That is the product's argument in four inches." *Doubt:* "Where do I see this across the team?" — **the first request in four reviews that is genuinely a new capability rather than a gap.**

**The common thread has moved again.** Review 1: *"and then what?"* Review 2: *"and I still can't do it here."* Now: **nobody said either.** Four of five asked about *other people's* accounts — a team view, an assignment queue, a manager's roll-up. The single-seller loop is closed.

---

## The staff-designer pass

**Apple.** Three buttons now sit under the account name, in the position of highest attention, and the page still has six sections of equal weight. **The hierarchy finding is now three reviews old and is the largest visual problem in the product.** 👁 **Medium · the brief's visual pass.**

**Stripe.** The reason field says it is permanent *before* it is typed. **The best microcopy in the product.** What is missing: after recording, nothing confirms it beyond the stage line changing.

**Linear.** The dialog traps focus and Escape cancels, both free. **No keyboard path to the actions themselves** — three tabs past a back link. **Low · interaction slice.**

**Notion.** The history reads as a document: date, state, who, why. **It is the only part of the product that reads like a record rather than a screen.**

**Cursor.** *"a person"* in the history where a name belongs — **D23**, now live rather than theoretical. The workflow log is where it hurts most: an audit trail that cannot name the auditor is half a trail. **High · needs the profile read path.**

**Perplexity.** Every claim on this surface is the customer's own. **Nothing to follow, and that is the answer.**

**OpenAI.** No model is involved in any of this and the product does not say so. Third review in a row for the same observation, now with the strongest case: **the audit trail is the one thing in Signora a regulator would ask about, and it is entirely deterministic.** **Medium · M12.4.**

---

## Rejected ideas

**An optimistic stage change.** The UI would feel instant. Rejected: everywhere else on this page a figure is one the server computed, and a stage that flipped locally and was then refused — a won deal cannot reopen — would be the one place the product stated something untrue, however briefly. *Returns only if measured latency makes the round trip painful, which is a measurement, not a guess.*

**A confirmation step on dismissal.** Considered because it is the destructive-feeling action. Rejected: **the required reason already is the confirmation**, and it collects something useful instead of asking the same question twice. *Will not return.*

**Making the reason optional on "I'm working this".** The friction is real — taking an account on is the one decision a seller wants instant. Rejected: the domain refuses a stateless reason, and routing around it with a client-supplied constant would put the same sentence on every account, which is R1-06's defect manufactured deliberately. *Will not return.*

**Checkboxes on "Before you act", now that a write path exists.** R2's rejection was *"nothing owns per-user state"* and this slice does not change that: an opportunity state is a workspace fact about an account, not a private note about a reader. **Storing a tick there would put one seller's reading habits into the account's permanent audit trail.** *Returns with per-user storage, which is a real schema decision.*

**Stage transitions from the attention list.** One click to dismiss a whole row, without opening it. Tempting and rejected: **the reason is what makes the dismissal worth collecting**, and a list-level control would either skip it or put a dialog on top of a triage surface. *May return* once the reason's value is proven and a keyboard-driven list exists.

**Bulk actions.** Rejected as premature — twelve accounts, no design partner, and the CRO's team-view request is a better answer to the same need. *Evidence-triggered.*

---

# Review 5 — the list, after it learned to say what is happening *(2026-08-01, M12.3)*

**J1, the daily habit.** *"If it is not good, nothing else gets used."* Same limitation as Reviews 1–4 — the browser UI could not be opened (OAuth-only sign-in, no credentials configured) — so the three requests were composed exactly as the page composes them and read in page order. Findings resting on visual judgement are marked 👁.

The real twelve, before and after:

```
BEFORE (Review 1)                              AFTER

 50  Databricks    New evidence arrived         75  Databricks    Expansion opportunity
 50  NVIDIA        New evidence arrived         75  NVIDIA        Expansion opportunity
 43  Snowflake     New evidence arrived         43  Snowflake     Active evaluation
 39  Stripe        CONTESTED                    39  Stripe        Active evaluation      CONTESTED
 33  7c33ed38      New evidence arrived         33  Atlassian     Active evaluation
 33  Atlassian     New evidence arrived         33  7622265e      Active evaluation
 20  HubSpot       Evidence aged out            20  HubSpot       Displacement opportunity  COOLING
 10  MongoDB       Evidence aged out            10  Salesforce    New decision maker
 10  Salesforce    New evidence arrived         10  MongoDB       Active evaluation         STALE
 10  Adobe         DISPUTED-NAME                10  Adobe         Displacement opportunity  COOLING
  5  Datadog       New evidence arrived          5  Datadog       Contraction risk          STALE
  1  Twilio        Evidence aged out             1  Twilio        Decision maker departed

2 distinct reasons across 12 rows          6 distinct reasons across 12 rows
```

---

## R5-01 · The list now has a shape, and the shape is the finding 🟢

**Observation.** Read top to bottom the list says: *two companies are expanding · four are actively evaluating · two are displacing an incumbent · one has a new decision maker · one is contracting · one lost its champion.* Previously it said *something happened* eight times and *something expired* four times.

**Why it matters.** This is the difference between a ranked list and a **book of business**. A seller can now form an intention before opening anything — *I'll do the two expansions first, and I need to look at Datadog because contraction risk is not something you leave* — which is the job the screen exists for.

**User impact.** *(AE)* "I know what my morning is without clicking anything." *(SDR)* "I stopped reading that column by the fourth row" — the Review 1 complaint — does not recur, because no two consecutive rows say the same thing until the four `active_evaluation`s.

**Priority:** — **Milestone:** shipped.

---

## R5-02 · A contraction risk sits eleventh, and the list gives no way to notice 🟠

**Observation.** *Datadog · Contraction risk · STALE · 5*. It is correctly ranked — the scoring model gives contraction less attention weight — and it is now **legible for the first time**, which is what makes the placement visible as a question.

**Why it matters.** Attention score and commercial urgency are not the same thing. An account that is contracting is one a seller may need to act on *sooner* than one that is expanding, and the list orders by the former while a human triages by the latter. **The pipeline already knows this** — `posture_summary()` separates expansionary from contractionary attention and refuses to net them, deliberately, because "two accounts can score identically and mean opposite things".

**User impact.** *(CRO)* "Churn risk at position eleven, under things that are going well. That is the row I would want at the top of my Monday."

**Suggested future improvement.** This is the strongest candidate yet for **D20**'s answer, and it has the property D20 asked for: **a grouping the pipeline already computes rather than a threshold somebody has to invent.** Group or mark by posture — *expansion* and *risk* as visibly different things — rather than picking a score cutoff. Needs a seller, still, because it trades a ranked list for a categorised one.

**Priority:** High. **Milestone:** the next list slice, with D20.

---

## R5-03 · Four rows still tie, and two of them are now identical in every visible way 🟡

**Observation.** Databricks and NVIDIA: both 75, both *Expansion opportunity*, both evidence-current. Atlassian and the unnamed account: both 33, both *Active evaluation*. Rows sharing a score fell from **7 to 4**, and for the remaining 4 the hypothesis does not separate them either.

**Why it matters.** R1-05's stated fix was *"once R1-01 lands, the signal title differentiates them"*. It differentiates **most** of them. Recorded as partly closed rather than closed, because a finding marked resolved on a prediction that only half held is how a register stops being trustworthy.

**User impact.** *(SDR)* "Why is Databricks above NVIDIA?" — still no answer on screen, for two rows instead of six.

**Suggested future improvement.** The honest remaining differentiator is *how much* evidence sits behind each — NVIDIA's 75 rests on one live signal, Databricks' on two. That is on the ledger and nowhere on the row. **Do not invent a tiebreak label**; if the ranking has a rule, state it.

**Priority:** Low. **Milestone:** the next list slice.

---

## R5-04 · The vocabulary is on screen and nothing explains it 🟡

**Observation.** *Displacement opportunity* and *Active evaluation* are Signal Catalog terms. A first-time reader meets nine of them with no definition anywhere on the list.

**Why it matters.** The catalog carries `why_it_matters` for exactly this, and the endpoint deliberately does not serve it — *the same prose in two places means the copy nobody looks at goes stale.* That reasoning holds for the **row**; it may not hold for a **legend**.

**User impact.** *(Sales Manager)* "I'd need to teach these nine words in onboarding. I'd rather the product taught them."

**Suggested future improvement.** Not a tooltip on every row — that is a wall. A one-time legend, or the definition on the brief where the hypothesis is already being explained by the validation surface. **The validation block already shows it on the brief**, so this may already be answered for anyone who clicks through, and the finding is really about the reader who never does.

**Priority:** Low. **Milestone:** unassigned; needs evidence that anyone is confused.

---

## R5-05 · The `signal_type` key would reach the screen if the catalog request failed 🟢 **Prevented**

**Observation.** The row carries `expansion_opportunity`; the title arrives in a separate request. If that request fails or is slow, the component renders **nothing** rather than the key.

**Why it matters.** Recorded as a confirmation. `expansion_opportunity` is not a sentence, and a reader who saw one would learn that this line is machine output — on the line the entire row is read for. A test asserts the raw key can never appear.

**Priority:** — **Milestone:** none. The bar to hold.

---

## The five roles

**SDR.** *First look:* the reasons, not the names — "the column that used to be wallpaper is now the thing I read." *Delight:* "Decision maker departed. That is a real reason to call someone." *Doubt:* R5-03.

**AE.** *First look:* the two expansions. *Confusing:* nothing. *Ignored:* the score, for the first time in five reviews — **the hypothesis is doing the triage and the number is doing the ordering**, which is the right division of labour and was not true yesterday.

**Sales Manager.** *Trust:* "Nine categories, applied consistently, with the same words every time." *Doubt:* R5-04 — "I'd have to teach the vocabulary."

**RevOps.** *Delight:* "The category comes from a versioned artifact, not from a model. I can report on it." **The first time in five reviews that RevOps has been delighted by something on the list rather than on the brief.** *Doubt:* nothing new.

**CRO.** *First look:* scanned for risk, found *Contraction risk* at eleven and *Decision maker departed* at twelve. **R5-02, stated as a complaint about the ordering rather than about the labels** — which is only possible now that the labels exist.

**The common thread.** In Review 1 every role reached *"and then what?"* within a minute. In Review 4 four of five asked about other people's accounts. **Now the complaints are about *ordering* — which is the complaint you get from someone who has read the whole list and believes it.**

---

## The staff-designer pass

**Apple.** The row is now name · reason · movement · badges · score, and it reads left to right in the order a person decides. **The list is in better shape than the brief**, whose six equal-weight sections have been the top visual finding for three reviews. 👁 **—**

**Stripe.** *"Expansion opportunity"* is a category, and a category invites the question *how many are there?* Nine — and the product never says so. **A count would frame every row.** 👁 **Low.**

**Linear.** Three requests, still no prefetch on hover, still no keyboard path through the list. **Unchanged and now more costly**, because the list is worth living in. **Medium · interaction slice.**

**Notion.** The row reads as a sentence: *Databricks — Expansion opportunity — +15.* **That is the first line of prose Signora writes with no model involved**, and it is better than the narration's opening sentence. 👁

**Cursor.** The reason changes when the evidence changes and the screen has no way to say *this one moved category since yesterday*. **That would be the single most valuable thing on this list** — an account that went from *Active evaluation* to *Contraction risk* is a different account. Needs per-user read state (**D5**). **High value, real schema decision · unassigned.**

**Perplexity.** The category is not followable from the list. It is one click away on the brief, where the validation surface explains it. **Correct as is** — a list that made every category a citation would be a list nobody could scan.

**OpenAI.** **The strongest thing here: no model touched this screen, and the categories come from a reviewed artifact with a version number.** Third review asking for that to be stated somewhere. On the daily surface it is the most defensible sentence the product could print.

---

## Rejected ideas

**A `Record<SignalType, string>` in the client, avoiding the catalog request.** One fewer round trip. Rejected: it is a second vocabulary, wrong the moment the catalog changes and invisible when it does — and the module that produces the row is forbidden from naming a hypothesis for precisely this reason. A test proves the client holds no table. *Will not return.*

**Serving the title on the attention row.** Simplest for the client. Rejected: `opportunity_engine`'s import contract forbids `modules.signal_engine` outright, with a stated reason — *"it never forms hypotheses or weighs them"* — and a workflow module that can name a hypothesis is one that can branch on one. *Will not return.*

**A batched score endpoint from the Buying Score Engine.** Architecturally the purest owner of *"which hypothesis leads"*. Rejected: the attention query already loads every score, so this would add a duplicate read to the one surface opened every morning in exchange for moving a field access. *Returns* if the attention list stops loading full scores.

**Keeping the trigger alongside the hypothesis.** Two reasons per row. Rejected: that is R1-02 preserved on purpose — two timeframes side by side that a reader must reconcile. *Will not return; it lives on the brief.*

**Grouping the list by posture, now.** The strongest idea in this review (R5-02) and deliberately not built. It reorders a list whose order is its ranking, and **trading a ranked list for a categorised one is a product decision with a seller in the room.** *Returns with D20.*

---

# Review 6 — the way in *(2026-08-01, M12.3 · ADR-0033)*

**The first screen every customer sees, and the first review conducted in a browser.** Five reviews carried the same limitation — *"I could not open the browser UI"* — because sign-in offered only OAuth and no credentials were configured. That limitation is now gone, and it turned out to be hiding a second one.

What the journey actually does, verified end to end through the real routes:

```
POST /api/auth/sign-up/email                        200   user created, unverified
POST /api/auth/sign-in/email    (before verifying)  403   refused
GET  …/verify-email?token=…                         200   emailVerified → true
POST /api/auth/sign-in/email    (after verifying)   200   session created
POST /api/auth/request-password-reset  (real addr)  200
POST /api/auth/request-password-reset  (unknown)    200   indistinguishable
GET  …/reset-password/{token}                       302 → /reset-password?token=…
POST /api/auth/reset-password                       200
     old password                                   401
     new password                                   200
     the used link, replayed                        400
```

---

## R6-01 · Sign-in had never worked on a fresh clone, for any method 🔴 **FIXED**

**Observation.** The `auth` schema existed and contained **no tables**. Nothing in the repository has ever created them — no migration, no script, no documented step. Better Auth's tables are the vendor's, created by its own tooling, and that tooling was never wired in.

**Why it matters.** This is the defect underneath the one that was reported. Enabling password sign-in without finding it would have produced *"relation auth.user does not exist"* and the product owner still could not have reviewed anything. **The OAuth gap was hiding it**: nobody could get far enough to see the second failure, because they never got past the first.

**User impact.** Every reviewer, every day, for five milestones.

**Implemented immediately** — a correctness bug, and the actual blocker. `npm run auth:migrate` uses `better-auth/db/migration`, so the already-ratified dependency is sufficient and no new package was added. `docs/RUNNING.md` now names it as step one.

**Priority:** — **Milestone:** done, M12.3.

---

## R6-02 · The observability hook had been breaking every completed auth request 🔴 **FIXED**

**Observation.** `hooks.after` was a bare async function. Better Auth 1.6 requires `createAuthMiddleware`. A plain function runs, emits its event, and then leaves Better Auth to continue with a context it did not build — so sign-up **created the user, sent the verification email, and returned 500.**

**Why it matters.** A side effect that succeeds behind a failed response is the worst shape a bug can have: the customer retries and gets *"an account already exists"*.

**How it stayed hidden.** It could only fire on a request that reached the end of an auth route, and no request ever had — see R6-01. **Two dormant defects, each concealing the other, in the subsystem with the most tests around it.**

**Implemented immediately.** The hook is wrapped, with a comment saying what it hides when it is not.

**Priority:** — **Milestone:** done, M12.3.

---

## R6-03 · The sign-in page was the one screen not built from the design system 🟠 **FIXED**

**Observation.** `app/(auth)` used Tailwind's default palette directly. `design-tokens.test.tsx` scanned `components/` and nothing else, so **the first screen every customer sees** was outside the rule the whole product follows.

**Why it matters.** A rule with a gap in its enforcement is a rule the code eventually finds the gap in — and it found it on the highest-traffic screen in the product.

**Implemented immediately** — an enforcement gap, not a redesign. The five auth screens are composed from `components/ui`, and the check now covers the directory. It caught its first violation on the first run: my own docstring, quoting the utilities it was describing.

**Priority:** — **Milestone:** done, M12.3.

---

## R6-04 · Three auth pages were prerendered, baking configuration into the build 🟠 **FIXED**

**Observation.** `/sign-in`, `/sign-up` and `/forgot-password` were static. They read `loadAuthConfig()`, so **which sign-in methods exist was decided at build time.**

**Why it matters.** An image built without OAuth credentials keeps showing no provider buttons after being deployed *with* them. That is the Infrastructure Contract's environment-based-configuration rule (§20b), and the violation predates this change — `/sign-in` has been static since M1.5.

**Implemented immediately.** All five auth routes read configuration at boot.

**Priority:** — **Milestone:** done, M12.3.

---

## R6-05 · Nothing tells a new account what to do next 🟠

**Observation.** Verify → signed in → `/workspaces` → an empty list and a create form. The journey from *"I have an account"* to *"I can see something"* is undescribed, and the seeded Playground is invisible until `make demo-seed` is re-run.

**Why it matters.** **The first ninety seconds are the only ones a new customer spends without a reason to leave**, and Signora currently spends them on a form with no explanation of what a workspace is or why they need one.

**User impact.** *(SDR)* "It asked me to name something before it showed me anything."

**Suggested future improvement.** The workspace screen is the last unreviewed surface in the product and it is now reachable. It needs its own slice — one that answers *what is this and why am I being asked* before it asks.

**Priority:** High. **Milestone:** the next slice — see below.

---

## R6-06 · A verified account still has no way in without a signing key 🟡

**Observation.** With no `SIGNORA_JWT_PRIVATE_KEY`, sign-in succeeds, `/workspaces` loads, and every API call fails. `/api/health` says `signing_keys: unavailable`; the UI says nothing.

**Why it matters.** The one remaining setup cliff, and it presents as a broken product rather than as missing configuration.

**Suggested future improvement.** The shell already fetches health. A single banner — *"Signora cannot reach its API: no signing key is configured"* — turns a mystery into an instruction. **Operator-facing, and it should never appear for a customer**, which is exactly why it can be blunt.

**Priority:** Medium. **Milestone:** unassigned; small and self-contained.

---

## The five roles

**SDR.** *First look:* "It looks like every other sign-up, which is what I want from a sign-up." *Doubt:* R6-05 — "then it asked me to make a workspace and I didn't know what that was."

**AE.** *Delight:* the password field states the length rule before it is broken.

**Sales Manager.** *Trust:* "It made me confirm my email. The tools that don't are the ones I worry about."

**RevOps.** *Delight:* "Password, Google and Microsoft all land in the same place and the backend can't tell which. That is one access review, not three." **The strongest endorsement any role has given an architectural decision.**

**CRO.** *First look:* signed in, saw an empty workspace list, asked where the accounts were. **R6-05, from the person least likely to ask twice.**

---

## The staff-designer pass

**Apple.** One card, one form, nothing decorative. **The quietest screen in the product and it should stay that way** — somebody here is not evaluating Signora yet.

**Stripe.** The reset confirmation is worded to be true whether or not the address exists — *"if there is an account for that address"*. **A security property expressed as copy rather than as a caveat.**

**Linear.** Enter submits, tab order follows reading order, both free from using a real `<form>`. **No keyboard path between the auth screens**, but they are not screens anyone lives in. **Low.**

**Notion.** Five screens, one voice, one frame. The verify screen says what will happen rather than what has happened.

**Cursor.** The verification link appears in the terminal you started the server in. **For a developer this is better than email**, and it is worth saying plainly that this is a local affordance, not a product feature.

**Perplexity.** Nothing to follow here, correctly.

**OpenAI.** No model touches any of this. Consistent with the rest of the product and, as in three previous reviews, unstated.

---

## Rejected ideas

**A development sign-in bypass.** What was originally imagined, and explicitly ruled out by the product owner before being ruled out here. `18-authentication.md` already names it an anti-pattern: it diverges the test path from production and inevitably reaches production. **It would also have failed the actual goal** — the point was to exercise the customer's journey, and a bypass exercises nothing. *Will not return.*

**A seeded test user.** Would have given a session without a sign-up, leaving registration, verification and reset unexercised — the three flows most likely to be wrong, and the two that turned out to be broken. It also puts a credential in the repository. *Will not return.*

**A `provider` claim in the JWT.** Tempting for analytics and audit. Rejected as the load-bearing decision of ADR-0033: a claim the backend can read is a claim the backend can branch on, and the first branch would be a security decision keyed to a method rather than a policy. Method is recorded in the auth event log, where nothing consults it. *Will not return.*

**An identity abstraction over Better Auth.** Better Auth *is* the abstraction. Wrapping it would duplicate authentication logic, which is what buying a vendor avoided. *Will not return.*

**Adding `@better-auth/cli` to run migrations.** Rejected: `better-auth/db/migration` exposes the same thing from the dependency already ratified, and a committed script is more reviewable than a command in a README. *Will not return.*

**Choosing an email provider now.** Tempting, since the console transport is obviously temporary. Rejected: it is a vendor decision and a new dependency, and taking it under time pressure to unblock a local review is how a five-year dependency gets chosen in an afternoon. **The port is what lets it wait.** *Returns with the first environment that is not a developer's machine.*

---

# Review 7 — the first run *(2026-08-01, M12.3)*

**The first review conducted by actually being a new customer.** Register, verify, sign in, and see what is there — which nobody had ever done, because until the previous slice nobody could.

It found three defects in a chain, each of which had been concealing the next.

---

## R7-01 · The two tiers had never agreed on what a user is 🔴 **FIXED**

**Observation.** Better Auth's default identifier is a 32-character nanoid — `oto6T8DoM1fZsFzfVqsCEzLDSGeSSAaZ`. It is carried verbatim as `sub`. The Python verifier does `UUID(str(claims["sub"]))` and **rejects the token outright.**

Proven, not inferred:

```
Better Auth default (nanoid)   REJECTED  The supplied token is not valid.
after the fix (uuid)           ACCEPTED  user_id=acf158b0-f88c-4b71-b503-e1693601de69
```

**Why it matters.** **Every API request from a real signed-in customer would have returned 401.** The JWT boundary — the architecture's most carefully specified seam — was violated by the identity provider itself, and had been since M1.2.

**Why it stayed invisible, which is the more useful finding.** Three things compounded:

1. **No user had ever existed** (R6-01), so `sub` had never carried a real Better Auth id.
2. **Every test mints `sub` as a `uuid4()`.** The test path and the production path differed in *exactly the field under dispute* — the one place a fake must not differ from the real thing.
3. **The comment at the site asserted the opposite**: *"Better Auth generates its own ids; we do not override them, so the two systems never disagree about who a user is."* True in intent, false in fact, and it is the sentence a reviewer would have trusted.

**Implemented immediately.** `generateId` is Better Auth's own hook, so nothing is reimplemented and the vendor still owns identity — this only says *which* generator. The function form rather than `'uuid'`: that setting resolves to a `gen_random_uuid()` **column default**, so it inserts null on any table created before the option was set, which is exactly what happened on the first attempt.

**Priority:** — **Milestone:** done, M12.3.

---

## R7-02 · The seeder looked for users in the wrong schema, and said so confidently 🟠 **FIXED**

**Observation.** `make demo-seed` enrols every signed-in user in the Playground. It queried `public."user"`; Better Auth's tables are in the **`auth`** schema. It therefore always found nobody, and printed:

> `members     none — no signed-in users exist yet`

**Why it matters.** A **false statement about a database that had a user in it** — the class of defect the repository-tells-the-truth principle names, and the reason the product owner signed in and saw an empty product with a full Playground sitting beside it.

It was accidentally true until this milestone, because there were no users anywhere (R6-01). **Its docstring even asserted the cause of its own failure**: *"Better Auth … creates its tables on first run in the Next tier"*, which nothing has ever done.

**Implemented immediately.** It reads `SIGNORA_AUTH_SCHEMA`, and now reports `members 1 signed-in user(s) enrolled as owner`.

**Priority:** — **Milestone:** done, M12.3.

---

## R7-03 · A signed-in user with no workspace saw a heading and blank space 🔴 **FIXED**

**Observation.** `useAccounts(null)` is `enabled: false`, so `isLoading`, `isError` and `data` are all falsy. Every branch on the page tests one of the three, so **none of them rendered.**

**Why it matters.** It is the state every brand-new account is in, and a page that renders nothing is indistinguishable from a broken one. The existing empty states all say *"this workspace has no accounts"* — a different sentence with a different next action, and reusing it would be a confident wrong answer.

**Implemented immediately** — see **D36**. A page-level regression test asserts it, and was checked by removing the fix: two of its four assertions fail without it.

**Priority:** — **Milestone:** done, M12.3.

---

## R7-04 · The daily surface is two clicks behind a screen describing a product that does not exist 🔴 **RAISED, NOT FIXED**

**Observation.** `/` is Overview, written at M1.5. It says *"Connect a data source to start seeing revenue signals here"* — **there is no way to connect a data source**; integrations are M13. It shows three permanently-empty counters, and its Opportunities card does not link to the Opportunities page, which exists and works.

**Why it matters.** A seller opens Signora every morning and the first screen is a placeholder that promises a capability a milestone away. **The list is good and it is behind a screen that is not.**

**Why it was not simply fixed.** The navigation is frozen (§20c), and this is the **second** finding to hit that surface — [D1](38-product-design-principles.md) recorded the *Opportunities* vs *Attention* naming problem at M12.1 and deferred it on exactly these grounds. **Two deferred findings on one frozen surface is what a due IA revision looks like**, and it should be one deliberate change rather than two opportunistic ones. Recorded as **D37**, awaiting a ruling.

**Priority:** High. **Milestone:** an IA revision, on the product owner's approval.

---

## The five roles — first run, in order

**SDR.** *"I signed up, confirmed my email, and landed on a page telling me to connect a data source I can't connect. Then I clicked Opportunities and it was blank."* **Every sentence of that is now either fixed or raised.**

**AE.** *Delight:* sign-up asked for a password once and told me the rule first.

**Sales Manager.** *Doubt:* three of six sidebar entries say *coming soon*. "That is what a demo looks like, not a product."

**RevOps.** *Delight:* one identity, three sign-in methods, one access review. *Doubt:* R7-01 — "so nobody has ever actually called the API as a real user?" **Correct, and that is the finding.**

**CRO.** Signed in, saw nothing, asked where the accounts were. **The shortest and most damning review any role has given.**

---

## The staff-designer pass

**Apple.** The empty state now explains itself before asking for anything. **The screen it sits on still should not be the first screen.**

**Stripe.** *"A workspace is where your accounts, evidence and decisions live"* — a term defined at the moment it is first required, which is the only moment anyone reads a definition.

**Linear.** The first run is four screens deep before any work appears. **A product for people who live in it should open onto the work.** D37.

**Notion.** The no-workspace copy offers both ways out — create one, or be added to a colleague's. Most sellers never create anything.

**Cursor.** **The three defects here were found by using the product for ninety seconds.** No test suite would have caught any of them, and 1992 backend tests did not. *That is the finding to carry forward.*

**Perplexity.** Nothing to follow.

**OpenAI.** No model involved anywhere in this journey.

---

## Rejected ideas

**Widening `user_id` to text across the schema so Better Auth's nanoid fits.** It would have worked. Rejected: it trades a type for a defect nobody would find again, and touches the schema, RLS, `app.user_id` and the principal — against one Better Auth option that does the same thing correctly. *Will not return.*

**`generateId: 'uuid'`.** Better Auth's own shorthand, and the first thing tried. Rejected on evidence: it resolves to a `gen_random_uuid()` **column default**, so it inserts null on any table created before the setting existed — observed as a not-null violation on the first sign-up after the change. The function form depends on no schema state. *Will not return.*

**Fixing the Overview page's copy instead of retiring it.** Cheaper and it would have removed the false promise. Rejected: the page's problem is that it exists between a seller and their work, not that its wording is wrong. *Returns only as part of D37's ruling.*

**Removing the three *coming soon* nav entries while I was there.** Tempting and out of scope: the navigation is frozen, and this is the second finding against it. **Bundling it into a page slice is precisely what the freeze exists to prevent.** *Returns with D37.*

---

# Review 8 — the front door *(2026-08-01, M12.3 · D38)*

Two changes reviewed together, because they answer the same question from opposite ends: **how long does it take somebody to get from a clone to a useful opinion?** Before this slice the honest answer was *nobody had ever done it.*

What the navigation was, and is:

```
BEFORE                          AFTER

  Overview        ← landing       Attention   ← landing, and the work
  Companies  Soon                 Settings
  Opportunities ← the product
  Signals    Soon
  Timeline   Soon
  Settings

6 entries, 2 of which went        2 entries, both of which go
anywhere. The product was         somewhere. The product is the
third in the list.                first thing you see.
```

---

## R8-01 · The navigation was the data model, not the workflow 🔴 **FIXED**

**Observation.** Companies, Signals, Opportunities and Timeline were four of the thirteen pipeline modules with a sidebar entry each.

**Why it matters.** **None of the six customer journeys is *show me all the signals* or *show me all the companies*.** A signal is what explains an account; a company is what an account *is*. Both were already on the brief, where they answer something. Timeline is journey J6 and is explicitly per-account.

Organising a menu by the modules that produce data is the most natural mistake an engineering team makes, and it is invisible from inside — the M1.5 comment states the intent plainly and reasonably: *"settle the information architecture before pages are written into it."* **The pages have since been written, and they disagreed with it.**

**Implemented after review** (D38), as an approved §20c change rather than a page slice bending the shell.

**Priority:** — **Milestone:** done, M12.3.

---

## R8-02 · Three of six entries advertised absence 🟠 **FIXED**

**Observation.** *Companies · Soon*, *Signals · Soon*, *Timeline · Soon* on the first screen a customer sees.

**Why it matters.** *(Sales Manager, Review 7)* — *"That is what a demo looks like, not a product."* A roadmap on the navigation tells a customer what they cannot do, in the place they look to find out what they can.

**Implemented.** The invariant that guarded them was rewritten rather than deleted: `no-mock-data.test.tsx` asserted *"a route exists exactly when its entry stops saying Soon"*; it now asserts **every navigation entry goes somewhere**, which is the rule that survived all three versions of that test.

**Priority:** — **Milestone:** done, M12.3.

---

## R8-03 · "Opportunities" was the product's own word for something else 🟠 **FIXED**

**Observation.** **D1, raised at M12.1 and deferred twice.** *Opportunity* is Signora's domain word for **the workflow object a human commits to** — and most rows on that list are not that yet.

**Why it matters.** Naming the section after the record rather than the question is the dashboard framing the product is trying to leave. **`Attention` is the domain's word too**: the score measures commercial attention, the ledger splits `attention_by_posture`, the query is `attention_list`. The vocabulary is now the same from the database to the sidebar.

**Priority:** — **Milestone:** done, M12.3. *Two deferrals, then one deliberate change.*

---

## R8-04 · Nobody could reach the product in under an afternoon 🔴 **FIXED**

**Observation.** A reviewer needed to: bring up Docker · run migrations under the owner identity · realise Better Auth's tables did not exist · generate a key pair · find OAuth credentials or register and hunt a verification link in server output · create a workspace · discover their workspace was not the seeded one · re-run the seeder.

**Why it matters.** **The product owner's ability to review is a product capability**, and it had been degrading while the product improved. Five reviews carried *"I could not open the browser UI."*

**Implemented.** `make demo` now does all of it: stack, schema, Better Auth's tables, **four sign-in accounts**, twelve accounts of pipeline output. `docs/RUNNING.md` is the single source of truth, with a troubleshooting table keyed on **what you see** rather than what went wrong.

**Priority:** — **Milestone:** done, M12.3.

---

## R8-05 · Signora has two roles and reviewers asked for five 🟡

**Observation.** The seeded personas are Revenue Operations, Sales Manager, Account Executive and Sales Development. **Signora's domain has `owner` and `member`.** The personas map onto those two, and RUNNING.md says so.

**Why it matters.** Recorded rather than fixed because **inventing a role model to satisfy a seeding script would be domain design done by a dev tool.** What the two roles buy today is real: an owner reaches Settings and a member does not, and two accounts are what makes *"held by someone else"* reviewable.

**Suggested future improvement.** A richer role model is a domain decision with a Casbin policy and an RFC behind it. **Trigger:** a customer who needs a manager to see a book without administering it — which is exactly what Marcus's persona is, and nobody has asked for yet.

**Priority:** Low. **Milestone:** unassigned; needs a demonstrated need.

---

## R8-06 · The verification link is in the terminal, and that is a local affordance 🟡

**Observation.** Registering as yourself still means reading the dev server's stdout. The four demo accounts skip it — they are created *and verified* through Better Auth's own routes.

**Why it matters.** Reviewing no longer requires it, which is the point. **It is worth stating that this is a local affordance and not a product feature**, because it is the kind of convenience that quietly becomes an assumption.

**Priority:** Low. **Milestone:** resolved by choosing an email provider, which is an outstanding ADR-0033 decision.

---

## The five roles — the front door

**SDR.** *"I signed in and the first thing on screen was my morning."* **The complaint from Review 7 does not recur.**

**AE.** *Delight:* two menu entries. "I know where everything is because there is nowhere else."

**Sales Manager.** *First look:* signed in as Marcus, went for Settings, and it is not in the menu. **Correct — a member cannot administer a workspace — and the first time client-side permission has been visible as a product behaviour rather than as a test.**

**RevOps.** *Delight:* four accounts, one password, in `make demo`. "I can put a designer in front of this."

**CRO.** Signed in, saw twelve ranked accounts with what is happening at each. *"This is the first time I have opened it and not asked a question."*

---

## The staff-designer pass

**Apple.** **Two entries.** The sidebar has stopped being a table of contents for the engineering team. *The brief's six equal-weight sections remain the largest visual problem in the product* — four reviews old now.

**Stripe.** The troubleshooting table is keyed on **what you see**, not on what went wrong, which is the only key a reader can look something up under.

**Linear.** Still no keyboard path through the list, and the list is now the front door — **which raises the cost.** **Medium · interaction slice.**

**Notion.** *Attention · Settings.* One is the work and one is the configuration. **A two-item navigation is a strong claim that the product knows what it is for.**

**Cursor.** `make demo` is one command. The two processes after it are two more. *"Would a single command run the whole stack?"* — it would, and it would hide the two processes a developer needs to see the logs of. **Recorded, not built.**

**Perplexity.** Nothing to follow here.

**OpenAI.** No model in the entry experience.

---

## Rejected ideas

**A Morning Brief as the landing page.** The product owner asked directly. Rejected **for now**, and the reason is the one that condemned Overview: a brief summarising the book is *a dashboard about the work* rather than the work, and **the attention list already is the morning brief** — ranked by attention, each row naming what is happening. *Returns when it can say something the list cannot — **what changed since you last looked**, which needs per-user read state (D5). Trigger: a design partner saying they cannot tell what is new.*

**Redirecting `/` to `/opportunities` instead of moving the page.** One line, no navigation change. Rejected: it leaves the sidebar saying *Overview* over a list of accounts. **A redirect that makes the menu lie is worse than the page it replaced.** *Will not return.*

**Keeping the *coming soon* entries as a visible roadmap.** Rejected: a customer is not the audience for a roadmap. *Will not return.*

**Seeding users by writing rows into `auth.user` with a hash we computed.** Simpler, no Better Auth API to learn. Rejected: that is authentication logic Signora would then own, in the one subsystem where a vendor was bought precisely so it would not. `auth.api.signUpEmail` and `auth.api.verifyEmail` are the same handlers the browser reaches. *Will not return.*

**Inventing Manager / AE / SDR workspace roles to match the personas.** Rejected: domain design done by a seeding script. *Returns with a demonstrated need — see R8-05.*

**Folding `npm run dev` and the API into `make demo`.** Rejected: it would hide the two processes whose logs a reviewer needs — including the one the verification link is printed to. *Will not return.*

---

# Review 9 — the Attention page, reviewed as a workflow *(2026-08-01, M12.3)*

> **The instruction was explicit: review the workflow, not the implementation.** Challenge every element. Does a row answer *what happened · why does it matter · what should I do · what evidence supports this · what could change this*?

The row, element by element, and what each is actually for:

```
  ┌──────────────────────────────────────────────────────────────────────┐
  │  NVIDIA Corporation                          [Yours]  [Contested] 75 │
  │  Expansion opportunity   +15                                         │
  └──────────────────────────────────────────────────────────────────────┘
      ↑ name          ↑ hypothesis  ↑ move    ↑ ownership  ↑ dissent  ↑ score
```

| Element | The question it answers | Verdict |
|---|---|---|
| **Account name** | *Who is this?* | **Earns its place.** A seller scans names, and it is the only link |
| **Hypothesis** | *What happened, and why does it matter?* | **Earns it, and it is the row's spine** — six distinct values across twelve accounts since the list slice |
| **Movement** | *What changed?* | **Earns it, narrowly.** It is the only *temporal* fact on the row |
| **Ownership** | *What should I do — or has somebody?* | **New this slice.** Silent on the common case |
| **Contested** | *What evidence disagrees?* | **Earns it, rarely.** One row of twelve, and it is the most interesting row |
| **Evidence health** | *What could change this?* | **Earns it, rarely.** Silent when current |
| **Score** | *How much attention?* | **Earns it as an ordering.** Redundant as a number — see R9-02 |

---

## R9-01 · The row answers four of the five questions, and the fifth is one click away 🟢

**Observation.** *What happened* (hypothesis) · *why it matters* (hypothesis + posture in the wording) · *what evidence supports this* (**not on the row**) · *what could change this* (evidence health) · *what should I do* (ownership, newly).

**Why that is right rather than a gap.** *"What evidence supports this"* is the brief's entire job, and putting it on a row would make twelve rows unscannable. **The list's contract is that every row is followable, not that every row is complete.** That is what progressive disclosure means on a list — information ordered so most of it is never read.

**Would a salesperson naturally click this row?** Yes, and the evidence is behavioural rather than aesthetic: they click the *name*, which is the only link, and the hypothesis beside it is the reason they chose that name over another. Before the list slice they had no reason and the click was arbitrary.

**Priority:** — **Milestone:** none. Recorded as the bar.

---

## R9-02 · The score is on the row twice 🟡

**Observation.** The list is *ordered by* score and also *prints* score. Position and number carry the same fact.

**Why it matters.** Every other element is silent when it has nothing to say. The number is the only one that is always present and never surprising — you already know row 1 outranks row 2, because it is row 1.

**The counter-argument, which is why this is not being changed.** The number is not only a rank: `75` and `1` differ in a way position cannot express, and **removing it would leave a reader unable to tell a strong book from a thin one.** That gap — between 75 and 1 — is exactly what D20 was reaching for, and it turns out the score *already* expresses it. The redundancy is in the ordering, not the number.

**Suggested future improvement.** If anything goes, it is the ordering's *implicitness*, not the number: a list that stated its own rule (*"ranked by attention, most pressing first"*) would make the number's second job legible. **The page subtitle already says this.** Recorded and closed.

**Priority:** Low. **Milestone:** none.

---

## R9-03 · A contraction risk still reads like a small opportunity 🟠

**Observation.** *Datadog · Contraction risk · 5 · stale* sits eleventh. Every element of that row is correct and the row looks exactly like *Salesforce · New decision maker · 10*.

**Why it matters.** **The hypothesis names the risk and nothing shows it.** A CRO scanning twelve rows for trouble reads twelve rows. The pipeline computes posture and refuses to net it away precisely because *"two accounts can score identically and mean opposite things"* — and the list is where that refusal stops being visible.

**Suggested future improvement.** Posture on the row, from the leading contribution — the pipeline's own word, not a set of catalog keys hardcoded in a component. **Deliberately not built in this slice:** it changes what a CRO scans for, which is a product judgement that wants a seller in the room, and D39 records it as the honest remainder of D20.

**Priority:** Medium. **Milestone:** next, with a seller.

---

## R9-04 · Every row is one line of a story and no row tells one 🟡

**Observation.** *"NVIDIA — Expansion opportunity — +15 — Yours — 75."* That is a sentence. **What it is not is a change**: nothing says whether this is new since yesterday, or the fourth morning it has looked identical.

**Why it matters.** A seller opening Signora daily is asking *what changed*, and the list answers *what is true*. Those coincide on day one and diverge by day three.

**Suggested future improvement.** **D5** — *what changed since you last looked* — needs per-user read state and is a real schema decision. It is also what would make a Morning Brief worth building, which D39 rejected for exactly this reason.

**Priority:** Medium. **Milestone:** unassigned. **Trigger:** a design partner saying they cannot tell what is new.

---

## R9-05 · Could this row become the defining interaction of Signora? 🟢

**Asked directly by the product owner, and worth answering directly: it already is, and one element makes it so.**

Every competitor's list is *name · number · trend*. Signora's row carries the **hypothesis** — a versioned, reviewed, deterministic classification of what is happening at that company, produced with no model, which a customer can follow to the evidence and challenge line by line.

**The defining interaction is the click, not the row.** The row earns the click; the brief survives it. No competitor's summary survives being clicked.

**What would strengthen it, in order:** posture (R9-03), then *what changed since you last looked* (R9-04). **What would weaken it:** anything that makes the row longer.

**Priority:** — **Milestone:** none.

---

## The five roles — the morning question, and whether the list answers it

**SDR** — *"Who do I call today?"* **Answered.** Top-down, stop when you have three. *"The reason column is why I pick one over another."*

**AE** — *"Which of my accounts moved?"* **Newly answered, partly.** Rows say *Yours*. *Doubt:* "I still read twelve rows to find my three." **A filter, at volume — D6's trigger.**

**Sales Manager** — *"Where should my team focus?"* **Partly.** *Taken* says somebody has it and not who. **D23**, and it bites hardest here.

**RevOps** — *"Is the intelligence behaving?"* **Not a list question**, and correctly so — theirs is answered by the brief's arithmetic. *Delight:* "Nothing on this screen was written by a model."

**CRO** — *"What is at risk?"* **Not answered.** R9-03. *"I read every row to find the two that matter."*

**The common thread.** Reviews 1–4 were about *whether the list said anything*. This one is about *whether it says it in the right order for the person reading* — three of five roles now want the same list arranged for them. **That is a filtering and grouping question, and it arrives when the list is long enough to need one.**

---

## The staff-designer pass

**Apple.** Seven elements on a row and **five of them are silent most of the time**. That is the discipline: the row grows only when the account is unusual. **The best-composed surface in the product.**

**Stripe.** The score prints beside an ordering that already implies it (R9-02) — and the number carries information the ordering cannot. **Kept, deliberately, and now documented.**

**Linear.** Still no keyboard path, and this is now the front door. `j`/`k` and `Enter` would cost little and this is the third review to ask. **Medium · interaction slice.**

**Notion.** *"NVIDIA — Expansion opportunity — +15 — Yours."* **Reads as a sentence, in a product where no model wrote it.**

**Cursor.** *Yours* is the first element on this screen that reflects the reader back at them. **The product now knows who is looking**, which is the beginning of it feeling like a tool rather than a report.

**Perplexity.** Every row is followable, and the click ends at provider readings. **The click is the product.**

**OpenAI.** Nothing on this screen is model-authored, on the screen opened most often. **Still unstated, four reviews running.** On the daily surface it is the most defensible sentence Signora could print.

---

## Rejected ideas

**Grouping the list.** Measured: six groups for twelve rows, **three holding a single row**. See **D39**. *Returns at D6's trigger — a list that stops fitting on one screen.*

**Pinning risk above everything else.** It works, and it puts *which hypotheses count as risk* in a React component — a second opinion about the Signal Catalog held by the layer least able to review one. *Returns as posture on the row, which is the pipeline's own word.*

**Named sections — Heating Up, Cooling, Decision Maker Left.** Each is a restatement of a field already on the row. *Will not return in this form.*

**Sorting owned rows to the top.** It makes the list's order depend on who is looking, and the ranking is the ranking. *Returns as a filter, not as an ordering.*

**A *mine / everyone* filter now.** Right at three hundred accounts, premature at twelve — **a control that always shows the same thing teaches people to ignore controls.** *Returns at D6's trigger.*

**Removing the score from the row.** Considered seriously under R9-02 and rejected: the gap between 75 and 1 is information the ordering cannot carry, and it is the very gap D20 was reaching for.

---

# Review 10 — the whole morning, as one journey *(2026-08-01, M12.3)*

> **The instruction was to stop thinking in screens.** Walk from sign-in to the end of a seller's work, and challenge every *transition*. The screens have each been reviewed twice; the joins between them never have.

## The journey, counted

A seller with twelve accounts, working top-down:

```
  sign in                                                    1 click
  ↓
  ATTENTION                                    the list, ranked
  ↓ click a name                                             1 click
  BRIEF          score · momentum · narration · what to check · ledger
  ↓ click a ledger line                                      1 click
  EVIDENCE       provider readings                    (Esc closes)
  ↓ decide                                                   2 clicks
  ↓
  ← "All accounts"                                           1 click
  ATTENTION      ...back at the top, scrolled to row 1
  ↓ find where you were, click the next name                 1 click + hunting
  BRIEF
  ↓
  × 12
```

**Twenty-four navigations for twelve accounts**, plus twelve acts of re-finding your place — and the list is **shorter each time you dismiss something**, so the place you are re-finding has moved.

---

## R10-01 · There is exactly one exit from the brief, and it is backwards 🔴

**Observation.** `← All accounts` is the only navigation on the account brief. **There is no next, no previous and no position.** Every account is an isolated visit; the product has no notion of *working through* a list.

**Why it matters — this is where momentum stops, and the question was asked literally.** A seller's morning is a sequence, and Signora models it as twelve unrelated errands. Every tool built for people who live in it all day — Linear, Gmail, Superhuman, Things — lets you move to the next item **without returning to the list**, because returning is where attention leaks.

**It is worse than a click.** `<Link href="/">` is a fresh navigation, so **the list scrolls back to the top every time.** After the eighth account you return to row 1 and scroll down again to find row 9.

**User impact.** *(SDR)* "I'd open three, get bored of the round trip, and do the rest from the CRM." **That is the sentence that matters** — it names where the user leaves the product, which is exactly what this review was asked to find.

**Suggested improvement — and this is the slice.** *Next account* on the brief, naming where it goes, with the position, and a keyboard path. **Needs no new endpoint**: the brief can read the same cached list the attention page already holds.

**Priority:** High. **Milestone:** M12.3, now.

---

## R10-02 · Recording a decision leaves you exactly where you were 🟠

**Observation.** Take an account on: the dialog closes, the stage line changes, and the page is otherwise identical. **You have finished with this account and the product does not know it.**

**Why it matters.** The decision *is* the end of the visit. It is the one moment the product can be certain the reader is done — and it is the moment it does the least.

**Suggested improvement.** Fold into R10-01: after a decision, the natural next thing is the next account. **Deliberately not an automatic redirect** — a page that navigates itself after you click something takes the reader's place away from them, and a dismissal is exactly when somebody wants to check what they just wrote.

**Priority:** Medium. **Milestone:** M12.3, with R10-01.

---

## R10-03 · Nothing remembers what you have already looked at 🟡

**Observation.** Return to the list after reading four briefs and it is identical to the list before you read any.

**Why it matters.** A seller cannot tell, in the middle of their morning, which rows they have dealt with. Accounts they decided *nothing* about are indistinguishable from accounts they never opened.

**Suggested improvement.** **D5** — per-user read state — which is a real schema decision and the same thing that would make a Morning Brief worth building (D39). **Trigger:** a design partner losing their place. R10-01 removes most of the need by removing the return trip.

**Priority:** Medium. **Milestone:** unassigned.

---

## R10-04 · The narration says "3 facts" and cannot show them 🟠

**Observation.** Ledger citations open. **Narration citations do not** — a sentence carries a fact count and no way to follow it. The tokens are `signal_contribution`, `buying_score` and `opportunity`; three resolvers do not exist.

**Why it matters.** It is the one place the product visibly promises something it does not do, on the surface whose entire argument is *you can check this*.

**Priority:** High. **Milestone:** M12.4. **Not this slice**, because a reader who cannot get to the *second* account will never reach the third narration.

---

## R10-05 · The evidence drawer is the best transition in the product 🟢

**Observation.** A ledger line opens a modal, Escape closes it, and **you are exactly where you were** — same scroll, same page, no navigation.

**Why it matters.** Recorded as the bar. **It is the only transition in the journey that costs the reader nothing**, and it is the model R10-01 should be measured against: the cheapest transition is the one that does not move you.

**Priority:** — **Milestone:** none.

---

## Where each role leaves the product, and why

| | Leaves at | Why | Could Signora prevent it? |
|---|---|---|---|
| **SDR** | The third round trip | Twenty-four navigations to read twelve accounts | **Yes — R10-01** |
| **AE** | *"which are mine?"* | Rows say *Yours*; twelve rows must still be read to find three | At volume, a filter. D6's trigger |
| **Sales Manager** | *"who has it?"* | *Taken* names nobody — **D23** | Needs a cross-tier profile contract |
| **RevOps** | Does not leave | The brief's arithmetic is their whole question | — |
| **CRO** | The first screen | Scans for risk, reads twelve rows to find two — **R9-03** | Yes, with a seller's ruling |

**Three of five leave for a reason the product could remove, and one of the three is a navigation gap.**

---

## Could someone complete their morning entirely inside Signora?

**Not yet, and the reason is not a missing feature.** Every question a seller asks has an answer somewhere in the product: *which accounts* (list), *why this one* (brief), *prove it* (evidence), *what to check* (validation), *I'm working it* (workflow). **The answers exist and the path between them costs too much.**

That is a different and much better problem than the one three reviews ago, when the answers themselves were missing.

---

## The staff-designer pass — interaction quality

**How many clicks?** **Two per account, plus a scroll-hunt.** One of the two is pure overhead.

**What receives visual emphasis?** On the brief: everything equally — six sections of identical weight, **four reviews running.** On the list: the account name, correctly.

**What is attended to first?** The brief's account name, then the action row. *The AE reads the action row before the score* — noted in Review 4 and unchanged.

**What is ignored?** The posture split, the reading validity line, and — newly — the back link, because it is at the top and the reader finishes at the bottom.

**What deserves animation?** **Almost nothing, and one thing genuinely does**: moving between accounts. A transition that shows direction is what makes a sequence feel like a sequence rather than a page load. *Recorded; not built in this slice, because correctness of the sequence comes first.*

**What deserves progressive disclosure?** Already correct — the limitations disclosure, the evidence drawer.

**What deserves summarisation?** Nothing on the brief. Every section is already the shortest true version.

**What deserves comparison?** *"Opened at 35, +15 since"* is the only comparison in the product and it is the AE's favourite line. **A second one — this account against the rest of the book — is a real idea and needs a seller.**

**What deserves storytelling?** The list row already reads as a sentence. **The brief does not** — it reads as six panels. That is the hierarchy finding, now four reviews old and increasingly the largest thing left.

**Apple.** The brief's six equal-weight sections. *Fourth review.*

**Stripe.** A decision is recorded and nothing confirms it beyond a changed line. **R10-02.**

**Linear.** *Third review asking.* No keyboard path anywhere. **This slice adds one where it pays most.**

**Notion.** Each screen reads well; **the document ends without a next page.**

**Cursor.** *"Where does the product stop helping?"* — **at the bottom of the brief.** Everything above it is excellent and there is nothing below it.

**Perplexity.** Ledger citations resolve; narration citations do not. **R10-04.**

**OpenAI.** Still unstated: the daily surface is entirely model-free. *Fifth review.*

---

# Review 11 — the citation that opens, and the vision audit around it *(M12.3, 2026-08-01)*

Two things happened in this pass: the **Vision & Roadmap Consistency Review** (recorded in [PRODUCT_ROADMAP.md](../../PRODUCT_ROADMAP.md), not repeated here) and the slice it did *not* change — **D42**, resolving narration citations.

**The review deliberately did not redirect the slice.** It found the largest gaps in the product's *entrance* — no ICP, no target account selection, no customer-authored configuration — and every one of them is either an architectural decision or a milestone of its own. Redirecting M12.3's last slice into them would have been the exact anti-pattern §20d names: building ahead to satisfy a finding the current milestone does not own.

## R11-01 · Nine of twenty lifecycle stages are implemented, and five more are built and unreachable 🔴

**Observation.** Reconstructed the full customer lifecycle and checked each stage against the repository rather than the roadmap. Implemented: workspace creation, graph, events, signals, scores, opportunities, workflow. **Built and unreachable:** AI reasoning (no released model), AI research (no entry point), the signal relevance profile (no endpoint, no screen), outcomes (recorded, unconsumed), invitations (a weaker capability wearing the name).

**Why it matters.** **The pipeline is not the risk.** Everything between "companies exist" and "a seller decides" works and is defensible. What is missing is the customer's own half — *who are we, what do we sell, who do we watch* — and it is missing so completely that no module owns it.

**Priority:** High. **Milestone:** recommendation 1 of the Consistency Review. **Raised, not fixed.**

---

## R11-02 · Three capabilities entered the roadmap through a demo scenario and never through a scope entry 🟠

**Observation.** *"Add a target account list"* (M2.1) · *"invite a colleague"* (M1) · business screens *"from M2 onward"* (already corrected 2026-07-31). Each was written as a demonstration step; none had a corresponding scope line; nothing afterwards reconciled the two.

**Why it matters.** **A Demo Checklist is a promise, and the roadmap has been reading it as prose.** It is also the mechanism by which a capability can be simultaneously "in the roadmap" and unscheduled — which is precisely how ICP disappeared without anyone deciding to drop it.

**Fixed here:** both demo scenarios corrected in place, dated rather than rewritten. **The rule that follows:** a capability named in a Demo Checklist and absent from that milestone's Scope is a roadmap defect, checked at the milestone boundary.

---

## R11-03 · Two documents made provider configuration a customer responsibility 🟠 **FIXED**

**Observation.** `04-modules.md` recorded Provider Platform as owning *"which providers are enabled **per workspace/plan**"*, and `37-product-surface.md` stated outright that *"provider precedence is a **customer** policy — the same category as the scoring model."*

**Why it matters.** The second is the dangerous one: it did not merely permit a customer-facing provider control, it **classified one as belonging to the same category as the scoring model**, which is genuinely customer-authored. A future milestone reading that sentence would have built a provider-precedence screen and been right to.

**Both corrected**, with the distinction written down permanently: *a company-intelligence provider is Signora's supplier; a CRM is the customer's system.* The customer-facing half survives — **disagreement is shown, never hidden** — because that is evidence, not configuration.

---

## R11-04 · A citation that resolves to another of Signora's own summaries is not a citation 🟢 **Design corrected before building**

**Observation.** R10-04 framed the gap as *"three resolvers do not exist"*. Building them would have closed the finding and been wrong: all three cited kinds — `opportunity`, `buying_score`, `signal_contribution` — are things **Signora wrote**, and the evidence drawer had already ruled that *"a citation has to end at [provider readings] rather than at another summary."*

**What the citation actually addresses** is the `EvidenceFact` the model was given — a summary and typed attributes, which are not stored but are **reproducible**, because `assemble()` is a pure function written so the seeder and the runtime produce byte-identical evidence.

**Why it matters.** It turned a three-endpoint slice into a no-new-endpoint one, **and produced a better product**: a reader now sees the prompt's own content rather than a record fetched afterwards. *The strongest possible form of "here is what it was told."*

---

## R11-05 · Re-deriving evidence without checking the digest would have been a quiet lie 🔴 **Prevented**

**Observation.** Re-deriving the evidence set and presenting it as *"what this sentence rests on"* shows **today's** facts. The narration was grounded against the set as it stood when it was written. Those differ the moment anything about the account moves.

**Why it matters.** It is the exact failure this codebase is built to refuse — a screen stating something subtly untrue, confidently, with no way for a reader to tell. `ai_narration.evidence_digest` has been stored since M8 and **read by nothing**; comparing against it is what makes the whole slice honest.

**And it is the better half of the feature.** A customer can now see *whether an explanation still stands*. `evidence_state` already answers that for the score; nothing answered it for the narration, which carried only a date.

---

## R11-06 · The attributes are engineering's words, and they stay that way 🟡

**Observation.** Run against real Playground data, a resolved fact reads `contested false · delta 0 · ceiling 120 · value 35`. `contested false` is not how a seller talks.

**Why it matters, and why it is not being fixed.** These are **verbatim what the model was shown**, and the digest covers their textual form. Prettifying `false` into *"No"* would show the reader something different from what was cited — a second vocabulary, and the one place where a second vocabulary would defeat the panel's entire purpose. **The verbatim-ness is the value.**

**Recorded as a deliberate trade-off**, not as debt. If it proves genuinely unreadable in front of a seller, the fix belongs upstream in `explanation.py` — where the *pipeline* chooses its wording — and never in the browser.

**Priority:** Low. **Milestone:** on evidence from a real reviewer.

---

## R11-07 · The narrations in the Playground are one bland sentence each 🟠

**Observation.** Verified end to end against three real accounts. Every citation resolved, `evidence_unchanged` was true, and the facts were genuine. **The narration itself read: *"This account is being tracked."*** — one statement, citing all four facts.

**Why it matters.** The slice works and **cannot be shown at its best**, because the sentence a reviewer would click is not worth clicking. This is D17 again — *the dataset, not the architecture, is the constraint* — now reaching the AI layer: those rows predate `playground@2`, and `make demo-narrate` against the current dataset has not been run since.

**Not a code defect.** The next demo pass should re-run `make demo-narrate` on `playground@2` before this slice is reviewed. **Priority:** Medium, and it is a *demonstration* task rather than an engineering one.

---

# Review 12 — the words the product uses *(M12.3, 2026-08-01)*

Commissioned on the product owner's clarification that **Workspace has always been an internal architectural concept**. The audit read every user-visible string in `app/` and `components/`.

## R12-01 · A password sign-in redirected to a route that has never existed 🔴 **FIXED**

**Observation.** `router.push('/workspaces')`. There is no `app/(app)/workspaces/page.tsx` and there never has been. **Every password sign-in for three slices landed on the not-found page.**

**Why it matters.** It is the first ten seconds of a new customer's life, on the flow ADR-0033 shipped specifically so the product owner could review the product. **1992 backend tests and 316 frontend tests did not catch it** — nothing asserted where a successful sign-in goes.

**And it is the vocabulary finding, not a separate bug.** The code was reasoning about a *tenancy* concept while the product needed a *destination*, and the two drifted apart because the repository has only ever had one word for them. Fixed to `/` — the attention list, a seller's morning (**D38**).

**Now enforced twice:** no route path may name an internal concept, and **every `router.push` must resolve to a page that exists.** The second is the durable one; it would have caught this on the day it shipped.

---

## R12-02 · The product explained its own tenancy model to a salesperson 🔴 **FIXED**

**Observation.** The new-organization dialog read: *"Workspaces are isolated from each other. Data never crosses between them."*

**Why it matters.** Every word is **true**, and it is a correct summary of [11-tenancy.md](11-tenancy.md). It is also a sentence about RLS shown to somebody who wants to add their company. **It answers a question nobody asked and raises one nobody wanted** — a customer who was not worried about data crossing between tenants is now.

**The empty state every new account sees** was the same defect at greater cost: *"A workspace is where your accounts, evidence and decisions live — and it is the boundary Signora keeps every customer's data inside."* Signora's architecture, taught to a seller before they had done anything.

---

## R12-03 · A screen-reader user was the only customer told the internal word 🟠 **FIXED**

**Observation.** `<Select label="Active workspace" labelHidden>` in the application header. Sighted users see the organization's name; the accessible name said *workspace*.

**Why it matters.** **The worst possible place for a leak to survive** — invisible to everyone reviewing the product, and audible only to the customer least able to work around it. The vocabulary test scans `aria-label` for exactly this reason.

---

## R12-04 · "Organization" appears nowhere in the repository 🔴 **The root cause**

**Observation.** Searched every markdown file, ADR, roadmap and source file. **The customer-facing term for a tenant has never been written down.**

**Why it matters, and why it is not a process failure.** Every leaked string was written deliberately, by an engineer who had read the architecture, in a codebase whose constitution has demanded a consistent ubiquitous language since the first commit. **They are what happens when the only vocabulary that is written down is the internal one** — an engineer reaching for the right word finds `Workspace`, correctly, because it is the only word available.

**This is the ICP pattern in a different register**: an intent that lived in discussion, never reached a document, and therefore never reached the build. `CLAUDE.md` §4 governs the language *between engineers* and has always been silent on the language *between the product and its customer*.

**Fixed by [ADR-0034](adr/0034-ubiquitous-language.md)**, which defines both vocabularies — and by the test, because *a guard that cannot fail is documentation pretending to be code*, and a glossary nobody can violate is the same thing.

---

## R12-05 · The test found a leak the audit had missed 🟢

**Observation.** `evidence.tsx` told a customer *"every **business event** should cite what produced it"* — internal pipeline vocabulary in an error message, in a file the manual audit had already read and passed.

**Why it matters.** **It is the argument for the test, made by the test on its first run.** A human reading for *workspace* does not see *business event*; a scan checking a list sees both. It also arrived through the most ordinary route imaginable — an error message, where an engineer naturally reaches for the word the system uses.

---

## R12-06 · Three more capabilities entered through a Demo Scenario 🟠

**Observation.** **Deprioritization intelligence** — a named differentiator, *"nearly free… sitting unclaimed"*, in M5's demo scenario and no milestone's scope. **The RevOps view** — Job 7, in M11's demo scenario, and [37-product-surface.md](37-product-surface.md)'s six journeys are all a seller's. **Invitations** — M1's demo scenario, already recorded.

**Why it matters.** With target-account selection from the first review, that is **four confirmed instances**. It is no longer a coincidence; it is **the dominant way capability leaves this roadmap**. A Demo Checklist is a promise and the roadmap has been reading it as prose.

**The RevOps one is the most commercially serious.** PRODUCT_ROADMAP calls that surface *"the first surface that serves the economic buyer rather than only the end user — which is what makes renewal and expansion conversations possible."* **The buyer who signs the cheque has no screen in the product surface design.**

**Priority:** High. **Raised, not fixed** — both are category-3.

---

# Review 13 — the full UI conformance audit *(QE, 2026-08-21, on `6442122e`)*

> ⚡ **This review exists to close the limitation this document opens with.** 📁 **The preamble above says *"I could not open the browser UI… which gives nothing about pixels: spacing, contrast, weight, rhythm."*** ✅ **This review measured pixels — in a real browser, at thirteen widths, in both themes** — and every figure below is a computed style read from a rendered page, never a class name read from a file.

## What was measured

| | |
|---|---|
| **Routes rendered and measured** | **39** — 15 authenticated · 13 authentication · 8 onboarding · 2 workspace · 1 not-found · 1 record detail |
| **Page renders** | **91** · **0 render errors** |
| **Responsive widths** | **13** — 320 · 360 · 390 · 430 · 600 · 768 · 900 · 1024 · 1100 · 1280 · 1440 · 1600 · 1920 |
| **Screenshots** | **89** |
| **Design documents parsed** | **35 of 35** in [`docs/design-snapshot/screens/`](../design-snapshot/screens/) |
| **Design tokens compared** | **37 roles × 2 themes**, design against implementation, by value |
| **Themes** | **light and dark**, both measured |

## Findings

| | Confirmed | Where |
|---|---|---|
| **P1** | **2** | [B-1050](../BUGS.md#b-1050) dark surface ramp · [B-1053](../BUGS.md#b-1053) non-existent account renders as empty account |
| **P2** | **2** | [B-1051](../BUGS.md#b-1051) five absent token roles · [B-1052](../BUGS.md#b-1052) `Badge` has no border |
| **P3** | **0 confirmed** | ⚠️ **see *what this review did not cover*** — the micro sweep of cards, tables and dialogs is not done |
| **Reopened** | **1** | [B-1046](../BUGS.md#b-1046) — the `Makefile` half was recorded `FIXED` and is not |
| **Design decisions required** | **2** | below |

⛔ **Full detail lives in [`BUGS.md`](../BUGS.md) and is deliberately not restated here** ([§2](../../CLAUDE.md) — *truth has exactly one authoritative representation*).

## R13-01 · The token layer is where the conformance defects are, and both themes had to be measured to see it

**The design's palette is unambiguous, and that had to be established first.** All **35** screen documents carry the same token block: **37 tokens, two themes, zero disagreements between files.** ⚡ **So any divergence is a defect and not an ambiguity** — which is what made the rest of this review answerable.

🔴 **Two defects share one shape: a token that is correct in light and wrong in dark, or the reverse.**

- [B-1050](../BUGS.md#b-1050) — `--color-surface-sunken` resolves to the **canvas colour** in dark. **112 `bg-surface-sunken` consumers**; on `/accounts` the avatar disc, the progress track and the segmented-control tray all render `rgb(13,20,24)` on a `rgb(13,20,24)` page, with `border-width: 0px`.
- [B-1051](../BUGS.md#b-1051) — `--color-accent-soft` **is** the design's `--brand-line` in dark and is `#a0c4de` against a specified `#c8ddee` in light.

⚡ **Neither is visible from the light theme alone, and neither is visible from a class name.** 📁 **[489](489-legacy-ui-standards-audit.md), [498](498-common-platform-audit.md) and [499](499-implementation-design-reconciliation.md) all read source files; [D-217](../DECISION_REGISTER.md) measured nine colour roles and pronounced the colour layer exact.** ⛔ **It is exact for those nine, in light.**

## R13-02 · A screen that never asks whether its record exists

[B-1053](../BUGS.md#b-1053). **20 API calls on the Account 360 page and not one fetches the account.** ⚡ **The evidence is already on the page** — four sub-resources `404`, and the account list that *was* fetched does not contain the id — **and the header renders a name derived from the URL instead.**

✅ **The product already has the right voice**: `/no-such-route-xyz` renders *"That address does not lead anywhere — Nothing in Signora sits at this link. It may have moved, or it may never have existed."*

## R13-03 · What the audit checked and found correct — recorded, because four candidate findings died here

⛔ **A conformance audit that reports only divergences overstates itself.** **These were measured and are right:**

| Checked | Result |
|---|---|
| **Horizontal overflow, 39 routes × 13 widths** | ✅ **zero**, at every width including 320 |
| **Navigation rail width** | ✅ **232px expanded, 56px collapsed** — the App Shell's values exactly |
| **Content width cap** | ✅ **exactly 1600px at a 1920 viewport** |
| **Responsive regimes** | ✅ off-canvas below 1024 · collapsed 1024–1279 · expanded from 1280 |
| **Top bar height** | ✅ **56px**, matching 13 designs that draw it |
| **`text-title`** | ✅ **26px / 700 / 1.15 / −0.026em** — §04's `Title` role exactly |
| **The `/` greeting at 27px** | ✅ **the Home design specifies 27px / 700 / −0.028em.** ⛔ **Not a defect** |

🔴 **Four candidate findings were discarded after measurement, and the reasons are the useful part:**

1. **"`--bg-rail` is absent"** — an artifact of using **one** screen's token block as the authority when that screen defines 27 of the 37 tokens. ⚡ **Fixed by taking the union of all 35, having first proven they agree.**
2. **"`--line-soft` is absent"** — the `globals.css` parser was **comment-blind**, and a doc comment containing `` `--line-soft: #eae5df` `` swallowed the real declaration. ⛔ **A false absence produced by the instrument, not by the code.**
3. **"The rail is 231px, one short of 232"** — **the measured element was the inner `<nav>`; the rail container is 232px with a 1px border.**
4. **"Content is uncapped past 1600"** — **`main` is 1645px at a 1920 viewport; the capped container inside it is exactly 1600.**

⚡ **All four share one shape: the INSTRUMENT produced the finding, not the code.** **Three measured a narrower thing than the question asked** — one screen instead of thirty-five, the inner `<nav>` instead of the rail, `main` instead of the capped container — **and one was simply a wrong parser.** ⛔ **All four would have shipped as P2/P3 conformance bugs from an audit that did not re-check its own instrument**, and each was disproved by measuring again rather than by doubting the result.

📁 **Neighbouring, not identical, to [B-1000](../BUGS.md#b-1000)** — *a correct diagnostic is produced and the reading discards it.* ⚡ **There the instrument was right and the reading was wrong; here the reading was faithful and the instrument was wrong.** **Same lesson from the opposite side: verify the instrument before believing what it says about the code.**

## Design decisions required — ⛔ not bugs

**D13-A · Does a screen document's raw pixel value override a §04 type role?**
📁 **[C-1414](../LANE_COORDINATION.md) ruled that *§04 is the type authority; §08's raw values are illustrative and are not a second specification*.** ⚡ **That ruling was about §08.** **The Home design specifies its greeting at 27px, the implementation renders 27px, and §04's `Title` role is 26px** — so the same question now arises for **screen** documents, which C-1414 did not reach. ⛔ **Recorded rather than filed: the implementation is faithful to a design document either way, and extending C-1414 is a ruling, not a fix.** ⚠️ **It governs every remaining screen migration, so it is worth answering before them rather than after.**

**D13-B · The expanded rail is 232px in App Shell and 238px in Settings.**
**Two design documents, two values.** ✅ **The implementation renders 232 — App Shell's — which is the defensible reading**, and [499](499-implementation-design-reconciliation.md) already treated 232/56 as the authority. ⛔ **Recorded so the Settings design is not later read as a conformance failure against a screen that is correct.**

## ⚠️ What this review did NOT cover, stated plainly

**The brief asked for a micro sweep of every card field, every table cell, every dialog, drawer, popover, menu and tooltip, plus a full accessibility pass. This review did not reach them.** ⛔ **They are recorded as not-done rather than implied by silence** ([§2](../../CLAUDE.md)).

| Not covered | Why it matters |
|---|---|
| **Card field-level and table cell-level conformance** | The brief's largest single ask. **Requires per-screen design extraction**, which the token work established the method for but did not consume |
| **Dialogs · drawers · popovers · menus · tooltips · command palette · notifications** | **None was opened.** All 39 routes were measured in their default state only |
| **Accessibility** | Only **structural counts** were taken (skip links, landmarks, heading order, `img` without `alt`). ⛔ **No keyboard traversal, no focus-order check, no contrast measurement** — and contrast is where [B-1050](../BUGS.md#b-1050) predicts failures |
| **Screenshot-to-design comparison** | **89 screenshots captured and not yet compared to the design renders** |
| **Data honesty** | ⛔ **Not attempted.** `no-mock-data.test.tsx` covers the static case; the *"producer-backed capability not surfaced"* direction is unexamined |
| **The other 31 design documents, screen by screen** | Token conformance is product-wide and done. **Per-screen structural conformance is done for 0 of 35** |

⚡ **The instrument is built and reusable** — sign-in, storage state, measurement, screenshots — so the remaining sweeps are execution rather than setup.


## R13-04 · The second pass — overlays opened, and Companies taken to the column

⚠️ **Added the same day, after the sections above were written.** ⛔ **The limitations table below is amended rather than rewritten** ([§2](../../CLAUDE.md)).

**Overlays — the surfaces no prior audit had opened.** ✅ **All three conform:**

| Surface | Measured | Design | |
|---|---|---|---|
| **Command palette** (`⌘K`) | `role=dialog` · `aria-modal=true` · **640 × 401.5** · **radius 16px** · labelled *"Search or ask…"* | dialog plane at `--r-xl` **16px** · the design's own label is *"Search or ask…"* | ✅ |
| **Ask Signora** | `<aside>` · **420px** · **radius 16px** · ⛔ **no `role=dialog`** — non-modal | drawer **420px, 16px, non-modal** | ✅ |
| **Shortcuts** | panel opens, **21 shortcuts listed** | keyboard map | ✅ |

🔴 **[499](499-implementation-design-reconciliation.md) recorded `Dialog` at 12px against a 16px design, `Drawer` *"correct, unmounted — 0 importers"*, and the command palette *"built, 0 importers"*.** ✅ **All three are now correct AND mounted.** ⚡ **That matrix is 12 days and 235 frontend commits stale, and this is the measurement that says so.**

⚡ **The Shortcuts panel discloses its own gaps in the product's voice** — ***"12 of these 21 shortcuts work today. The other 9 are part of Signora's published design and nothing binds them, so pressing one does nothing."*** ⛔ **Not a defect. A stated absence**, and the pattern [P-A](../DOMAIN_DISCOVERY_REGISTER.md) exists to reward.

**Companies — the design's own vocabulary tested against the rendered screen.** 67 distinct strings extracted from [`Fortune Signora Companies.dc.html`](../design-snapshot/screens/), the product-facing ones checked against `/accounts`, a row expanded, and all 33 controls enumerated without truncation.

| | |
|---|---|
| **Columns rendered** | `Preview · Company · Segment · Open ACV · Renewal · Owner · Tags` + selection |
| **Columns in the design** | `Company · Segment · Open ACV · Signora score ↑ · Renewal · Owner · Tags` |
| **Difference** | **`Signora score` absent · `Preview` added** |

⛔ **Neither is filed, and the reason is the finding.** ✅ **The screen SAYS SO, unprompted:** ***"A Signora score is not on this list yet. Value, renewal and stage arrive from a connected system — until one is connected they read as not reported, never as zero."*** 📁 **And [TASK-1475](../BACKLOG.md) narrowed its own scope in writing before it was claimed** — `New company`, `Import`, numbered pages and a denominator all **cut, with reasons**, and [C-1431](../LANE_COORDINATION.md) settled the pager as *"a page number and no denominator"*, which is exactly what renders.

⚡ **A naive design-diff would have filed ten bugs here. The correct count is zero**, because every absence is either scoped-out with a recorded reason or disclosed on the screen in the customer's own words.

⚠️ **One thing this pass could NOT verify, stated rather than assumed:** the Playground holds **15 accounts and therefore one page**, so *"Rows 1–15 of 15"* is trivially accurate and **the denominator's behaviour beyond one page is untested.** ⛔ **Not filed — a suspicion is not a finding.**

## R13-05 · Five candidate findings died on inspection, not four

⚠️ **[R13-03](#r13-03--what-the-audit-checked-and-found-correct--recorded-because-four-candidate-findings-died-here) names four. The second pass produced a fifth**, and it is the one most likely to be filed by a future audit:

**5. *"Companies renders raw hex identifiers — `459128fe`, `9061f113` — as company names."*** ⛔ **It is the settled design and it is defended in the code.** 📁 [`entity-name.tsx`](../../frontend/components/intelligence/entity-name.tsx):62 shows **the real identifier** and argues ***"a fabricated name is indistinguishable from a real one"***; 📁 [B-290](../BUGS.md#b-290)'s rule is ***"a name that has not arrived is not a name that does not exist"***; and the row carries `<span class="sr-only"> — no source has named this account yet</span>`. ⚡ **The inconsistency that IS real — four surfaces hand-rolling `'Unnamed account'` against `EntityName`'s identifier — is already recorded as *"a product decision, and not this lane's to take by picking one"*.**

> ⚡ **Five of nine candidates did not survive.** 📁 **The audit's own hit rate is worth recording**: **four confirmed, five discarded**, and every discard was killed by measuring again or by reading the register, never by doubting the instrument in the abstract.

## Amendment to *what this review did NOT cover*

✅ **Now covered:** command palette · the Ask Signora drawer · the Shortcuts panel · Companies at column and control level · one row expansion.

⛔ **Still not covered, unchanged:** **per-screen conformance for 34 of 35 designs** · popovers, menus and tooltips · **keyboard traversal and focus order** · **contrast measurement** — ⚠️ **which [B-1050](../BUGS.md#b-1050) predicts will fail in dark theme and which nothing here has measured** · the 89 screenshots against the design renders · the *producer-backed-but-unsurfaced* direction of data honesty.


## R13-06 · Contrast measured — and it refutes this review's own prediction

⚠️ **[R13-04](#amendment-to-what-this-review-did-not-cover)'s amendment said contrast was unmeasured and that [B-1050](../BUGS.md#b-1050) *"predicts it will fail in dark theme."* ⛔ **Measured, that prediction is wrong, and it is corrected here rather than left standing.**

**203 text nodes across `/home`, `/accounts` and `/settings/team`, both themes, computed foreground against the nearest painted ancestor background:**

| Theme | Below WCAG AA | Distinct failing pairs |
|---|---|---|
| **Light** | **29 of 203** | **5** |
| **Dark** | 🔴 **0 of 203** | **0** |

⚡ **Dark theme passes text contrast completely.** ⛔ **So [B-1050](../BUGS.md#b-1050) must not be argued on text contrast, and this review will not do so.**

📁 **B-1050 is a NON-TEXT contrast failure — WCAG 2.2 SC 1.4.11, which governs UI components and requires 3:1** — and it is not marginal: a sunken surface against the canvas in dark theme is `rgb(13,20,24)` on `rgb(13,20,24)`, **a ratio of exactly 1.00 against a required 3.0**. ⚠️ **A text-contrast instrument cannot see it**, which is precisely why the two measurements are reported separately rather than merged.

## D13-C · The light theme's failing pairs are the DESIGN's pairs — a decision, not a bug

🔴 **Every failing colour is a design token, in a pairing the design itself specifies.** ⛔ **The implementation is faithful. Filing this against Lane A would be the misleading-implementation-bug the brief forbids.**

| Foreground | Background | Ratio | Needs | Where |
|---|---|---|---|---|
| **`--ink-3`** `#857d75` | `--ai-tint` `#f0f1fc` | **3.60** | 4.5 | `⌘⇧A` · 11px/400 |
| **`--ink-3`** `#857d75` | `--sunken` `#f4f1ed` | **3.60** | 4.5 | *Not now* · 14px/400 |
| **`--ink-3`** `#857d75` | `--bg` `#faf8f6` | **3.82** | 4.5 | *"Cannot change your organization's…"* · 14px/400 |
| **`--ink-3`** `#857d75` | `--surface` `#ffffff` | **4.05** | 4.5 | *August 21, 2026* · 12px/500 |
| **`--warn`** `#a5691f` | `--warn-tint` `#fbf2e4` | **4.08** | 4.5 | *New decision maker* · 11px/600 |

⚡ **`--ink-3` is the muted-text role and it fails AA on every surface the design puts it on, including plain white at 4.05.** ⚠️ **It is the third rung of the design's own four-step ink ramp, so this is not a misuse — it is the role working as specified.**

**The decision is the product owner's**, and it is a real one because **accessibility sits in the *Enterprise Ready* milestone** ([§20e](../../CLAUDE.md)'s five milestones) — *"what a buyer asks about"*:

- **Darken `--ink-3`** to reach 4.5:1 on `--bg` and `--surface`, which changes the design; **or**
- **Rule that `--ink-3` is a large-text-and-decoration role only**, and migrate the ~29 small-text sites off it; **or**
- **Accept AA failure for muted text and record it**, which is a defensible commercial position and an indefensible silent one.

⛔ **Not filed as a bug against any lane.** ✅ **Recorded so that the next audit does not file it either, and so the buyer's question has an answer that was decided rather than discovered.**

⚠️ **Scope of this measurement, stated:** three routes, 203 text nodes, **text only.** ⛔ **No focus-visible states, no hover states, no disabled text, no placeholder text, no non-text UI components beyond B-1050**, and no keyboard traversal.


## R13-07 · Account 360, and the first fault-injection pass

**2026-08-21, after a machine restart.** ⚡ **The environment rebuilt in minutes because the traps were written down; the audit resumed at the screen it had named.**

**Design authority: [`Fortune Signora Account 360.dc.html`](../design-snapshot/screens/)** — 110KB, the largest screen document. **128 distinct visible strings extracted; the 34 that name a section or a header control tested against a rendered account.**

| | |
|---|---|
| **Design elements present** | **13 of 34** — Account score · Customer health · Buying intent · Signals timeline · Research summary · Open opportunities · Contacts · Organisation chart · Relationship graph · Technology stack · Market signals · Meetings · *On this page* |
| **Absent** | **21** — Competitors · Battlecards · Win rate · Recent activity · Tasks · Emails · Files · Notes · Custom fields · Historical timeline · Integrations & billing · Risk indicators · Recommendations · AI reasoning · Log activity · Book meeting · Brief me · Owner · Show reasoning · Confidence · Open all evidence |

⛔ **None of the 21 is filed.** ⚠️ **A count is not a finding**: the sections the product has not built say so in the customer's own voice — *"An organisation chart is inferred from email, calendar and public sources. **Signora is not reading any of those yet**"* — and the reads behind the rest return **empty**, not wrong. 📁 **The gap is scope, and scope belongs to [`BACKLOG.md`](../BACKLOG.md), not to this register.**

### The method that was new: induce the failure

📁 **The design document specifies section states explicitly — Normal · Loading · **Error** (*"Contacts could not load"* · *Retry* · *Ask what changed* · `req_2b71-40cd`) · Empty · Collapsed · Focus mode.** ⚡ **An error state cannot be audited by looking at a healthy page**, so seven account reads were intercepted in turn and fulfilled with `500`, and each section was compared **healthy against failed on one tree**.

| Forced failure | What renders | |
|---|---|---|
| **`…/score`** | The **page-level** *"Could not load this account"* — every section withdraws | ✅ **correct**, and it is the behaviour [B-207](../BUGS.md#b-207)'s withdrawal vindicated |
| **`…/observations`** | ✅ *"Signora could not load what changed at this account. **Nothing has changed about the account** — reload to try again."* — 🔴 **above it, the count renders `0` where healthy renders `21`** | ⛔ **[B-1054](../BUGS.md#b-1054)** |
| **`…/opportunity`** · **`…/buying-committee`** · **`…/competitors`** | unchanged — ⚡ **these return `[]` on this account, so a forced failure loses nothing and proves nothing** | ⚠️ **inconclusive, and recorded as such rather than as a pass** |
| **Contacts · Org chart · Relationship graph** | unchanged — **capability copy that does not consume the read** | ✅ **correct** |

⚡ **[B-1054](../BUGS.md#b-1054) is the whole yield, and it is a good one**: the prose is exemplary — it names the failure *and* removes the inference a reader would otherwise draw — **and the count beside the heading contradicts it with a number nobody measured.** 📁 **[P-A](../DOMAIN_DISCOVERY_REGISTER.md)'s quietest form: `0` rendered as a fact, in the line a scanner reads first.**

### A sixth candidate died, and this one nearly shipped

🔴 **The first sweep reported `observations`, `opportunity`, `buying-committee` and `account-identities` as having NO error state.** ⛔ **Wrong — the instrument waited 1500ms and read the pre-error render.** ✅ **Re-run with a healthy/failed pair on one tree, `observations` has an exemplary error state and the real defect is one badge.**

⚠️ **Filed as written, that sweep would have been a 🔴 P1 against four sections that are mostly correct.** 📁 **Six of ten candidates in this audit have now died on re-measurement**, every one of them an instrument fault rather than a product fault — **which is the ratio worth remembering the next time a sweep looks conclusive.**

### Amendment to coverage

✅ **Now covered:** Account 360 at section level · the first fault-injection pass across seven reads · per-section error states.
⛔ **Still not covered:** **33 of 35 designs** · popovers, menus, tooltips · keyboard traversal and focus order · the loading and collapsed/focus-mode states the design also specifies · screenshots against the design renders.


## R13-08 · The micro pass — five more findings, and the row this audit had to correct against itself

**2026-08-21, continued.** ⚡ **Four surfaces the audit had named as uncovered were taken: Signal Center, the Loading state, keyboard focus, and per-screen coverage across seven shipped screens.**

| | Finding | |
|---|---|---|
| **[B-1055](../BUGS.md#b-1055)** 🟠 | **The tab pattern is incomplete product-wide.** On `/signals`: **6 `role="tab"` across 2 tablists, 0 with `aria-controls`, and ZERO `role="tabpanel"` in the document.** [`tabs.tsx`](../../frontend/components/ui/tabs.tsx) is the source and has three importers | a11y |
| **[B-1056](../BUGS.md#b-1056)** 🟡 | **`/signals` and `/profile/security` render 20px/600 headings with no verdict** in [TASK-1446](../BACKLOG.md)'s adoption sweep — whose deliverable was *"a verdict each"* for eleven screens and which published nine | conformance |
| **[B-1057](../BUGS.md#b-1057)** 🟡 | **A loading state is visual only.** Skeletons are correctly `aria-hidden` and **nothing replaces them**: `aria-busy` nowhere, both live regions empty, no *loading* word. **WCAG 2.2 SC 4.1.3** | a11y |
| **[B-1058](../BUGS.md#b-1058)** 🟡 | **Four focus indicators on one screen, one of them the design's.** The design draws focus **21 times** as `0 0 0 3px var(--brand-tint)`; the product renders that ring, a 2px solid accent outline, a ring with white offset, and a link outline | conformance |
| **[C-113](../LANE_COORDINATION.md)** | **`/settings/connections` is the one shipped screen of seven with no row owning its finalized design.** Raised for Product Office; ⛔ **not a defect and not QE's scope to propose** | coverage |

### The correction this audit made against its own filed row

🔴 **[B-1050](../BUGS.md#b-1050) was filed with overstated visual evidence, and QE found it rather than Lane A.**

⛔ **The original claim named the avatar disc, a progress track and the segmented-control tray and said all three vanish in dark theme.** ⚠️ **It compared each element's fill to `document.body`'s background — the PAGE colour — instead of to the element's own painted backdrop.** ⚡ **Measured properly, the avatar disc sits on `rgb(21,32,39)`, a card, and is perfectly visible.**

**Found by generalising rather than by doubting**: a sweep of nine routes in dark for surfaces with no fill contrast, no border and no shadow returned **one class on two routes** — far less than the row implied — **so the row was re-measured instead of the sweep.**

✅ **What survives, and it is the half that matters**: the token values disagree with a design **all 35 screens state identically**, the ramp is shifted by one, and `--bg-rail`'s dark value exists nowhere. ⛔ **That is provable without any claim about what a customer sees.** ✅ **And one rendered consequence survives measurement against its true backdrop — the loading skeleton, `1117×64`, self `rgb(13,20,24)` == backdrop `rgb(13,20,24)`, no border, no shadow.**

**The row's title, severity and evidence were corrected in place and the mistake recorded in it** — 📁 **[§2](../../CLAUDE.md): correct a claim about the present, and do not quietly replace the wrong evidence.**

### The instrument count, which is now the more useful number

> **Sixteen candidates examined across this audit. Nine confirmed. Eight died on re-measurement — and the eighth was a row already filed.**

**The four new ones this pass:** `/settings/products` reported as having **no `h1`** (a render race — it has one, three runs out of three) · `/accounts` reported as having **no loading skeleton** (its list is server-rendered, so none is owed — `held=0` proved the delay never applied) · the utility panel's icon tabs reported as **nameless** (they carry `aria-label`; `textContent` does not see it) · and **B-1050's own evidence**.

⚡ **Every one was an instrument fault, not a product fault.** ⛔ **Filed as written, three of the four would have been P1s against behaviour that is correct.**

### What was verified correct and is deliberately NOT filed

✅ **Signal Center's error handling** — a `500` on `/triage` or `/signal-catalog` renders *"The queue could not be loaded — Signora could not reach the signal service"* and the tabs **withdraw entirely rather than showing zeros**, which is strictly better than [B-1054](../BUGS.md#b-1054)'s section. ✅ **Its counts reconcile** — the tab reads 13 and the seven type groups sum to 13. ✅ **Keyboard traversal** — 28 stops on each of three routes, **every one reachable and visibly focused, no trap, no skipped control**, skip links first. ✅ **Skeleton shape** — `/signals` and `/home` render skeletons of the loaded shape, which is the design's *"Same shape"* rule.

### Amendment to coverage

✅ **Now covered:** Signal Center · the Loading state · keyboard focus and traversal · per-screen string coverage for seven shipped screens · a dark-theme invisible-surface sweep across nine routes.
⛔ **Still not covered:** **popovers, menus and tooltips** · the **collapsed and focus-mode** states · screenshots against the design renders · the *producer-backed-but-unsurfaced* direction of data honesty · **28 of 35 designs at element level**.


## R13-09 · Overlays, tooltips and the responsive regimes — one finding, and the shell is correct to the pixel

**2026-08-21, continued.** ⚡ **The three surfaces this audit had listed as never-opened were taken: menus and popovers, tooltips, and the App Shell's per-regime specifications.**

### The one finding

**[B-1059](../BUGS.md#b-1059)** 🟢 — **`account-menu.tsx`:164 uses `rounded-md` and renders 280×352 at 8px**, where Design System v2 §05 assigns menus **12px** (`--r-lg`) and gives 8px to *button, input, select, nav item*. ⚡ **Four of the five overlay containers in the product already measure 12px**, so it is one line and **the last instance of the class [499 §1](499-implementation-design-reconciliation.md) found in `Dialog` and [TASK-1453](../BACKLOG.md) fixed.**

### The App Shell's regime table, measured number by number

📁 **The design states four regimes with explicit widths. Every one was rendered and measured, with the utility panel opened by its documented `⌘.`:**

| Regime | Design | Rail | Utility panel | |
|---|---|---|---|---|
| **Desktop** ≥1600 | rail 232 · panel 360, both open | **232** | **360** | ✅ |
| **Laptop** 1280–1599 | rail 232 · panel 300 | **232** | **300** | ✅ |
| **Small laptop** 1024–1279 | rail 56 icons + tooltips · panel → 28px tab rail | **56** | **28** | ✅ |
| **Tablet & phone** <1024 | rail becomes a sheet · tables become row cards | **off-canvas at `x=-232`** | absent | ✅ |

✅ **Content overlap is `0px` at every width** — the design's *"the content narrows and does not overlap"*, measured as geometry rather than trusted. ✅ **A `role="tabpanel"` exists whenever the panel is open** at all four widths.

> ⚡ **This is the most exact conformance result in the audit.** **Seven numbers from a design document, seven matches, measured in a browser.**

### Two candidates died here, and both were the instrument aiming at the wrong thing

🔴 **"The utility panel never docks — it is 28px at every width."** ⛔ **The CONCLUSION was wrong.** **[TASK-1433](../BACKLOG.md)'s DoD says *"the panel docks at 300px, `⌘.` toggles it"* — the toggle is a keyboard shortcut and I had been clicking the tab.** ✅ **Pressing `⌘.` docks it to 300/360 with a tabpanel, and toggles it back.**

> ### 🔴 CORRECTED 2026-08-21 — and this one is a FALSE NEGATIVE, which is a class this review had not been counting
>
> ⛔ **The observation underneath that dismissed candidate was TRUE and I discarded it.** 📁 **My own log**: `viewport 1920: panel before=28px tabFound=1 after={"w":28, "tabpanels":0}` — **I clicked the *Insights* tab, watched nothing happen, and moved on because `⌘.` worked.**
>
> 🔴 **Lane A treated the same behaviour as a defect and were right.** ⚡ **A visible 24px control that does nothing when clicked is broken whether or not a keyboard shortcut exists** — and their diagnosis is one layer below anything I measured: **`onTab` only changed an invisible selection, so the click had never done anything a person could see.**
>
> ⚠️ **I let a working alternative excuse a broken control.** ⛔ **"The documented path works" is not a reason to discard an observation; it is a reason to ask why the undocumented one does not.**
>
> ### What this changes about this review's own tally
>
> **Every figure published so far counts FALSE POSITIVES only** — candidates raised and killed. ⛔ **It says nothing about what was measured and wrongly dismissed**, and that is the more dangerous direction: **a false positive costs a lane an argument; a false negative ships.**
>
> 📁 **Known false negatives to date: one, this one, found by Lane A rather than by QE.** ⚠️ **That count is almost certainly not the true one** — **an audit cannot measure its own misses**, which is precisely why the second reader mattered here and why the tally should be quoted with this caveat attached.

🔴 **"No tooltips anywhere — the shared `Tooltip` has one importer."** ⛔ **Wrong, and it would have been a plausible P2.** 📁 **The App Shell asks for tooltips on the COLLAPSED rail specifically** — *"Collapsed items expose their label as an accessible name and a 300ms tooltip"* — **and I had hovered top-bar controls at a width where the rail is expanded.** ✅ **At 1100 the 55px rail shows a `role="tooltip"` reading *Home* after ≈375ms with `aria-label="Home"` on the anchor; at 1440 the expanded rail correctly shows none.** ⚠️ **375 against a 300ms specification is inside this instrument's 100ms sampling granularity and is NOT reported as a discrepancy.**

⚡ **Both were caught the same way: by asking what the design actually specifies, and by reading the promoted row before writing one.**

### Also verified and not filed

✅ **Every overlay closes on `Escape`** and returns the document to zero overlays — workspace menu, notifications, account menu. ✅ **Workspace menu 340×131 @12px · notifications 400×166 @12px · system status and offline status @12px** — all matching §05. ✅ **The notifications popover is `role="dialog"`**, defensible for a panel carrying its own actions. ✅ **Below 1024 the table is gone** — `tables=0`, consistent with *"tables become row cards"*.

⚠️ **[B-1055](../BUGS.md#b-1055) is sharpened rather than changed by this pass**: with the panel open `tabpanels=1`; collapsed, `tabpanels=0` **while the tabs remain in the tree**, which is exactly what that row reports.

### Amendment to coverage

✅ **Now covered:** menus · popovers · tooltips · the four responsive regimes at their stated widths · the utility panel's docked widths and overlap.
⛔ **Still not covered:** **the collapsed and focus-mode section states** on Account 360 · screenshots against the design renders · the *producer-backed-but-unsurfaced* direction of data honesty · **28 of 35 designs at element level**.


## R13-10 · The failure mode has a name in this register, and I cited it while committing it

**2026-08-21.** ⚡ **Lane A's sharpening of [R13-09](#r13-09--account-360-and-the-first-fault-injection-pass)'s false negative is worth more than the row it corrects.**

> ⛔ **The problem was not that I failed to measure. My log holds the complete record of the defect:**
>
> ```
> viewport 1920: panel before=28px  tabFound=1  after={"w":28, "tabpanels":0}
> ```
>
> ⚡ **The instrument was right and the reading was wrong.**

🔴 **That is [B-1000](../BUGS.md#b-1000) — *"a correct diagnostic is produced and the reading discards it"* — the register's own named class.** ⛔ **And this review cited B-1000 four times while doing it**, each time to describe the *opposite* direction: *"there the instrument was right and the reading was wrong; here the reading was faithful and the instrument was wrong."* ⚠️ **Both directions were in play and only one was being counted.**

⚡ **Lane A also declined the flattering version of their own catch, and it is the more accurate account**: they did not find it by being more careful. **[B-1055](../BUGS.md#b-1055) sent them to read `onTab` to add a roving `tabindex`, and the call site was two lines away.** ⛔ **The wrong inference was simply unavailable to them.** 📁 **A row routed a reader to the right file; that is the mechanism, not diligence.**

### The practice this produces, and it was run rather than proposed

⛔ **A tally cannot see a miss, so noting the caveat changes nothing on its own.** ✅ **What can be done is re-reading the captured evidence with the conclusions removed** — the raw measurements, asked fresh questions, without the narrative that dismissed them.

**Run across all 14 shell routes at 1440, asking only structural questions this audit had captured and never analysed:**

| Checked | Result |
|---|---|
| Exactly one `<h1>` | ✅ **14/14** |
| First heading in the document is `h1` | ✅ **14/14** |
| Duplicate headings at the same level | ✅ **0** |
| Skipped heading levels (`h2 → h4`) | ✅ **0** |
| `<img>` without `alt` | ✅ **0** |
| Buttons with no accessible name | ✅ **0** |
| Links with no accessible name | ✅ **0** |

⚡ **The re-read produced NO new finding, and that is reported as the result rather than hunted past.** 📁 **It also resolved one thing this audit had noticed and passed over**: `/settings/products` appeared to render two `<h2>Ideal customer</h2>`. ✅ **Filtering to *visible* headings shows one — the second is a hidden responsive variant.** ⛔ **Not a defect, and the earlier observation was an artifact of counting the DOM rather than the page.**

### What still is not measured

⚠️ **Known false negatives: one, found by Lane A rather than by QE.** ⛔ **That is not the true count and cannot be**, because **an audit cannot measure its own misses.** ⚡ **The second reader is the only instrument that found one all day**, which is the argument for the exchange rather than for either party's method.

📁 **Lane A adopted the same caveat for their own work, unprompted**: *"'compared, clean' from me means 'I looked and did not see', not 'there is nothing there'"* — ⚠️ **and noted that two of their ten findings sat inside areas they had already reported as compared.**


## R13-11 · A defect no screenshot could ever have shown — the limit of this review's own instrument

**2026-08-21. Raised by Lane A, verified here independently.**

⚡ **Review 13's premise is that prior audits read source files and this one measures rendered pixels.** ⛔ **That premise has a limit, and one of the audit's own findings sits outside it.**

📁 **Measured across all 35 design documents:**

| | |
|---|---|
| Colour roles declared | **33** |
| Roles **declared and used zero times** | 🔴 **2** — `--brand-strong` (2/35 documents) and `--c4` (2/35), **`var()` uses: 0** |

🔴 **`--brand-strong` is the role whose dark value `--color-accent-hover` was holding wrongly** ([B-1051](../BUGS.md#b-1051)'s second half). ⛔ **No screenshot comparison could ever have found it. Nothing in the corpus DRAWS with that role, so there is no rendered thing to compare against.**

> ⚡ **Only a value-against-design check, in both themes, reaches it** — **which is exactly what [B-1050](../BUGS.md#b-1050)'s acceptance criterion asked for, and which this review had been treating as belt-and-braces.** ⛔ **For that role it is not a second opinion. It is the only instrument.**

**So the instruments are not ranked; they have different reach:**

| Instrument | Reaches | Blind to |
|---|---|---|
| **Rendered measurement** — this review's premise | Anything drawn: [B-1050](../BUGS.md#b-1050)'s skeleton, [B-1054](../BUGS.md#b-1054)'s count, [B-1058](../BUGS.md#b-1058)'s four treatments | **A role nothing draws with** |
| **Value-against-design** | Every declared role, both themes | Whether the value is applied to the right thing |
| **Source reading** — 478, 489, 498, 499 | Structure and adoption | Values that are correct in one theme and wrong in the other |

⚠️ **Lane A's own re-read is the corroboration and it produced a clean result**: *"for EVERY colour role the design publishes, is its value carried by some implementation token, in both themes?"* — **33 roles, both themes, no new finding**, reported as the result rather than hunted past.

⛔ **And their first version of that check was wrong**: a reverse value→token lookup, where several implementation tokens share a value and the map silently kept the last one inserted. **It printed 8 confident orphans, all collisions.** ⚡ **[B-1000](../BUGS.md#b-1000) in the other direction, built in two minutes** — which is the rate at which this class appears when anybody writes a new instrument.

✅ **Not filed, and correctly**: a role the design declares and does not use is **a fact about the design corpus, not a defect in the product**, and the guard covers it either way.

### One claim withdrawn

⛔ **[R13-10](#r13-10--the-failure-mode-has-a-name-in-this-register-and-i-cited-it-while-committing-it) said a row *"routed a reader to the right file"* and offered it as an argument for file-level specificity.** ⚠️ **Lane A qualified their own credit and they are right: [B-1055](../BUGS.md#b-1055) named `tabs.tsx` and `utility-panel.tsx:394` for CITATION, and the routing was a side effect.** ✅ **Still an argument for naming files; a weaker one than *"it works"*.**

