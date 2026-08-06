# 478 · Design conformance audit — is the implementation derived from the finalized design?

**Lane C · Product Office · 2026-08-06.** **[D-137](../DECISION_REGISTER.md) §3 and §4.**

> ⛔ **This is not an implementation audit.** **It answers one question: *is the implementation derived from the finalized design documents, or from an earlier implementation or a local interpretation?***

---

# 0 · The audit became possible today, and that is the first finding

**[C-421](../LANE_COORDINATION.md) said no lane could read the design. It was wrong, and this office wrote it.** ✅ **The canonical set is directly readable** — `DesignSync`, project `1d043179-1ee9-4c9f-b59e-592e04297cad`, *"Signora design system specification"*, **26 screen documents**, `canEdit: true`.

⚠️ **So this audit could have been run two days ago**, and every classification below is evidence that was available and ungathered.

---

# 1 · The five classifications, and what each required

**[D-137](../DECISION_REGISTER.md) §5: *"Do not assume compliance based on dates or commit messages."*** **Dates are used here only to bound the question; the classification rests on measured content.**

| Evidence used | How |
|---|---|
| **The design's own named elements** | Extracted from `Fortune Signora Authentication.dc.html` — **73,728 characters, read in full** |
| **Presence in implementation** | Searched **71 `.tsx` files** across `app/(auth)`, `app/(app)` and `components/` |
| **Design references in code** | `grep` for `410-approved`, `Design System v2`, `.dc.html` across `frontend/app` and `frontend/components` |
| **Implementation history** | `git log --diff-filter=A` per file, against the design's landing date |

---

# 2 · ⚡ The measurement — Authentication

**The design names these. The implementation contains one of them.**

| Design element | In the implementation? |
|---|---|
| **Verify your email** | ✅ **present** |
| **Keep me signed in for 30 days** | ⛔ absent |
| **Use single sign-on** · the SSO surface | ⛔ absent |
| **Send reset link** | ⛔ absent |
| **Confirm password** | ⛔ absent |
| ***"This signs you out of…"*** | ⛔ absent |
| **Password updated** · **Continue to Signora** | ⛔ absent |
| ***"This invitation has expired"*** · **Request a new invitation** | ⛔ absent |
| ***"Your session expired"*** | ⛔ absent |
| ***"You're signed in as"*** | ⛔ absent |

> ## **1 of 11. And the design also specifies states the implementation has no equivalent of at all — an SSO failure path (*"Okta rejected the sign-in"*) and an invitation acceptance screen (*"Anders Hald invited you"*).**

⛔ **`grep` for any reference to the canonical design across `frontend/app` and `frontend/components` returns nothing.** **No implementation file cites a design document.**

---

# 3 · Classification — the eight screens [D-137](../DECISION_REGISTER.md) §4 names

**The finalized design landed `2026-08-04`.**

| Screen | Created | Last touched | Classification |
|---|---|---|---|
| **Sign in** | 2026-08-01 | 2026-08-03 | 🟠 **Legacy implementation** — predates the design; **1 of 11 elements match** |
| **Registration** | 2026-08-01 | 2026-08-01 | 🟠 **Legacy implementation** — untouched since three days before the design |
| **Email verification** | 2026-08-01 | 2026-08-01 | 🟠 **Legacy implementation** — ⚡ **the one element that matches lands here, and it matches by coincidence of wording, not derivation** |
| **Forgot password** | 2026-08-01 | 2026-08-01 | 🔴 **Diverged** — the design's *Send reset link* is absent |
| **Reset password** | 2026-08-01 | 2026-08-01 | 🔴 **Diverged** — *Confirm password*, *Password updated*, *Continue to Signora* and the *signs you out of* warning are all absent |
| **Workspace Setup / Creation** | 2026-07-28 | 2026-08-04 | 🔴 **Diverged** — ⚠️ **a text field inside `settings/page.tsx`; the design is a separate screen.** **Touched on the design's landing date, and by [TASK-448](../BACKLOG.md) tokens rather than by this design** |
| **Team Management** | 2026-08-02 | 2026-08-04 | 🟡 **Partially aligned — and it is the only genuinely ambiguous one.** **8 commits, last on the design's own landing date.** ⛔ **Concurrent, not derived: no file references the design** |
| **Workspace Invitation** | 2026-08-05 | 2026-08-05 | 🟡 **Partially aligned** — ⚡ **built *after* the design and is the only one that could have been derived from it.** ⛔ **But *"This invitation has expired"* and *"Anders Hald invited you"* are both absent, so it was not** |

> ⛔ **Nothing is classified *Final design compliant*.** ⚡ **And nothing is classified *cannot determine* — the design was readable, so that category does not apply to this audit.**

---

# 4 · The finding, stated once

> ## **No UI in this repository is derived from the finalized design. Every screen examined was built from an earlier implementation or a local interpretation, and none references a design document.**

⚠️ **That is not a criticism of the lanes.** **Five of the eight predate the design entirely**, and the three that do not **could not read it** — because [C-421](../LANE_COORDINATION.md) said so, and [C-421](../LANE_COORDINATION.md) was this office's error.

---

# 5 · Backlog impact — [D-137](../DECISION_REGISTER.md) §6

⛔ ***"Do not create refinement work simply because a screen predates the design."*** **Measured differences exist, so the existing rows stand and gain evidence; no new row is created.**

| | |
|---|---|
| **[TASK-467](../BACKLOG.md)** authentication surface | ✅ **Confirmed as refinement, and now sized: 10 of 11 named elements absent, plus two states with no equivalent** |
| **[TASK-468](../BACKLOG.md)** Workspace Setup | ✅ **Confirmed as *replace entirely*** — the measurement supports what the row already said |
| **[TASK-471](../BACKLOG.md)** Team Management | ⚡ **The row asked whether this is a refinement or a no-op. It is a refinement** — concurrent with the design and not derived from it |
| ⛔ **No new row** | **Registration, verification, forgot- and reset-password sit inside [TASK-467](../BACKLOG.md)'s scope already** |

✅ **All three are unblocked as of today** — [C-421](../LANE_COORDINATION.md) is closed.

---

# 6 · What this audit did not do

⛔ **It measured one design document of twenty-six.** **Authentication was chosen because [D-137](../DECISION_REGISTER.md) §4 names it first and because eight of its screens cluster around the design transition.**

⚠️ **The other twenty-five are unaudited, and the finding above should not be assumed to hold for them** — **it is *likely*, since no implementation file anywhere references a design document, but likely is not measured.** ⚡ **Per-screen conformance belongs in each refinement slice's own gap analysis, which is where [D-129](../DECISION_REGISTER.md) puts it.**
