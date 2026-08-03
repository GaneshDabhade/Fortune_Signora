# Product Experience — what would stop somebody buying Signora

> **The register for Product Experience Engineering** (Lane B, mission set by the product owner 2026-08-03).
>
> **One question, asked every cycle:** *"If I were evaluating Signora for my sales organization today, what would stop me from purchasing it?"*
>
> Not *"does it work?"* — that is `BUGS.md`. Not *"is it fast?"* — that is Production Readiness. **This is the register of everything between a trial starting and somebody saying yes.**

---

## UX philosophy — questions, not filters

**Ratified by the product owner, 2026-08-03**, on evidence from Epic A's audit. **The first principle in this document that came from being wrong.**

> **A filter is a control the seller must think to use. A question is one the product volunteers.**

**Where it came from.** [51](architecture/51-implementation-specifications.md)'s A2 specified the accounts workspace as *filters* — score, posture, owner, freshness, saved views. Lane A had already built the same surface as **questions the list is being asked**: *"Building, and nobody has taken it"*, *"Taken on, evidence has since aged"* — each narrowing the list, each **absent entirely when no account raises it.**

**Why the second is better, and it is not a matter of taste.**

| | **Filters** | **Questions** |
|---|---|---|
| Who supplies the intent | **The seller.** They must already know what they are looking for | **The product.** It says what is worth looking at today |
| When there is nothing to say | The controls sit there, all returning everything | **The strip disappears.** No chrome for an empty answer |
| What it teaches | How to operate a table | What Signora noticed |
| Failure mode | A seller who never opens the filter panel gets the default list forever | A seller who ignores it loses nothing — the list is still ranked |

**The rule that follows.** When a surface would let a customer narrow a set, **ask what the product already knows about why they would want to** — and offer that instead of the general control. Offer the general control too, if a real customer asks for it; **do not lead with it.**

**Where this does not apply.** A question is a claim that something matters, so it must be derivable from facts the platform holds. Lane A's own SW-04 refused four of six proposed questions on exactly that test — *"which deals slowed"* would be read off a workflow timestamp that measures decisions rather than activity. **A question the product cannot honestly answer is worse than a filter**, because a filter never claimed to know anything.

## How a finding gets here

**By using the product with nobody explaining it.** `make review-product` opens a browser at human pace, and every finding below was seen on a screen rather than inferred from code.

**Every finding is classified twice.** What kind of problem it is, and what it costs a purchase decision — never how hard it is to fix.

| Category | What belongs here |
|---|---|
| **Critical Trust** | The customer stops believing the product |
| **Product Contradiction** | Two parts of Signora disagree with each other |
| **Missing Capability** | Not a bug and not polish — something a buyer expects and cannot find |
| **UX** | Layout, density, hierarchy, wording, workflow |
| **Enhancement** | Good, later, not a blocker |
| **GA Blocker** | Signora does not feel production-ready without it |
| **Future Product** | A real module. **Documented thoroughly, never half-built** |

**And a strength register**, because a review that only complains cannot be trusted about what is wrong either.

**Ten small frictions lose more customers than one large defect**, so nothing is too small to record. What is *not* recorded is anything unverified: three findings from the first walk turned out to be artifacts of the review instrument, and they are listed at the bottom rather than quietly dropped.

---

## Review 1 — 2026-08-03 · a trial, day one

**Signed in as a Revenue Operations owner with twelve accounts already scored.** Front door → attention list → one account → its evidence → Settings → Your business → Connections.

### 🔴 Critical

#### PX-301 · The list a seller works from contains an account with no name

```
48ecfdbd — no source has named this account yet
Active evaluation · No change · Attention score 33
```

**Fifth in the list. Above Atlassian, HubSpot and Adobe.**

A CRO opening Signora for the first time sees a hex string presented as an account worth their team's morning. **It reads as a bug on the most important screen in the product**, and the specific damage is not the row — it is that the ranking beside it stops being believable. If Signora will rank *that*, what else is it ranking?

The wording is honest and the honesty is the wrong response here. **A record nobody can act on does not belong on the working list at all**; it belongs wherever unresolved records go to be resolved.

*Kind: missing workflow. Module: Product Surface · `knowledge_graph`.*

#### PX-314 · The product scores twelve accounts while telling you it cannot

Two screens, one trial, three clicks apart:

