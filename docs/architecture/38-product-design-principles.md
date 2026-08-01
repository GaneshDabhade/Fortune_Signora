# 38 — Product Design Principles, and the observations M12.1 deferred

> Created 2026-07-31 during M12.1. **A `PRODUCT_DESIGN_CONSTITUTION.md` was referenced but does not exist in this repository** — I checked both that name and `38-product-design-principles.md`, and neither was present. This document is started here so the design observations the milestone produced have somewhere to live, and so the next screen inherits a stated position rather than re-deriving one. It records the principles as they were given, not as I invented them.

> **Superseded 2026-07-31 by the Signora Product Constitution v2.0.** The principles below were the M12.1 working set; the Constitution ratifies them and settles three questions this document had left open. Recorded rather than rewritten, because the sequence is the record.
>
> **The three rulings, and what changed:**
>
> 1. **The purpose is not to eliminate uncertainty** — it is to make uncertainty visible, understandable, quantifiable, explainable and actionable. *"Pretending certainty where none exists destroys trust."* This is what the architecture already believed: contested scores are never averaged away, dissent is preserved, `evidence_state` is derived on every read, and a disputed name says so.
> 2. **Progressive disclosure is mandatory, and reasoning must be *reachable* rather than always visible.** Summary → reasoning → evidence → raw observations → provider details, each one interaction apart. This resolves the tension between *"never hide reasoning"* and *"reduce cognitive load"*, which as separately stated would have produced opposite screens.
> 3. **Deterministic truth outranks generated opinion.** *"If the answer can be derived deterministically, never ask AI to invent it."* AI is used only where reasoning genuinely adds value.

## The principles this milestone worked to

Stated by the product owner at M12.1 and applied to every decision below:

1. **Reduce uncertainty.** A screen that leaves a seller unsure what they are looking at has failed, however complete it is.
2. **Increase confidence.** They should be able to act without checking somewhere else first.
3. **Reduce cognitive load.** Fewer things to read, ordered so most are never read.
4. **Workflow, not dashboard.** A dashboard reports on a period; a workflow surface answers a question someone is about to act on.
5. **Tell the account's story.** Not a leaderboard of numbers.
6. **Prefer deterministic information to AI.** Where the pipeline already knows something, do not ask a model to say it.
7. **Respect progressive disclosure.** Detail on demand, never by default.
8. **Lead to the next action.** A screen that ends in a full stop is a report.

### One principle this milestone added

**The daily surface is entirely deterministic.**

Everything on the attention list — score, movement, reason, evidence state — is computed by the pipeline from recorded facts. No model wrote any of it, and that is a deliberate product position rather than a limitation of what shipped: **the screen a person opens every morning should be the one they never have to second-guess.** AI belongs on the account brief, where each claim can be read beside the evidence it cites and checked (§J3). Putting a generated sentence on the morning list would make the one habitual screen the one with the lowest defensibility.

---

## Observations deferred from M12.1

Each was discovered while building the attention list, each is better than what shipped, and none was implemented — recorded here instead, per the milestone's own discipline.

### D1 — "Attention" is the right noun; the navigation says "Opportunities"

**Why better.** *Opportunities* is CRM vocabulary for a record. The screen answers *"what deserves my attention today"*, and naming it for the record rather than the question is the dashboard framing the product is trying to leave behind. It also collides with Signora's own domain language, where an Opportunity is specifically the **workflow object a human commits to** — most rows on this list are not that yet.

**Principle.** 4 (workflow, not dashboard) and 3 (cognitive load).

**Why deferred.** The application shell, navigation and routing are frozen (CLAUDE.md §20c) and the information architecture was settled deliberately at M1.5 *"so the shell's IA is settled before pages are written into it, rather than growing one link at a time."* I renamed the label while building, noticed it was a foundation change, and reverted it. **A rename belongs to a deliberate IA revision, not to the first page that happens to disagree with it.**

### D2 — Rows are named by a truncated identifier, which is close to unusable

**The most serious gap in what shipped.** A row currently reads `6b8efd21` where a company name belongs. A seller cannot triage a list of identifiers.

**Why deferred.** No module in the ratified dependency graph can reach both workflow and entity names: `Opportunity Engine → Buying Score Engine` only, and `Revenue Intelligence Platform` reaches Opportunity Engine, AI Reasoning, Recommendation and Timeline — never the Knowledge Graph (05-module-dependencies.md). The resolution needs a Knowledge Graph endpoint the frontend composes with, which is **the first thing M12.2 does** (37-product-surface.md).

**Why a placeholder was not used.** A fabricated name would have been mock business data, which `no-mock-data.test.tsx` forbids and which teaches a reader the wrong model. Showing the real identifier is worse to look at and honest about what the system currently knows.

### D3 — The screen does not lead to a next action

**Why better.** Principle 8. A seller reads the list, decides, and then has nowhere to go — the row should open the account brief.

**Why deferred.** The brief is M12.2. Building a destination now would be implementing a later milestone's functionality to make this one demonstrate better (CLAUDE.md §20d), and a link to a page that does not exist is worse than no link. **Rows become links in M12.2, in the same change that gives them somewhere to land.**

### D4 — There are no sort or filter controls, and a client-side one would have lied

J1 as originally framed included *"sort and filter"*.

**Why deferred, and this one is a correctness argument rather than a scheduling one.** The endpoint returns one ranked page. A sort control in the browser would reorder **only the rows already loaded**, presenting the top of one page as the top of the whole list. That is not a limitation to work around — it is a wrong answer rendered confidently, which is the failure mode this product exists to avoid. Sorting and filtering must happen server-side over the whole set, as query parameters with their own tests.

### D5 — *"What changed overnight"* is answered per-row, not per-session

The list shows each account's score movement, which is the honest version of the question. **The better version — *what changed since you last looked* — needs stored read-state per user**, and therefore a schema change, which M12.1 explicitly excludes.

**Trigger to revisit:** a design partner reporting that they cannot tell what is new. Not before; a "last seen" marker nobody asked for is a table to maintain forever.

### D6 — Grouping by reason may beat ranking once lists are long

At fifty accounts, *"New evidence: 3 · Score moved: 12 · Cooling: 5"* may reduce load more than a flat ranking, because a seller triages by kind before severity.

**Why deferred.** The golden set produces **two** accounts, and 28-ai-platform.md already records "variety 1" as the main caveat on the evidence available. Designing a grouping affordance against two rows would be designing for an imagined list. **Trigger:** a workspace with enough accounts that the ranked list stops fitting on one screen.

---

## Decisions taken in M12.1, recorded so the next screen inherits them

