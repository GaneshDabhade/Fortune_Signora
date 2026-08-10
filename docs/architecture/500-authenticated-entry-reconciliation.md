# 500 · The authenticated entry experience, reconciled against what runs

**Lane A, 2026-08-10. [TASK-1456](../BACKLOG.md), under [D-224](../DECISION_REGISTER.md).**

📁 **Design authority**: [`Fortune Signora Authenticated Entry.dc.html`](../design-snapshot/screens/) — ⚡ [`Fortune Signora Entry Coverage Review.dc.html`](../design-snapshot/screens/) is planning authority only ([D-207](../DECISION_REGISTER.md) §1) and is not cited as a requirement anywhere below.

⛔ **This is an audit. It changes no production code, and it does not decide the implementation sequence.** [D-224](../DECISION_REGISTER.md) withdrew the wiring instruction that was in the row, and the withdrawal is taken at face value: nothing here wires `resolveEntry`, [TASK-1401](../BACKLOG.md) stays `BLOCKED`, and [D-205](../DECISION_REGISTER.md) stands.

---

## 0 · How to read the evidence classes, and the one that matters

| | |
|---|---|
| 🟢 | **Correct and reusable — do not touch** |
| 🟡 | **Partially compliant** — a precise correction, not a rebuild |
| 🔴 | **Incorrect** — the design requirement and the conflicting implementation are both cited |
| ⚪ | **Missing** — what was searched is named |
| 🔵 | **UNVERIFIED** — ⛔ **may never be reported as compliant** |

⚡ **Every 🟢 and 🔴 below carries runtime evidence, not source inspection.** [D-224](../DECISION_REGISTER.md) §10 assigns runtime to this lane precisely because source cannot settle it, so the dev server was started on **3300** and every destination the engine can return was requested. **The transcript is §3.**

> 🔴 **The risk this row named before it was met, and it was met.** ⛔ *"Treating [TASK-1400](../BACKLOG.md) as evidence of compliance because it was implemented, tested, covered, reviewed and accepted."* ✅ **It is not treated as evidence.** ⚡ **And the audit's sharpest finding is that TASK-1400's gates were all honest**: the engine it built is faithful to the design, 35 tests pass, and **the product does not contain the behaviour** — because no gate asked whether anything called it.

---

## 1 · What was inherited as proven, and re-measured anyway

📁 **Lane C proved one thing** ([D-222](../DECISION_REGISTER.md) §6): the five exports have zero production callers. ✅ **Re-measured here rather than inherited**, because a count carried from another lane's report is the habit [D-224](../DECISION_REGISTER.md) itself was written to catch.

| Export | References outside `lib/entry/` in `app/` · `components/` · `lib/` · `hooks/` |
|---|---|
| `resolveEntry` | **0 calls.** ⚡ **4 textual hits, all of them prose** in [`app/(onboarding)/onboarding/exit.ts`](../../frontend/app/(onboarding)/onboarding/exit.ts) — §5 below, because that file is not a bystander |
| `resolveWorkspace` | **0** |
| `workspaceHome` | **0** |
| `RULES` | **0** |
| `GATES` | **0** |
| `REASON_CODES` | **0** |

✅ **Indirection ruled out, both ways.** The only `import(` expressions in the tree are `lib/auth/keys.ts:145` (`jose`) and two **type-only** positions in `lib/entry/session.ts`:166 and :168. **No barrel re-export.** ⛔ **Confirmed.**

---

## 2 · The engine itself is faithful. That is the surprise, and it changes what the work is

⚡ **Question A — *is the engine design-compliant* — is the one question with a good answer, and it was checked mechanically rather than by reading.** The design's 24 rules were parsed out of the snapshot's own data array and compared to `REASON_CODES`:

```
design rule order == REASON_CODES order:  True   (24 of 24, position for position)
RULES declares 24 rules, one per code, in the same order
tests/unit/entry-engine.test.ts:            35 tests, green
```

✅ **So the engine is 🟢 in isolation.** 📁 Its own comment is accurate: *"the order is load-bearing and is not alphabetical… reordering this tuple silently reorders the product's routing."*