| Screen | What it says |
|---|---|
| **Your business** | *"What Signora needs to know about your company **before it can tell you anything useful about anyone else's**."* → **No products yet** |
| **Attention** | NVIDIA **75** · Databricks **75** · Snowflake **43** · nine more |

**It told me anyway.** A sceptical evaluator does not need to be clever to find this — it is the second and third screen of the product, and the contradiction is in the product's own words.

**One of the two screens is wrong, and which one matters enormously.** If scoring is meaningful without a declared catalogue, Settings overstates what it needs. If it is not, then **every number on the first screen is meaningless**, and the product's headline capability is being demonstrated against nothing.

*Found on a **freshly seeded** organization — so this is what the Playground demonstrates, and what any demo or review starts from.*

*Kind: missing business value / product coherence. Module: Product Surface · `opportunity_engine` · the Playground scenario.*

#### PX-302 · The brief shows the same score three times, on two different scales

```
75
90 of 120 points
Attention score 75 out of 100, from 90 of 120 points.
```

**A buyer asks one question: "so is it 75, or 90?"** Answering requires explaining that the model has a raw total and a normalised score — which is an internal fact that has reached a customer's screen. The decomposition is the product's strongest idea, and this is the first thing a sceptic hits when they pull on it.

*Kind: confusing UX / internal vocabulary. Module: Product Surface.*

### 🟠 High

#### PX-315 · Every dialog claims the same HTML id, so a screen reader can announce the wrong one

```
duplicate ids on /settings/products:  ["dialog-title", "dialog-title"]
```

`components/ui/dialog.tsx` hardcodes `id="dialog-title"` and points `aria-labelledby` at it. **Three dialogs are mounted on Your business at once**, so the attribute resolves to whichever comes first in the document — **not the open one**. A sighted user sees the right title; somebody using a screen reader is told they opened something else.

*Kind: bug. Module: **frontend foundation** — frozen, and squarely §20c's accessibility clause. **Not fixed by this lane**: same component as [B-312](BUGS.md), same reasoning.*

#### PX-303 · Five badge vocabularies and no legend anywhere

`Yours` · `Contested` · `Cooling` · `Evidence expired` · `No change` — on one screen, unexplained. **`Yours` is the worst of them**: it appears on two rows and could mean ownership, assignment, or the seller's own book. A trial user will not ask; they will assume, and half of them will assume wrong.

*Kind: missing explanation. Module: Product Surface.*

#### PX-304 · A list titled "worth a look" includes accounts scoring 10

Three of the twelve score 20, 10 and 10. **The screen promises *"Accounts your evidence says are worth a look"* and then shows accounts the evidence plainly does not.** Either they should not be there, or the promise should be smaller — but as it stands the product contradicts its own headline, which is exactly what a sceptical evaluator looks for.

*Kind: missing business value. Module: Product Surface · `opportunity_engine` owns the threshold.*

#### PX-305 · A sentence that stops halfway

```
Opened at 75, 5 weeks ago      unchanged since
```

**Verified in the DOM**, not an artifact: the element contains those two fragments and nothing else. *Unchanged since* **what?**

*Kind: poor wording. Module: Product Surface.*

#### PX-306 · The account brief has no `<h1>`, and one `<h2>` is empty

The document outline of the product's most-used screen begins at level 2, and its first heading is `H2:""`. **Already filed as [B-313](BUGS.md)**; recorded here because the customer-facing half is different from the accessibility half — the page a seller lives in does not state its own name in its structure.

*Kind: bug. Module: Product Surface.*

#### PX-307 · A disabled button with no name

```html
<button disabled class="… bg-accent text-accent-contrast …">
```

Primary-styled, disabled, and **nothing says what it is or why it cannot be pressed**. *"Why is this button disabled?"* is on the product owner's own list of questions a customer asks.

*Kind: bug + missing explanation. Module: Product Surface.*

### 🟡 Medium

#### PX-308 · The brief has eight sections, four of which sound identical

*Deeper research* · *What this comparison found* · *What contributed* · *The evidence behind this*. A first-time reader cannot tell which one answers *"why should I believe this?"* — and that is the question the whole page exists to answer.

#### PX-309 · Two accounts tie at 75 with identical badges

Databricks and NVIDIA are indistinguishable on the list, and one is above the other. **A ranked list must be able to say why**, or the ranking is decoration.

> **Checked before being written up as worse than it is.** The order looked unstable — Databricks led one walk, NVIDIA the next — which would have been a serious trust defect. **Five consecutive reloads return the identical order**; the two walks ran against different seeds. **Stable, and still unexplained** — a UX finding, not a determinism one.

