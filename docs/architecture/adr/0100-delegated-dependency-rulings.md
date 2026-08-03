# ADR-0100 — Delegated dependency rulings, 2026-08-03

**Status:** Accepted
**Decided by:** **QE, under product-owner delegation granted 2026-08-03.** Not by the product owner directly.
**Supersedes:** nothing. **Amends:** `CLAUDE.md` §20a (see R-1), `CLAUDE.md` §20e (see R-2, R-4)

> **Attribution is the point of this preamble.** `CLAUDE.md` §2 requires the repository to tell the truth about itself, and recording these as *"the product owner decided"* would be false. **A delegated agent decided them, with the product owner's authority and none of the product owner's customer knowledge.**
>
> **Every ruling below is therefore reversible on request**, and each states what evidence it rests on so the reversal is cheap. Where a ruling rests on **judgement rather than evidence**, it says so — those are the ones to re-examine first.

---

## R-1 · The platform freeze admits one composition amendment — **Pack A**

**Closes [C-012](../../LANE_COORDINATION.md), [C-013](../../LANE_COORDINATION.md), [C-021](../../LANE_COORDINATION.md), [C-207](../../LANE_COORDINATION.md).**

**Decision.** `signora_platform/` is amended **once**, under a single RFC, granting four capabilities:

| | Unblocks |
|---|---|
| **1 · `EventHandler` receives a session** | 7 modules' event consumption ([C-012](../../LANE_COORDINATION.md)) |
| **2 · `PublishableEvent` is satisfiable by a frozen dataclass** | 13 files' `# type: ignore` ([C-013](../../LANE_COORDINATION.md)) |
| **3 · An event handler may reach a provider adapter through a port** | PP-02's last wire, all of PP-03, [C-007](../../LANE_COORDINATION.md) ([C-021](../../LANE_COORDINATION.md)) |
| **4 · Casbin can express an action on oneself** | Leaving an organization, and every self-directed operation ([C-207](../../LANE_COORDINATION.md)) |

**Evidence, not judgement.** `make runtime-composition` has measured **7 of 9 declaring modules unwired** every cycle since the check existed. [C-013](../../LANE_COORDINATION.md) predicted *"a `type: ignore` in eight places trains people to add a ninth"* — **there are now 13**, so its own forecast is the measurement. Open since **M3A**, the longest-running blocker in the repository.

**Why one amendment and not four.** Four RFCs produce four shapes for one problem — the duplication [L-1](../../../ENGINEERING_LAWS.md) forbids. **The freeze did its job**: it turned four silent commits into one decision, which is exactly what §20a exists for.

**Constraints on the implementation, and these are binding:**

- **Additive only.** A module not using a new capability behaves identically.
- **One module rewired per slice**, with `make runtime-composition` measured after each. **Seven independently certifiable slices, not one large one.**
- **The RFC lands before any rewiring.** §20a's *"explicitly approved architectural changes"* means approved *then* implemented.
- **`make runtime-composition`'s `BLOCKED_BY_C012` list shrinks by exactly one per slice.** A module leaving that list is how the architecture records that it now expects live consumption.

**What this does not do.** It does not thaw the platform. §20a stands; this is the "explicitly approved architectural change" branch being used for the first time, and the next one needs its own ruling.

---

## R-2 · A roadmap row is not claimable until it names its bounded context — **Pack B**

**Closes [C-020](../../LANE_COORDINATION.md) *(with R-3)*, [C-023](../../LANE_COORDINATION.md), [C-200](../../LANE_COORDINATION.md).**

**Decision.** **A milestone may not enter `READY` in [`BACKLOG.md`](../../BACKLOG.md) until it names its bounded context and owning module.** Where the product owner prefers not to decide that up front, **the milestone's first task is an explicit discovery slice** whose deliverable is the boundary.

**Evidence.** Three lanes hit this independently — M7, M13, M14b — and all three wrote a discovery document unprompted. `CLAUDE.md` §20e sets *"multiple lanes hit the same friction"* as the threshold for governance change; **this is three.**

**[C-023](../../LANE_COORDINATION.md) closes separately and on different grounds:** it asked whether M13 was *executable*, and Lane B executed three slices of it. **The question was empirical and implementation answered it.**

**`CLAUDE.md` §20e gains this rule** — a lane may record a skip when a top-priority `READY` item lacks a bounded context, and that skip is a finding rather than a re-prioritisation.

---

## R-3 · ADR-0038 is ratified, with all three open questions answered

**Completes [C-020](../../LANE_COORDINATION.md). M7 may proceed.**

