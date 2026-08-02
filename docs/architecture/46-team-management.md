# Team Management — product discovery

> **Phase 1 and Phase 2 of the Team Management initiative, assigned to Lane A by the product owner on 2026-08-02.** No code has been written and none will be until the bounded-context question in §6 has an answer.
>
> **This is a product discovery, not a design document.** It starts from the customer, measures what exists, and ends with the one decision that is not a lane's to take.

**Measured at `origin/integration`, 2026-08-02.** Membership from `backend/modules/workspace_tenancy/`, authorization from `policy.csv`, authentication from `frontend/lib/auth/`, and the vendor surface from `node_modules/better-auth/dist/plugins/`.

---

## 1 · What exists today, measured

| | |
|---|---|
| **Aggregates** | `Workspace` and `Membership`, deliberately separate — *"independent lifecycles… no consistency requirement forcing it"* |
| **Roles** | `owner` and `member`. Two, and the enum says *"deliberately minimal today"* |
| **Use cases** | `create_workspace` · `add_member` · `get_workspace` · `list_user_workspaces` · `list_workspace_members`. **Five, and all of them create or read** |
| **Endpoints** | `GET`/`POST /workspaces` · `GET /workspaces/{id}` · `GET`/`POST /workspaces/{id}/members` |
| **Who becomes the first administrator** | Whoever creates the workspace. `create_workspace` mints *"the founding OWNER membership atomically"* — a good decision, already made |
| **Screens** | **None.** `useWorkspaceMembers` exists and its list reaches no page |

### Four things are missing, and they are not the same kind of missing

| | |
|---|---|
| **1 · There is no way to invite anybody** | `POST /members` takes **`user_id: UUID`**. A customer cannot type one, and nothing resolves an email to a user. **An organization is permanently whoever created it** |
| **2 · There is no way to remove anybody** | **`p, owner, *, member, remove` is granted in [`policy.csv`](../../backend/signora_platform/authorization/policies/policy.csv):5** — and there is **no endpoint, no use case, and no domain method.** A reviewed authorization grant for an operation the system cannot perform |
| **3 · A membership has no lifecycle** | Created, never changed. No role change, no suspension, no departure, no ownership transfer. `Membership` carries `updated_at` and `updated_by`, and **nothing has ever updated one** |
| **4 · Nobody has a name** | [C-024](../LANE_COORDINATION.md). A team page today renders UUIDs |

> **Number 2 is the most interesting.** It is the same shape as the seam that produced PS-03, PS-05, TS-02 and three Provider Platform slices: **a contract the repository declared and never honoured.** Somebody reviewed that grant and decided owners may remove members. The product cannot.

---

## 2 · The questions, answered from the customer rather than the schema

**The product owner set thirty. They collapse into six decisions, and the rest follow from those.**

### D1 · An invitation is addressed to an email, not to a user

**A customer inviting a colleague knows their email address and nothing else.** They do not know whether that person has a Signora account, and **they must not need to.** Every alternative — invite links, join codes, domain auto-join — either requires the invitee to already exist or lets anybody with the link in.

**Consequences, and each answers several of the thirty:**

| | |
|---|---|
| *What if they already have an account?* | Accepting attaches a membership to the existing user. **Nothing new is created** |
| *What if they sign in with Google instead of email?* | **Irrelevant, and deliberately.** [ADR-0033](adr/0033-authentication-methods.md) already rules that a method is not a fallback — the token carries no record of how anybody signed in. An invitation names an address; how they prove they own it is Better Auth's |
| *Can one email belong to multiple organizations?* | **Yes**, and it already can: `list_user_workspaces` exists and the shell has a workspace selector. Membership is `(workspace, user)` and always was |
| *Can somebody belong to multiple workspaces?* | Same fact from the other side. **Already true, already built** |

### D2 · An invitation is a first-class record with a lifecycle, not a link

**Because the product owner's questions are all about its states**, and a link has none: *pending · accepted · revoked · expired.*

