# 413 — Migration inventory: frontend artifacts and documentation

> **Lane C — Product Office, 2026-08-04.** Deliverables 8–11 of the Product Transition Directive (Revision 2). Counted from `origin/integration`, not estimated.
>
> **Cleanup occurs only when replacement implementation exists.** Nothing in this document is an instruction to delete anything today.

## 1 · Frontend migration inventory

**Every artifact, classified. `KEEP` — already matches the approved design. `REPLACE` — the capability stays, the implementation converges. `DELETE` — genuinely superseded.**

| Category | Count | | Reason |
|---|---|---|---|
| **API routes** — `app/api/**/route.ts` | 6 | **KEEP** | Auth callback, token, health, integration OAuth start/callback, proxy. **Not presentational. The approved design changes none of them** |
| **`lib/` — client, auth, query, state, design** | 33 | **KEEP** | A redesign does not touch a query key, a JWT verifier or a permission gate. **The single largest KEEP in the repository** |
| **Query hooks** — `lib/query/hooks/**` | 8 | **KEEP** | Typed against backend contracts, not against layout |
| **Auth pages and forms** — `(auth)/**` | 11 | **KEEP** | **The approved design project contains no authentication screens.** Nothing supersedes them |
| **`components/ui/`** | 9 | **REPLACE** | Design System v2 specifies **18 canonical components**. These nine converge into that set; the directory stays |
| **Feature components** — `commercial/`, `intelligence/`, `integrations/`, `shell/`, `timeline/`, `feedback/`, `workspace/`, `team/` | 37 | **REPLACE** | Each backs a capability the approved design keeps. **The capability survives; the markup converges** |
| **App pages** — `(app)/**/page.tsx` | 7 | **REPLACE** | Overview, business, accounts/[id], settings ×4. Every one has an approved successor |
| **Layouts and shells** | 4 | **REPLACE** | The approved **App Shell** is a 22-section specification. **This is where the largest single change lands** |
| **`error.tsx` · `not-found.tsx`** | 2 | **REPLACE** | App Shell §17 specifies error pages render *inside* the shell |
| | | **DELETE: 0** | — |

> **Nothing is classified `DELETE`, and the wording *Superseded by Approved UI Specification* is applied nowhere.** It is reserved for functionality genuinely replaced, and **no shipped screen has an approved successor that removes it.** Applying the phrase early would make it meaningless at the point it is actually needed.

**The honest reading: 58 of 104 frontend artifacts are `KEEP`.** The repository built its foundation before its screens, so the redesign lands almost entirely on the 46 that are screens.

## 2 · Frontend test inventory

| Category | Count | | Reason |
|---|---|---|---|
| **Component tests** — `tests/components/**` | 45 | **REWRITE with their components** | Not before, not separately. A test rewritten ahead of its component asserts a screen nobody has built |
| **E2E specs** — `tests/e2e/*.spec.ts` | 15 | **KEEP** | Property-based, not appearance-based — see §3 |
| **E2E support** — fixtures, page objects, setup | 10 | **REPLACE** | Page objects encode selectors; those move with the markup |
| **Unit tests** — `tests/unit/**` | 10 | **KEEP** | JWT contract, events, keys, owner scope, triage, people, acquisition. **Not UI** |
| **Contract · endurance · review** | 7 | **KEEP** | Not UI |
| | | **DELETE: 0** | — |

**Storybook stories: 0 · Cypress specs: 0 · Visual-regression baselines: 0 · Pixel snapshots: 0.** The directive asks for these to be classified; **they do not exist**, and their absence is deliberate rather than accidental.

## 3 · Why no UI test is deleted

**`e2e/visual.spec.ts` states the reasoning, and it survives the transition unchanged:**

> *"A pixel snapshot of a screen whose content is computed from **today's** dates fails daily and is re-baselined until it asserts nothing… What is asserted instead: **properties a customer would notice and a designer would call a bug**, none of which depends on a pixel — the page never scrolls sideways · nothing is clipped · no text is invisible · no image is broken · the layout does not jump after it loads."*

**Every one of those is also true of the approved design.** So is `consistency.spec.ts`'s question — *does the product agree with itself?* — which the approved design makes **harder and more important**, because sixteen screens share more data than five did.

**Two tests become more valuable rather than less:**

| | |
|---|---|
| **`design-tokens.test.tsx`** | Asserts **no component hardcodes a colour**. Design System v2's whole complaint is that *"every screen re-declares the palette by hand"* — **this test is the guard against the thing the design review measured** |
| **`no-mock-data.test.tsx`** | *"A page built against hand-written JSON encodes a shape the domain does not have; the mock becomes the contract."* **The single most relevant test in the suite while sixteen designed screens are built against a backend that does not yet serve all of them** |

**No backend test is affected by anything in this document.** API, domain, application, repository, integration, security, tenancy, migration and Security Invariant suites are untouched, and the Security Invariants remain undeletable under `CLAUDE.md` §11 regardless.

