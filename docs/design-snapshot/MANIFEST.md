# Design Snapshot — the implementation authority for this wave

**Created 2026-08-06 by Lane C · Product Office, on [D-138](../DECISION_REGISTER.md).**

> ## ⛔ **Every implementation lane works from these files. Not from the upstream project, and not from a copy of them.**

| | |
|---|---|
| **Snapshot date** | **2026-08-06**, ⚡ **partially refreshed 2026-08-08 — see the refresh record below** |
| **Upstream authority** | **Claude Design project `1d043179-1ee9-4c9f-b59e-592e04297cad`** — *"Signora design system specification"* |
| **Upstream reference** | `https://claude.ai/design/p/1d043179-1ee9-4c9f-b59e-592e04297cad` |
| **Design system** | **Modernist** — `c798a756-9b5d-4587-a7bc-6f61a447ebab`, the version every screen links |
| **Design version** | ⚠️ **The project exposes none.** **This snapshot's identity is the content hashes below** — stated rather than invented |
| **Contents** | ✅ **31 files · 2,286,072 bytes · 29 screen designs** — **re-measured 2026-08-10 by [TASK-1455](../BACKLOG.md), never transcribed forward.** ⚡ **The snapshot now holds every `Fortune Signora` screen the upstream project has: 29 of 29** |
| ⚠️ **Why the previous total did not reconcile** | ⛔ **This row read *"28 files · 2,124,212 bytes · 27 screen designs"* and had been WRONG SINCE 2026-08-08.** ⚡ **Adding the two new designs to the old total gives 2,215,560 — 70,512 short of the measured 2,286,072, and the gap is the finding.** 📁 **Measured by `git log --diff-filter=A`: `Fortune Signora Authenticated Entry.dc.html` was added 2026-08-08 and `Fortune Signora Entry Coverage Review.dc.html` on 2026-08-09, and NEITHER updated this header.** 🔴 **[§2](../../CLAUDE.md) — *the repository itself should always tell the truth* — and a summary row that silently stops counting is the same defect class as the count that hid the two missing designs for three days. ✅ **Recorded rather than quietly overwritten** |