- **The score is typographic, never a gauge.** A filled ring implies a maximum that means something; the score is an ordering of attention, not a probability, and a test asserts no `progress`, `meter` or `%` reaches the screen.
- **Badges appear only when they carry information.** "Evidence current" is not shown, because a badge on every row saying everything is fine trains people to stop reading badges — including the one that matters.
- **A contested account is marked, never warned about.** The Buying Score Engine refuses to average opposing readings away because a fought-over account warrants *more* attention; wording implying doubt would invert the meaning the pipeline computed. Asserted by test.
- **Five triggers get five distinct sentences.** A translation, never a paraphrase: a seller reading *"new evidence arrived"* must be able to find the `signal_generated` behind it. Blurring two into one friendly phrase makes the reason uncheckable.
- **Absence is rendered as absence.** A stale account shows no score rather than a zero — zero is a reading, and it would rank a stale account as actively uninteresting.
- **Business vocabulary lives in `components/intelligence/`, not `components/ui`.** A design system that knew what a buying score was would have started learning the pipeline's language. These compose *from* the design system and add the one thing it must not have: an opinion about what a score means.


---

## M12.2 — Account Identity

### The finding that shaped it

**An account has no name.** `Entity` is an identity and carries no attribute values, because *"a `name` column here would be truth-resolution in miniature, and it would immediately disagree with the claims underneath it."* A company's name is `LEGAL_NAME`: a claim, from a provider, at a time — and providers can disagree.

So *"do not think entity endpoint, think Account Identity"* was righter than it looked. **Naming an account is a truth-resolution the Knowledge Graph deliberately declined to make**, and the identity layer is where it gets made — once, visibly, and without discarding the disagreement.

### The UX decision this produces

**Disagreement is shown, not resolved away.**

When providers agree, the row shows the name and nothing else — no badge, no adornment, because a marker on every row saying *"everything is fine"* is the noise M12.1 already refused. When they disagree, the row shows the chosen name **and says so quietly**, opening to the provider-by-provider view.

**This is J3 — *"prove it"* — applied to the most ordinary field on the screen.** A competitor's list shows a company name as though it were a fact. Signora's shows it as what it is: the freshest of several claims, with the others one click away. That the mechanism was already sitting in `ClaimSet.agrees()` is the tell that the architecture anticipated this.

**Why it earns its place on the daily surface** — the principle is *reduce uncertainty*, and a name a seller half-recognises is uncertainty. Being told *"two of your providers call this company different things"* removes more doubt than silently picking one.

### Deferred from M12.2

**D7 — provider precedence is a customer policy, not a default.**
Recency ships as the selection rule: a company that renamed should display its new name, and recency is the only ordering the claim record supports without inventing a provider trust ranking. **A customer who would rather see their CRM's name than the freshest third-party one is expressing a policy** — the same category as the scoring model and the opportunity policy, both of which are versioned, customer-owned artifacts. Encoding a precedence order in code now would put an unreviewed judgement in the substrate.
*Trigger:* a customer disagreeing with a displayed name. Not before.

**D8 — the identity layer will want a name nobody claimed.**
Some accounts will have no `LEGAL_NAME` claim at all. The row must then show something, and the honest something is the domain if one is bound, falling back to the identifier. Building a richer fallback chain — trading names, aliases, CRM display names — is speculative until a real dataset shows how often the simple one is insufficient.
*Trigger:* measuring how many accounts in a real workspace have no name claim.


---

## Staff design review — the attention list with names *(M12.2)*

Reviewed as though for Linear or Stripe. **What shipped is correct and it is not yet good.**

### What works

**The row is quiet.** One number, one sentence, a badge only when something is wrong. Most rows carry no badge at all, which is what makes the badge mean something.

**The ⓘ on a disputed name is the product's thesis in one glyph** — a company name presented as a *claim* rather than a fact, with who said it a hover away. No competitor's list does this because no competitor's list could.

### What does not, and belongs to later slices

**D10 — the row has no shape.** ✅ **Fixed.** The account name is now the anchor: it leads the row at content weight, and the score is subordinate — muted, tabular, right-aligned in its own column. **The list is already sorted, so position carries the ranking**; the number only answers *how strongly*, which is a sanity check rather than the thing being scanned. A score set at display weight made every row equally loud, which is the same as having no hierarchy at all.

*Original observation:* Score, name, reason and badges sit on one horizontal line at one weight. A seller scanning fifty rows has no visual anchor: everything is equally loud, so nothing leads. Linear's issue row works because *one* element owns the line and the rest recede. **The name should be the anchor and currently competes with the score.**
*Principle: reduce cognitive load; calm hierarchy.* **Deferred** — reshaping the row is a design pass, and doing it before the row can be clicked would tune a layout that is about to gain an affordance.

**D11 — a hover title is not disclosure.** ✅ **Fixed, and it was not a deferral.** *"Your sources disagree"* was behind `title=`: invisible on touch, unreachable by keyboard, 500 ms away from everyone else. The frontend foundation treats an unreachable control as a **defect** rather than an enhancement (CLAUDE.md §20c), so deferring it was the wrong call and it was corrected in the same milestone. It is now a focusable `button` with `aria-expanded`, operable by Enter, Space and tap, whose explanation sits in the accessibility tree whether or not it is open — `hidden` would remove it from both the tree and browser search, which is what the tooltip did.

**Why an inline region rather than a popover.** A popover must trap focus, escape a scroll container and survive a virtualised row. An inline disclosure needs none of that and reads identically to a screen reader. When M12.3 builds the evidence surface this becomes its entry point rather than a second disclosure pattern to unify.

**D12 — names arrive after the rows, and the shift is visible.** ✅ **Fixed.** The name cell renders a skeleton at the height the name will occupy, so the row does not rewrite itself under the reader. Rows still do not *wait* for names — the score and the reason are what a seller triages on, and blocking the list on a label would trade the decision for the name of the thing being decided.

*Original observation:* The identity request resolves second, so a row renders as `6b8efd21` and becomes `Northwind Traders`. Correct behaviour, poor experience: a list that rewrites itself under the reader's eye costs more confidence than the extra 80ms would have.
*Principle: increase confidence.* **Deferred** — the fix is a skeleton on the name cell rather than blocking the list, and it belongs with D10's row pass.

**D13 — there is nothing to *do*.** The screen answers *which accounts* and *why*, and then stops. A seller reads it and leaves. That is the largest gap in the product and it is exactly M12.3.

### Reusable intelligence components — and one that has not earned it

