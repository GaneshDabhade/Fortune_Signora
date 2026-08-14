# ADR-0414 · Inbound machine credentials are their own bounded context

**Status: ACCEPTED — product owner, 2026-08-13, ruling [C-1404](../../LANE_COORDINATION.md) ⓐ. Drafted by Lane C.**

> ⛔ **This ADR answers exactly one question: *where does the inbound API-key capability live?*** ⚠️ **It authorizes no generalized IAM system, no OAuth redesign, no new authentication mechanism, no additional machine-principal types, no credential sharing and no new webhook product features.**

---

## 1 · The decision

✅ **A new bounded context owns the inbound API-key credential lifecycle: issuance · rotation · one-time display · revocation · per-call audit.**

⛔ **It does NOT live in [`workspace_tenancy`](../../../backend/modules/workspace_tenancy/).** 📁 **The product owner's reason, recorded verbatim:** ***"API-key issuance, rotation, one-time display, revocation and per-call audit/logging constitute a credential lifecycle and should not be placed inside `workspace_tenancy`."***

⛔ **It does NOT live in `platform_foundation`** — that module has no runtime surface, and API keys need endpoints.

⛔ **And it does NOT live in [`integrations`](../../../backend/modules/integrations/), which is the near-miss.** ✅ **That module already publishes `Credential`, `ConnectedAccount`, `ConnectionState` and `ExecutionContext`** — 🔴 **for the opposite direction.** 📁 **[§13](../../../CLAUDE.md) forbids exactly this class of reuse — *"a sign-in OAuth token must never be reused as an integration OAuth token"*** — **and an inbound machine credential placed in the module that owns outbound ones is that defect with new nouns.**

## 2 · The boundary, in one table

| | Direction | Owner |
|---|---|---|
| **API key** | **A third party authenticates INBOUND to Signora** | ✅ **This context** |
| **Integration credential** | **Signora authenticates OUTBOUND to a provider** | 📁 `integrations`, unchanged |
| **Webhook** | **Signora performs durable OUTBOUND delivery** | 📁 **The existing outbox/relay pattern — [ADR-0011](0011-background-processing-and-event-bus-transport.md)** |

⛔ **Webhook delivery must not be placed in this context merely because both appear in [C-1404](../../LANE_COORDINATION.md).**

## 3 · What `workspace_tenancy` keeps

✅ **The ownership relationships, unchanged and not redesigned: the workspace · the member · machine-principal ownership.**

📁 **This is what [495](../495-principal-and-identity-boundary.md) already requires and why the anchors stay put:** **`workspace_id` is *"non-nullable for every non-human kind — a machine identity that is not workspace-scoped is a cross-tenant credential"*** · **`owner_user_id` — *"every machine principal is owned by a human… what makes revocation on offboarding tractable and audit attributable."***

⚡ **So the credential lifecycle moves and the anchors do not.** **A key is issued by this context, owned by a member, and scoped to a workspace.**

## 4 · What this ADR deliberately does not decide

⛔ **The module's name · its table names · its API shape · the key format and hashing scheme · the per-call audit record's fields · the retention of that audit.** ✅ **All Lane A's, and settled in the implementation task rather than here.**

⚠️ **The `PrincipalKind` members remain [495](../495-principal-and-identity-boundary.md)'s.** ⛔ **This ADR adds none and Lane A must not invent one.**

## 5 · Tenancy and security, which are not open questions

🔴 **The credential table is workspace-owned**, so [§8](../../../CLAUDE.md) binds in full: **non-nullable `workspace_id` · `FORCE ROW LEVEL SECURITY` · policies in the creating migration · registration in `tenancy_policy.py` in the same change.**

🔴 **A key is shown once at creation and never again** — 📁 the approved design's words — **so only a hash is stored, and the plaintext exists in one response and nowhere else.**

## 6 · Consequences

✅ **[TASK-1413](../../BACKLOG.md) becomes buildable once this is on `integration`**, scoped to the API-key half alone.
✅ **The webhook half separates and needs nothing from this ADR.**
⛔ **[C-1404](../../LANE_COORDINATION.md) is resolved and is not reopened** unless implementation reveals a concrete contradiction with an approved design or ADR.
