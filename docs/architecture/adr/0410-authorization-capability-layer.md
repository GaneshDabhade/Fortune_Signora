# ADR-0410 — Authorization capability separates from tenancy membership

| | |
|---|---|
| **Status** | ✅ **RATIFIED — product owner, 2026-08-12, as [C-1429](../../LANE_COORDINATION.md)** |
| **Decision** | ✅ ***"Use a capability/permission layer ABOVE the existing `WorkspaceRole` enum. Do NOT simply expand `WorkspaceRole` from OWNER/MEMBER into every UI role shown by the designs."*** |

## 1 · The two concerns, and why the enum was right to stay small

📁 **The ruling states it:** *"`WorkspaceRole` represents tenancy membership and is currently deliberately constrained to `OWNER`/`MEMBER`. The designs' Admin / Analyst / Effective permissions concepts represent **authorization capabilities**, which is a different concern."*

| | **Membership — `WorkspaceRole`** | **Capability — this ADR** |
|---|---|---|
| **Answers** | *Does this person belong to this workspace, and may they administer it?* | *May this person perform this action on this resource?* |
| **Changes** | ⚡ **Almost never** — it is a tenancy primitive | **Whenever the product grows a surface** |
| **Authority** | 📁 `workspace_tenancy/domain/entities.py` | 📁 **Casbin, unchanged** ([ADR-0010](0010-identity-and-access.md)) |

⛔ **Widening the enum would have made every new screen a change to a tenancy primitive.** ⚡ **That is why `OWNER` and `MEMBER` stay exactly as they are.**

## 2 · Casbin remains the implementation authority

📁 **The ruling: *"Existing authorization/RBAC/Casbin architecture must remain the implementation authority."*** ⛔ ***"Do not create a second independent authorization model."***

**So `Admin` and `Analyst` are *named sets of capabilities*, expressed in the authorization layer the repository already has** — 📁 [§7](../../../CLAUDE.md): a Casbin policy check wired as a FastAPI dependency, evaluated before application code, **always including `workspace_id` in the policy tuple.**

⚡ **`policy.csv` is already a registry every lane extends**, and [§20a](../../../CLAUDE.md) already distinguishes **declaring a `Resource`** from **granting authority**. **This ADR adds no new mechanism; it says which mechanism these belong to.**

## 3 · Effective permissions

📁 **The design draws *"Effective permissions"* and *"A Member will be able to…"*.**

✅ **That is a *read* of the authorization layer — the resolved answer for a person, computed, never stored.** ⛔ **A stored copy of a derivable fact is the defect [§2](../../../CLAUDE.md) names**, and here it would be a security defect too: **a stale copy of what somebody may do is a claim the enforcement point does not honour.**

## 4 · Field-level permissions — in scope, and stated separately

📁 **[C-210](../../LANE_COORDINATION.md)'s ruling: *"Field-level permissions are ALSO NOT implicitly approved… That is a separate authorization capability question."*** ✅ **It is *this* question, and it lands here rather than nowhere.**

⚠️ **Casbin's resource/action model does not express a per-field grant**, and the design requires one — *"read-only fields show a lock on hover"*.

⛔ **This ADR does not choose the mechanism.** ✅ **It records that a per-field grant is an authorization concern, belongs in this layer, and must not be solved by a UI-only convention** — 📁 [§20c](../../../CLAUDE.md): *a client-side permission check is a courtesy, never enforcement, and must never be the only check.*

## 5 · Migration and backward compatibility

📁 **The ruling requires it explicitly: *"Migration/backward compatibility must be explicitly addressed by the architecture contract."***

- ⛔ **No existing membership changes meaning.** **Every current `OWNER` and every current `MEMBER` keeps exactly the authority it has today** — the capability layer is additive.
- ⛔ **No endpoint's authorization weakens during the migration.** ⚡ **A capability that is not yet granted denies**, which is the safe direction; the reverse is a security defect.
- ✅ **The Security Invariants suite gains the guarantee rather than documenting it** ([§11](../../../CLAUDE.md)): **a member must not acquire an owner's capability through the new layer.**

## 6 · What this releases

✅ **Settings** — *Roles & permissions*, *New role*, and the role half of its remaining scope.
✅ **Team Management** — `Admin`, `Analyst`, *Change to Analyst*, *Effective permissions*, *A Member will be able to*.

⛔ **And what it does not:** 📁 ***"Do not invent UI-only roles that have no authorization semantics."*** ⚡ **A role a screen shows must be a set of capabilities something enforces.**

## 7 · What this ADR deliberately does not decide

⛔ **The capability vocabulary · the named role sets and their contents · schema · API shape · how a per-field grant is expressed · the migration's steps · any UI.**

✅ **All of it is Lane A's, against Casbin as the implementation authority.** ⚠️ **Lane A proposes the capability names and role sets in its Slice Handoff; they become part of the ratified contract.**
