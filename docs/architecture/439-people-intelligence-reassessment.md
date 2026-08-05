# 439 · People Intelligence, re-assessed against the long-term vision

**Lane C · Product Office · 2026-08-05.** Product Office directive: *"revisit the current narrowing of People Intelligence… evaluate as an architectural foundation rather than as a feature request."*

> ## The finding, before anything else
>
> **This decision already exists, you approved it, and it is on `integration`.**
>
> **[ADR-0400 · A person becomes an entity](adr/0400-person-as-an-entity.md)** — **`PRODUCT OWNER APPROVED`, 2026-08-04, [D-021](../DECISION_REGISTER.md).** Five alternatives assessed, one recommended, boundary stated, model specified, three open questions named.
>
> **And it anticipated exactly this moment, in writing:**
>
> > *"Ratifying this ADR records the bounded context **so it is not re-derived when the epic resumes**; **it neither approves nor unblocks Epic C.**"*

**So the answer to *"should Signora introduce a first-class People entity"* is: you already ruled that it should, and separated that ruling from the decision to build it.** **C-221 narrowed the epic. It did not narrow the architecture** — and the ADR was written so the two could move independently.

---

# 1 · What the long-term vision changes — and it is confirming, not new

**The directive lists eleven future capabilities. Ten of them are one thing.**

| The vision says | ADR-0400 calls it |
|---|---|
| Executive movement · champion tracking · **buying committee evolution** · role transitions · **stakeholder timelines** · engagement history · employment history · job changes · promotions | **`Affiliation`** — *person × company × title × **interval*** |

> **`Affiliation` as an entity rather than a field is the load-bearing choice**, and the ADR's reason is exactly the vision's requirement: ***"Priya left Acme" is not a mutation of Priya — it is an interval closing.* Storing a current employer as a field would destroy the history the entire product is built on, and would be the one place in this repository where a state change overwrites its own evidence.**

**Every "movement", "transition" and "history" capability in the directive is an interval query over that entity.** **The vision does not require a different model; it requires the one already chosen.**

## ⚠️ The one item that does *not* fit, and it matters

**"Contact influence"** and **"relationship intelligence"** are **judgements**, and ADR-0400 forbids People from holding them — naming the failure mode precisely:

> *"A person is **one plausible field away from becoming an influence model**. `seniority_score`, `is_key_contact`, `priority`, an ordered list read as a ranking — each turns an identity into a scoring input, **in the module least equipped to review it.**"*

**Recommendation: influence belongs to `buying_score_engine`, which already holds a reviewed scoring catalog with weights and postures.** **People supplies the subject; the engine supplies the judgement.** **This is the same separation `commercial_profile` and `timeline` already hold** — *record and compute nothing*, *project and compute nothing*, ***identify and compute nothing***.

**And "AI-generated account narratives" and "future agent workflows" hit a different wall** — [437](437-ai-platform-future-epic.md)'s statelessness ruling, not this one.

---

# 2 · Repository reuse audit — the twelve named modules