`EntityName` is the third component in `components/intelligence/`, after the attention set. All three are now used by one screen and designed for two.

**`EntityCard`, `BuyingScoreBadge`, `ConfidenceIndicator`, `FreshnessIndicator`, `NarrativePreview`, `RecommendationSummary` are deliberately not built.** Each would have exactly one caller today, and a component with one caller is a function with extra ceremony. They earn their place when the account brief needs the same vocabulary the list already renders — **demonstrated reuse, not anticipated reuse**.

### D9 — Product Playground

A stable demo dataset behind `make demo` is the right idea: the golden set has **two structurally identical accounts**, and `28-ai-platform.md` records "variety 1" as the main caveat on every evaluation the repository holds. Realistic accounts would improve design review, stakeholder demos, and — more importantly — every prompt evaluation.

**It must not be a parallel seeding system.** The Provider Simulation Framework already owns scenarios and was commissioned for ten *"deepening each milestone"*; one exists. A demo dataset belongs there, inheriting the seeded determinism, the fault injector and the provenance fields. Building a second seeder beside it would split all three across two owners — the mistake ADR-0032 declined to make with certification scenarios.

**Its own slice**, and probably the highest-value non-UI work available: it unblocks D6 (grouping), makes D10's row pass reviewable against a real list, and widens the evidence base for every future prompt release.


---

## D9 — the Product Playground, built

**Twelve accounts, twelve shapes.** Not twelve rows: the technology migration, the hiring surge, the provider disagreement, the acquisition, the rapid grower, the stale account, the false positive, the silent account, the rebranding, the contested account, the slow burn, and the one that is cooling.

**Why shapes rather than volume.** Twelve copies of one story would pass a count and answer no design question. The Constitution's rule is *never design for two rows*, and the reason is that ranking-versus-grouping, row density and column scanning are all questions that only have answers at scale — a test asserts the accounts differ in *evidence*, not merely in name.

**Why fictional companies.** The Constitution named real ones. I used the placeholder convention instead, with every domain on the RFC 2606 `.example` reserved TLD, and a test that fails on a recognisable brand. **Fabricated buying signals attached to a real company are indistinguishable from real ones in a screenshot**, and a demo that could be read as a claim about somebody's business is a liability rather than an asset. The legibility a real name buys is not worth that.

**Why in the Provider Simulation Framework.** It already owns scenarios, the seeded determinism, the fault injector and the provenance fields. A second seeder beside it would split all four across two owners — the mistake ADR-0032 declined to make with certification scenarios. One source of truth for design, AI evaluation and demonstration, as the Constitution requires.

### What it unblocks

- **D6 (grouping vs ranking)** becomes answerable rather than speculative.
- **D10 (row hierarchy)** becomes reviewable — I have been making density judgements against two identical rows and could not have told you whether the row scans at twelve.
- **Every prompt evaluation** gains variety; *"two cases, one shape"* has been the standing caveat on every release the repository holds.
- **`fabrikam-industrial` carries two legal names from two providers**, so the disputed-name disclosure is exercised by real pipeline output rather than a component test.

### `make demo` — built, and it runs the real product

The Playground is now seeded by the **same function the pipeline suite runs**, over `playground@1` instead of `baseline@1`. Provider simulation → ingestion → normalization → knowledge graph → observations → business events → signals → buying scores → opportunities. **No branch anywhere knows it is a playground**; the only difference is which scenario file is named.

Reaching that took four widenings, each with defaults that left every existing test untouched — the suite passing at 1901 unchanged is the proof. `_adapter` gained a scenario, `_ingest_every_provider` gained subjects, `_scored`/`_tracked` forward both, and `_acme` gained the anchor whose evidence decides the moment a scenario is scored at. **Widening rather than redesigning**, exactly as the execution principles require.

### The first thing the Playground told us

**Twelve accounts in; four qualified.** The other eight did not meet the qualification threshold — and that is the product working, not a seeding bug. The silent account has one employee count and nothing else. The false positive has loud intent and no corroboration. The stale one's evidence expired. **A playground that produced twelve qualified opportunities would have been lying**, and would have validated a list nobody will ever see.

**It also means the attention list still cannot be judged at scale.** Four rows is better evidence than two identical ones, and it is not twelve. Whether the list needs grouping (D6) and whether the row scans in a column (D10) remain open — the honest position is that the Playground has moved them from *unanswerable* to *partially answerable*.

**D14 — the eight unqualified accounts are invisible, and that may be wrong.** A seller whose evidence is thin on eight accounts currently sees nothing about them. There is a real product question here: is *"we are watching these and they have not met your bar"* worth a surface? It is not a bug, it is a gap in the story the product tells, and it belongs to a milestone that owns qualification rather than to this one.
*Trigger:* a design partner asking where an account they expected went.

---

## The account brief — first slice *(M12.2, 2026-07-31)*

The score, the arithmetic, and every line that produced it. Three decisions are worth inheriting, and two observations are recorded rather than built.

### Decisions taken

**The score is shown as a division, not a gauge.** `68 of 120 points` beside the number. A ring or a bar implies a maximum that means something — and the number is an ordering of commercial attention, so a filled 40% would state a confidence the pipeline never computed. A customer can check `min(100, points × 100 ÷ ceiling)` on paper in four seconds; **this is the moment the product either earns trust or asks for it, and asking is what every other tool does.**

**The reason is placed, never paraphrased.** Each line's sentence is rendered by the pipeline from the same fields an auditor checks. The screen positions it and does nothing else. A friendlier rewording — and there were several available — would blur two lines together and make the number uncheckable against the record, which is the one thing this product cannot afford to be.

**Lines that counted nothing stay on the page**, subordinate but present, with the reason they counted nothing. A zero a customer can read is information; a row that vanished is a mystery, and the question it produces goes to support.

**The disagreement is stated as a reason to look harder, not as a caveat.** A contested account gets a note saying Signora has neither picked a side nor split the difference. Wording that apologised for the disagreement would invert the meaning the Buying Score Engine computed: a fought-over account warrants *more* attention, not hedged attention.

### D15 — the brief has no next action either

**The same gap D3 recorded on the list, one screen deeper.** A seller can now see which accounts, and why — and still cannot do anything from either page. The brief is the more acute case: it is where somebody finishes being convinced, and finishing convinced with nowhere to go is a worse experience than never being convinced.

*Owner:* M12.3, which owns stage transitions and assignment. Recorded, not built — the endpoints do not exist and inventing a disabled control would be worse than the absence.

### D16 — the ledger is legible at four lines; nobody knows about forty

