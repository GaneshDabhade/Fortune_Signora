# 489 · The legacy UI standards audit — how many competing visual languages the repository actually exposes

**Lane C · Product Office · 2026-08-07.** **[D-154](../DECISION_REGISTER.md) — the finalized Signora Design System supersedes all legacy UI.**

> ⛔ **[D-154](../DECISION_REGISTER.md) asks one operational question and this document answers it: *"There must never be multiple competing UI standards inside the repository. The repository should expose exactly one active visual language."*** **So: how many are there, where are they, and what has to be removed or archived?**

---

## 0 · The answer, before the evidence

> ## ✅ **① There is exactly one file in this repository that asserts a visual value: `frontend/app/globals.css`. Everything else — the Tailwind config, the theme module, the token test, every component — holds names and no values.**
>
> ## ⛔ **② But that one file is comprehensively the wrong standard. Zero of the design's sixteen colours. A radius scale shifted one whole step. Cool-grey shadows. No easing token. And the product declares no font at all, where the design specifies Archivo.**
>
> ## ⚠️ **③ There is no obsolete UI *documentation* to archive, and that is a finding rather than an absence of work. Seven candidate documents, zero style assertions between them, three already carrying supersession notices. The competing standard was never in the docs. It was in one CSS file the whole time.**

---

## 1 · ✅ The sweep — where a visual standard could be hiding, and whether it was

**[D-154](../DECISION_REGISTER.md) names nine categories. Each was searched across the whole frontend, and each search was run with a control so a zero means *absent* rather than *the pattern was wrong*** — **[487](487-legacy-ui-migration-status.md) records a sweep that returned zero for every pattern because a pathspec matched nothing, and that is not repeated here.**

