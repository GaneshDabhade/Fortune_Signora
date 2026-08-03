# Product Experience — what would stop somebody buying Signora

> **The register for Product Experience Engineering** (Lane B, mission set by the product owner 2026-08-03).
>
> **One question, asked every cycle:** *"If I were evaluating Signora for my sales organization today, what would stop me from purchasing it?"*
>
> Not *"does it work?"* — that is `BUGS.md`. Not *"is it fast?"* — that is Production Readiness. **This is the register of everything between a trial starting and somebody saying yes.**

---

## How a finding gets here

**By using the product with nobody explaining it.** `make review-product` opens a browser at human pace, and every finding below was seen on a screen rather than inferred from code.

**Every finding is classified twice.** What kind of problem it is, and what it costs a purchase decision — never how hard it is to fix.

| Priority | Means |
|---|---|
| **Critical** | **Blocks adoption.** A trial ends here. Must be fixed before GA |
| **High** | A customer will definitely notice, and it costs trust |
| **Medium** | Improves the experience; schedule it |
| **Future Module** | A real capability. Needs architecture. **Document thoroughly, never half-build** |
| **Nice to have** | Captured, and then left alone |

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