Every judgement made here — that the list needs no grouping, that uncounted lines can stay inline, that the reasons scan as a column — was made against a Playground account with a handful of contributions. **A busy account with forty lines has not been seen**, and the honest position is the same one D10 holds about the list: partially answerable, not answered.

The three plausible answers are collapse-uncounted-by-default, group-by-posture, and leave it alone. **Choosing now would be guessing**, and the current shape is the one that hides nothing, which is the right default to be wrong in.

*Trigger:* an account whose ledger does not fit one screen. *Owner:* whichever milestone first produces one.

### D17 — the Playground's twelve shapes are not reaching the screen

**Found by opening the brief against real Playground data, 2026-07-31, and it partly corrects what D9 claimed.**

Every one of the four qualified accounts reads **evidence expired**, and `adventure-outdoor` — the account whose *shape* is "stale evidence" — shows a ledger of `fresh evidence (100%)`. The scenario defines twelve shapes; the screen is showing something else.

**The cause is known, dated, and not new.** [26-buying-score-engine.md](26-buying-score-engine.md) recorded it at M5B's close: the simulated payloads describe events months in the past, so at wall-clock now every hypothesis has passed its shelf life, and scoring a live account requires asking the question *as of* a moment derived from the evidence. The Playground inherited that because it runs the same helper the pipeline suite runs — **which is the single-product property working exactly as designed, and is why the defect is in the data rather than in the code.**

Two consequences, and the second is the more serious:

1. **Every reading is expired at wall-clock now**, so the current-reading path — the normal state of the product — is never demonstrated.
2. **All twelve accounts are scored at one moment chosen by one of them** (`northwind-logistics`, the declared anchor). A scenario whose whole point is that accounts differ *temporally* — fresh, cooling, stale — cannot express that when every account is evaluated at the same instant.

**This narrows what D9 established.** The Playground did deliver twelve distinct *evidence* shapes, and did make the disputed-name path real. It has not yet delivered the twelve *temporal* shapes it names, and the "four of twelve qualified" result reported at D9 is therefore weaker evidence than it looked: an account may be unqualified because its evidence is genuinely thin, or because it was scored at a moment that did not suit it. **Those are not the same finding, and today they cannot be told apart.**

*Not fixed here.* `playground@1` is content-hashed and published, so a correction is `playground@2`; and per-account scoring moments are a Provider Simulation Framework concern, not a screen's. Both are the *"evidence recent enough that several signals are concurrently live"* work M5B already scheduled and M2.0 already owns.

*Owner:* the Provider Simulation Framework. *Trigger:* immediate — this degrades every design review, every demo and every prompt evaluation that uses the Playground, which is now all of them.

### D18 — half the qualified accounts have no name

`887bf469` and `051391d2` render as identifiers because no provider in their scenario steps emits a `LEGAL_NAME` claim. The fallback behaves exactly as designed — the real identifier, never a fabricated name — but a demo in which half the list is unnamed undersells the identity work that shipped hours earlier.

A scenario-authoring gap rather than a product one: the accounts that matter should be named by at least one provider. Folded into D17's `playground@2`.

---

# M12.1.5 — Playground v2, and the product review it made possible

**The milestone existed because the demo data was limiting product development.** D17 recorded that; this is what changed and what reviewing against real data then showed.

## What the dataset now does

Twelve recognisable companies with **entirely invented business situations**, spanning five months against a shortest relevance window of ninety days — so *current*, *recent*, *ageing*, *cooling* and *stale* all occur, produced by band arithmetic rather than declared. Details in [20-provider-simulation.md](20-provider-simulation.md).

**Real company names were the product owner's call, made twice.** D9 recorded my objection — fabricated buying signals attached to a real company are indistinguishable from real ones in a screenshot — and it stands. The mitigation is that the disclaimer lives *inside the dataset*, and a test asserts it names screenshots, because that is how this data leaves the context that explains it. **The objection is recorded, not re-argued.**

## D19 — the ledger repeats itself on a composite signal

NVIDIA's expansion rests on two independent grounds, and the brief shows **two identical sentences at thirty points each**. Databricks shows the same.

It is not a bug in the arithmetic — the ledger's unit is the *business event*, deliberately, so an expansion resting on two events contributes twice. It is a defect in the **language**: `reason` names the hypothesis and never the evidence beneath it, so two lines that a customer cannot tell apart look like a display error rather than two grounds.

**This is the first thing a reviewer notices on the highest-scoring account in the demo**, which makes it the worst possible place for it.

*Owner:* the Buying Score Engine — the ledger's wording belongs where its arithmetic lives, and the fix is to render the contributing event into the sentence, not to collapse the lines. Collapsing them would hide the second ground, which is the opposite of what the ledger exists for.

## The five review questions, answered honestly

**Does each account tell a unique story?** **Yes, now.** Twelve distinct chains, all nine signal types, all three postures, all four identity states. Under `playground@1` the answer was no — one temporal shape, twelve times.

**Does opening multiple accounts feel repetitive?** **Partly.** The *shapes* differ; the *presentation* does not vary with them. A one-line ledger and a three-line ledger get the same layout, the same weight and the same heading. Twilio at 1 point and NVIDIA at 50 are the same screen — and they should not be, because one is a rounding error and the other is the reason a seller opens the product.

**Are there opportunities for richer storytelling?** The largest is that **the brief still has no narrative**. The pipeline computes *why now*, the contradiction, and the ageing — and the page reports them as a table of facts. The AI narration and Decision Package are the missing half, and they are the remaining M12.2 scope. **Second: nothing on either screen says what happened *before*.** A score that fell from 30 to 10 is a story; the brief shows only where it landed.

**Does the demo communicate Signora's value in under five minutes?** **Yes, for the explainability claim; no, for the product.** Open the list, click Stripe, see two opposing readings both counted with the minority named — that lands in ninety seconds and no competitor's summary survives it. What does not land is what a seller *does* next, because there is nothing to do (D3, D15).

**Would this be compelling in a customer demonstration?** **To a technical buyer, yes.** To an economic buyer, not yet: it demonstrates a system that is right, not a workflow that saves anyone time. The gap is not more intelligence — it is the action surface M12.3 owns.

## D20 — the list does not distinguish a 50 from a 1

Twelve rows, scores from 50 down to 1, rendered identically. **The bottom of this list is noise** — Twilio at 1 point is one contextual signal at 60% weight, and presenting it with the same visual weight as an account with two live primary hypotheses is the product declining to have an opinion it demonstrably has.