⛔ **Two rules diverge from the design in what they PRODUCE, and both are 🔴 rather than 🟡** — see rows *Deep link · forbidden* and *Session expiry* in §4.

> 🔴 **The consequence for planning, stated plainly: this is not a rework.** ⛔ **Nothing in `lib/entry/` needs rebuilding.** ⚡ **The gap is entirely in the two things around it — nothing invokes it, and almost nothing it can return exists.**

---

## 3 · Runtime evidence — every destination the engine can return, requested

**Lane A dev server, port 3300, 2026-08-10.** ⚡ **`404` and `307` separate cleanly**: Next.js matches the route *before* `(app)/layout.tsx` runs its session check, so **`404` proves the route does not exist** and **`307 → /signin` proves it does and is gated.**

| Requested | Result | Reading |
|---|---|---|
| `/w/abc/home` | **404** | ⛔ **rules 11 · 12 · 14 · 19 · 20 · 21 · 22 · 24 — eight rules, including the default** |
| `/workspaces` | **404** | ⛔ **rules 09 · 13, and the fallback of 04 and 23** |
| `/workspaces/none` | **404** | ⛔ **rule 10** |
| `/w/abc/suspended` | **404** | ⛔ **rule 15** |
| `/w/abc/archived` | **404** | ⛔ **rule 16** |
| `/w/abc/deleted` | **404** | ⛔ **rule 17** |
| `/account/deleted` | **404** | ⛔ **rule 01** |
| `/account/suspended` | **404** | ⛔ **rule 02** |
| `/auth/locked` | **404** | ⛔ **rule 03** |
| `/auth/step-up` | **404** | ⛔ **rule 05** |
| `/onboarding` · `/onboarding/company` · `/onboarding/you` · `/onboarding/goals` | **307 → `/signin`** | ✅ **rule 18 — the only rule whose destination exists** |
| `/signals` · `/settings` · `/business` · `/profile` · `/join/abc` | **307 → `/signin`** | ✅ **the intent targets of rule 06 exist** — ⛔ **and §4 shows the intent never reaches them** |
| `/accounts` | **404** | ⚡ **not an entry destination; it independently reproduces [C-269](../LANE_COORDINATION.md)** |

### The count, and it is not the one on record

> 🔴 **18 of 24 rules resolve to a route that returns 404 unconditionally.** ⚡ **Two more — 04 `SESSION_EXPIRED` and 23 `USER_DEFAULT` — return 404 on their fallback path**, which is the path taken whenever there is no intent and no stored preference, and **nothing in the product writes either**. ✅ **Two land somewhere real: 06 `INTENT_HONOURED` and 18 `ONBOARDING`.**
>
> ⛔ **[D-205](../DECISION_REGISTER.md) records *"eleven terminal reason codes render nothing."* Measured at runtime it is eighteen, twenty counting the two fallbacks.** ⚠️ **The earlier figure is not corrected here** — it may have counted a narrower class, and **this document does not rewrite another register's number from the outside.** 📁 **Raised as [C-270](../LANE_COORDINATION.md) so the office that owns the figure reconciles it.**

---

## 4 · The reconciliation table

📁 **The shape [D-224](../DECISION_REGISTER.md) §14 requires: Area · Design requirement · Existing implementation · Status · Action.**