> ## ✅ RESOLVED 2026-08-10 by [TASK-1455](../BACKLOG.md) — both designs are in the snapshot
>
> | Retrieved | Bytes | SHA-256 |
> |---|---|---|
> | `screens/Fortune Signora ICP Builder.dc.html` | **45,852** | `ab4e9438a7d06c19` |
> | `screens/Fortune Signora People Intelligence.dc.html` | **45,496** | `b97bd11ab8bf08ea` |
>
> ⚠️ **Both were TRANSCRIBED, not binary-copied** — `DesignSync · get_file` returns content through a session's context, so writing it to disk is the drift risk [D-137](../DECISION_REGISTER.md) forbids. **This is the same disclosure `design-system/styles.css` already carries below, and the same reason it is acceptable: the check, not the intention.** ✅ **Verified structurally rather than asserted** — sc-for blocks balanced open-to-close (11 and 14), `x-dc` balanced, 29 `crit()` calls corroborated by the ICP design's own prose *"All 29 map to a field"*, 7 contacts, 6 timeline entries, 30 `&quot;` entities each, the `/[^\d.]/g` regex intact across the JSON boundary, and the characters most likely to be lost in transit present: the curly apostrophe, both curly quotes, `Sørensen`, `Køhler`, `→`, `✦`, `✉`.
>
> ⛔ **The record below is NOT rewritten** ([§2](../../CLAUDE.md) — *a record of what was true then must not be rewritten to match now*). **It is why this took until 2026-08-10, and it is the more useful half.**
>
> ---
>
> ## 🔴 The two designs no lane has ever been able to read *(the dated record, kept)*
>
> **Measured 2026-08-09 by `DesignSync · list_files` against project `1d043179-1ee9-4c9f-b59e-592e04297cad`, on the product owner's [D-222](../DECISION_REGISTER.md) instruction.**
>
> | Absent from this snapshot | Upstream | Named as authority in [D-222](../DECISION_REGISTER.md) §1? |
> |---|---|---|
> | **`Fortune Signora People Intelligence.dc.html`** | ✅ present | ✅ **yes** |
> | **`Fortune Signora ICP Builder.dc.html`** | ✅ present | ⛔ **no — and it exists anyway** |
>
> 🔴 **CORRECTED 2026-08-09, and the correction is worse than the claim it replaces.** ⛔ **This note first said the manifest *"named neither"* and that *"a count is not actionable"*.** ⚡ **It named both.** 📁 **Line 113, in the Entry Coverage Review refresh record: *"`ICP Builder` and `People Intelligence` remain unimported — the debt recorded in the 2026-08-08 refresh below still stands and is now one cycle older."*** ⛔ **So the record was actionable, it named the two files, it flagged the debt as ageing, and it said so twice on two separate days.** 🔴 **Nobody acted — including this office, across [478](../architecture/478-design-conformance-audit.md), [498](../architecture/498-common-platform-audit.md) and [499](../architecture/499-implementation-design-reconciliation.md).** ⚠️ **I then read the summary row at the top of this file, saw a count, and asserted something about the whole document. The failure is not the record's shape; it is that a named, dated, ageing debt was read past three times.**
>
> 🔴 **And both have implementations already.** ⛔ **`frontend/components/commercial/icp.tsx` — 437 lines, shipped 2026-08-04 — was built while its design sat unread upstream.** ⛔ **`backend/modules/people/` has a full domain, application, infrastructure and `public/`.** ⚡ **Six backlog rows name ICP or People.**
>
> ✅ **So [D-222](../DECISION_REGISTER.md) §15 already has a partial answer, and it is *no* for at least these two capabilities** — **not because a lane built against an old design, but because the finalized design was never made reachable.** ⛔ **Retrieving them is [TASK-1455](../BACKLOG.md) and it is the first action of the D-222 audit, not a step within it: an audit against an incomplete authority cannot be authoritative** ([D-138](../DECISION_REGISTER.md)).
| **Retrieved with** | `DesignSync` · `get_file`, one call per path |

---

## Verified, not assumed

⚡ **A screen was re-fetched after harvesting and compared byte-for-byte:** `Fortune Signora Reports.dc.html` — **48,859 bytes, SHA-256 `7c0f92bf50b16a67…`, identical.** **The screens are upstream content, not a rendering of it.**

⚠️ **`design-system/styles.css` is the one file transcribed rather than harvested**, because it is small enough to arrive inline. **It is verified against the upstream `_ds_manifest.json`'s machine-readable token list — 48 tokens defined locally, 20 spot-checked against upstream values, zero mismatches.** ⛔ **Stated plainly because a transcription is exactly the drift risk [D-137](../DECISION_REGISTER.md) forbids, and the check is what makes it acceptable rather than the intention.**

⛔ **The hashes below are the snapshot's identity.** **A refresh that changes any of them is a new baseline** ([D-138](../DECISION_REGISTER.md)), **and every planned implementation task is assessed against it before the new snapshot propagates.**

---

## No live drift

⛔ **Do not reconnect to the upstream project during ordinary implementation.** ⛔ **Do not pull newer designs silently.** ⛔ **Do not compare against upstream unless the product owner explicitly requests a refresh.**

> **Every lane works from the same revision for the whole wave. That is the point.**

**Accessible to Lane A · Lane B · Lane C · QE with no external access** — ⚡ **which is what removes [C-421](../LANE_COORDINATION.md) as an operational dependency rather than merely closing it.**

**Reference a screen by its path**, e.g. `docs/design-snapshot/screens/Fortune Signora Authentication.dc.html`. ⛔ **A path is a reference. A paraphrase is a second specification.**

---

## Contents