Three plausible answers: a threshold below which accounts are collapsed; a visual break between *worth your morning* and *worth knowing*; or grouping by why-now rather than ranking (D6, now genuinely reviewable). **Choosing needs a seller, not a designer** — this is the first finding in the set that the Playground cannot settle on its own.

*Owner:* M12.3, alongside the sort and filter controls D4 deferred.

---

# The account brief — the workflow half *(M12.2, 2026-08-01)*

The Opportunity Engine has always recorded *what was true when somebody committed*. The brief never read it. Adding it answers the first of the eight questions the brief must answer — **what changed** — and it is the one figure no other screen can produce: the list knows today's score and today's overnight move, neither of which says whether an account has been climbing for a month.

## Decisions taken

**One delta on this screen, not two.** The list shows `+8` — *what moved overnight*. The brief shows `+20` — *what has happened since we started watching*. The first draft had both, and **two deltas ask a reader to reconcile two numbers that answer different questions.** The overnight figure stays where "what moved overnight" is the question. Recorded because it is a subtraction, not an addition: the screen got better by losing a number.

**The workflow line sits under the name, not in the score card.** It is about the *account*, not the number, and a seller reads it once on arrival and never again. Putting it beside the score would have given it a weight it has to earn every time the page is opened.

**`tracking` says out loud that nobody has committed.** *"Signora is tracking this · nobody has taken it yet."* **Intelligence suggests; humans commit** is the principle the module is shaped around, and a screen presenting a suggestion as a decision would quietly invert it. This is the one place in the product where that principle is visible to a customer.

**Contradiction is reported only when it is news.** *"Your sources did not disagree when this opened. They do now."* An account that has *become* contested is a different situation from one that always was; a line saying *"still contested"* on every contested account is a fact nobody needed.

**`dismissed` is not softened into `closed`.** One is feedback about Signora's judgement, the other is a sales outcome, and collapsing them destroys the only signal the platform gets about its own qualification quality.

## D21 — a workflow timeline with one entry is a list pretending to be a history

**Planned, then not built, and the reasoning is the finding.** Every account in the demo has exactly one workflow state: the opening one. A timeline component would render a single row on every account in the product, look like a stub, and teach a reader that the section is not worth reading.

The information is **one sentence** until transitions exist — *"Signora opened this five weeks ago at 30"* — and that is what shipped. The timeline belongs to M12.3, which owns transitions and will therefore have something to put in it.

*The rule worth keeping:* a component whose value depends on data volume should not ship before the volume does. It is the same judgement that kept the citation un-clickable rather than drawing a dead link.

## D22 — the Playground can demonstrate a falling score, never a rising one

**Found by shipping the momentum line and looking at all twelve accounts.** Eight of twelve read *"unchanged since"*, and the four that moved all moved **down**.

That is truthful and it is a demo limitation rather than a product one. All the scenario's evidence arrives in a single ingest, so after the opportunity opens the only thing that can happen is decay — nothing new ever arrives to push a score up. In production the common case is the opposite: an account climbs because evidence keeps arriving.

**The consequence is that the brief's headline answer to *"what changed?"* is "nothing" on two-thirds of the demo**, and that the product's most encouraging story — *this account is heating up* — cannot be shown at all.

*The fix:* the seeder ingests in two passes — an early set, score, qualify, then the recent set and score again — which is what actually happens to a customer. *Owner:* the Provider Simulation Framework, alongside `playground@3`. Not done here: it is Playground scope, and rebuilding the seeder inside a product slice is how milestones stop meaning anything.

## D23 — an owner is a UUID with no name behind it

`owner_id` is a user identifier and **there is no read path from a user id to a person**. The demo never exercises it (nothing has been assigned), so the screen currently says *"nobody has taken it yet"* and is correct — but the moment M12.3 ships assignment, the brief will need to render a person and will have nothing but a UUID.

*Owner:* M12.3, which introduces assignment and therefore introduces the need. It is a real API gap, not a styling question: Workspace & Tenancy owns members and exposes them, but nothing joins a member to the identity that Better Auth holds.

> **Outcome, 2026-08-01:** M12.3 shipped assignment and answered this only halfway — the screen can say *"you"* and says *"held by someone else"* for anybody else. See **D32**, which records why the remaining half is a cross-tier contract rather than a slice.

---

## Product Design Review — the account brief

Reviewed as the teams named in the brief would review it. **Every item below is a criticism I agree with**; none is fixed here, and each names its owner.

### Apple — *is every element earning its place?*

**The brief has four cards and no hierarchy between them.** Score, contested note, contested-since, ledger — each is a `Card`, each has the same border, the same padding and the same visual weight. A page where everything is a panel has told the reader nothing about what matters. The score card should be the page's subject and the rest should be quieter.

**The back link is a link, and could be the product's first real navigation gesture.** *"← All accounts"* is what a prototype ships.

### Stripe — *would a developer trust this?*

**The arithmetic is the best thing on the screen and it is whispered.** `60 of 120 points` sits at `text-sm` in muted grey beside a `text-4xl` number. **That ratio is exactly backwards for a product whose differentiator is that the number can be checked.** The check should be as prominent as the claim.

**No page states its own freshness.** The reader is told when the *reading* expires and never when the page was loaded. Stripe's dashboards always say when data was fetched, because a stale browser tab is indistinguishable from stale data.

### Linear — *is it fast, and is it keyboard-reachable?*

**Three sequential requests, no prefetch.** Hovering a row on the list could warm the brief; nothing does. And **the brief cannot be reached or left from the keyboard beyond tabbing** — no `j`/`k` through the list, no `Esc` to go back. A product for people who live in it all day should not require the mouse.

**Nothing indicates position.** Opening the fourth of twelve accounts, a seller loses the list. There is no *"4 of 12"*, no next/previous.

### Notion — *does the page read as a document?*

**It reads as a form.** The strongest version of this screen is a paragraph a seller could paste into an email — *"NVIDIA has been climbing since June: hiring and revenue both moved, and nothing contradicts it."* Signora computes every fact in that sentence and renders none of it as prose. That is what the narration slice is for, and it is the largest remaining gap.

**Section headings are inconsistent.** *"What contributed"* is the only heading on the page; the score card and the momentum line have none. Either everything is titled or nothing is.

### Cursor / OpenAI — *where is the AI, and is it honest about itself?*

**There is no AI on this screen at all, and that is currently correct** — `reasoning@1` has no released model, and the narration is not wired. But it means the brief today shows Signora's *deterministic* half only, and a customer told this is an AI product will ask where it is.

**When narration lands, provenance must be visible on the page**, not in a tooltip: which prompt, which model, when. The M12.2 definition of done already requires it; recording it here so it is not discovered late.