| Question | Answer |
|---|---|
| Should invitations expire? | **Yes.** An invitation is a standing grant to enter a customer's data. One that never expires is a credential nobody remembers issuing |
| Can they be revoked? | **Yes**, and revocation must be immediate — it is the control an administrator reaches for when they got the address wrong |
| Can they be resent? | **Yes**, and resending is **a new delivery of the same invitation**, not a new invitation. Two live invitations to one address is two ways in |
| How does an administrator know whether somebody accepted? | The state is on the record. **Pending invitations appear beside members**, because *"who is in my organization"* includes *"who is on their way in"* |
| How do we recover abandoned ones? | An expired invitation stays visible with its state. **Expiry is not deletion** — an administrator needs to see that it lapsed to know to resend |

### D3 · Leaving and removal are the same operation with different actors, and the record is immutable

**`CLAUDE.md` §2: immutability is the default for anything that records a fact.** A membership that once existed is a historical fact — the Timeline, decision history and audit trail all cite actors.

> **A membership is therefore ended, never deleted.** The row survives with the moment and the actor that ended it, exactly as `WorkflowState` records a decision.

**This answers the departure questions at a stroke:** what happens to assignments, timeline entries, decision history and audit actors when somebody leaves is **nothing** — every one of them cites a membership that still exists and still says who it was.

### D4 · The last owner cannot leave, and that is a domain invariant rather than a UI check

*What if there is only one owner?* — **the operation is refused, in the domain.** A workspace with no owner is a workspace nobody can administer, and it is unrecoverable without support intervention.

> **Types should make incorrect architecture impossible** (§2). The refusal belongs where the aggregate can see the count, not in a dialog that a second tab can race.

**Ownership transfer is therefore the *enabling* operation, not a convenience:** a sole owner who wants to leave must first make somebody else an owner. **That is one flow, not two**, and it is the honest sequence.

### D5 · Suspension is deferred, with the trigger stated

**Suspend/reactivate was on the product owner's list.** Discovery says it is **not Day One**, and the reason is not effort:

**Removal already covers the customer need** — *"this person should not have access."* Suspension is meaningfully different only when access must be **restored with its history intact**, which matters when a membership carries accumulated state: assignments, saved views, quotas. **Signora has none of that yet.**

**Trigger to build it:** the first capability that attaches durable per-member state to a membership. **Until then, suspend is remove-and-reinvite**, and the record shows both.

### D6 · Two roles remain two, and the enum's own comment is the reason

`WorkspaceRole` says *"deliberately minimal today (owner/member). Casbin owns fine-grained, resource-level permission evaluation."*

**That separation is already correct and is what makes custom roles cheap later**: a role is a Casbin subject, and adding one is a `policy.csv` line rather than a schema change. **Adding roles now would be building for a load nobody has** (§14) — and would need the permission-explanation UI in §4 before it helped anybody.

---

## 3 · The customer experience, in the order it is met

**Not a page. A capability, and it appears in four places.**

```
  first run          administration            joining              leaving
  ─────────          ──────────────            ───────              ───────
  create org         Settings → Team           email → accept       leave, or be removed
  ↳ you are owner    ├ members + roles         ↳ existing account   ↳ record ends,
  ↳ "invite your     ├ pending invitations       attaches             never deletes
     colleagues"     ├ invite · revoke · resend ↳ new account
                     └ transfer ownership         signs up first
```

| Surface | What it answers |
|---|---|
| **Settings → Team** | *Who is in my organization, who is on their way in, and what can each of them do* |
| **The invitation email** | *Somebody asked me to join. What is this and what happens if I click* |
| **First run** | *I have an organization and nobody in it.* The empty state is the invitation prompt — **the one moment an administrator is guaranteed to be looking** |
| **Every actor line already in the product** | Decision history, the workflow line and the timeline all say *"somebody here"* today ([D23](38-product-design-principles.md)). **They become names**, and nothing about them changes structurally |

**States, in full**, because the product owner asked for them and because R2-02's lesson is that an absent state reads as a missing feature: **no members yet** (impossible — the creator is one) · **no pending invitations** · **invitation expired** · **invitation revoked** · **you are the only owner** (transfer offered, leave refused *with the reason*) · **loading** · **the request failed** · **you are a member, not an owner** (the list is readable, the controls are absent, never disabled).

---

## 4 · Stress test — against Signora's roadmap, not against every enterprise feature

