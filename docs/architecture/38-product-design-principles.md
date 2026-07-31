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

### What is not done

**`make demo` does not exist yet.** The scenario and cast are built, loadable and tested; wiring them through ingestion into a seeded workspace behind one command is the next step. The dataset is the hard half and the command is the useful half — shipping the first without the second is honest progress, not a finished feature.