#### PX-310 · Nothing anywhere says when Signora last looked

No *"as of"*, no *"last synced"*. **A product whose promise is *"here is what changed"* cannot let a seller distinguish *"nothing happened at this account"* from *"nothing has been collected since Tuesday."*** Carried forward from the previous cycle; seen again on every screen of this walk.

#### PX-311 · "Exactly correct until Sep 23, 2026, when the oldest evidence beneath it changes band"

Precise, true, and written by an engineer. *Band* is internal vocabulary ([ADR-0034](architecture/adr/0034-ubiquitous-language.md)) and a salesperson would not use it unprompted.

### 🔵 Future Module

#### PX-312 · An unresolved-records surface

**PX-301's real answer.** Records that no provider has named need somewhere to go, somebody to resolve them, and a way back onto the list once resolved. That is a capability with a bounded context, not a filter — **documented, deliberately not half-built**.

### What is already good, because a review that only complains is not a review

**The empty states are the best writing in the product**, and they were invisible until the environment was cleaned. Every dependent section explains *why* it is empty and what to do about it, in the customer's words:

> **No products yet** — *"Add the first thing your company sells. A name is enough to start."*
>
> **Add a product first** — *"An ideal customer is the kind of company that buys something specific, so there is nothing to describe until you have said what you sell."*

That is a product refusing to show an empty table with a shrug. **It answers *what is happening*, *why*, and *what should I do next*** — three of the questions on the product owner's own list — without being asked.

**The evidence drawer does what it promises.** *"Prove it"* returns `open roles 300→480 · coresignal · Jul 26, 2026`. A number, its source, its date. **A customer can argue with that**, which is worth more than being impressed by it.

**And the product declines to overclaim.** *"Signora has not written one for this account yet"* where a narration is missing; *"Connecting this is not available yet"* on every provider; *"What this cannot tell you"* under every signal, including two more the customer can expand. **A product that volunteers its own limits is the rarest thing on this list**, and it is the strongest reason a sceptic would keep reading.

### Environment — fixed this cycle

#### PX-313 · The review environment showed test data as product data ✅ **FIXED**

The walk found six products named `E2E Product 1785781052731`, a watched company `E2E Company 1785781079694`, and a decision reading `E2E: taking this on 1785781525814` in the account history.

**This lane caused it.** The E2E suite writes through the product — correctly — into the same Playground a reviewer reads. `make e2e` and `make product-demo` both re-seed first; `make review-product` did not.

> **It matters more than it looks.** Nothing was broken, and the product *looked* broken — which is precisely the distinction this register exists to make. A reviewer cannot tell "this product is full of junk" from "the last thing to touch this database was a test."

**Fixed:** `make review-product` re-seeds, like every other command that shows somebody the product.

---

## What the instrument got wrong, recorded rather than quietly dropped

**Three of the first walk's suspicions were artifacts of the review tool, and checking them cost less than reporting them would have.**

| Suspected | Actually |
|---|---|
| `PlaygroundActive` — a name and a status run together | `Playground<span class="ml-2">Active</span>` — **there is a visible gap.** `innerText` concatenates inline elements |
| `NVIDIA Corporationj` — a stray character in a link | A `<kbd aria-hidden="true" class="hidden …">` keyboard hint. **Not visible, not announced** |
| *"What contributed"* lists every line twice | The visible text plus its `sr-only` twin — the same pattern already known from `\d+ of \d+ points` |

> **A review that reports its own artifacts as defects burns the credibility it needs.** The instrument reads `textContent`; a screen reads pixels; and the gap between them is exactly three findings wide on the first attempt.

---

## Review 2 — 2026-08-03 · the accounts the product is not proud of

**Review 1 opened the account at the top of the list, which is the one Signora is proudest of.** This opened the four it is not: the account whose sources disagree about its own name, the one whose evidence has expired, the one being contested, and the one nobody has named.

> **No new dataset was written, deliberately.** `playground@2` already produces every one of those states, and produces them honestly — from provider readings over five months, so *contested* and *stale* **emerge from the pipeline rather than being declared**. Authoring a second messy scenario before reading the first would have proved nothing.

### 🔴 Critical Trust

#### PX-316 · Signora invites you to work an account it cannot name