| Area | Design requirement | Existing implementation | Status | Action |
|---|---|---|---|---|
| **Entry engine** | 📁 *"Twenty-four rules, evaluated top to bottom… Rules are pure: same inputs, same destination, no network call inside the decision."* | 📁 [`lib/entry/`](../../frontend/lib/entry/) — 24 rules, codes in the design's exact order, pure, 35 tests | 🟢 | ⛔ **Do not touch.** ✅ **Reuse it whole** |
| **Engine invocation** | 📁 *"Engineering implements this as one component with one ordered rule list"* | ⛔ **Nothing calls it.** 📁 [`app/(app)/layout.tsx`](../../frontend/app/(app)/layout.tsx):33–37 is the entire entry behaviour: get session → `redirect('/signin')` if absent → render the shell | ⚪ | **An invocation site.** ⛔ **Blocked on destinations — see the last row** |
| **Redirect ownership** | 📁 *"Modules register, never redirect. A redirect written inside a module is a defect, because two of them produce a loop that only appears for one combination of role and state."* | ⛔ **17 files perform their own navigation.** 🔴 **The named one is [`components/shell/route-guard.tsx`](../../frontend/components/shell/route-guard.tsx):33 — `if (!permitted) router.replace('/')`** | 🔴 | **Route refusals through the engine's rule 07.** ⚡ **See the next row — this is the same defect seen from the other side** |
| **Deep link · forbidden** | 📁 Rule 07: *"The 403 page for that object, naming the missing role and the approvers. **Not Home, not a silent redirect.**"* | 🔴 **Both prohibited behaviours are what ships.** ⛔ `route-guard.tsx` is *literally* the silent redirect to Home. ⛔ And the engine's own rule 07 returns `` `${intent.path}?error=403` `` ([`rules.ts`](../../frontend/lib/entry/rules.ts):227) — ✅ **grepped: nothing anywhere reads `error=403`**, so the parameter is inert | 🔴 | **A 403 page that names the role and the approvers.** ⚡ **The refusal DATA exists** — `guardFor()` returns the required capability |
| **Deep link · honoured** | 📁 Rule 06: *"Go there. **Do not pass Home.** The workspace in the URL becomes the active workspace."* | 🔴 **The intent is never captured, so it cannot be honoured.** 📁 `layout.tsx`:35 is a bare `redirect('/signin')` — ✅ **runtime-confirmed: `GET /signals` → `307 → /signin`, no `?next=`.** Sign-in then goes to `AFTER_SIGN_IN = '/'` ([`lib/auth/client.ts`](../../frontend/lib/auth/client.ts):41) | 🔴 | **Capture the attempted route at the gate and carry it to `callbackURL`.** ⚡ **Smallest real fix in this table, and it is a customer-visible bug today** |
| **Deep link · gone** | 📁 Rule 08: *"The 404 page with the merge or deletion history if known."* | ⛔ `?error=404`, inert, same as rule 07. 📁 A generic [`app/not-found.tsx`](../../frontend/app/not-found.tsx) exists and knows nothing about merges | 🟡 | **Per-object 404** — ⛔ **and *"merge or deletion history"* has no source; see §6** |
| **Session expiry** | 📁 Rule 04: *"Re-authenticate **in place**. Route, filters and **unsaved drafts** preserved and restored."* | 🔴 **A route return cannot express *in place*.** The rule returns `intent?.path ?? '/workspaces'` — ⛔ **a navigation, and the fallback 404s.** ⛔ **Nothing preserves a draft anywhere in the tree** | 🔴 | **Design and engine disagree about what rule 04 IS.** 📁 **Raised as [C-271](../LANE_COORDINATION.md)** |
| **Step-up** | 📁 Rule 05: *"MFA or IdP re-assertion, then continue to the original intent."* → `/auth/step-up` | ⛔ **404.** ⚡ [`lib/auth/step-up-freshness`](../../frontend/lib/) exists and is tested (5 tests) — ✅ **the freshness LAW is built; the screen is not** | ⚪ | **The screen.** ✅ **Reuse the freshness rule — do not write a second one** |
| **Workspace resolution** | 📁 Rules 09–14 — no membership · sole · last-used · ambiguous · fell-through | ✅ **Implemented in [`rules.ts`](../../frontend/lib/entry/rules.ts) `resolveWorkspace`, and correct.** ⛔ **All five destinations 404** | ⚪ | **`/workspaces` and `/workspaces/none`.** ⚠️ 📁 **[TASK-1421](../BACKLOG.md) already records that the Workspace Chooser has no specification** — this audit does not re-open that |
| **Home route** | 📁 §04: *"Every authenticated person lands on `/w/:workspace/home`"* | ⛔ **404. No `app/**/w/` directory exists.** 🔴 **And [`tests/unit/route-map.test.ts`](../../frontend/tests/unit/route-map.test.ts):139 ASSERTS the absence** — `expect(routes()).not.toContain('/w/[workspaceId]/home')` | ⚪ | 📁 **[TASK-1438](../BACKLOG.md) is exactly this row and is `READY`.** ⚡ **It is the single highest-leverage unblock in the table: it alone converts eight rules from 404 to reachable** |
| **Home compositions** | 📁 *"One route, four compositions"* — Executive · Seller · RevOps · Activation | ✅ **[`lib/home/composition.ts`](../../frontend/lib/home/composition.ts) — the resolver, total, 8 exhaustive tests, `PROMOTED` to `main` 2026-08-10.** ⛔ **Zero callers, because its route 404s** | 🟡 | ⛔ **Nothing to build here.** ✅ **It becomes live the moment [TASK-1438](../BACKLOG.md) lands** |
| **Executive composition** | 📁 §04, stated as settled fact: *"**The Executive Dashboard already built** is the executive composition of Home."* | 🔴 **There is no Executive Dashboard.** ✅ **Searched: `Executive` appears in exactly three files — onboarding's role picker, and `composition.ts`.** 📁 **[TASK-438](../BACKLOG.md) delivered the DATA — `GET /workspaces/{id}/pipeline-health` — and ✅ grepped: no frontend consumer** | 🔴 | 🔴 **A design premise that is false against this repository.** 📁 **Raised as [C-272](../LANE_COORDINATION.md)** |
| **Seller · RevOps compositions** | 📁 §05 draws the seller composition in full — briefing, *Needs you today*, meetings, overnight agent work, *Pick up where you left off* | ⚪ **No composition renders anywhere.** ⚡ **Card sources partly exist** — the attention list at `/` is close in intent to *Needs you today* | ⚪ | **The card catalogue.** ⛔ **Out of this row's scope by [D-224](../DECISION_REGISTER.md); it is what the audit JUSTIFIES, not what it does** |
| **Activation composition** | 📁 Rule 19: *"Home, activation composition. Same route, same shell — the three connection steps replace the cards."* | 🟡 **The resolver returns `activation` correctly and it is the ONLY composition that resolves today** — 📁 emptiness is a fact the platform has, role is not ([C-268](../LANE_COORDINATION.md)) | 🟡 | **The three connection steps as cards.** ✅ **Resolution logic is done** |
| **Workspace states** | 📁 §07 — twelve cases, ⚡ *"including the four that happen while a person is already signed in, which is where most implementations fail — they handle entry and ignore change"* | ⛔ **Entry-side rules 15–17 exist and 404.** 🔵 **The four mid-session transitions were NOT verified** — they need a workspace suspended *underneath* a live session, which needs a runtime fixture this audit did not build | 🔵 + ⚪ | ⛔ **🔵 may never be reported as compliant.** **A follow-on row builds the fixture** |
| **Invitation accepted** | 📁 Rule 22: *"The new workspace becomes active, with a welcome strip. **Never a sign-out, never a lost tab.**"* | 🟡 📁 [`app/(app)/join/[workspaceId]/page.tsx`](../../frontend/app/(app)/join/) exists, ✅ **honours *never a sign-out***, and 🔴 **routes to `/` — `router.push('/')` at :103 and :141 — not to `/w/:new/home`.** ⛔ **No welcome strip** | 🟡 | **Re-point to the engine once Home exists** |
| **Onboarding exit** | 📁 Rule 18, and the coordination notice: *"both must exit through `resolveEntry` with `intent=null` — do NOT choose a destination in either flow"* | 🟢 **The seam is already built and is the best-prepared thing in this table.** 📁 [`onboarding/exit.ts`](../../frontend/app/(onboarding)/onboarding/exit.ts) — `onboardingExit()` returns `'/'` from **one line whose stated purpose is to be replaced**, read by all three call sites | 🟢 | ✅ **One line becomes `resolveEntry({ intent: null })`.** ⚠️ **Its doc comment says *"`resolveEntry` does not exist"*, written before [TASK-1400](../BACKLOG.md) — 🟡 stale prose, correct code |
| **Shell navigation & layout** | 📁 §06 four layers, and §04's IA — ⚡ *"the rail never exceeds nine items"* | 🔴 **Already measured and filed: nine of the rail's eleven design entries have no destination** | 🔴 | 📁 **[C-269](../LANE_COORDINATION.md) — ⚠️ and it is still not readable from `integration`; see §7** |
| **Reason-code observability** | 📁 *"Written to the session, attached to the redirect log, and included in the support diagnostics bundle."* | ⛔ **Zero of the 24 codes are observable at runtime**, because no decision is ever taken. ⚡ **The codes are produced correctly by a function nobody calls** | ⚪ | **Follows invocation.** ⛔ **Not separately actionable** |

