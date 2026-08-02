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
| **4 · Nobody has a name** | [C-203](../LANE_COORDINATION.md). A team page today renders UUIDs |

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
| **Comments · mentions · approvals · notifications** | All need *"which person"*, which is [C-203](../LANE_COORDINATION.md), and all cite a membership that D3 guarantees still exists | ✅ |

### The four architectural questions, answered

| | |
|---|---|
| **Have I mixed identity with authorization?** | **No, and the split is the design.** Better Auth owns *who you are*; Casbin owns *what you may do*; Membership owns *which organization you belong to*. Three things, three owners, and the invitation is the only place they meet |
| **Have I mixed workspace membership with business ownership?** | **They are already separate and must stay so.** `Opportunity.owner_id` is *who is working this account*; membership is *who may sign in to this organization*. **D3's ended-membership record is what keeps an assignment readable after somebody leaves** |
| **Is another bounded context emerging?** | **One is, and it is not Team Management** — see §6 |
| **Am I coupling unnecessarily?** | **One coupling is real and unavoidable:** every module that names an actor depends on membership resolving to a person. That is C-203, and it is a *contract* rather than a coupling — the same shape as `EntityName` |

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

## 7 · [C-203](../LANE_COORDINATION.md) can be narrowed on evidence, before any ruling

**The product owner asked that dependencies be narrowed by evidence rather than by another decision. Discovery produces one.**

**C-203's hard half was never *"can we get a name"* — it was *"which ids may a caller resolve"*, a privacy-scoping question.** Every option in that item needed an answer to it.

> **An email-addressed invitation removes the question for the Team page.** The membership records **the address the organization typed when it invited them.** There is nothing to resolve and nobody to look up: **the organization already knows, because it supplied it.**

**And the distinction that keeps this inside §13:** an invited address is **an immutable fact about an invitation** — a record of what an administrator did. A display name is **a mutable mirror of somebody's profile**, which is what §13 keeps out of the Python tier and what would go stale. **Recording the first is not owning identity.**

| | |
|---|---|
| **Narrowed** | The Team page can list an organization's members **without any cross-tier lookup, BFF, or admin plugin.** TS-01 stops depending on C-203 |
| **Still open** | Display names, avatars, AI attribution, audit actors and mentions. **C-203 remains, and remains the highest-leverage item** — it is simply no longer what blocks Team Management |

---

## 8 · What is proposed, and what is not

**Not proposed: a new module.** Membership is `workspace_tenancy`'s and stays there — it is the tenancy root, and §13's server-side verification reads it. **Team Management is a capability across two tiers, not a fifteenth bounded context**, and the analysis in §4 found no aggregate that wants its own boundary.

**Not proposed: any code.** Option C enables a vendor capability, which is 🔴.

**Proposed: a ruling on §6**, and then implementation in slices, each independently releasable — the members list first, because it is the one that needs nothing from §6 and closes [J9](43-customer-experience.md).

---

## 9 · Phase 3 — the administrator's experience, and two corrections to §7

**Written before implementation, and it began by finding two things wrong with this document's own conclusions.** Both are recorded rather than quietly edited, because each is a claim about sequencing that a lane acted on.

### Correction 1 — the C-203 narrowing is real, and it lands later than §7 says

**§7 concluded that the members list stops depending on C-203.** The reasoning holds. **The delivery does not.**

`MembershipResponse` carries `id · workspace_id · user_id · role · created_at`. **There is no address**, because no address was ever supplied: `create_workspace` mints the founder's membership from a session, and `POST /members` takes a `user_id`. **The column the narrowing depends on is written by the invitation flow**, which is [C-206](../LANE_COORDINATION.md).

**And it cannot be backfilled.** For every membership that exists today nobody typed an address, and inventing one would be the mistake [B-004](../BUGS.md)'s migration explicitly refused — *"existing rows keep an empty subject rather than a guessed one."*

> **So the narrowing stands and the sequencing was wrong.** The members list becomes nameable **with TM-03, not before it.** *"TS-01 is unblocked"* was a claim about the design, stated as though it were a claim about the schema.

