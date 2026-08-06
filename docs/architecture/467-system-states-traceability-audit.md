# 467 · System States — platform-foundation traceability audit

**Lane C · Product Office · 2026-08-06.** **[D-102](../DECISION_REGISTER.md).** **Platform foundation module 10 of 10 — the first of the ten to receive the audit the sixteen business screens received.**

> **Evidence First, applied from the first line:** ***"Every recommendation should first attempt to disprove itself."***

---

# 0 · ⚡ The audit disproved its own premise, and that is the finding

**I expected to discover a foundational capability. It was discovered on 2026-08-05, it is the highest-priority unowned item in the register, and an implementation lane filed its ninth instance the same week.**

| | |
|---|---|
| **[R-15 · Stated absence](../DOMAIN_DISCOVERY_REGISTER.md)** | 📐 **P-A.** **8 instances, 0 implementations.** **🔴 Highest, and unowned.** And the register's own note: **🟠 *"Name before the ninth"*** |
| ⚡ **[C-226](../LANE_COORDINATION.md)** | **Raised by Lane A, 2026-08-05, owner Lane C, still `OPEN`.** ***"Six sections on one page have rendered a failed read as an empty account, and each was fixed alone"*** |

> ## **The ninth arrived. It arrived as six at once, on one screen, fixed by four different slices, and nothing connected it to the pattern that predicted it.**

**P-A, stated in the register on 2026-08-05:**

> ***"A result says what it could not evaluate… absence can never distinguish itself from failure."***

**C-226, raised independently the same day:**

> ***"`undefined` then means both 'the API said there is none' and 'the request failed', and the section's empty branch states the first as a fact."***

⚡ **Two documents, one sentence, neither citing the other.** **P-A is the answer to the question C-226 asks — *is this a repository invariant?* — and it was already ratified as a pattern before C-226 was written.**

## What this changes

⛔ **The System States audit produces no new foundational capability, and that is a success** ([D-092](../DECISION_REGISTER.md) — *"a methodology capable of concluding 'nothing new is required' is considerably more trustworthy"*).

✅ **What it produces instead is the trigger.** **R-15 was 🟠 *name before the ninth* with no consumer urgent enough to force it. C-226 is a customer-visible defect class, found six times on the first screen anybody built.** **The trigger has fired.**

---

# 1 · The fifteen states, traced

**418 records System States as *"15 states, one grammar, three questions before a button"* and *"every screen inherits it."*** **Traced against the repository rather than against the design.**

| Element | Business meaning | Single source of truth | Repository verdict | Owner | Consumers | Priority |
|---|---|---|---|---|---|---|
| **Loading** | *"Signora is fetching this"* | `ui/skeleton` | ✅ **Built** | frontend foundation | all 26 | — |
| **Empty — nothing yet** | *"Correctly, there is none"* | `ui/empty-state` | ✅ **Built** | frontend foundation | all 26 | — |
| ⚡ **Failed read** | *"Signora could not find out"* | ⛔ **Nothing** | 🔴 **[R-15](../DOMAIN_DISCOVERY_REGISTER.md) · [C-226](../LANE_COORDINATION.md)** — **the audit's whole finding** | **unowned** | **all 26** | 🔴 |
| **Page error** | The route failed | `app/error.tsx` | ✅ **Built** | frontend foundation | all | — |
| **404 not found** | The record is absent | `app/not-found.tsx` | ✅ **Built** | frontend foundation | all | — |
| ⚡ **404-instead-of-403** | **The record's existence is confidential** | ✅ **`CLAUDE.md` §7** | ✅ **Ratified, and 418 found the design and the constitution already agree** | platform | all | — |
| **403 with role request** | *"Ask somebody who can"* | ⛔ Nothing | 🟠 **Absent** — and it needs [R-13](../DOMAIN_DISCOVERY_REGISTER.md)'s dimensions plus a request workflow | unowned | Settings · Team | 🟡 |
| ⚡ **Failure scoping** — widget / region / page | **How much of the screen is untrustworthy** | ⛔ Nothing | 🔴 **Absent.** 418: *"One chart cannot reach its service, and a person loses their filters"* — **a defect in 26 screens at once** | unowned | all 26 | 🔴 |
| ⚡ **Draft and filter preservation** | **A failure must not cost typed work** | ⛔ Nothing | 🔴 **Absent** — ⚠️ **and it is [R-02](../DOMAIN_DISCOVERY_REGISTER.md)'s, not this screen's.** *A filter that survives an error is a saved view with a one-request lifetime* | **`workspace_tenancy`**, if R-02 lands | all 26 | 🟠 |
| **404 merge provenance** | *"This record became another"* | ⛔ Nothing | 🟠 **Absent** — ⚠️ **`knowledge_graph` owns identity resolution and already holds `IdentityState`.** **Not a new concept; an unpublished one** | `knowledge_graph` | Account 360 · Search | 🟡 |
| **Offline / degraded** | A dependency is down | 🟡 `live_capabilities` | 🟡 **Partial** — 418 records it for Help Center; **no screen reads it for its own sections** | `provider_platform` | all | 🟡 |
| **Read-only degradation** | **Billing lapsed** | ⛔ Nothing | ⏸ **Blocked by product — [C-200](../LANE_COORDINATION.md)**, and 418 §5a already names it as reaching every module | unowned | all 26 | ⏸ |
| **Shell survives every state** | *"Losing navigation during an error strands people"* | **App Shell §16–18** | ✅ **Design-side ratified; 418 defers to it** | frontend foundation | all 26 | — |
| **Timeout / slow** | Distinguishable from failure | ⛔ Nothing | ⬜ **Not yet extractable** — the design's grammar does not say whether this is a state or a loading variant | — | — | ⬜ |
| **Retry affordance** | *"Try again"* without losing context | ⛔ Nothing | 🟠 **Absent, and it depends on draft preservation above** | unowned | all 26 | 🟡 |