---

## 5 · Reuse before reimplementation — what already exists and must not be rebuilt

📁 [D-224](../DECISION_REGISTER.md) §8, and ⚡ **this is the half of the audit that saves work rather than creating it.**

| Already built | Do not rebuild it |
|---|---|
| 📁 `lib/entry/` — the whole engine, 24 rules, 35 tests | 🟢 **Faithful to the design. It needs callers, not corrections** |
| 📁 `lib/home/composition.ts` | 🟢 **Total resolver, exhaustively tested, on `main`** |
| 📁 `onboarding/exit.ts` | 🟢 **A seam built for this exact substitution** |
| 📁 `lib/auth/step-up-freshness` | 🟢 **The freshness law. The step-up SCREEN is what is missing** |
| 📁 `lib/state/permissions.ts` — `guardFor` · `can` | 🟢 **Already returns the capability a 403 page must name** |
| 📁 `lib/state/workspace-provider.tsx` | 🟢 **Workspace context and its *"stored id is a hint, never a grant"* rule** |
| 📁 `app/(app)/join/[workspaceId]/` | 🟡 **Invitation acceptance — re-point its destination, do not rewrite it** |

⛔ **What must NOT be built** ([D-224](../DECISION_REGISTER.md) §6): no compatibility layer around `route-guard.tsx`, no second entry resolver beside `lib/entry/`, no `/home` invented because `/w/:ws/home` does not exist yet, and **no merge of the old and new redirect paths.**