```
70b04700
— no source has named this account yet
Attention score 33 · 40 of 120 points

  [ I'm working this ]   [ Lost without pursuing ]   [ Not a real opportunity ]
```

**This is [PX-301](#px-301--the-list-a-seller-works-from-contains-an-account-with-no-name), and it is much worse than a bad row in a list.** The account has a full brief, a score, a decomposition, and **three workflow buttons**. A seller can take ownership of it. *Call whom?*

**And the shape of the problem is the interesting part.** Signora knows a great deal about this company:

> *"Researching Design Systems — 4 weeks of elevated activity, peaking at 87"*

**Identity resolution failed and intelligence succeeded.** The product surfaces the second without treating the first as a blocker to action — so the most confident thing on the screen is an invitation to act on a company nobody can identify.

*Category: Critical Trust · GA Blocker. Module: Product Surface · `knowledge_graph`.*

### 🟠 UX

#### PX-317 · The delta sentence is broken in every state, not just one

```
Opened at 33, 5 weeks ago      unchanged since        ← the unnamed account
Opened at 20, 5 weeks ago      -10 since              ← Adobe, cooling
```

[PX-305](#px-305--a-sentence-that-stops-halfway) found the first and assumed it was one screen's typo. **It is the component**: *"since"* trails off in the unchanged case *and* in the changed case. Every brief in the product has a sentence that stops mid-thought.

*Category: UX. Module: Product Surface.*

---

## The reading load, measured rather than argued

**The product owner's observation was *"far too much text… it doesn't feel like modern SaaS."*** That is a number, not an opinion, so here it is — measured on a freshly seeded organization at 238 words per minute.

| Screen | Words | To read | Paragraphs ≥25 words | Things you can do | **Words per action** |
|---|---|---|---|---|---|
| **Attention list** | 169 | 0.7 min | **0** | 13 | **13** |
| Settings | 68 | 0.3 min | 1 | 4 | 17 |
| **Account brief** | **619** | **2.6 min** | 4 | 17 | **36** |
| **Your business** | 344 | 1.4 min | 4 | 6 | **57** |
| **Connections** | 138 | 0.6 min | 0 | **0** | **138** |

### What the numbers actually say

**The density problem is not uniform, and that matters more than the complaint.**

> **The attention list is the best-designed screen in the product** — 169 words, thirteen actions, **not one paragraph over 25 words**. It is scannable, it ranks, and it gets out of the way. Whatever produced it should produce the rest.

**The account brief costs 2.6 minutes of reading before a decision.** A seller with twelve accounts spends **31 minutes reading briefs** before doing any selling. That is the single most quotable number in this review, and it is why *"too much text"* is a commercial problem rather than a taste one.

**Connections is 138 words and zero actions.** A screen that can only be read. Every provider says *"Connecting this is not available yet"*, which is honest — and a whole screen of honesty with nothing to press reads as a stub.

**Your business is 57 words per action** — 24 paragraphs to support 6 controls.

### The paragraph that proves the point

> *"Budget unlocked rests on this business event too, already counted through a higher-weighted hypothesis. Counted once, so the same grounds read two ways cannot inflate the score."*

**That is an engineer explaining a de-duplication rule to a salesperson**, on the screen where they are deciding whether to make a call. The *idea* is excellent — double-counting would inflate scores and Signora refuses to. **The idea deserves a badge, not two sentences.**

### What this suggests, concretely

| Today | Could be |
|---|---|
| Two sentences explaining de-duplication | A **`counted once`** chip, with the sentence on hover |
| *"Exactly correct until Sep 22, 2026, when the oldest evidence beneath it changes band"* | **`accurate until 22 Sep`**, expandable |
| *"What this cannot tell you"* × 3 per signal, all expanded | **One `limits` disclosure per signal**, collapsed by default — it is already collapsible for two of the three |
| Eight full-width prose sections | **Three columns**: what changed · why it scores · what to do |
| A section header plus a paragraph explaining the section | **Header only.** If a section needs a paragraph to justify existing, that is a finding about the section |

*Category: UX. Module: Product Surface.*

---

## Product completeness — what a buyer expects and cannot find

**Asked deliberately without looking at the implementation:** *if I had never seen this codebase, what would I expect from a Revenue Intelligence platform in 2026?*

### The navigation answers most of it before I finish asking

```
Attention  → /
Settings   → /settings
```

**Two items.** That is the entire product surface a customer can reach. Everything else is reached by clicking a row.

### Missing capabilities, ranked by how early a trial hits them

| # | Missing | When they notice | Why it matters |
|---|---|---|---|
| **MC-1** | **Search.** No way to find an account by name | **Minute two.** *"Show me Databricks"* | A ranked list is not a way to answer *"what about this one?"*, and it is the first thing anybody tries |
| **MC-2** | **Filters and saved views** — by score, posture, owner, freshness | Minute five | Twelve accounts scroll. Two thousand do not. **This is the capability that decides whether Signora survives real volume** |
| **MC-3** | **People.** The buying committee is *job titles*, never names | First real account | *"Who do I call?"* is the question a seller actually has. ZoomInfo and Apollo answer it; Signora describes the shape of the committee and not its members |
| **MC-4** | **CRM write-back.** Salesforce and HubSpot read *"not available yet"* | During evaluation | Without it Signora is a second system to check. **Every competitor writes back**, and RevOps will ask in the first call |
| **MC-5** | **Notification or digest** — nothing tells you something changed | Day two | A product whose value is *"here is what changed"* requires you to come and look. **The value is time-sensitive and the delivery is not** |
| **MC-6** | **A manager view.** No roll-up, no team pipeline, no coverage | First demo to a VP | The buyer is a CRO. **There is no screen addressed to them** |
| **MC-7** | **Export** — no CSV, no share, no link to a brief | First time they want to forward one | *"Can you send that to me?"* has no answer |
| **MC-8** | **Guided first run.** A new organization gets correct empty states and no path | Minute one | The empty states are excellent (see strengths) and none of them *starts* anything |

*Category: Missing Capability. MC-1, MC-2 and MC-4 are **GA Blockers** in my judgement; the rest are sequencing.*

### Where Signora is genuinely ahead

**This is not politeness — it is the part of the product a competitor cannot copy quickly.**

| | |
|---|---|
| **Every claim decomposes to a provider reading with a date** | `open roles 300→480 · coresignal · Jul 26 2026`. **Gong, 6sense and Common Room all present scores; none lets you take one apart to a single reading.** |
| **The product states its own limits, unprompted** | *"What this cannot tell you"* under every signal, twice more on expansion. **Nobody ships this**, because it reads as weakness until you have been burned by a confident wrong score |
| **Disagreement is disclosed rather than resolved silently** | *"Your sources disagree on this name. Showing what crunchbase reported most recently, of 2 sources that named this account."* **This is the single best interaction in the product** |
| **Decay is visible** | *"Evidence aged out"*, *"Cooling"*, *"-10"* — the score is allowed to fall, and says why |

> **On messy data Signora is more impressive than on clean data**, which was the opposite of what I expected walking in. The disagreement disclosure and the ageing evidence are the strongest arguments for buying it — and both are only visible on the accounts a demo would avoid.

---

## Proposed information architecture

**Not a redesign to implement — a shape to grow into**, revisited as modules land. The problem with two nav items is not that it is small; it is that **the first three additions will be appended rather than placed.**

```
INTELLIGENCE          what Signora thinks
  Attention           the ranked list                    ← exists
  Accounts            all of them, searchable, filtered  ← MC-1, MC-2
  Signals             what changed, across the book      ← MC-5
  Research            deep comparisons, and their results ← exists, buried on the brief

SELL                  what a person does
  My work             taken, contested, waiting
  Team                roll-up for a manager              ← MC-6

YOUR BUSINESS         what Signora needs from you
  Products · Ideal customers · Buying committees · Focus · Watchlist
                                                        ← exists, one long page today

PLATFORM
  Connections         providers                          ← exists
  People              members and roles                  ← exists, buried in Settings
  Organization        name, billing later
```

**Three judgements behind it.** *Intelligence* and *Sell* separate **what the product knows** from **what a person is doing** — the line every mature platform eventually draws, and the one that lets a manager view exist at all. **Your business is a section, not a page**: five capabilities on one scrolling page is why it measures 57 words per action. And **Research already exists but is reachable only from inside an account**, which is why nobody would discover it.

*Category: UX / Future Product. Raised for the product owner; **nothing built.***

---

## Review 3 — 2026-08-03 · the first hour

**A person who has never existed signed up through the real form.** `priya.raman.…@northwind.example`, a real password, the product's own sign-up route. No seeding.

> **Honest scope: this is the first *ten minutes*, not the first hour.** The walk stopped at the organization gate because the instrument never pressed *Create an organization*. Everything below is what happens before that button, and it is enough.

### 🔴 Critical Trust · GA Blocker

#### PX-319 · Nobody has ever walked in through the front door

```
2 · The moment after signing up
  │ Confirm your email
  │ We sent a link to priya.raman.…@northwind.example. Follow it and you will be signed in.

  next steps offered: Send the link again · Back to sign in
```

**The link is written to the dev server's stdout.** `console` is the only transport this build has, and `loadAuthConfig` refuses to start in production with it — which is correct engineering and has a consequence nobody has stated:

> **In every environment this team possesses — including Human Review — a new customer's first hour ends at *"check your email"*, and the link is in a terminal.**

**Every account that has ever existed in Signora was created by `demo-users.ts`**, which mints a verification token and redeems it through `auth.api.verifyEmail` — **skipping the front door entirely**. So the sign-up flow is fully implemented, carefully written, and **has never been walked end to end by a human being.**

**This is the same shape as the finding that created this lane.** *Every component proven; the composition never exercised.* There it was the browser's route to the API; here it is the path a customer takes to become one.

**What is not claimed:** that production will lack a transport. That is a deployment decision belonging to M14.5, and it is raised as [C-320](LANE_COORDINATION.md) rather than assumed. **What is claimed** is that until one exists somewhere, *no one can review the most important hour in the product*, and the register should say so.

*Category: Critical Trust · GA Blocker. Owner: product owner / M14.5 deployment.*

### 🟢 Product Strength

#### PX-321 · The organization gate is the clearest screen in the product

```
  │ You are not part of an organization yet
  │ Your organization is your company on Signora — where its accounts, evidence
  │ and decisions live. Create one, or ask a colleague to add you to theirs.
  │ [ Create an organization ]
```

**One sentence of what it is, one of why it matters, and both routes out** — create one, or be added to one. **One button.** Nothing else on screen.

Measured against everything else in this register: **13 words per action on the attention list, 138 on Connections — and this screen is a single decision.** It is the strongest evidence that the product's writing problem is one of *editing*, not of ability. Somebody here knows exactly how to do this.

### 🟡 UX

#### PX-322 · Every address collapses to one screen, silently

`/settings`, `/settings/products` and `/settings/connections` all render the organization gate **at URL `/`**. The gating is right — there is nothing to configure without an organization. **The silent rewrite is not**: a customer following a shared link to Connections lands on Attention with no explanation, and the address they typed is gone.

*Category: UX. Module: Product Surface.*

---

## Missing capabilities, classified

**As requested, each is now classified by *when it is needed* rather than by how much it is wanted.**

| # | Capability | Classification | Why that classification |
|---|---|---|---|
| **MC-1** | **Search** — find an account by name | **Essential for GA** | *"Show me Databricks"* is the first thing every evaluator types. A ranked list cannot answer it |
| **MC-2** | **Filters and saved views** | **Essential for GA** | Twelve accounts scroll; two thousand do not. **This decides whether Signora survives a real book** |
| **MC-4** | **CRM write-back** (Salesforce, HubSpot) | **Enterprise requirement** | RevOps asks in the first call. Without it Signora is a second system to check, and adoption dies quietly |
| **MC-3** | **People** — the committee as names, not job titles | **Important within six months** | *"Who do I call?"* Signora describes the shape of a committee, never its members. ZoomInfo and Apollo answer this |
| **MC-5** | **Notification or digest** | **Important within six months** | A product about *what changed* that requires you to come and look. **The value is time-sensitive; the delivery is not** |
| **MC-6** | **A manager view** — roll-up, coverage, team | **Important within six months** | The buyer is a CRO and **there is no screen addressed to one** |
| **MC-8** | **Guided first run** | **Important within six months** | Excellent empty states, none of which *starts* anything |
| **MC-7** | **Export / share a brief** | **Nice to have** | *"Can you send me that?"* has no answer, but a screenshot suffices at first |
| **MC-9** | **Explainable scoring as a public artifact** | **Competitive advantage** | Every claim already decomposes to a provider reading with a date. **No competitor can copy this quickly** — it is a consequence of the architecture, not a feature |
| **MC-10** | **Activity capture** (email, calendar) | **Future platform capability** | Gong and People.ai are built on it. Signora lists the connectors and offers none — a deliberate, correct *"not available yet"* |

---

## Navigation — challenged, and a second proposal

**The product owner's example was five groups.** Working through it as each persona, three things did not survive.

| Challenged | Why |
|---|---|
| **Sales** containing *Outreach · Meetings · Tasks* | **Signora does not send, schedule or track anything, and should not.** Putting three empty sections in the sidebar advertises absence on every screen. A nav item is a promise |
| **Customers** as a top-level group | A seller does not think *"I will go to Customers"* — they think about **an account**. Accounts are a destination reached from work, not a section of a product |
| **AI Insights** as its own item | **The AI is not a place.** Every insight in Signora is attached to an account, and a separate AI section is how a product signals that its intelligence is a bolt-on |

### The proposal

```
WORK                  what I am doing today
  Attention           the ranked list                     ← exists
  My accounts         taken, contested, waiting on me     ← MC-2
  Team                roll-up, for a manager              ← MC-6

INTELLIGENCE          what Signora knows
  Accounts            all of them, searchable             ← MC-1, MC-2
  Signals             what changed, across the book       ← MC-5
  Research            deep comparisons and their results  ← exists, unreachable

YOUR BUSINESS         what Signora needs from you
  Products · Ideal customers · Buying committees · Focus · Watchlist
                                                          ← exists, one long page

ADMINISTRATION
  Connections · People · Organization
```

**The judgement that changed from the first proposal:** *Work* comes before *Intelligence*, and it is a separate group rather than a heading inside one.

> **A seller does not open a Revenue Intelligence platform to browse intelligence. They open it to find out what to do before their first call.** Gong opens on *your* calls. Salesforce opens on *your* pipeline. **Signora already gets this right with Attention** — the proposal simply gives that instinct a home to grow in, instead of filing it under a section named after the technology.

**Search belongs in the header, not the sidebar** — it is a verb, not a place.

*Category: Navigation / Information Architecture. **Nothing built.** Raised for the product owner.*

---

## The unnamed account — challenged as philosophy, not as a screen

**[PX-301](#px-301--the-list-a-seller-works-from-contains-an-account-with-no-name) and [PX-316](#px-316--signora-invites-you-to-work-an-account-it-cannot-name) asked for a fix. The better question is what should be true.**

| Question | My answer, and it is arguable |
|---|---|
| Should an unnamed company **appear** at all? | **Yes** — hiding it loses real intelligence. Four weeks of research on Design Systems is worth knowing about |
| Should it appear **on the working list**? | **No.** The list answers *"who should I call?"* and this record cannot be called |
| Should it **contribute to a score**? | **Yes.** The score measures the evidence, and the evidence is real. Identity is a separate axis from significance |
| Should it become an **opportunity**? | **No.** An opportunity is something a person can pursue |
| Should it be **workable** — *"I'm working this"*? | **Never.** This is the sharpest edge: today those buttons are offered |
| What should it be? | **`Needs identity` — a queue, not a filter.** Records arrive, somebody resolves them or dismisses them, and a resolved one joins the book with its evidence intact |

> **The principle underneath: identity and significance are different axes, and Signora currently multiplies them into one list.** A record can be highly significant and unidentifiable; that combination is *interesting*, and it is not *actionable*. **Every product that gets this wrong gets it wrong the same way** — by treating "we do not know who this is" as a display problem rather than as a state with its own workflow.

*Category: Future Product — see [PX-312](#px-312--an-unresolved-records-surface). **Documented, deliberately not half-built.***

---

## Persona lenses — what each would say after an hour

| Persona | The sentence they would say |
|---|---|
| **SDR** | *"Where are the contacts? I can't call a company."* — MC-3 |
| **AE** | *"This is the best explanation of why an account matters I have seen. Now how do I find the ones I already own?"* — MC-1, MC-2 |
| **Sales Manager** | *"There is no screen that shows me my team."* — MC-6 |
| **CRO** | *"Nothing here is addressed to me."* The buyer has no view — MC-6 |
| **RevOps** | *"Does it write back to Salesforce?"* No. **This is the first question and the shortest conversation** — MC-4 |
| **Founder** | *"It tells me what it cannot tell me. I have never seen a vendor do that."* — the strongest reaction available today |
| **Procurement** | *"Who else uses it, what is the SLA, where is the data held?"* **None of it exists**, and none of it is this lane's to build |
| **Enterprise evaluator** | *"SSO, SCIM, audit log, retention."* Better Auth covers sign-in; the rest is unbuilt |
| **Customer Success** | *"What does an unhealthy account look like?"* Signora scores opportunity, never risk |