**Each row asks the same question: does today's design absorb it, or need rewriting?**

| Growth | Absorbed by | Verdict |
|---|---|---|
| **Startup → mid-market → enterprise** | Membership is `(workspace, user, role)`. Scale changes the page, not the model | ✅ |
| **Departments · business units · subsidiaries** | **Multiple workspaces**, which already work — `list_user_workspaces` and the selector exist | ✅ **and it is the answer we already have** |
| **Multiple owners · org administrators · managers · reps · SDRs · RevOps** | **Casbin subjects.** A role is a `policy.csv` line; the membership schema does not move | ✅ |
| **Consultants · contractors · guests · temporary access** | An invitation with an expiry is already the mechanism. **A time-bounded *membership* is the same field one level along** | ✅ |
| **Read-only users** | A Casbin role with reads and no writes. **Already expressible today** | ✅ |
| **Custom roles · fine-grained permissions** | Casbin's model. **The UI is the harder half** — §5 |
| **Bulk invitations · bulk role changes** | A list operation over a single-item domain method. **The domain does not change; the screen does** | ✅ |
| **Ownership transfer · restructuring** | D4 makes transfer a first-class operation on Day One | ✅ |
| **Audit exports · compliance history** | **D3's immutable ended-membership record is the audit trail.** Export is a projection over it | ✅ **because immutability was chosen now** |
| **SSO · SCIM · Azure AD · Okta · Google Workspace** | ⚠️ **The one that needs saying.** SCIM *provisions memberships from an external directory* — an invitation flow it bypasses entirely. **It does not break the model**: SCIM becomes a second author of the same membership record. **What it breaks is the assumption that a membership is always created by an invitation**, so the record must not require an invitation id |
| **Comments · mentions · approvals · notifications** | All need *"which person"*, which is [C-024](../LANE_COORDINATION.md), and all cite a membership that D3 guarantees still exists | ✅ |

### The four architectural questions, answered

| | |
|---|---|
| **Have I mixed identity with authorization?** | **No, and the split is the design.** Better Auth owns *who you are*; Casbin owns *what you may do*; Membership owns *which organization you belong to*. Three things, three owners, and the invitation is the only place they meet |
| **Have I mixed workspace membership with business ownership?** | **They are already separate and must stay so.** `Opportunity.owner_id` is *who is working this account*; membership is *who may sign in to this organization*. **D3's ended-membership record is what keeps an assignment readable after somebody leaves** |
| **Is another bounded context emerging?** | **One is, and it is not Team Management** — see §6 |
| **Am I coupling unnecessarily?** | **One coupling is real and unavoidable:** every module that names an actor depends on membership resolving to a person. That is C-024, and it is a *contract* rather than a coupling — the same shape as `EntityName` |

---

## 5 · Where the design is hardest, and it is not the schema

**Two honest weaknesses, recorded now rather than discovered at slice four.**

| | |
|---|---|
| **Permission explanation** | A customer asks *"what can a member actually do?"* Casbin holds the answer as 30 policy tuples, in engineering's vocabulary. **Rendering that honestly, in a seller's words, is harder than every other screen here**, and it gets worse with custom roles. **No design yet** |
| **Navigation** | D38 reduced navigation to two entries on purpose, and Team is a third destination. It fits under Settings today — **and Settings is owner-only ([C-008](../LANE_COORDINATION.md))**, so a member cannot see who their colleagues are. **The same guard, blocking the same population, for the second time** |

---

## 6 · The decision that is not a lane's

### Better Auth ships this capability, and it is installed and unused

`node_modules/better-auth/dist/plugins/organization/` is **present** and **not enabled** in [`lib/auth/server.ts`](../../frontend/lib/auth/server.ts). Its error codes name the whole domain: `INVITATION_NOT_FOUND` · `INVITATION_LIMIT_REACHED` · `MEMBER_NOT_FOUND` · `ORGANIZATION_MEMBERSHIP_LIMIT_REACHED` · `ORGANIZATION_SLUG_ALREADY_TAKEN`.

**`CLAUDE.md` §13 and Principle 15 are unambiguous:** authentication and authorization are **bought, not built**, and *"Claude must never implement a bespoke auth mechanism, even a small or temporary one."*