---

## 6 · Ambiguities, raised surgically and not guessed

📁 [D-224](../DECISION_REGISTER.md) §7 — ⛔ *"one unresolved question does not block the rest of the audit"*, so each is narrow and none of them held up a row above.

| | What the design does not specify | Where it bites |
|---|---|---|
| **[C-270](../LANE_COORDINATION.md)** | ⚡ **Not a design gap — a register reconciliation.** [D-205](../DECISION_REGISTER.md) says eleven terminal codes render nothing; **runtime says eighteen** | Any row sized against the smaller figure |
| **[C-271](../LANE_COORDINATION.md)** | 📁 Rule 04 requires re-authentication ***in place*** with **unsaved drafts preserved** — ⛔ **a route-returning function cannot express either.** **Is rule 04 a routing rule at all, or a modal contract the engine only tags?** | Rule 04, and the shape of `EntryDecision` |
| **[C-272](../LANE_COORDINATION.md)** | 📁 §04 asserts *"the Executive Dashboard **already built**"* as the executive composition — ⛔ **no such screen exists here.** **Does the executive composition need building, or does the design describe a different repository's state?** | The executive composition, and [TASK-1401](../BACKLOG.md)'s sizing |
| **Rule 08** | 📁 *"the merge or deletion history **if known**"* — ⛔ **no module publishes a merge history.** ⚡ *"if known"* may make it optional; **it is not this lane's to decide** | The per-object 404 |
| **Rule 23** | 📁 *"Person set a custom start page… available in profile preferences"* — ⛔ **no preference store, and no bound on what a start page may be.** ⚠️ **An unvalidated stored route is a redirect the customer controls** | `USER_DEFAULT`, and it has a security shape |

---

## 7 · What this audit did not do, said plainly

- ⛔ **No production code changed.** 📁 The row's Change Budget: *"the audit itself touches no production code."*
- ⛔ **No implementation sequence chosen.** 📁 [D-224](../DECISION_REGISTER.md) returned that to this lane, and it is decided when the rows are claimed — **not asserted inside an audit**.
- 🔵 **The four mid-session workspace transitions are UNVERIFIED and are reported as such**, never as compliant.
- ⚠️ **[C-269](../LANE_COORDINATION.md), [C-270](../LANE_COORDINATION.md), [C-271](../LANE_COORDINATION.md) and [C-272](../LANE_COORDINATION.md) are on `lane-a-product-surface` and NOT on `integration`** — 📁 a claim commit may carry only [`ACTIVE_ASSIGNMENTS.md`](../ACTIVE_ASSIGNMENTS.md) and [`BACKLOG.md`](../BACKLOG.md) ([§20e](../../CLAUDE.md)), and a coordination item is neither. ⛔ **So four items addressed to Product Office are unreadable by it until QE integrates this branch.** ✅ **Lane C has claimed [TASK-497](../BACKLOG.md) for exactly this channel gap; this is a fourth instance of it, offered as evidence rather than as a second report.**

