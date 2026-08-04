# 419 — C-326 narrowed to two artifacts, and Lane B's executable work

> **Lane C — Product Office, 2026-08-04**, on the product owner's instruction that Lane B has been idle too long. **Dependency Resolution** under [PRODUCT_OFFICE §1](../PRODUCT_OFFICE.md) — *what is actually blocking, and what is the smallest unblock.* Measured against `origin/integration`.

## 1 · Why Lane B is idle, stated honestly

**Three causes, and one of them is mine.**

| | |
|---|---|
| **1** | **TASK-300 is `IN VALIDATION`.** Lane B pushed A4, A1 and A5's backend on 2026-08-03. **It is with QE, and the lane correctly did not wait** |
| **2** | **TASK-402's read is blocked on C-326**, which is genuinely the product owner's |
| **3** | **[417](417-executable-slice-audit.md) identified two Lane B slices and I drafted READY rows for Lane A's four only.** The product owner asked for Lane A's; **I should have flagged that Lane B's had no row and therefore nothing to claim.** Corrected in §4 |

**Cause 3 is the operative one.** Lane B was not blocked from having work — **it was blocked from having a claimable row**, and the Task Claim Protocol requires one.

## 2 · What C-326 actually blocks — measured, not assumed

**[ADR-0300](adr/0300-inbound-source.md) offers four options: A a sibling port · B extend the Provider Port · C a second ingestion path · D bypass raw records. A slice is blocked only if it would encode an assumption about which is chosen.**

**Applying that test to E1's parts:**

| E1 component | Built? | Encodes an assumption? | |
|---|---|---|---|
| OAuth start, callback, connection, grant, catalog, encrypted credentials | **Built** | — | ✅ |
| `ResolveExecutionContext` | **Built**, tested, published, unwired | — | ✅ |
| **`HubSpotCompanies`** — paging, `_changed_since`, and the full error taxonomy `CrmTransient` · `CrmRateLimited` · `CrmCredentialRejected` · `CrmPayloadInvalid` · `CrmPermanent` | **Built** | — | ✅ |
| **`HubSpotCompanyMapper`** in `provider_normalization` | **Built** | **No** — ADR-0300 says so itself: *"a CRM mapper is one more `ProviderMapper` subclass, and nothing about it is special"* | ✅ |
| **The source port** `IntegrationSourceAdapter` | Not built | **Yes.** Its existence *is* option A | 🔴 |
| **The runner** in `provider_platform` | Not built | **Yes**, and it is another lane's module | 🔴 |
| Deals and contacts mapping | Not built | **Yes** — needs new `ClaimAttribute` members, **ADR-0300 part 3, its own 🔴 ruling** | 🔴 |

> **So C-326 blocks exactly two artifacts — the port and the runner — plus the vocabulary, which was always a separate ruling.**
>
> **Lane B has already built everything on both sides of them.** The client that reads HubSpot exists with its error taxonomy; the mapper that normalises the result exists; the context that supplies the credential exists. **What is missing is the wiring between them, and the wiring is the decision.**

**That is a sharper statement than *"E1's read is blocked"*, and it changes what is claimable.** [409](409-inbound-source-port-contract.md) remains the contract for the moment C-326 is ruled — **and it becomes a small slice, not a large one, because both ends already exist.**

## 3 · What is executable inside `integrations` today

**Required by the approved **CRM Integrations** screen, and encoding no assumption about C-326.**

> *"Health is checked every minute. **Two consecutive failures pause writes** and raise a signal to the workspace admins."*

**What exists:** `ConnectionResponse` carries `state`, `attention`, `reason`; `SystemResponse` carries `working` and `needs_attention`. **All of it is derived from grant and credential *records*.**

**What does not exist: any check that the credential actually works.** A connection whose token is structurally valid and whose HubSpot user lost a permission reads as healthy — **which is the exact scenario the approved screen is built around**: *"Writes are paused — the connected user lost a permission… two fields became read-only for the integration user at 06:41."*

**A reachability probe needs only what is already built** — `ResolveExecutionContext` for the credential, `HubSpotCompanies` for the call, and its existing error taxonomy to classify the outcome. **No source port. No runner. No vocabulary. No new claim.**

## 4 · Lane B's claimable work

**Two slices, drafted as [TASK-407](../BACKLOG.md) and [TASK-408](../BACKLOG.md).** Both are in modules Lane B already holds, both serve an approved screen, and neither waits on anything.

| | Slice | Module | Why it is not blocked |
|---|---|---|---|
| **B-i** | **Connection health probe** | `integrations` | §3 — uses only built components |
| **B-ii** | **Global Search typed grouping and explainable ranking** | `knowledge_graph` | `account-search` exists; the approved screen specifies grouping, ranking factors and the dominant-factor disclosure |

**The saved-view store from [417](417-executable-slice-audit.md) §4 is deliberately not drafted.** Its placement is a [C-010](../LANE_COORDINATION.md)-shaped question, and **giving a lane a row whose home is undecided is how the last collision happened.**

## 5 · What this does not do

**It does not resolve C-326.** The port is genuinely a product-owner decision, re-tested here and confirmed: **building it encodes the ruling**, and a lane may not proceed where proceeding encodes the answer.

**It does not move E1's estimate.** The read still needs the port, the runner and the vocabulary. **What changed is the measurement of how much of E1 is already done** — more than the board records — and therefore how small the post-ruling slice is.

**It does not reassign a module.** Lane B holds `integrations` and `knowledge_graph`; both slices are inside them.

> **The finding worth carrying forward: *blocked* was true of the task and false of the lane.** A task blocked on a decision does not make its module unavailable, and **the register recorded the task's state where a reader would look for the lane's.**
