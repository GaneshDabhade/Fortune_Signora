# 456 · CRM Integrations — screen-by-screen traceability audit

**Lane C · Product Office · 2026-08-05.** **Eleventh audit under [D-078](../DECISION_REGISTER.md).**
**Screen 11 of 16** — *"Connect, map, sync, health, disconnect"* ([410](410-approved-ui-specification.md)). **Wave 5.**

---

# 0 · The finding: this is the most complete backend behind any unbuilt screen

**`integrations` has 25 domain classes and they cover the screen's five verbs end to end.**

| Screen verb | Domain | |
|---|---|---|
| **Connect** | `ConnectedAccount` · `Credential` · `OAuth` · `IntegrationGrant` | ✅ |
| **Map** | `Capability` · `CatalogEntry` · `IntegrationSourceDescriptor` | ✅ |
| **Sync** | **`IntegrationSourceAdapter`** · `IntegrationFetchRequest` · `IntegrationRecord` · `IntegrationPage` | ✅ **[409](409-inbound-source-port-contract.md) is the contract, [C-326](../LANE_COORDINATION.md) ruled** |
| **Health** | `ConnectionProbe` · `ProbeResult` · `ConnectionHealth` | ✅ |
| **Disconnect** | `ConnectionState` · `ConnectionTransitionError` | ✅ *"The customer disconnected it here. Deliberate, and reversible"* |
| **Failure** | **Six typed errors** — transient · rate-limited · permanent · unsupported · invalid payload | ✅ **[ADR-0037](adr/0037-failure-categories.md)'s taxonomy, applied** |

> **Every element the screen names has a domain type, and [TASK-402](../BACKLOG.md) is `IN VALIDATION`.** ⚠️ **The one remaining blocker is not architectural: it is the HubSpot developer application** — **external, and no amount of preparation moves it.**

---

# 1 · ⚡ Two open items land here, and neither was raised on this screen

## [446 §3](446-companies-traceability-audit.md)'s import challenge is this module's

**Companies' *"import"* built as a file upload would be a second inbound path for customer data.** **This screen owns the first one.**

> **An import is an `IntegrationSourceAdapter` whose transport is a file** — same resolution, same provenance, same falsifiability, same *"each mapper reads only its own vendor's shape."* ✅ **`IntegrationSourceDescriptor` and `IntegrationPage` already express a paged, described source.** **The port needs no change; it needs a second implementation.**

## The `Execution Context` collision [452 §1](452-app-shell-traceability-audit.md) found is this module's word

**`ExecutionContext` is `integrations`' — the resolved context for calling a customer's system.** **The shell's is `CurrentWorkspace`.** ⚡ **Registered as `qualified` in the [vocabulary](../coordination/vocabulary.toml): `Integration Execution Context` and `Workspace Context`, on the `Owner` pattern** — **no rename, and the bare word refused in new work.**

---

# 2 · Findings

| | |
|---|---|
| **Existing and correctly modelled** | All five verbs · the six-error taxonomy · `ResolveExecutionContext` · the source port and its descriptor |
| **Extension candidates** | ⚡ **A file-transport `IntegrationSourceAdapter`** — Companies' import, arriving in the module that already owns inbound data |
| **Architectural evolution** | ⛔ **None** |
| **Missing foundational capabilities** | ⛔ **None** |
| **Missing workflows · entities · events · permissions · projections · platform capabilities** | ⛔ **None.** **Sync health, field mapping and write-back are all [TASK-402](../BACKLOG.md)'s remaining slices, not gaps** |
| **Vocabulary** | ⚡ **`Execution Context` → qualified** — §1 |

**Nothing new. The screen is blocked on a developer application, and that is a business action rather than an architectural one.**
