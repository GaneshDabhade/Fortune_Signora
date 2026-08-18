# 502 · Recovery reconciliation — what survived the interrupted session

**Dated record, 2026-08-18. Lane C, on the product owner's instruction.** ⛔ **A record of what was true then; it is never rewritten** ([§2](../../CLAUDE.md)).

> ## ⚡ **The work is implemented in Lane A's working clone. Portions of it are not yet published.** ⛔ **Unpublished is NOT missing, and the two must never be collapsed.**

## 🔴 Why this record exists

**A session was interrupted mid-verification.** ⚠️ **The recovery brief named eleven commits as evidence of completed work — eight for Companies, `760e8bf6`, `a0fa4a68`, `7afb10c2`.** ⛔ **Every one of them is absent from every published ref**, because the branch was rebased after pushing.

⚡ **SHA identity is therefore not a reliable indicator of whether work survived.** ✅ **Every finding below was measured by CONTENT.**

> ⚠️ **Both lanes nearly mis-filed promoted work within the same hour, by opposite methods.** **Lane C searched for a `companies` route, found none, and nearly filed Companies as missing — it shipped under `/accounts`, which is the rail vocabulary.** **Lane A searched for the eight SHAs, found them on no ref, and nearly concluded the work was orphaned — it was rebased.** ⛔ **Neither method was wrong; both were incomplete, and each would have produced a confident false report.**

## The refs as measured

| Ref | Commit |
|---|---|
| `main` | `2d26cca3` |
| `integration` | `19149dc6` — **1 ahead of `main`** |
| `lane-a-product-surface` | `282960f2` — **2 ahead of `integration`, 18 behind** |
| `lane-c-sync` | `068efc7a` — **12 ahead of `integration`** |

## The reconciliation

| Area | State | Evidence |
|---|---|---|
| **Companies** | ✅ **IMPLEMENTED + PROMOTED** | Shipped as the **Accounts** screen — `frontend/app/(app)/accounts/page.tsx`, **56,413 bytes**, 44 design-marker hits, `OPEN_ACV`/`RENEWAL_DATE`/`COMMERCIAL_STAGE` in the read path. **Byte-identical on all three refs.** Promoted as `7b2b2077..908bd548`, **15 commits, both ends ancestors of `main`** |
| **Onboarding — Welcome · Workspace (03) · You (05) · Goals (06)** | ✅ **IMPLEMENTED + PROMOTED** | 14 files on `main` |
| **Onboarding — introduction · rail** | 🔵 **IMPLEMENTED, UNPROMOTED** | `4e46f818`, `282960f2` on `lane-a-product-surface` |
| **Onboarding — Connect (07) · creating/error (08) · significance (09)** | 🟠 **IMPLEMENTED, UNPUBLISHED** | On **no published ref** |
| **`workspace.slug` · migration `0062`** | 🟠 **IMPLEMENTED, UNPUBLISHED** | ⛔ **Highest published migration is `0060` on every ref** |
| **Home — role-aware composition** | ✅ **IMPLEMENTED + PROMOTED** | `composition.ts` · `activation.ts` · `home-composition.spec.ts`; seller · executive · revenue_operations · activation all present |
| **Home — `/triage` integration · 1360 cap · *See all … in Signals* · Playwright guard** | 🟠 **IMPLEMENTED, UNPUBLISHED** | Zero markers on `main` |
| **`AccountAttention` absent from Home** | ✅ **ALREADY TRUE** | **15 files reference it; ZERO are Home** |
| **Regression** | ✅ **NONE** | ⚡ **Nothing complete-then-broken. Every gap is *never reached a published ref*** |

## 🔴 `AccountAttention` — what a repository-wide deletion would cost

⛔ **The instruction is *do not reintroduce it into Home*, and it is already satisfied.** ⚠️ **The 15 consumers are other surfaces** — Account 360, the `/` attention screen, the triage components, and shared types and hooks. ⛔ **Deleting the symbol repository-wide would strip surfaces nobody asked to change.**

📁 **See also [C-1532](../DECISION_QUEUE.md)**, which asks whether the `/attention` screen survives — **a product decision, and the five orphaned components are measured there.**

## ⚡ The protection this record establishes

⛔ **Unpublished work is PROTECTED work.** **It is never recreated, never cherry-picked from another source, never deleted, never marked missing, and never assigned to a second lane.**

✅ **Publication is the owning lane's responsibility.** ⛔ **A blind force-push is not recommended** — the branch has diverged, and published history is preserved by transferring the unpublished implementation as a controlled patch or commit series.

⚡ **When a promotion candidate is presented, it is compared by CONTENT and not by SHA:** **file comparison · diff against merge-base · the migration graph · affected-module inventory · the relevant tests · headed Playwright verification.**