| Question | Ruling | Basis |
|---|---|---|
| **❓1 · Meilisearch now, or Postgres first** | **B — Postgres first.** Meilisearch on a stated trigger: *the first customer asking to search or facet a timeline rather than scroll it* | **Evidence.** The primary query is `ORDER BY occurred_at DESC` — an index, not a search. ADR-0008 ratifies the *technology*, never the *schedule*, and §14 forbids building for load with no evidence |
| **❓2 · Six events now, or wait for the seventh** | **Ship the six.** `recommendation.created` joins when M11 resumes | **Evidence.** A projection that cannot absorb a new entry kind later is wrong regardless, so this costs nothing and proves extensibility on the first occasion |
| **❓3 · Does the timeline reach a customer in M7** | **Already answered by implementation.** The feed is mounted on the account brief (**CX-03**), Option A, with B and C ruled out in the file | **Evidence.** `accounts/[accountId]/page.tsx:335`. Lane B's position was implemented before ratification |

> **❓3 is worth reading twice.** The decision was taken by a lane writing code, correctly, and the ADR asking it stayed `Proposed` for five cycles while QE escalated the question. **A blocker can outlive its own answer**, and nothing in the repository was checking.

---

## R-4 · QE owns code that belongs to no module; a rotating lane verifies it — **Pack D**

**Closes [C-010](../../LANE_COORDINATION.md), [C-004](../../LANE_COORDINATION.md), [C-014](../../LANE_COORDINATION.md).**

**Decision.** **QE is the assignee for `apps/`, `signora_platform/`, the frontend foundation and repository process.** Because QE may not verify its own work, **a nominated implementation lane verifies QE's fixes each cycle**, rotating, **starting with Lane B** — which has the precedent from [TASK-001](../../BACKLOG.md).

**Evidence.** **Eight defects have landed in this gap** — B-007, B-012, B-013, B-014, B-022, B-025, B-100, B-101 — and the last four were all found *and fixed* by QE in consecutive cycles because nobody else may touch that code. **The verification half is the only part that was actually missing.**

**Consequences:**

- **[C-004](../../LANE_COORDINATION.md) resolves.** **QE may correct factual drift in `docs/architecture/01`–`21`** — recording what was built, never changing a decision. A decision change still needs an ADR. §12 already makes drift a bug; this removes the carve-out that made the bug unfixable.
- **[C-014](../../LANE_COORDINATION.md) resolves.** Accessibility and performance testing are QE's and get a milestone slot **after M14**, not before. **They are not urgent**: §20c already treats an accessibility issue as a defect class, so the capability gap is measurement, not protection.

---

## R-5 · Sellers see the commercial profile, beside the account — **[C-008](../../LANE_COORDINATION.md)**

**Decision.** **Yes — read-only, for `member`, beside the account brief rather than under `/settings`.**

**Evidence, and it is unusually clean.** `policy.csv` already grants `member` read on `product`, `icp`, `buying_committee` and `commercial_focus` — **four separate reviewed decisions, all saying the same thing.** The API and the product disagree, and **the API is right**: an AE working an account cannot currently see the ideal customer that account is supposed to match.

**Why beside the brief and not under settings.** *Your business* is a settings page and **it is not a setting** — a setting is something you change, and this is something you consult while selling. Under `/settings/*` it sits behind `workspace:update`, which is why the granted read is unreachable.

**Judgement, marked as such:** placement beside the brief rather than as its own route is mine. It follows [D38](../38-product-design-principles.md) — *navigation is journeys, not data* — and it is the same shape as CX-03's timeline mount, which worked. **Reverse this one first if it feels wrong in review.**

**This is a two-lane build**: Lane B owns `commercial_profile`'s read surface, Lane A owns the mount. **[C-008](../../LANE_COORDINATION.md) becomes an implementation dependency, not an architectural one.**

---

## R-6 · A contraction risk never renders like an opportunity — **[C-011](../../LANE_COORDINATION.md)**

**Decision.** **Posture reaches the attention row, and a contraction risk is visually and textually distinct from an opportunity.** Not a shared score reading with a different number.

**Evidence.** *Attention is unsigned for every posture and opposing readings never net* holds **inside the score and does not reach the row** — so a contraction risk currently presents as a low-scoring opportunity, and the two mean opposite things to a CRO scanning a list. **That is the product telling a customer something false**, which is the class [B-027](../../BUGS.md) belongs to.

**Judgement:** the specific treatment — label, colour, icon, ordering — is the implementing lane's, within the design system. **The ruling is that they must not be confusable**, not how.

---

## R-7 · Signora owns the invitation; delivery is manual in v1 — **[C-206](../../LANE_COORDINATION.md)**

**Decision.** **An `invitation` table in `workspace_tenancy`, keyed by email.** Acceptance matches a pending row against the **`email` claim already in the verified JWT**. **Better Auth's `organization` plugin is not adopted.**