| File | Bytes | SHA-256 |
|---|---|---|
| `design-system/styles.css` | 10,554 | `d2dd60f524bcae23` |
| `screens/Fortune Signora AI Copilot.dc.html` | 78,924 | `de371be8e89dea3b` |
| `screens/Fortune Signora AI Research.dc.html` | 53,918 | `2ba0fbe4fa63f61b` |
| `screens/Fortune Signora Account 360.dc.html` | 110,135 | `efb9b4786c649027` |
| `screens/Fortune Signora App Shell.dc.html` | 135,212 | `9b95979ee6a02ff4` |
| `screens/Fortune Signora Authentication.dc.html` | 73,936 | `c5138337c5437e8e` |
| `screens/Fortune Signora Billing.dc.html` | 83,934 | `ecb0599f6f346001` |
| `screens/Fortune Signora CRM Integrations.dc.html` | 54,011 | `34d0742fa88c0c07` |
| `screens/Fortune Signora Companies.dc.html` | 58,968 | `41628ba95e28b49a` |
| `screens/Fortune Signora Design Review.dc.html` | 50,097 | `43d95bbd2d698546` |
| `screens/Fortune Signora Design System v2.dc.html` | 139,309 | `f6ccb5025837087b` |
| `screens/Fortune Signora Executive Dashboard.dc.html` | 101,630 | `4412b01db33d52c5` |
| `screens/Fortune Signora Global Search.dc.html` | 85,228 | `5539c1a1d5db1a79` |
| `screens/Fortune Signora Help Center.dc.html` | 77,337 | `7eac46ca8ca551bd` |
| `screens/Fortune Signora Notification Center.dc.html` | 78,050 | `79bf15d7ebefbd11` |
| `screens/Fortune Signora Onboarding.dc.html` | 72,986 | `0c1de98d8fd0cd7f` |
| `screens/Fortune Signora Opportunity Intelligence.dc.html` | 66,607 | `ef8719ccd233a129` |
| `screens/Fortune Signora Reports.dc.html` | 48,965 | `7c0f92bf50b16a67` |
| `screens/Fortune Signora Security Center.dc.html` | 86,181 | `563b12635ae4caf6` |
| `screens/Fortune Signora Settings.dc.html` | 52,249 | `51eff41cdef1e649` |
| `screens/Fortune Signora Signal Center.dc.html` | 53,992 | `f4d6e5a923de2f80` |
| `screens/Fortune Signora System States.dc.html` | 76,879 | `8599fd9978345aac` |
| `screens/Fortune Signora Team Management.dc.html` | 81,150 | `a3a9e6a4c591742f` |
| `screens/Fortune Signora User Profile.dc.html` | 72,655 | `4afe93cb1826a2f8` |
| `screens/Fortune Signora Workflow Automation.dc.html` | 54,788 | `d625d2ef310db976` |
| `screens/Fortune Signora Workspace Setup.dc.html` | 89,041 | `b35a3edc1a3e72d5` |
| `screens/Workspace Setup.dc.html` | 88,918 | `25f1f80610ac0e68` |

---

## ⚠️ Two things this snapshot is not

⛔ **Not a specification anybody rewrote.** **These are the upstream files unchanged** — [D-137](../DECISION_REGISTER.md) forbids copied specifications, exported checklists and summarised artifacts, and a byte-identical snapshot is none of those. **It is the same document, stored where the lanes can open it.**

⚠️ **Not evidence of conformance.** **[478](../architecture/478-design-conformance-audit.md) measured the authentication surface against this design and found one of eleven named elements present.** **Having the design and following it are different milestones** — `CLAUDE.md` §20e, *the five product milestones*.

---

## ⚡ Refresh record — 2026-08-09, the Entry Coverage Review

**Instructed by the product owner** ([D-206](../DECISION_REGISTER.md)) **to review `Fortune Signora Entry Coverage Review` as a mandatory architectural review before further Entry decomposition.**