### Correction 2 — a self-directed action cannot be authorized at all

**Leaving an organization looked like the one slice needing neither names nor a ruling.** It needs neither, and it still cannot be built.

`policies/model.conf` defines the request tuple as **`(sub, dom, obj, act)`**, where `sub` is *"the caller's workspace role"*. **The caller's identity is not in the tuple** — only their role. So Casbin can express *"an owner may remove a member"* and **cannot express *"anybody may remove themselves"***.

| Route out | Why not |
|---|---|
| Add `Action.LEAVE` | `Action` lives in `signora_platform/authorization/enforcer.py` — **frozen (§20a)** |
| Grant `p, member, *, member, remove` and restrict to self in the handler | **The policy would then say members may remove members, which is false.** A reviewed authorization grant that overstates is worse than an absent one — this repository already has one such grant, and it is finding #2 of §1 |
| Skip authorization for this endpoint | §7: *"Authorization for every endpoint is a Casbin policy check."* No carve-out, and rightly |

> **Every self-directed operation in Signora's future is inexpressible today** — leave an organization, change your own notification settings, delete your own account. **Raised as [C-207](../LANE_COORDINATION.md).** It is small, structural, and it will be met again.

### What this leaves buildable today: nothing, and that is the honest answer

| Slice | Blocked on |
|---|---|
| **Members list** | [C-203](../LANE_COORDINATION.md) — until TM-03 supplies addresses |
| **Leaving** | [C-207](../LANE_COORDINATION.md) — self-directed authorization |
| **Removal · role change · ownership transfer** | Naming a person — [C-203](../LANE_COORDINATION.md) |
| **Invitations** | [C-206](../LANE_COORDINATION.md) |

**The design below is therefore written now and implemented when the rulings land.** That ordering is deliberate: the questions it answers are product questions, and none of them gets easier by waiting.

---

## 10 · The design — an administrator's workspace, not a table of users

> **The test the product owner set:** *"A good Team Management page should feel like an administrator's workspace rather than a table of users."*
>
> **What separates the two is that a workspace answers questions and a table answers lookups.** An administrator arrives with one of four questions, and the page is ordered by how often they arrive with each.

```
  Settings → Team

  ┌────────────────────────────────────────────────────────┐
  │  Your team                                             │
  │  4 people · 2 can administer Signora                   │  ← the answer to
  │                                                        │    "is this right?"
  │  ┌──────────────────────────────────────────────────┐  │
  │  │ ⚠ 2 invitations sent over a week ago,            │  │  ← only when true
  │  │   still unaccepted            Resend · Revoke    │  │
  │  └──────────────────────────────────────────────────┘  │
  │                                                        │
  │  People                                                │
  │  ana@acme.com          Owner    joined 12 June   You   │
  │  ravi@acme.com         Owner    joined 2 July          │
  │  jo@acme.com           Member   joined 4 July          │
  │                                                        │
  │  Invited                                               │
  │  sam@acme.com          Member   sent 6 days ago        │
  │  kit@acme.com          Member   expired 2 days ago     │
  │                                                        │
  │  ＋ Invite a colleague                                  │
  └────────────────────────────────────────────────────────┘
```

### The eleven questions, answered