---

# 2 · Evidence First — five things I looked for and found already built

> ***"Discovering that something already exists is just as valuable as discovering something missing."***

| Searched for | ⚡ Found |
|---|---|
| **A 403/404 confidentiality rule** | ✅ **`CLAUDE.md` §7, ratified** — *"a caller who is not a member gets `404`, never `403`… a security property, not an inconsistency to tidy up."* **418 already found that the design and the constitution agree without having been reconciled** |
| **An empty-state component** | ✅ **`ui/empty-state`**, and `ui/skeleton` beside it |
| **Route-level error handling** | ✅ **`app/error.tsx` · `app/not-found.tsx`** — Next.js's own boundaries, already in place |
| **A precedent for a repository-wide frontend invariant** | ✅ **Two** — `no-mock-data.test.tsx` and `design-tokens.test.tsx`. **C-226's recommendation is the same shape, which is why it is credible** |
| ⚡ **A pattern covering absence-versus-failure** | ✅ **[R-15 / P-A](../DOMAIN_DISCOVERY_REGISTER.md), ratified 2026-08-05** — **§0.** **The one I most expected to be missing** |

⛔ **And one thing I looked for and did not find, which is worth stating because its absence is the finding:** **no screen distinguishes *widget failed* from *page failed*.** **Every one of the 26 inherits that.**

---

# 3 · The consolidated answer to C-226

**C-226 asks one question: *is "a section must distinguish absence from failure" a repository invariant, and if so who writes it?***

> ## ✅ **It already is one. It is [P-A](../DOMAIN_DISCOVERY_REGISTER.md), ratified 2026-08-05, and C-226 is its ninth recorded instance.**

**So the question narrows from *should this be an invariant* to *who implements the one it already has*, which is a much cheaper question.**

| | |
|---|---|
| ✅ **Lane A's recommendation is right and this office endorses it** | **A page-level test, not a per-component prop.** *"Render the account brief with every hook erroring and assert the page says so — one test, no new prop on any component, and it cannot be silenced by adding a field"* |
| ⚡ **And Lane A's refusal is the better half** | *"A naive guard would be wrong."* **`EntityName` falls back to the real account identifier and makes no false claim under any error** — **a guard that flagged it would teach lanes to add a prop to silence it.** ⛔ **That is Decorative Logic (`CLAUDE.md` §2) predicted before it was written** |
| ⛔ **What this office does not do** | **Write it.** **The assertion reaches sections other lanes own, and `brief.test.tsx` is Lane A's harness.** **Lane A offered to build it on request; the request is this document** |
| 🔴 **What still needs the product owner** | ⚡ **Only the scope.** **A test on one page is 🟢 and Lane A's.** **Making *"absence is not failure"* a repository-wide frontend invariant binding all 26 screens touches the frozen frontend foundation — §20c, 🔴** |