### Perplexity — *can every claim be followed?*

**The ledger names its evidence and cannot open it.** Each line carries `signal_id` and `business_event_id` on the wire and neither is reachable. **This is the single largest trust gap in the product**: the page's whole argument is *"you can check this"*, and the check stops one level short. M12.3 owns it, and it should be the next thing built after the narration.

**The posture split has no explanation.** *"Expansion 60"* assumes a reader knows what posture is. One sentence would fix it, and its absence is the difference between a figure and a fact.

### The one thing all seven would say

**The screen is right and it is not yet persuasive.** Every number is correct, checkable and honestly qualified — and a salesperson reads it as a report rather than as an argument. The missing element is not data; it is **narrative**, and the next slice is exactly that.

---

# Narration on the brief *(M12.2, 2026-08-01)*

The first model-authored content in the product, and the first surface whose design problem is **trust rather than layout**: can a reader tell what a machine wrote, and how far to rely on it.

## Decisions taken

**Prose after the number, never before it.** Deterministic truth outranks generated language, so a reader meets the score and its arithmetic first and the narration is the bridge between them. Putting generated sentences above a checkable figure would invert the Constitution's own ordering.

**One line carries the whole AI claim:** *"the model chose the words, not the facts."* It appears on every narration rather than once in documentation, because the reader who needs it is the one who has just been surprised by a sentence. Without it this is indistinguishable from any other tool's summary.

**The citation is a count, not a link.** *"3 facts"* beside each sentence. Evidence resolution is M12.3's; a citation drawn as clickable and going nowhere costs more than the missing feature. The count is honest today — it says the sentence is anchored without pretending the anchor is reachable — and it becomes the affordance that opens the evidence the day there is any.

**No summary line, ever.** Not on the block, not above it. The one sentence a reader looks at first must not be the one exempt from grounding — which is why the domain refuses an un-cited `summary` field, and why the screen must not invent one.

**Absence renders nothing at all.** An account with no narration shows no panel, not an empty state. The brief explains itself without this; a box announcing a gap would appear on every account until a worker caught up, and would advertise the gap rather than fill it.

**Raw citation tokens never reach a reader.** `signal:38b821b4-…` is an address, not information.

## F-11 — a zero-padded figure can never ground its unpadded form

**Corrected 2026-08-01, and the correction is the finding.** The first
narration run succeeded on 2 of 12 accounts, and I recorded that as an
evaluation-dataset problem: a prompt released against a two-case golden set
failing to generalise. **That was wrong.** The failures had a single
deterministic cause, and a clean run afterwards succeeded on **10 of 12**, with
both remaining failures transient timeouts rather than refusals.

### The defect

`_normalise` in `grounding.py` folds thousands separators and trailing decimal
zeros into one canonical form. It does not fold **leading** zeros:

| | tokens after normalisation |
|---|---|
| evidence `2026-08-01` | `2026`, `08`, `01` |
| prose *"August 1, 2026"* | `2026`, `1` |

`1` is not `01`, so the statement is refused as ungrounded — **correctly by the
letter of the check and wrongly by its purpose.** Any date falling on the first
nine days of a month fails this way, as does any zero-padded quantity a model
writes the way a person would.

It was hidden by the same accident that hid F-10: the golden set has no
zero-padded figure, so nothing had ever asked.

### Why it looked like a dataset problem

The opportunity's `opened_on` was wall-clock now — the `created_at` defect fixed
in this slice — which on 1 August rendered as `2026-08-01`. Fixing the
timestamp moved it to `2026-06-27`, and `27` needs no padding. **The success
rate went from 2/12 to 10/12 because of a date change, not a prompt change**,
which is exactly the shape of evidence that should stop anyone reaching for the
prompt.

*Severity:* 🟠 Medium — deterministic, silent, and it discards valid output.
*Owner:* AI Platform. *Shape of the fix:* `plain.lstrip("0") or "0"` in
`_normalise`, so `007` and `7` are one figure for the same reason `1.50` and
`1.5` already are. **Not applied:** `ai_platform/` is frozen, and this *loosens*
a grounding check. Relaxing a guarantee is a product-owner decision, not a
coding-session one — the whole point of the freeze.

### What survives from the original F-9

Only this, and it is worth keeping: **grounding refused every one of those
outputs, and nothing fabricated reached the database.** The guard was
over-strict rather than absent, which is the correct direction for it to be
wrong in. The *"variety 1"* caveat on the golden sets is still real and still
unpriced — this run simply did not price it.

## D24 — a violation report named a figure nobody wrote

The failures read: *"the figure `'1,'` appears in the text but in none of the facts this statement cites."*

`'1,'` is not a figure. It is the number tokeniser (`\d[\d,]*`) swallowing the comma in *"August 1, 2026"*. The real defect was a date, and an engineer reading `'1,'` looks for a stray digit instead of a hallucinated date — **an incorrect attribution is worse than none, because it misdirects the investigation**, which is a principle this repository already ratified about vendors and applies unchanged here.

*The fix is one line* — report `_normalise(token)` rather than the raw match, or quote the surrounding phrase. *Not applied here:* `ai_platform/` is frozen as of M10's close, and a diagnostics improvement is not a security fix or a production defect. It is raised rather than taken.

## D25 — the demo cannot show what it cannot narrate

Ten of twelve accounts have no narration, so the brief's narrative half is invisible on most of the demo. That is correct behaviour and a poor review environment — the same shape as D22.

It resolves when F-9 does. Until then `make demo-narrate` is honest about what it produced: it prints which accounts succeeded, which had nothing to explain, and which were refused, rather than reporting a total.

## D26 — the demo database and the test suite share a machine

Running `pytest` while `make demo-narrate` was working truncated the Playground underneath it, and the narration run continued writing into a workspace that no longer existed. Both commands are correct in isolation; together they are destructive, and nothing says so.

Not a product defect and not worth a lock — the honest fix is that **`make demo-narrate` should refuse to start if the tables it depends on can vanish**, or simply that the two are documented as mutually exclusive. Recorded because the failure looked like a narration bug for several minutes, which is exactly how a workflow hazard costs more than it should.

**It happened three times in one session** — twice before it was written down and once after, by the person who had just written it down. That is the argument for a guard rather than a note: `make demo-narrate` now re-checks that the workspace still exists before each account and aborts with the cause named, turning a silent several-minute misdiagnosis into one sentence. **A note in a document does not stop anything; it only makes the eventual failure feel avoidable.**

The original observation follows. Both times the symptom was *"narration produced nothing"* and the cause was a `pytest` run in another terminal; both times it cost several minutes of looking in the wrong place.