| Module | What exists | Verdict |
|---|---|---|
| **`knowledge_graph`** | Identity resolution, provenance, `IdentityState`, ambiguity. **`EntityKind` = `COMPANY`, `TECHNOLOGY`** | ✅ **Reuse wholesale.** Its docstring already names the trigger: *"Person is deliberately absent: claims carry role changes but no person **identifier**, so there is no identity to resolve. **Adding people now would mean inventing one.**"* |
| **`commercial_profile`** | `CommitteeRole(title, part)` — **two fields, no id** | 🟨 **One field when a consumer exists.** *"Nothing cites a role… **Trigger for adding one: the first consumer that needs to cite a particular seat.**"* **People is that consumer** |
| **`provider_normalization`** | `RoleChangeValue(title, seniority, direction)`; mappers read `name` for **companies and technologies only** | ✅ **The ingestion path exists.** A person's name would be a new claim attribute, not a new pipeline |
| **`observation_engine`** | Classifies role changes as occurrences | ✅ Unchanged — *"a person is a **subject**, never a second pipeline"* |
| **`business_event_engine`** | `LEADERSHIP_APPOINTED` · `LEADERSHIP_DEPARTED` | ✅ Unchanged |
| **`signal_engine`** | `new_decision_maker` · `decision_maker_departed` — **live and scored** | ✅ **Two shipped signals gain a subject.** The ADR calls this *"the smallest change with the largest visible effect"* |
| **`buying_score_engine`** | Reviewed catalog, weights, postures | ✅ **Where influence belongs**, per §1 |
| **`timeline`** | Nine projection rules, `PROJECTIONS` as the authority | ✅ Projects People's five events. ⚠️ **`runtime-composition` reports 2 of 9 consumers wired** — [TASK-901](../BACKLOG.md), and People's projection would land dark without it |
| **`opportunity_engine`** | — | ✅ Consumes signals, unchanged |
| **`ai_research_engine`** · **`ai_reasoning_engine`** | Evidence sets, grounding | ✅ A person becomes evidence, not a new capability |
| **`provider_platform`** | `ProviderAdapter`, capability descriptors | ✅ **A person-supplying provider is an adapter**, and the port already refuses vendor-specific logic |
| **`workspace_tenancy`** | `Membership`, `member_email` | ⛔ **Deliberately unrelated.** *"A `Member` is a customer's employee using Signora; a `Person` is somebody at a target account who has never heard of Signora. Different lawful basis, different lifecycle"* — **pinned by a test asserting the two are not joinable** |

> **Six modules already run this intelligence in production and not one knows a person's name.** **That is the reuse story, and it is why the ADR chose a thin new context over extending any of them.**

## On provider payloads — ZoomInfo, Apollo, Cognism, LinkedIn-style

**The directive asks for a provider-neutral domain, and the repository already enforces one.** `ProviderPersonIdentity` in ADR-0400 is the provider-neutral shape; `IdentityState` already models *resolved · ambiguous · unresolved*; the mapper rule already holds — ***"each mapper reads only its own vendor's shape. No vendor field name appears"*** outside it.

**So the mapping question is answered by the existing anticorruption layer.** **What those vendors add is a `person_identifier`, and that identifier is precisely what the graph says is missing.**

---

# 3 · The directive's seven questions, answered

| | Question | Answer |
|---|---|---|
| **1** | First-class People entity? | ✅ **Yes, and ruled on 2026-08-04.** ADR-0400 §Decision |
| **2** | Committee roles reference People when known, anonymous otherwise? | ✅ **Exactly the design.** *"`commercial_profile` owns the declaration; People supplies only the identifier it cites"* — **and role-only intelligence is today's behaviour, which continues unchanged** |
| **3** | How does People relate to everything else? | ✅ **§What People does not own.** A subject, never a pipeline. Five events, projected by `timeline` |
| **4** | Core domain versus provider metadata? | ✅ **Names are *claims*, identities are `ProviderPersonIdentity`, resolution state is explicit.** The existing claim/provenance model, unchanged |
| **5** | Avoid speculation without later refactor? | ✅ **This is what a ratified-but-unbuilt ADR is for**, and the repository has done it twice — [ADR-0035](adr/0035-commercial-profile.md) and [ADR-0038](adr/0038-timeline.md) *"took the route: draft first, ratify, then build — never the other way round"* |
| **6** | No change · deferred ADR · roadmap prep · placeholder? | ✅ **No change. The ADR is the preparation and it is complete and on `integration`** |
| **7** | Would introducing People today simplify or complicate? | ⚠️ **Complicate — see §4** |

---

# 4 · Recommendation — build nothing, and here is the test that says so

**The ADR's own condition is unmet and nothing has changed it.**

> **❓1 · Does the production provider return a person's name?** **Re-measured 2026-08-05: no.** `simulation/generators/enrichment.py` emits `type · title · seniority · occurred_on`. `mappers/enrichment.py` reads `name` for **organisations and technologies only**. **No person's name enters the platform from any source.**