| | |
|---|---|
| **How does an administrator know who should be invited next?** | **The product does not know, and must not guess.** Signora has never seen a customer's org chart. **What it can do is make the absence visible**: a workspace of one says so, and every seller who signs in and finds an empty attention list is a person somebody forgot to invite. *(If a directory is ever connected — SSO, SCIM — the question becomes answerable and the answer is theirs, not ours.)* |
| **How does the product help recover forgotten invitations?** | **The banner, and it is the whole feature.** An invitation older than a week and unaccepted is surfaced at the top with *Resend* and *Revoke* beside it. **Nobody goes looking for a forgotten invitation** — that is what forgotten means — so the page has to raise it |
| **What happens when they expire?** | **They stay, marked expired.** Deleting them would erase the evidence that somebody was invited and never came, which is the one fact an administrator needs to act on |
| **Should pending appear differently from members?** | **Different section, not a status column.** *"Who is in my organization"* and *"who is on their way in"* are different questions, and a `Status: pending` column invites sorting a person next to a not-yet-person |
| **How does first-run become Team Management?** | **The empty state is the invitation prompt.** A workspace of one has one honest sentence — *"You are the only person here. Signora is more useful when the people working these accounts can see them."* — and one control. **The one moment an administrator is guaranteed to be looking** |
| **What should a brand-new workspace look like?** | Exactly that. **Not an empty table with headers** — a table of one row with column headings is the product showing its schema |
| **How is ownership transfer explained?** | **As a gain, then a loss, in that order.** *"Ravi will be able to administer Signora, invite people and change your organization's settings."* — then, only when the actor is the sole owner and is leaving: *"You will no longer be able to."* **The second sentence is the dangerous one and it appears only when it is true** |
| **What if an owner accidentally removes themselves?** | **They cannot, if they are the last one** — refused in the domain (D4), not in a dialog a second tab can race. **If they are not the last, it succeeds and is recoverable**: another owner re-invites them, and D3's ended-membership record shows exactly what happened and when |
| **How are dangerous actions progressively disclosed?** | **By scope, not by hiding.** Row actions live behind a per-row menu; *Transfer ownership* and *Leave* live at the foot of the page, away from the list — **an administrator scanning names should not be one mis-click from restructuring the organization** |
| **Which actions deserve confirmation?** | **Those that are hard to reverse or affect somebody else**: removing a person, transferring ownership, leaving. Each names the person and the consequence — never *"Are you sure?"*, which asks a question the customer cannot answer |
| **Which deserve undo instead?** | **Revoking an invitation** — reversible by resending, and confirming it would be ceremony over a control an administrator uses to correct a typo. **Nothing else here is undoable**, and offering undo where the underlying operation cannot be reversed is worse than a confirmation |

### The rest of the surface, decided

| | |
|---|---|
| **Search · filter · sort** | **Not on Day One, and the trigger is stated:** a workspace where the list does not fit on one screen. Three people do not need a search box, and D38's reasoning applies — a control that earns its place at 200 rows is furniture at 4 |
| **Last active** | **Not built, and not merely deferred.** It needs per-user activity tracking that does not exist, and it is the kind of number that reads as surveillance to the people in the list. If it arrives, it arrives with a stated purpose |
| **Bulk operations** | Same trigger as search. **The domain methods are per-member either way**, so the screen changes and nothing else does |
| **Ownership indicator** | **The role column, and the count in the header.** *"2 can administer Signora"* is the sentence that matters — it is what makes D4's refusal comprehensible before a customer meets it |
| **Permission explanation** | **Still the weakest part of this design.** *Owner* and *Member* are shown; what each may actually do is thirty Casbin tuples in engineering's vocabulary. **A tooltip would be a lie by compression.** Recorded in §5 and unsolved |
| **Keyboard and accessibility** | The list is a `<table>` with real headers; row menus are buttons; the dialog is the existing native `<dialog>`, which already traps focus. **Nothing new is invented** |
| **Responsive** | **Deferred to [C-026](../LANE_COORDINATION.md)** like every other screen, and it will be a real question here: five columns do not survive one column |

### Reuse — what this needs and what already exists

**Audited before designing, not after.** Everything below exists and will be used unchanged.

| Need | Already built |
|---|---|
| The member list | `useWorkspaceMembers`, `queryKeys.members`, `Membership` — **all three shipped and uncalled** |
| The viewer's own role | `useViewerRole` (TS-02) |
| Table · dialog · badge · empty state · skeleton · button · input · select | `components/ui/*` |
| Success and failure messaging | `useToast`, with `correlation_id` |
| Route guarding | `GUARDED_ROUTES`, `RouteGuard` |
| The settings entrance | **`/settings` and its card pattern (CX-01)** — a Team card joins Products and Connections |

**Nothing new is proposed for `components/ui`.** The one shape this page introduces — a per-row action menu — is used exactly once, and §20c is explicit that a component earns promotion to the library on its second caller, not its first.