*Owner:* unassigned. *Smallest honest fix:* the suite and the demo should not share a database by default — `SIGNORA_TEST_APP_DATABASE_URL` already exists to point the suite elsewhere, and defaulting the demo to its own database name would make the collision impossible rather than merely documented. A line in `docs/RUNNING.md` is there now, and a line is what failed to stop it the second time.

## F-10 — the pipeline computed "grew headcount 3678%", and every layer faithfully passed it on

**The most serious finding of the session, and narration is what made it visible.**

NVIDIA's brief carries two contradictory sentences: *"The company grew headcount 17% over 38 days"* and *"The company grew headcount 3678% over 38 days."* Both are grounded. Both are in the evidence. **The model invented nothing.**

### Root cause

`_HeadcountRule.evaluate` pools its attributes into one series:

```python
relevant = tuple(o for o in series if o.attribute in self.attributes)
```

`HiringSurge` declares `{EMPLOYEE_COUNT, OPEN_ROLES}`. So the ratio is taken from `window[0].previous_value` — an **open-roles** figure of 900 — to `window[-1].current_value` — an **employee-count** figure of 34,000. `(34000 − 900) / 900 = 3678%`. The recorded fact then labels the attribute from `last.attribute`, so it claims to be about `employee_count`, which it half is.

The module's own docstring states the guarantee it was built for:

> *"The series is always one provider's. No rule here sees two providers' values together, so nothing can combine them into a synthetic truth."*

**It guards the provider axis and not the attribute axis.** Same defect class, one dimension over — and open roles and employees are no more comparable than two providers' figures are.

### What this says about the architecture, which is the part worth keeping

**Grounding guarantees fidelity to the pipeline. It cannot guarantee the pipeline is right** — and it never claimed to. Every layer behaved exactly as specified: the rule computed, the signal cited, the evidence rendered, the model reported, grounding verified, the screen displayed. A false number travelled the whole length of the system without a single component failing its own contract.

That is not an argument against grounding; it is the argument for **why the deterministic half must be defensible on its own.** Signora's claim is that a human can check every statement — and here a human checking this one would find it correct against the evidence and still absurd. The check that was missing is the one no citation can supply: *is this ratio comparing like with like?*

**It also vindicates the demo environment.** This defect has existed since M4. It survived the unit tests, the pipeline suite, the smoke test and certification, because `baseline@1` never gave one entity both an employee count and an open-roles count in the same window. **Twelve varied accounts found it in the first run.**

*Severity:* 🔴 High — customer-visible, and it is a fabricated statistic presented as a measurement.

### ✅ Fixed 2026-08-01, as its own slice

`_HeadcountRule` now evaluates **one measure at a time**, producing at most one detection per declared attribute. The pipeline's output on the same data:

```
Grew headcount 17% over 38 days     employee_count  29000 → 34000
Grew open roles 56% over 38 days    open_roles        900 →  1400
```

Two conclusions, each with its own baseline, each named for what it measured — and the 3678% gone.

**Two halves, and the second was easy to miss.** Emitting per-attribute detections is not enough on its own: the summary template said *"Grew headcount {percent}%"* regardless of attribute, so the open-roles detection would have read *"Grew headcount 56%"* — a new false statement replacing the old one. The phrasing now takes the measure's own noun.

**The pattern was already in the same file, one class down.** `BuyingIntentSurge` groups by topic, with the reasoning written out: *"a company researching two unrelated topics is two pieces of news. A rollup across topics would produce a number that means nothing to anybody."* Employees and open roles are two unrelated measures on precisely that argument. **The fix was to apply a principle the module had already articulated and then not generalised** — which is the more useful lesson than the arithmetic.

Four regression tests pin it, including the exact 900 → 34,000 shape.

---

# M12.3 — what to build, decided before writing code

**The milestone's goal, as set by the product owner:** *reduce uncertainty after an account has been selected*, and begin answering **"what should I do?"** — with no Recommendation Engine, no invented AI, and only deterministic information the platform already holds.

Every deferred finding was re-read against that goal. Most did not survive it.

## What the deferred findings actually belong to

| Finding | Verdict |
|---|---|
| **R1-01** the *why now* line repeats 11 times of 12 | **Not M12.3.** It is a *list* improvement — it changes which account you select, not what you do after selecting one. Real and high-value; it belongs to a list slice with R1-05 and D20. |
| **R1-02** trigger and evidence state contradict on a row | **Not M12.3**, same reason. It is a trust bug on the list. |
| **R1-04** the brief never mentions cooling | **Yes.** It is on the brief, it is a contradiction between two screens, and it costs trust exactly where M12.3 is trying to build it. Small. |
| **R1-05 / R1-07 / D20** ties, and a 1-point account | **Not M12.3.** List hierarchy. |
| **R1-06** the workflow line is identical everywhere | **Resolves itself** the moment assignment exists, which M12.3 introduces. No action. |
| **Perplexity — a citation cannot be followed** | **Yes.** This is J3 and it is the differentiator. |
| **D3 / D15 — no next action** | **Yes.** This is the milestone. |
| **D23** an owner is a UUID with no name | **Yes, forced.** Assignment cannot ship without it. |
| **D22** the Playground cannot show a rising score | Playground scope, not product. |
| **F-11** leading zeros in grounding | Needs a product-owner ruling; loosens a guarantee inside a frozen module. |

## The thing already in the repository that answers *"what should I do?"*

**The Signal Catalog carries `limitations` and `suggested_validation` on every signal type, and nothing has ever displayed them.**

```
expansion_opportunity
  limitations:
    - Investment ahead of growth says nothing about budget for *your* category —
      capacity spend is often funded by cutting elsewhere.
    - It does not indicate that a purchase decision is underway, only that the
      company is adding capability.
    - Growth in one division does not imply growth in the one you sell to.
  suggested_validation:
    - Check which functions the recent hiring is in, and whether they are the
      ones that would use your product.
    - Ask on a first call which division the investment sits in — the signal
      cannot tell you.
```

That is **action guidance, written for a customer, versioned, reviewed like code, and entirely deterministic.** It is the answer the milestone asked for, and it has been sitting in `signals@1.json` since M5A.

**Why this is not "displaying more data".** `suggested_validation` tells a seller *what to do next*. `limitations` tells them *what the score cannot support*, which stops the over-reading that a confident number invites. **Naming the uncertainty is the uncertainty reduction** — it is the Constitution's *"make uncertainty legible rather than eliminate it"* applied to the moment before someone acts.