**So building `Person` today would mean inventing the identifier the graph refuses to invent** — its own words. **An aggregate whose every instance is anonymous is a table, a migration, an erasure obligation and a test suite, in exchange for nothing a customer can see.**

**And the cost of waiting is the thing this assessment had to check, because that is the real question.** **It is low, and specifically:**

| Change deferred | Cost when it lands |
|---|---|
| `EntityKind.PERSON` | **One enum member.** The docstring already reserves it |
| `CommitteeRole` stable id | **One field**, and *"the trigger that module already wrote down"* |
| `Affiliation` intervals | **A new table. Never a migration of an old one** — because no current-employer field exists to unpick |

> **That last row is the whole answer to question 7.** **The expensive version of this decision is the one where a `current_employer` field ships and later has to become a history.** **ADR-0400 already prevented that**, and it prevented it *by being written*, not by being built.

## The minimum preparation required today

**None in code.** **Three things in the record, and two are already done:**

**① ADR-0400 stays ratified and unimplemented.** ✅ Done — on `integration`.
**② The two triggers stay written where the code will be read.** ✅ Done — `identity.py:32` and `committee.py:116` both state their own condition.
**③ ❓1 becomes a provider-contract question on the roadmap, not an open architectural one.** **This is the only gap**, and it is one line: **Epic C resumes when a provider contract supplies a person identifier** — which is a commercial decision, not an engineering one.

---

# 5 · What genuinely changed since 2026-08-04

**Two things, and both sharpen ❓2 rather than the model.**

**① [TASK-426](../BACKLOG.md) now exists** — the deletion and retention strategy, approved in principle today. **ADR-0400's `person.forgotten` event and `ForgetPerson` use case are the first real consumer of it.** **Sequence TASK-426 before Epic C**, not after: erasure designed into a bounded context is cheap, and retrofitted is not.

**② The vision names capabilities that make ❓2 harder to defer.** *"Champion tracking"* and *"relationship intelligence"* pull toward contact channels — and **the repository still has no lawful basis declared for personal data.** **Lane C's recommendation is unchanged and now more load-bearing:** *no contact channel in Epic C; read contacts from the customer's own CRM when E1 lands, **under the customer's own basis**; never buy contact data without an explicit ruling.*

> **The erasure surface is near-zero today.** Signora holds member emails and nothing else about a human. **That is the cheapest possible moment to decide what erasure means — and it stops being cheap the day `Person` ships.**

---

# 6 · What this document did not do

| | |
|---|---|
| **Implemented** | **Nothing** |
| **Assigned** | **Nothing.** No task created, no queue touched |
| **Migrations** | **None** |
| **Ownership** | **Unchanged** |
| **New modules** | **None proposed.** ADR-0400's `people` module remains **recommended and unbuilt** |
| **C-221** | **Unchanged and still correct.** *"Avoid speculative architecture"* is exactly what this concludes |

**The directive asked whether introducing a provider-neutral People domain now is the correct long-term decision. It is — and it was taken on 2026-08-04.** **What remains is a provider, not an architecture.**

---

# 7 · ⚠️ Completed, not reversed — 2026-08-05

**§4's *"build nothing"* rested on a cost-of-waiting analysis that is still correct in every figure it reports** — one enum member, one field, a new table rather than a migration. **It measured the wrong cost.**

> **It measured what changes in the backend when the domain arrives late. It never measured *wave order*** — and **[440](440-people-roadmap-integration.md) found four screens in waves 1–4 depending on a domain scheduled at wave 6**, one of which had already shipped two ⬜ stated absences.

**The cost of arriving late is not paid in the domain. It is paid in every screen that shipped around the gap**, which is why a backend-only assessment could be complete and still reach the wrong recommendation.

**Ruled [D-074](../DECISION_REGISTER.md), 2026-08-05.** **The plan is [441](441-people-roadmap.md); the rule that catches the next instance is [441 §5 · P-01 · Domain precedence](441-people-roadmap.md).** **§1, §2, §3, §5 and the sentence above stand unchanged** — the provider question is real, it still gates named people, and **it now gates [TASK-429](../BACKLOG.md) rather than the entity.**