| | |
|---|---|
| **Retrieved** | **`Fortune Signora Entry Coverage Review.dc.html`** — **59,958 bytes** |
| **sha256** | `eeb8c31713bef5aeec4873920423aac9…` |
| **Method** | `DesignSync` · `list_files` then `get_file`, against project `1d043179-1ee9-4c9f-b59e-592e04297cad` |
| **Kind** | ⚠️ **NOT a screen specification** — it draws nothing and specifies no destination. ⚡ **A COMPLETENESS AUDIT of `Fortune Signora Authenticated Entry`** |
| **Authority** | ✅ **THE PLANNING AUTHORITY FOR REMAINING DESIGN WORK** — [D-207](../DECISION_REGISTER.md) §1. ⛔ **NOT an implementation authority**: 📁 its own §07, *"It did not design the missing screens."* ⚡ **A lane implementing from it would build nothing; Product Office plans the design backlog from it** |
| **Answers** | ✅ **Design COMPLETENESS — *can it be built without inventing behaviour?*** ⛔ **NOT design CORRECTNESS — *is the behaviour logically consistent?*** ([D-207](../DECISION_REGISTER.md) §3). **The second is tracked as Design Clarifications in [`LANE_COORDINATION.md`](../LANE_COORDINATION.md)** |

> ## ⛔ **It does not join [D-138](../DECISION_REGISTER.md)'s implementation authority, and the distinction is load-bearing.** **A lane implementing from this document would build nothing — it names owners for gaps and deliberately does not fill them** (📁 its own §07: *"It did not design the missing screens"*). ✅ **The four documents it RECOMMENDS would be implementation authorities; this one is the argument for writing them.**

⚠️ **The upstream project now returns 34 paths.** ⛔ **`ICP Builder` and `People Intelligence` remain unimported** — the debt recorded in the 2026-08-08 refresh below still stands and is now one cycle older.


## ⚡ Refresh record — 2026-08-08, partial and deliberately so

**Instructed by the product owner** ([D-193](../DECISION_REGISTER.md)) **to adopt `Fortune Signora Authenticated Entry` as the authority for all post-authentication behaviour.**

| | |
|---|---|
| **Retrieved** | **`Fortune Signora Authenticated Entry.dc.html`** — **98,921 bytes** |
| **sha256** | `515d333563d4eedcbfe716928ffd2412…` |
| **Method** | `DesignSync` · `get_file`, one call, against project `1d043179-1ee9-4c9f-b59e-592e04297cad` |
| **Workflow** | **29** in [`workflows.toml`](../coordination/workflows.toml) |

### 🔴 The refresh found the snapshot stale by THREE documents, not one

⛔ **`list_files` on the upstream project returns 30 paths where this snapshot held 26.** ⚡ **Two documents besides the instructed one exist upstream and have never been imported:**

| Upstream document | Status here |
|---|---|
| **`Fortune Signora Authenticated Entry.dc.html`** | ✅ **Imported 2026-08-08** |
| ⚠️ **`Fortune Signora ICP Builder.dc.html`** | ⛔ **NOT IMPORTED** — **read and confirmed to exist; a full customer surface with seven criterion groups, a scoring model, TAM funnel, backtest and validation rules** |
| ⚠️ **`Fortune Signora People Intelligence.dc.html`** | ⛔ **NOT IMPORTED** — **listed upstream, not yet read** |

> ## ⛔ **This is [D-138](../DECISION_REGISTER.md)'s own failure mode.** **The snapshot is the implementation authority *because* it is refreshed deliberately — and a deliberate refresh that imports one file while two others sit unimported leaves the authority incomplete in a way nothing detects.**

⚡ **Recorded rather than quietly completed, for two reasons.** ⛔ **① [D-138](../DECISION_REGISTER.md) says *"a refresh is a new baseline"* and *"Product Office assesses whether already-planned work is affected BEFORE the new snapshot propagates"* — importing two further customer surfaces is a second baseline change and deserves its own assessment.** ⛔ **② [TASK-406](../BACKLOG.md) — *an ICP criterion is scored against outcomes* — is `IN PROGRESS` right now, and a design document for that surface arriving mid-slice is exactly the case D-138 asks to be assessed rather than dropped on a lane.**

✅ **Action: both are imported in the next cycle with an impact assessment against [TASK-406](../BACKLOG.md) and the People Intelligence rows ([C-203](../LANE_COORDINATION.md), [C-307](../LANE_COORDINATION.md)).**