**Why it is not a recommendation.** It says nothing about *this* account. It is a property of the *hypothesis type* — what `expansion_opportunity` fails to prove is identical on Tuesday and Wednesday and for every workspace, which is why the catalog owns it. A recommendation would be account-specific and inferred; this is neither.

## The interaction, challenged before it was built

**Rejected — bolting the guidance onto the score endpoint.** It would have been one fewer request and it merges *how the number was computed* with *what to do about it*. Those are different questions asked at different moments, and a response answering both would be read as one.

**Rejected — deriving the guidance from the score's ledger.** The ledger names contributing signals, so the guidance could be keyed to what actually drove the number. But the Buying Score Engine is downstream of the Signal Engine, and asking it for catalog prose would put the score in the business of explaining hypotheses it only weighs. **The live signals are the right input**: a hypothesis worth validating is one that is *current*, not one that happens to carry points.

**Rejected — showing the guidance on the attention list.** Twelve accounts × three limitations each is a wall. It belongs where somebody has already chosen to concentrate.

**Chosen:** the Signal Engine owns it, keyed by account, derived from that account's **live** signals. `GET /workspaces/{id}/accounts/{account_id}/validation`. No new persistence, no new module, no duplicated logic — the catalog is already loaded and the signals are already queryable.

## The objection that must travel with it — F-3

**`limitations` and `suggested_validation` are engineering-authored pending domain review** (finding F-3, open since M5A). Displaying them promotes unreviewed text to customer-facing product copy, and *"ask on a first call which division the investment sits in"* is advice a real seller will act on.

The content is good. That is not the same as it being **signed**. Shipping this to a paying customer requires closing F-3 first; shipping it to the Playground does not. **Recorded here so the milestone cannot quietly convert a known gap into a customer promise.**

---

# M12.3 — evidence and action, as built *(2026-08-01)*

## D27 — a closed opportunity keeps its brief

M12.2 left `OpportunityQueries.brief()` returning `None` for an account with no **open** opportunity, and said so in the docstring: *"deliberate until M12.3, which owns reopening and therefore owns the question of what a closed opportunity's brief should say."*

**The answer is that it keeps it**, and the reasoning only became visible once a customer could make the decision. Until then nothing was lost by hiding a closed opportunity. The moment a seller can dismiss an account, a brief that vanished with the dismissal would:

- take **their own words** with it — the dismissal reason is the only feedback Signora ever receives about its qualification quality, and it would become unreadable the instant it was written;
- make a **legal transition unreachable** — `dismissed → tracking` is allowed by the domain, and being able to undo a dismissal is what makes dismissing safe to do;
- read as **the product deleting the account they just judged**.

The open opportunity still wins whenever there is one, so the ordinary path stays a single query and history can never shadow live work. Otherwise the most recent generation, which is the one whose outcome a reader is asking about.

**The commitment outlives the score that created it; the record outlives the commitment.**

*Found by a test, not by design review* — two assertions about closing an account failed with a 404 the moment they were written.

## D28 — the legal moves are sent, never inferred

The brief carries `allowed_next`, derived from the domain's `allowed_from(stage)`. A client that reimplemented the transition table would be **a second representation of the rules, wrong the moment either changed** — and the drift would be invisible, because both sides would look correct in isolation.

The server refuses anything else regardless: **a list a caller can ignore is not enforcement.** The client-side offer is a courtesy in exactly the sense §20c means it, and the integration suite proves the refusal independently of the offer.

**The ordering is part of the contract.** Sorted by the `Stage` enum's own declaration — `tracking → engaged → won → lost → dismissed`, the order work actually moves in — which is deterministic *and* meaningful. The first draft sorted alphabetically, which was equally deterministic and put **"Lost"** ahead of **"I'm working this"** on every account in the product (R4-01).

## D29 — who decided is never on the request

`RecordDecisionRequest` carries `stage`, `reason` and `owner_id`. It does **not** carry `actor_id`, and a test asserts the field set rather than only the behaviour.

A request able to name its own actor would let one member sign another's name to a dismissal. The workflow history is **the one record in Signora that nothing can recompute** — every derived table rebuilds byte for byte from the evidence beneath it, and a decision does not — so a wrong entry there is wrong permanently.

Who *decided* and who *holds it* stay separate facts, because a manager assigning work depends on them being separate.

## D30 — every decision costs a sentence, and the sentence is the point

The domain refuses a state with no reason. The interface does not route around it: each action asks a **different** question, because a single *"Reason"* label collects a single kind of answer.

| Move | Asked |
|---|---|
| `engaged` | Why are you taking this on? |
| `dismissed` | Why shouldn't Signora have shown you this? |
| `closed_won` | What won it? |
| `closed_lost` | Why was it lost? |
| `tracking` | Why are you picking this back up? |

The dismissal question is the valuable one: it is the only feedback loop from a seller's judgement back into qualification quality, and *"not interested"* and *"they are a reseller, wrong profile entirely"* are worth very different amounts.

**Considered and rejected:** supplying a default reason so that taking an account on is one click. It would have put the same sentence on every account — R1-06's defect, manufactured deliberately.

## D31 — a refusal is shown in the domain's own words

The Opportunity Engine's messages were written to be read: *"A won deal does not reopen — the next deal at that account is genuinely a new opportunity, and conflating them distorts every win-rate figure computed later."* The platform's domain-error handler passes `str(exc)` through and the dialog renders it.

Replacing that with *"Something went wrong"* would discard the best explanation in the system. **Anything without the API's error envelope gets a sentence that does not pretend to know what happened**, because a network failure is not a refusal.

**The cost, recorded as R4-03:** those messages were written for logs and now contain identifiers a customer cannot use. Passing them through was right and was decided without reading what they said.

## D32 — D23 is now live, and only half answerable

Assignment shipped, so the brief now renders ownership — and **Signora can say "you" and can say nobody else's name.** Better Auth owns user profiles in the Next.js tier; the Python tier verifies tokens without ever learning who a person is (ADR-0026). An owner arrives as an identifier and nothing more.

The screen says *"held by someone else"*. A raw identifier would be the same absence dressed as information.

**This is an API gap, not a styling question.** Workspace & Tenancy owns members and exposes them; nothing joins a member to the identity Better Auth holds. The workflow history is where it costs most — *"a person"* where a name belongs, in the one part of the product whose entire value is attribution.

*Owner:* unassigned, and it needs a decision rather than an implementation — whether profiles are read through a Next.js route over Better Auth's tables, or surfaced through `workspace_tenancy` from a profile the Python tier is told about. **The second is a new cross-tier contract and belongs in an ADR, not a slice.**