---

## 8 · The work this audit justifies — named, sized, and NOT created as rows

📁 **The row's Definition of Done says *"the implementation work it justifies **has been created**"*.** ⛔ **This lane cannot create it.** 📁 [§20e](../../CLAUDE.md): ***"A lane never reorders, reprioritizes, removes, or inserts `READY` work without the product owner."*** ⚡ **So the work is named here with its evidence, and creating the rows is Lane C's** — ⚠️ **and the DoD's wording is worth correcting, because as written it asks the implementing lane to do the one thing the governance reserves.**

| Justified work | Evidence above | Already has a row? |
|---|---|---|
| **`/w/:workspace/home` exists** | ⚡ **Converts eight rules from 404 to reachable — no other change is close** | ✅ **[TASK-1438](../BACKLOG.md), `READY`.** ⛔ **Nothing new needed** |
| **Capture the attempted route at the auth gate and honour it after sign-in** | 🔴 **Rule 06 inverted; runtime-confirmed `307 → /signin` with no `?next=`** | ⚪ **No row.** ⚡ **Smallest fix in the table and a live customer-visible bug** |
| **A 403 page that names the missing role and the approvers, replacing `route-guard.tsx`'s silent `replace('/')`** | 🔴 **Two design prohibitions breached by one line; `?error=403` inert** | ⚪ **No row** |
| **`/workspaces` and `/workspaces/none`** | ⛔ **Four rules 404** | ⚠️ 📁 **[TASK-1421](../BACKLOG.md), `BLOCKED` — the chooser has no specification** |
| **The step-up screen** | ⛔ **Rule 05 404s; ✅ the freshness law is built and must be reused** | ⚠️ 📁 **[TASK-1423](../BACKLOG.md) covers gate screens, `BLOCKED`** |
| **Account-state pages — deleted · suspended · locked** | ⛔ **Rules 01–03 404** | ⚠️ 📁 **Partly [TASK-1423](../BACKLOG.md)** |
| **Workspace-standing pages — suspended · archived · deleted** | ⛔ **Rules 15–17 404** | ⚪ **No row** |
| **A runtime fixture for the four mid-session workspace transitions** | 🔵 **UNVERIFIED, and may never be reported as compliant without it** | ⚪ **No row** |
| **The card catalogue behind the four compositions** | ⚪ **No composition renders; ✅ the resolver is done and on `main`** | ⚪ **No row** |
| **A gate that fails when an exported module has zero production callers** | 🔴 **Fifth instance of the class.** ⛔ **[TASK-1451](../BACKLOG.md)'s guard walks `components/ui` and would not have caught a `lib/` subsystem** | ⚠️ 📁 **[TASK-1451](../BACKLOG.md) exists and needs widening** |

## 9 · The finding underneath all of it

⚡ **Every gate in this repository passed on [TASK-1400](../BACKLOG.md).** Implemented, tested to 35 cases, covered, reviewed, accepted, certified, promoted. ✅ **And the engine really is good — §2 checked it mechanically against the design and it matches, position for position.**

⛔ **What no gate asked was whether the product routes through it.** 📁 [§2](../../CLAUDE.md) has a name for the class: **implementation that appears to enforce a property but whose removal would not change the product.** ⚠️ **Delete `lib/entry/` today and every customer-visible behaviour is identical** — which is the only test that would have caught this, and **it is cheap enough to be a gate.**