> **So the question is real and it must be answered before any code:** is an invitation an **authentication** concern the vendor already solves, or a **tenancy** concern that belongs where `workspace_id` lives?

### Why the answer is not simply "use the plugin"

| | |
|---|---|
| **The auth schema is unreadable by the application** | Migration `0005` revokes `signora_app` from the `auth` schema, and [ADR-0026](adr/0026-jwt-boundary-architecture.md) keeps the tiers apart deliberately. **Membership in the plugin's tables is membership the Python tier cannot verify** |
| **§13 requires server-side re-verification** | *"The `active_workspace_id` claim is a routing hint, never a grant. Membership is re-verified server-side against Workspace & Tenancy, on every request."* **That check reads `membership`.** Moving membership out of reach would break the tenancy model at its root |
| **RLS needs `workspace_id` on application tables** | Tenancy is enforced in Postgres, in the application schema. **A vendor's organization table cannot participate** |

### Three options, and the recommendation

| | | |
|---|---|---|
| **A** | **Enable the plugin and own membership there** | ❌ **Rejected on evidence, not preference.** It breaks server-side membership verification and the RLS root. This is not a build-vs-buy trade — it is a tenancy-model change |
| **B** | **Build invitations in `workspace_tenancy`** | Keeps one owner for membership and needs no cross-tier work. ⚠️ **But an invitation is addressed to an email that may not be a user yet, which is identity** — and §13 says do not build identity |
| **C** | **Split at acceptance — recommended** | **Better Auth owns the invitation** (an address, its expiry, its delivery, and proving the recipient owns it — all authentication). **Signora owns the membership** it creates on acceptance. **The handoff is one call at the moment somebody accepts** |

**C is recommended, and it is the boundary the repository already draws.** Better Auth answers *who are you*; Signora answers *what may you reach*. An invitation is a claim about an address becoming a person — the vendor's question. A membership is a tenancy fact — Signora's, and already is.

**What C costs, stated plainly:** enabling a plugin is a **new vendor capability**, which needs the product owner and an ADR amendment to [ADR-0010](adr/0010-identity-and-access.md); and acceptance becomes a two-tier operation whose failure modes must be designed rather than discovered.

**What it buys:** Signora writes no token minting, no expiry logic, no email-ownership proof and no delivery — the four parts of an invitation that are security-sensitive and entirely commodity.

---

## 7 · [C-024](../LANE_COORDINATION.md) can be narrowed on evidence, before any ruling

**The product owner asked that dependencies be narrowed by evidence rather than by another decision. Discovery produces one.**

**C-024's hard half was never *"can we get a name"* — it was *"which ids may a caller resolve"*, a privacy-scoping question.** Every option in that item needed an answer to it.

> **An email-addressed invitation removes the question for the Team page.** The membership records **the address the organization typed when it invited them.** There is nothing to resolve and nobody to look up: **the organization already knows, because it supplied it.**

**And the distinction that keeps this inside §13:** an invited address is **an immutable fact about an invitation** — a record of what an administrator did. A display name is **a mutable mirror of somebody's profile**, which is what §13 keeps out of the Python tier and what would go stale. **Recording the first is not owning identity.**

| | |
|---|---|
| **Narrowed** | The Team page can list an organization's members **without any cross-tier lookup, BFF, or admin plugin.** TS-01 stops depending on C-024 |
| **Still open** | Display names, avatars, AI attribution, audit actors and mentions. **C-024 remains, and remains the highest-leverage item** — it is simply no longer what blocks Team Management |

---

## 8 · What is proposed, and what is not

**Not proposed: a new module.** Membership is `workspace_tenancy`'s and stays there — it is the tenancy root, and §13's server-side verification reads it. **Team Management is a capability across two tiers, not a fifteenth bounded context**, and the analysis in §4 found no aggregate that wants its own boundary.

**Not proposed: any code.** Option C enables a vendor capability, which is 🔴.

**Proposed: a ruling on §6**, and then implementation in slices, each independently releasable — the members list first, because it is the one that needs nothing from §6 and closes [J9](43-customer-experience.md).