## 4 · Documentation migration inventory

**`CLAUDE.md`'s reading guide resolves most of this before judgement is applied:** documents `30`+ are *"records and cross-cutting notes — dated; never rewritten. **As history, not as instruction.**"*

**So the audit reduces to one question: is this document a record, or is it an instruction?**

| Document | | Reason |
|---|---|---|
| `39-product-review-findings` · `47-opportunities-and-signals` · `48-customer-journey-review` · `49-end-to-end-product-validation` · `50-product-capability-audit` · `51-implementation-specifications` | **KEEP** | **Every one opens with *"a record, not an instruction"* and carries a date.** Rewriting one to match the approved UI is the failure `CLAUDE.md` §2 names explicitly: *"falsifying history to make the repository look consistent"* |
| `43-customer-experience` | **UPDATE** | Claims to be *"the authoritative description of Signora as a customer meets it — every screen, every route, every journey."* **It is no longer authoritative for screens.** Its gap analysis remains valuable and true; **the authority sentence is now false and must be corrected, not deleted** |
| `38-product-design-principles` | **UPDATE** | States UI principles as instruction. **Design System v2 now specifies tokens, type scale, radius scale and control heights.** Where the two overlap, the design project governs; where 38 states principles the design project does not cover, it stands |
| `51-sales-workspace` | **UPDATE** | Designs an unbuilt landing screen — *"when a salesperson logs into Signora every morning, they should land here."* **The approved Executive Dashboard and App Shell now answer that.** Its reuse audit and its four challenges to the brief remain valid findings and are the reason it is not archived |
| `37-product-surface` | **UPDATE** | The M12 design. **Its backend half shipped and is true** — 46 endpoints exist because of it. Its UI half is superseded. **One note, at the top, distinguishing the two** |
| `PRODUCT_EXPERIENCE.md` · `PRODUCT_REVIEW_PLATFORM.md` | **KEEP** | A standing register and a platform design. **Neither asserts what a screen looks like** |
| **Every ADR** | **KEEP** | **Never rewritten.** ADR-0400, 0401, 0402 gain relevance from this transition and lose no accuracy |
| Lane C packages `400`–`408` | **UPDATE** | Each carries a UI section written before the design project existed. **Replaced by a reference, not by a rewrite** — see §5 |
| | **ARCHIVE: 0 · DELETE: 0** | **Nothing in the repository's documentation is obsolete enough to remove.** Six documents need one corrected sentence each |

> **No architectural history is deleted. No ADR is rewritten. No dated record is altered.** The audit found six documents needing correction and zero needing removal — which is a smaller result than the directive anticipated, and it is what the evidence supports.

**Two of the four corrections were made; two were not, and the reason is ownership rather than effort.**

| | |
|---|---|
| **Made** | `43-customer-experience` — the authority sentence was false the moment the directive landed, and `CLAUDE.md` §2 requires the repository not to assert something untrue about itself. `37-product-surface` — one note distinguishing the half that shipped from the half that is superseded |
| **Not made — `38-product-design-principles`** | **`CLAUDE.md` assigns documents `38` and `39` to QE.** Lane C does not edit them, and *"the design project now governs where they overlap"* is a sentence QE should write after reading both |
| **Not made — `51-sales-workspace`** | **It does not exist on this branch.** It is on `integration`, written by Lane A on 2026-08-03. **Editing it from a branch 151 commits behind creates a conflict for no gain** |

## 5 · What `UPDATE` means for the Lane C packages

**Packages [400](400-epic-c-people.md)–[408](408-revenue-intelligence-platform.md) each carry a *frontend* or *UX* area from the thirteen-area template.** Under [PRODUCT_OFFICE.md §5a](../PRODUCT_OFFICE.md) that half is retired.

**The edit is a substitution, not a rewrite:** the section states **which approved screen consumes this capability**, and stops. **What the screen looks like is no longer the package's to say.**

**Three of the packages change more than a section, and it is worth naming why:**

| | |
|---|---|
| **[400 — Epic C, People](400-epic-c-people.md)** | Its blocking question ❓1 and the approved **People Intelligence** screen are the same question. **The package stops being a proposal about whether people are needed and becomes the implementation of a decision the product has already made** — pending O1 |
| **[402 — Epic F, Workflow](402-epic-f-workflow.md)** | The approved **Workflow Automation** screen specifies simulate-before-run, approve-before-write and reversible-after. **ADR-0402's §2 — a rule publishes an event and calls nothing — is compatible with all three and was written without seeing them** |
| **[404 — Epic G, Copilot](404-epic-g-copilot.md)** | The approved **AI Copilot** specifies **six verbs and no others**, and one contract across 17 surfaces. **That is a tighter specification than the package had**, and it narrows the epic rather than widening it |