> 🔴 **The same shape has now been found five times**: 📁 `command-palette.tsx` ([C-259](../LANE_COORDINATION.md)) · `confidence.tsx` ([C-266](../LANE_COORDINATION.md)) · `drawer.tsx` and `copyable-id.tsx` ([498](498-common-platform-audit.md) §5.1) · **and this, which is a subsystem rather than a component.** ⛔ **[TASK-1451](../BACKLOG.md)'s guard as specified would not catch it — that guard walks `components/ui`, and this is `lib/`.**

---

## TASK-1422 · Last-used workspace — the write half the engine was missing *(2026-08-10)*

⚡ **This document's audit found the engine's read half correct and complete.** 📁 **`resolveEntry` reads `session.lastUsedWorkspaceId` for rule 12 `LAST_USED`** — ⛔ **and nothing in the platform wrote it, or cleared it.**

### 🔴 The hazard, and the shape that removes it rather than guarding against it

📁 **[D-196](../DECISION_REGISTER.md)**: *"last-used workspace is a stored preference that **OUTLIVES MEMBERSHIP** — if it is not cleared on removal, a departed member's next login routes at a workspace they can no longer see, which is an authorization failure wearing a convenience feature's clothes."*

⛔ **The obvious implementation is a `last_used_workspace_id` pointer, and it is the one that carries the hazard.** ⚡ **The pointer is a second representation of a fact the preference rows already hold**, so the two disagree the first time a membership ends without something remembering to rewrite it — 📁 [§2](../../CLAUDE.md), *truth has exactly one authoritative representation.*

✅ **So there is no pointer.** **Each workspace's `person_preferences` row records `last_entered_at`, and the answer is DERIVED over the person's LIVE memberships.**

🔴 **That is what makes the clearing provable rather than diligent.** **A workspace somebody has left is not in the set the derivation reads**, so the stale row is **unreachable rather than merely stale** — ⛔ **there is nothing to forget to clear**, which is [§2](../../CLAUDE.md)'s *prefer a violation that is unrepresentable over one that is merely discouraged.*

⚠️ **`ForgetWorkspaceEntry` still runs on both membership-ending paths, and it is documented as HYGIENE rather than sold as the fix** — **a guard that is not load-bearing but is described as one is exactly the Decorative Logic [§2](../../CLAUDE.md) names.** ✅ **A record of where somebody used to work should not outlive their access to it, and removing it costs nothing.**

### ⚠️ The row names three paths; this product has two, and the third is structural

| Path | Found |
|---|---|
| **Removal** — `remove_member` | ✅ **Exists, and now forgets** |
| **Leaving** — `leave_workspace` | ✅ **Exists, and now forgets** |
| **Workspace deletion** | ⛔ **No use case exists.** ✅ **The `person_preferences.workspace_id` foreign key is `ON DELETE CASCADE`, so the rows go with the workspace whenever one is built** — **structural rather than something a future use case has to remember** |
| **Role change that revokes access** | ⚠️ **Does not revoke access in this product.** ⛔ **Both roles — `owner` and `member` — can see the workspace**, so a role change ends nothing. **Rule 20 `ROLE_CHANGED` exists for what a person is shown, not for whether they may enter.** ⛔ **A clear wired here would fire on nothing**, which is the Decorative Logic case again — **so it is recorded rather than built** |

### ⚡ The row's own distinction, kept in the tests

📁 *"A stale preference cannot ROUTE anybody — [TASK-1400](../BACKLOG.md) already asserts that over 2,880 session/intent pairs — ⛔ but it CAN cost a person their real destination and land them at the chooser, which is a correctness defect rather than a security one."*

✅ **Both halves are true and the tests state them separately.** **The engine is the security control; this is the correctness one, and neither is asked to be the other.**

### ⛔ Two defects the tests caught before they shipped

**① `left()` would have INSERTED a row for somebody who never had one.** ⚡ **Every membership that ends calls it, and most people have never entered most of their workspaces** — so a `replace` that always produced a new object would write a preferences row **that did not previously exist**, in order to store the absence of a fact. ✅ **It returns `self` when there is nothing to forget.**

**② Entry is monotonic.** ⛔ **An `at` older than the stored moment is ignored rather than written**: entries arrive out of order — a retried request, a clock that stepped back — **and letting an older moment win would move somebody's last-used workspace backwards, which is the wrong answer at the one moment it matters.**
