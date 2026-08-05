# 458 · Settings — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Thirteenth audit under [D-078](../DECISION_REGISTER.md).**
**Screen 16 of 16** — *"Attributed, reversible, in the audit log"* ([410](410-approved-ui-specification.md)). **Wave 6.**

---

# 0 · The finding: this screen's one sentence contains three separate capabilities

> **410 describes the whole screen as *"attributed, reversible, in the audit log."*** **Three words, three capabilities, and only one of them exists.**

| | | |
|---|---|---|
| **Attributed** | ✅ **Built** — `created_by`, `actor_id` in 37 files, `Membership` records who changed what | ✅ |
| **Reversible** | 🔴 **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)** — the seventh screen asserting it | 🔴 |
| **In the audit log** | 🔴 **[R-07](../DOMAIN_DISCOVERY_REGISTER.md)** — attribution exists everywhere; **a readable surface exists once**, as `GET /workspaces/{id}/history` | 🔴 |

> ⚡ **So Settings is not a screen that needs three things built. It is the screen where three cross-cutting capabilities are *stated together as one product promise*** — and [454 §3](454-r02-r03-implementation-preparation.md) already recommended `workspace_tenancy` as R-07's owner **on the strength of that single history endpoint.** **This audit is the evidence for that recommendation, arriving after it.**

---

# 1 · The matrix

| UI element | Source of truth | Audit | Consumers |
|---|---|---|---|
| **Members, roles, invitations, ownership transfer, history** | `Workspace` · `Membership` · `Invitation` · `WorkspaceRole` · `OwnershipTransferError` | ✅ **Built — 14 routes, the largest router in the repository** | Settings |
| **Leaving an organization** | `LastOwnerCannotLeaveError` + `Action.LEAVE` | 🔨 **[TASK-437](../BACKLOG.md) `CLAIMED`** — the grant shipped, the route is Lane A's | Settings |
| **Seats and billing** | — | 🔴 **[R-05](../DOMAIN_DISCOVERY_REGISTER.md) workspace lifecycle** · [TASK-411/412](../BACKLOG.md) | Settings · App Shell |
| **SSO · SCIM · API keys · webhooks** | — | 🔴 **[438 Epic J and K](438-platform-initiatives.md)**, deferred with triggers | Settings |
| **Audit-log export** | — | 🔴 **[R-07](../DOMAIN_DISCOVERY_REGISTER.md)**, and ⚠️ **export is [R-13](../DOMAIN_DISCOVERY_REGISTER.md)'s field dimension arriving from a fifth screen** | Settings · Companies · Reports |
| **Branding on exported artefacts** | — | ⬜ **Not extractable.** [415 §3](415-platform-foundation-incoming.md) records it overlapping incoming Modules 3 and 8 | ⬜ |

---

# 2 · Findings

| | |
|---|---|
| **Existing and correctly modelled** | The membership domain end to end · ownership transfer as one operation *(*"composing it from promote and demote leaves an intermediate state"*)* · `Action.LEAVE` and its two grants · the one history endpoint |
| **Extension candidates** | **[R-07](../DOMAIN_DISCOVERY_REGISTER.md) built on the existing history endpoint** — ✅ **the recommendation [454 §3](454-r02-r03-implementation-preparation.md) already made, now with its evidence** |
| **Architectural evolution** | ⛔ **None** |
| **Missing foundational capabilities** | **[R-03](../DOMAIN_DISCOVERY_REGISTER.md)** *(7th screen)* · **[R-05](../DOMAIN_DISCOVERY_REGISTER.md)** · **[R-07](../DOMAIN_DISCOVERY_REGISTER.md)** *(3rd screen)* — **all three already carried** |
| **Missing permissions** | ⚠️ **[R-13](../DOMAIN_DISCOVERY_REGISTER.md)'s field dimension, fifth screen** — an audit export must redact per reader |
| **Missing workflows · entities · events · projections** | ⛔ **None new** |
| **Vocabulary** | ✅ **`Workspace Owner` is canonical and this is the screen that renders it** — the qualification ruled at [C-420](../LANE_COORDINATION.md) has its first UI consumer here |