| [D-154](../DECISION_REGISTER.md) names | Where it would live | Measured |
|---|---|---|
| **Obsolete colour palettes** | Tailwind palette classes in components | ⛔ **1 hit, and it is inside a comment** — `globals.css:11`, explaining why `bg-slate-50` is forbidden. ✅ **Zero in code** *(control: `bg-surface` appears in 30 files)* |
| **Obsolete design tokens** | hex or `rgb()` literals in `.ts`/`.tsx` | ✅ **Zero** |
| **Obsolete typography rules** | arbitrary `text-[…]` | ⛔ **2 hits, both inside `globals.css` comments** recording the values a slice removed. ✅ **Zero in code** |
| **Obsolete spacing rules** | a second spacing scale | ✅ **None exists** — ⚠️ **and see [§3](#3--what-the-repository-has-no-standard-for-at-all), because *none* is its own problem |
| **Obsolete component standards** | `components/ui` | ✅ **Thirteen components, no literal colour in any of them** |
| **Obsolete styling conventions** | `tailwind.config.ts` · `lib/design/theme.ts` | ✅ **Neither holds a value.** **The config maps semantic names onto CSS custom properties; the theme module stamps `data-theme` and knows no colour** |
| **Obsolete shell definitions** | `--sidebar-width` · `--topbar-height` | ⚠️ **Two values, and the design specifies its own** — measured in [487](487-legacy-ui-migration-status.md) at **0 of 29**, and [TASK-447](../BACKLOG.md)'s |
| **Obsolete layout guidance** | the architecture documents | ✅ **Zero style assertions across all seven candidates** |
| **Obsolete UI documentation** | `docs/` | ✅ **Nothing to archive — [§4](#4--the-documents-and-why-none-of-them-needs-archiving)** |

> ## ⚡ **So the whole competing standard is 48 tokens in one file.** ✅ **A repository that had let literal colours spread would face a rewrite. `design-tokens.test.tsx` has never let one land — it pins no *value*, only the *discipline* — and that single test is the reason [D-154](../DECISION_REGISTER.md) costs one file instead of the frontend.**

⛔ **Do not "clean up" `design-tokens.test.tsx` as part of this migration.** **It is the mechanism, not the obstacle.**

---

## 2 · ⛔ What `globals.css` asserts, against what the design specifies

**48 distinct tokens, each declared twice — once on `:root`, once on `:root[data-theme='dark']`.** **The design declares 38.**

### Colour — 0 of 16

**Measured in [488 §2](488-workflow-1-login-gap.md) and not repeated: not one of the design's sixteen hex values appears in `globals.css`.** ⚡ **The palette is Tailwind's default `slate` and `blue` ramps** — `--color-canvas: 248 250 252` is `slate-50`; `--color-accent: 37 99 235` is `blue-600`; `--color-content: 15 23 42` is `slate-900`. ⛔ **Design System v2's `Critique of Version 1` names that exact failure twice — *"cool greys"* and *"accent-as-alarm"*.**

### Radius — the scale is the design's, shifted one whole step down

| Step | `globals.css` | The design | |
|---|---|---|---|
| **`xs`** | ⛔ **absent** | **4px** | |
| **`sm`** | **4px** | **6px** | 🔴 **one step tight** |
| **`md`** | **6px** | **8px** | 🔴 **one step tight** |
| **`DEFAULT`** | **8px** | ⛔ **no equivalent** | **the extra step that causes the shift** |
| **`lg`** | **12px** | **12px** | ✅ |
| **`xl`** | **16px** | **16px** | ✅ **added by [TASK-478](../BACKLOG.md)** |
| **`2xl`** | ⛔ **absent** | **20px** | |

> ⚡ **The repository already knew, and wrote it down rather than fixing it.** **`globals.css:92`: *"The design also renames the lower steps (its `md` is 8px where this scale's is 6px); renaming them is a value change across every rounded corner in the product and is not this slice's."*** ✅ **That was the right call for slice 3 and [D-154](../DECISION_REGISTER.md) is what settles it** — **the design wins, always** — **so the deferral now has an owner and a workflow instead of a comment.**

### Elevation — 3 against 4, and all three are cool

**`--shadow-sm`, `--shadow`, `--shadow-lg` are all tinted `rgb(15 23 42 / …)`** — ⛔ **`slate-900`.** **The design's four are `rgba(33,31,29,…)`** — **a warm near-black, matching its `--ink`.** ⚡ **Even the shadows carry the legacy standard**, which is the design's *"flat planes"* critique showing up where nobody looks for a colour.

### Motion — the token does not exist

**The design declares `--ease: cubic-bezier(.32,.72,0,1)` and gives six durations.** ⛔ **`globals.css` has no easing token.** ✅ **`prefers-reduced-motion` *is* handled globally, which is the half that is usually forgotten** ([488 §1](488-workflow-1-login-gap.md)).

### Typeface — the product declares no font

> ## ⛔ **`grep` for `fontFamily`, `font-family`, `next/font` and `Archivo` across `app/`, `components/` and `tailwind.config.ts` returns *nothing*.**

**The design specifies `--font-body: "Archivo", system-ui, sans-serif`.** ⚡ **The product currently renders in whatever the browser defaults to** — **which is not a *competing* standard, it is the absence of one**, and it is the single change with the widest visible effect per line.

---

## 3 · ⚠️ What the repository has no standard for at all

**[D-154](../DECISION_REGISTER.md) asks for obsolete standards to be removed. Three of the design's standards have no counterpart to remove, because nothing was ever adopted.**

| | The design specifies | The repository |
|---|---|---|
| **Spacing** | **Seven steps — 4 · 8 · 12 · 16 · 20–24 · 40 · 64px** — each with its stated use, and **three named v1→v2 corrections: card padding *"was 16px in v1"* → 20–24 · page margins *"was 32px"* → 40 · section rhythm *"was 48px"* → 64** | ⛔ **No spacing scale.** **Tailwind's default 4px ramp is used directly**, so the three corrections are expressible and unexpressed |
| **Line height** | *"1.6 leading"* — **corrected from v1's 1.55** | ⛔ **Not tokenized** |
| **Hairlines** | *"1px warm hairlines"* — **corrected from v1's 2px dividers** | ⚠️ **`--color-border` exists; its *weight* is per-component** |

⛔ **No row is written for these here.** ⚡ **They are inputs to the token pass [488](488-workflow-1-login-gap.md) already places inside Workflow 1**, and inventing three standards-adoption rows would be exactly the *"temporary engineering infrastructure"* [D-151](../DECISION_REGISTER.md) ⑥ says to prefer a finished journey over.

---

## 3a · Token role coverage — 11 of the design's 38 roles cannot be expressed

**Each of the design's 38 tokens was mapped by *role* onto the repository's set** — ⛔ **by role rather than by name, because the two vocabularies are both semantic and neither is wrong.** `--brand`↔`--color-accent`, `--ink`↔`--color-content`, `--pos`↔`--color-success`, `--e1`↔`--shadow-sm`.

> ## ⛔ **27 of 38 map. Eleven have no equivalent, so the current token set cannot express the design even after every value is corrected.**

**`--font-body` · `--ease` · `--r-xs` · `--r-2xl` · `--bg-rail` · `--ink-4` · `--brand-ink` · `--brand-line` · `--ai-ink` · `--ai-line` · `--e4`**

⚡ **Two patterns, and both matter for Workflow 1.** **① The design gives every accent family three parts — a fill, an *ink* for text on it, and a *line* for its border** (`--brand`/`--brand-ink`/`--brand-line`, `--ai`/`--ai-ink`/`--ai-line`); **the repository has fill and tint only**, which is why a bordered brand-tinted element has no token for its border. **② `--bg-rail` gives the navigation rail its own ground** — ⛔ **and [487](487-legacy-ui-migration-status.md) scored that shell at 0 of 29.**

⚠️ **A name-for-name rename is *not* recommended and is not asked for.** **[D-154](../DECISION_REGISTER.md) makes the design authoritative for *"everything visible to the customer"* — a CSS custom property is not visible to a customer.** ⛔ **Renaming 48 tokens would touch every component for zero visible change**, which is the opposite of what this program is for. ✅ **Correct the values, add the eleven missing roles, keep the names.**

---

## 4 · ✅ The documents, and why none of them needs archiving

**Seven documents were candidates — every one in `docs/` that mentions a design system, a token, a palette, typography or a spacing scale and is not itself an audit.**

| Document | Asserts a style value? | Status |
|---|---|---|
| **[37 — The Product Surface](37-product-surface.md)** | ⛔ **No** | ✅ **Already carries a dated supersession note on its UI half** |
| **[38 — Product Design Principles](38-product-design-principles.md)** | ⛔ **No** | ✅ **Already marked superseded, 2026-07-31** |
| **[43 — Customer Experience Blueprint](43-customer-experience.md)** | ⛔ **No** | ✅ **Already marked *"superseded as the authority on screens, 2026-08-04"*** |
| **[410 — The Approved UI Specification](410-approved-ui-specification.md)** | ⛔ **No** | ✅ **Keep — it is the *record of authority*, not a competing spec.** ⚡ **It already states [D-154](../DECISION_REGISTER.md)'s rule in [D-128](../DECISION_REGISTER.md)'s words: *"The finalized design documents are the authority. Existing code is not."*** |
| **[411](411-ui-convergence-assessment.md) · [413](413-migration-inventory.md)** | ⛔ **No** | ✅ **Measurements, not guidance** |
| **[51 — Implementation Specifications](51-implementation-specifications.md)** | ⛔ **No** | ✅ **Capability specifications; names no visual value** |
| **[`PRODUCT_EXPERIENCE.md`](../PRODUCT_EXPERIENCE.md)** | ⛔ **No** | ✅ **A register of buying objections** |

> ## ⚠️ **Zero of seven asserts a colour, a size, a weight or a spacing value. There is nothing here to remove or archive.**

⚡ **And that is worth stating positively rather than as an empty result.** **[D-137](../DECISION_REGISTER.md) forbids *"a copied specification · an exported checklist · a duplicated design document · a summarized design artifact · an intermediate implementation guide"*, and [D-138](../DECISION_REGISTER.md) made the snapshot the implementation authority.** ⛔ **This audit is the test of whether those rules held. They did** — **no document in this repository has ever become a second visual specification**, which is precisely the failure [D-154](../DECISION_REGISTER.md) is written to prevent.

⚠️ **One exception is named rather than glossed: [`docs/design-snapshot/design-system/styles.css`](../design-snapshot/MANIFEST.md), 10,554 bytes.** ✅ **It is part of the snapshot and is *upstream*, not a repository standard** — **it is the design's own file, and archiving it would be archiving the authority.**

---

## 5 · ⚠️ What [D-154](../DECISION_REGISTER.md) changes about work already prepared

### ① [TASK-467](../BACKLOG.md) is framed as refinement, and [D-154](../DECISION_REGISTER.md) forbids that framing

**The row carries a field titled *"Why this is refinement, not new work"*.** ⛔ **[D-154](../DECISION_REGISTER.md): *"do not approach Workflow 1 as a refinement exercise… Do not begin from the legacy implementation and iterate toward the design. Begin from the design."*** ✅ **Corrected in the row.**

⚡ **The scope does not change and neither does the budget** — **what changes is the starting point, and it is not cosmetic**: iterating from `sign-in-form.tsx` inherits its ordering decision *(password above providers, which the design inverts)*, its labels *(`Email` for `Work email`)* and its card. **Starting from the design inherits none of them.**

### ② [C-432](../LANE_COORDINATION.md) — §20c now forbids what [D-154](../DECISION_REGISTER.md) mandates

**`CLAUDE.md` §20c: *"From M1.5, the frontend foundation is **frozen**… Business milestones **consume** the Design System, Shared Components, Application Shell… they do not modify them,"* permitting change only for a production defect, an accessibility issue, a security issue or an approved RFC.**

> ⛔ **[D-153](../DECISION_REGISTER.md) and [D-154](../DECISION_REGISTER.md) are that approval, and they are ruled by the product owner — so nothing is blocked.** ⚠️ **But `CLAUDE.md` is the constitution a cold session reads first, and it currently reads as forbidding the program.** **§2: *the repository itself should always tell the truth* — and `CLAUDE.md` is the product owner's file, so this office records the inconsistency and does not edit it.**

### ③ What [D-154](../DECISION_REGISTER.md) does *not* answer, and it stays open

**[C-431](../LANE_COORDINATION.md) is unchanged.** ⚡ **[D-154](../DECISION_REGISTER.md) settles *which* authority wins when the design and the code disagree; C-431 is not a disagreement — three controls the design draws have no backing capability at all.** ✅ **It does narrow it: option B — *render the control and route it somewhere* — is now clearly out, because a control that cannot do what it says is not the approved experience either.** ⛔ **A and C remain, and both are the product owner's.**

---

## 6 · ⛔ What is Lane C's here, and what is not

| | |
|---|---|
| ⛔ **Not this office's to change** | **`frontend/app/globals.css`** — **`frontend/` is `product_surface`, Lane A's, by [D-151](../DECISION_REGISTER.md) ① and [`modules.toml`](../coordination/modules.toml).** ⚡ **This office wrote production code into `frontend/lib/auth/` once, before reading its own register ([C-430](../LANE_COORDINATION.md)). It does not do so again** |
| ✅ **This office's** | **The measurement above · the coordination items · the row corrections · publishing all of it where a lane reads on its poll** |

> ⚡ **So the deliverable of this audit is not an edit. It is that the token pass inside Workflow 1 now has an exact target: 16 colour values · a radius scale shifted one step · four warm elevations · an easing curve · a typeface · and eleven roles that do not yet exist.** ⛔ **[488](488-workflow-1-login-gap.md) already places that pass inside [TASK-467](../BACKLOG.md), so no row is created here** — **[D-135](../DECISION_REGISTER.md): a finding becomes an owned action item, never an anonymous backlog row.**

---

## 7 · The one sentence worth keeping

⚡ **[D-154](../DECISION_REGISTER.md) reads as a large ruling and it lands on a small surface, and both facts are true at once.** **It is large because it changes what *counts as authority* for every visible thing in the product.** **It is small because one test — `design-tokens.test.tsx`, written in M1.5 by somebody who could not have known — made sure there was only ever one place for a colour to live.**

> ⛔ **A repository whose conventions are enforced by a machine can change its mind cheaply. One whose conventions were written down could not.**