---

# 4 · The twelve dimensions

| | |
|---|---|
| **Foundational entities** | ⛔ **None new.** ⚡ **The audit's subject is a *result property*, not an entity** — which is why R-15 is 📐 a pattern with no module |
| **Aggregates** | ⛔ **None** |
| **Value objects** | 🟡 **One candidate**: a *scope* for a failure — widget · region · page. **Not proposed** — one screen's need, and [P-C](../DOMAIN_DISCOVERY_REGISTER.md) says wait for the consumer |
| **Workflows** | 🟠 **403 → role request** is a genuine workflow with no home |
| **Business events** | ⛔ **None.** A render state is not a business fact |
| **Permissions** | ✅ **Settled** — §7's 404-not-403, ratified and already agreeing with the design |
| **Lifecycle models** | ⏸ **Read-only degradation** is Billing's, blocked on [C-200](../LANE_COORDINATION.md) |
| **AI capabilities** | ⛔ **None, and deliberately.** ⚠️ **A model asked to explain a failed read would invent a cause** — `CLAUDE.md` §10, *never ask a model to invent what the platform knows* |
| **Platform capabilities** | 🟡 **`live_capabilities` exists and no screen reads it for its own sections** |
| **Reusable abstractions** | ⚡ **R-15 is the abstraction, and it is already named.** **26 consumers** |
| **Vocabulary** | ⚠️ **`unmeasured` · `unknown` · `unscored` · `missing_gates` · `not yet extractable` — one idea, five spellings**, already recorded at [Register line 284](../DOMAIN_DISCOVERY_REGISTER.md). **This screen adds a sixth: *failed read*.** **Registering it is [R-15](../DOMAIN_DISCOVERY_REGISTER.md)'s job, not a new one** |
| **Ownership** | 🔴 ***Unowned*, and it is the only row here that worries me.** **A pattern with 26 consumers and no module is the shape [D-090](../DECISION_REGISTER.md) warns about** — *"ownership should be an architectural decision rather than an implementation accident"* — **and nine instances have now been decided by whoever met one** |

---

# 5 · Architectural risk

> ## ⚠️ **R-15 has nine instances, zero implementations, and no owner. Every one of the nine was resolved locally and correctly by whoever met it.**

**That is exactly how a pattern becomes nine incompatible implementations rather than one capability** — and it is [R-00](../DOMAIN_DISCOVERY_REGISTER.md)'s shape, which [D-077](../DECISION_REGISTER.md) caught in time by sequencing the capability ahead of its first consumer.

**The difference is that R-00 had one consumer approaching and R-15 has twenty-six already here.**

---

# 6 · Recommendation

| | | |
|---|---|---|
| **1** | ✅ **Close [C-226](../LANE_COORDINATION.md) by citing [P-A](../DOMAIN_DISCOVERY_REGISTER.md)** | **The invariant it asks for exists.** **Done in this document** |
| **2** | **Ask Lane A to build the page-level test it offered** | 🟢 **One test, its own harness, its own screen.** **Needs no ruling** |
| ⚡ **3** | 🔴 **Rule on R-15's ownership** | **The only product owner decision here.** **Twenty-six consumers, no module, nine local decisions already taken** |
| **4** | ⏸ **Failure scoping** | **Genuinely absent and genuinely needed.** ⛔ **Not proposed as a capability yet** — it needs 2 and 3 first, and proposing it now would be the speculative abstraction §6 forbids |

⛔ **No backlog row created · no ADR drafted · no lane assigned · no vocabulary term promoted · nothing implemented.**

---

# 7 · What this audit did not do

**It did not invent a UI element** ([D-079](../DECISION_REGISTER.md)) · **did not re-derive [418](418-platform-foundation-assessment.md)** · **did not reopen §7's ratified 404 rule** · **did not propose a System States module.**

⚡ **And it did not report its central finding as a discovery.** **The capability was already in the register, already ranked highest, already unowned, and already predicted to need naming *before the ninth instance*.** **The audit's contribution is that the ninth arrived, that it arrived as six at once, and that nobody had connected [C-226](../LANE_COORDINATION.md) to [R-15](../DOMAIN_DISCOVERY_REGISTER.md) — including the office that wrote both.**