**Evidence, and it is decisive.** Migration `0005` revokes `signora_app` from the `auth` schema, so **membership in the plugin's tables is membership the Python tier cannot read** — and §13 requires membership re-verified server-side on every request against `membership`. **Adopting the plugin would break the tenancy model**, which is the one thing `CLAUDE.md` never negotiates.

**Lane A's own finding removes the rest.** Every access token already carries `email` and `email_verified` as **required claims the Python verifier type-checks**, and Better Auth already enforces verification — so accepting an invitation is matching a pending row against a claim that already arrives. **No plugin, no new dependency, no frozen-file change.**

**Email delivery — judgement, and the part to challenge.** **v1 creates the invitation and surfaces the link in-product for the inviter to share.** No transactional email dependency is added.

**Reasoning:** adding an email provider is a new dependency requiring its own ADR (§6), and it would gate a capability that works without it. **In a B2B tool the inviter usually knows the invitee.** The domain is unchanged by the delivery mechanism, so transactional email can be added later as a slice rather than a redesign. **If you would rather ship with email from the start, this is the ruling to reverse** — it costs one ADR and one slice, and nothing else moves.

---

## R-8 · Desktop-first; phone is not a v1 target — **[C-205](../../LANE_COORDINATION.md)**

**Decision.** **Signora targets desktop, and remains usable down to tablet width. A phone layout is explicitly out of scope for v1.**

**Judgement, and the thinnest-evidenced ruling here.** The primary journeys — an account brief carrying evidence, contributions and a decision history — are dense information surfaces, and the product's core claim is *explainable with evidence*, which needs room. **Committing to phone would constrain every layout decision for a use case nobody has evidenced.**

**What it makes concrete:** [B-019](../../BUGS.md)'s hidden aside below 768px is **correct behaviour**, not a defect. **The decision is reversible and cheap to reverse now**; it becomes expensive after another ten screens.

---

## R-9 · The onboarding honesty principle is ratified as D39 — **[C-017](../../LANE_COORDINATION.md)**

**Decision.** **Ratified**, into [`38-product-design-principles.md`](../38-product-design-principles.md) as `D39`. Text was already written and reviewed.

**Zero-cost, and it should not have waited five cycles.** A principle with ratifiable text and no objection is a decision nobody was making rather than a decision anybody was weighing.

---

## R-10 · Pack C is **not** consolidated — the product owner's ruling, recorded

**Decision, and this one is the product owner's directly, 2026-08-03.**

> **ADR-0041 defines how customer intent is modeled, versioned, governed and referenced. [C-002](../../LANE_COORDINATION.md) defines how that intent is interpreted against normalized provider data. They are complementary capabilities, not one combined decision.**

**QE's Pack C grouping is withdrawn.** The reasoning that replaces it: a versioned ICP aggregate is the authoritative representation of customer intent that matching, AI recommendations, search, analytics and reporting all reference — **and it holds that value before automated matching exists.**

**What QE's challenge was right about, and what must be documented:** a future engineer must never assume *"storing an ICP"* means *"the platform understands it."* **ADR-0041 states the boundary explicitly**, and [C-002](../../LANE_COORDINATION.md) remains open as the interpretation half.

**[C-018](../../LANE_COORDINATION.md) and [C-204](../../LANE_COORDINATION.md) stay with [C-002](../../LANE_COORDINATION.md)** — all three are the interpretation question.

---

## What is deliberately **not** ruled

**These stay open, and each says why.**

| Item | Why it is still the product owner's |
|---|---|
| **[C-002](../../LANE_COORDINATION.md) · [C-018](../../LANE_COORDINATION.md) · [C-204](../../LANE_COORDINATION.md)** | **Where customer language becomes a canonical claim.** Three candidate homes contradict something already ratified; choosing needs product intent QE does not have |
| **[C-203](../../LANE_COORDINATION.md)** | **How the product names a person.** Touches AI attribution, audit actors, notifications and mentions at once — a product-semantics decision, not an engineering one |
| **[C-003](../../LANE_COORDINATION.md) · [C-005](../../LANE_COORDINATION.md) · [C-007](../../LANE_COORDINATION.md) · [C-009](../../LANE_COORDINATION.md) · [C-025](../../LANE_COORDINATION.md)** | **Not yet re-validated against current code.** Ruling on them without that read would be the register-not-repository error this exercise exists to correct |
| **[C-302](../../LANE_COORDINATION.md)** | **A notification is per-person and workspace RLS is not enough.** A tenancy decision, and `CLAUDE.md` never negotiates tenancy inside a session |

> **Ten rulings, four deferrals, and the deferrals are the honest part.** A delegation that returned *"all resolved"* would mean the hard ones had been decided by somebody without the information to decide them.
