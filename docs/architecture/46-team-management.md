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

---

## 11 · Challenging my own conclusions — and one of them was wrong

**Seven challenges set by the product owner, answered against the repository rather than from memory.** One overturns a recommendation this document made two sections ago.

### Challenge 1 · Is Better Auth really the right owner for an invitation? — **No, and §6 was inconsistent with itself**

**§6 rejected option A — membership in the vendor's tables — on one argument:** the `auth` schema is unreadable by `signora_app`, so **the Python tier cannot verify what it cannot read.**

> **That argument applies just as forcefully to the invitation record, and §6 did not apply it.** *"Ana invited sam@acme.com to Acme Revenue as a member on 2 August"* is **workspace-scoped tenant data** — it needs `workspace_id`, RLS and an audit trail — and §6 recommended putting it where none of those reach. **The recommendation contradicted its own reasoning one paragraph earlier.**

**The product owner's finer split is the correct one, and the evidence supports going further than it proposes.**

An invitation is **two facts with two owners**, and separating them dissolves most of the dependency:

| The fact | Owner | Why |
|---|---|---|
| *"This address belongs to the person holding it"* | **Better Auth** | Authentication, and **it already does this** |
| *"Ana invited this address into this workspace, as a member, on this date"* | **Signora** | Workspace-scoped business intent, RLS-enforced, audit-relevant, and **the row that supplies the address [C-203](../LANE_COORDINATION.md)'s narrowing needs** |

### And the proof of ownership already arrives, in the token

**Measured, not assumed:**

| | |
|---|---|
| `frontend/lib/auth/jwt.ts` | Every access token carries **`email`** and **`email_verified`** |
| `backend/signora_platform/auth/jwt_verifier.py:36-37` | Both are **required claims**, and `email_verified` is type-checked as a boolean |
| `frontend/lib/auth/server.ts:58` | **`requireEmailVerification: true`** — a password account cannot sign in unverified, and an OAuth provider asserts it |

> **So the Python tier already knows, on every request, a verified email address that the caller has proved they own.** Accepting an invitation is *matching a pending row against a claim the token already carries* — **no plugin, no invitation token, no expiry logic in a link, and no cross-tier call.**

**Signora writes none of the security-sensitive parts, which was the whole reason to reach for the vendor** — and it reaches for the part of the vendor it is already using rather than enabling a new one.

**What this leaves of [C-206](../LANE_COORDINATION.md): who sends one email.** The Python tier has no transport; `lib/auth/email.ts` has one, with a two-value `purpose` union and a comment saying it is a port *"without anticipating"* a third. **That is a narrowing from *"which system owns invitations"* to *"which tier delivers a message, and is that M14a's"*.**

### Challenge 2 · Is Membership the correct business aggregate? — **Yes, and Invitation is a third one**

`Membership` is *"this person belongs to this workspace with this role"*. Its lifecycle — created, role changed, ended — is its own, and nothing outside it is transactionally consistent with it. **The existing split is right and the code's own reasoning for it still holds.**

**Invitation is not part of Membership**, and the test is that it exists when no membership does. Its lifecycle is `pending → accepted | revoked | expired`, and **acceptance is where one aggregate creates another** — which is exactly the shape the last decision needs to be explicit about.

### Challenge 3 · Is Workspace the aggregate root? — **For the membership *set*, yes. For a membership, no.**

**The question is decided by the invariant, not by the entity.** D4's rule — *the last owner cannot leave* — spans **every membership in a workspace**. An invariant over a set means the consistency boundary is the set's owner.

| | |
|---|---|
| **Workspace** is the root for **anything that changes the shape of the membership set** — ending, transferring, the last-owner refusal |
| **Membership** is its own aggregate for **its own facts** — its role, when it began, when it ended |

**This does not mean loading every membership to change one**, which is what the code deliberately avoids. **The invariant needs a count, not a collection**, and a count is one query inside the same transaction.

**"Person within a workspace" is not an aggregate and should never become one.** It is a *projection* over a Signora membership and a Better Auth identity, and making it an aggregate would put user identity in the Python tier — the thing §13 exists to prevent.

**What this settles for later:** audit, timeline, notifications, mentions, assignments and billing seats all cite a **membership** — a durable, workspace-scoped, immutably-ended record. **None of them needs a person aggregate**, and each keeps working after somebody leaves precisely because D3 keeps the row.

### Challenge 4 · Is *"self-operation is not authorization"* always true? — **No. There is a counterexample, and it sharpens the rule**

**Stress-tested against every self-operation Signora will plausibly have:**

| Operation | Self? | Where it belongs |
|---|---|---|
| **Leave a workspace** | ✅ | Membership + the last-owner invariant. **Not Casbin** |
| **Password · MFA · avatar · email · delete account** | ✅ | **Better Auth's, entirely.** These never reach the Python tier |
| **Notification preferences** *(M14a)* | ✅ | Self, per workspace. **Not Casbin** |
| **API tokens** | ✅ | Self. **Not Casbin** |
| **Disconnect "my" connected system** | ❌ **The counterexample** | **It is not yours.** A connected system belongs to the *organization* — `integration:update` is owner-only, and the person who connected HubSpot is not thereby entitled to disconnect it. **Casbin, correctly** |

> **The refinement the counterexample forces:** a self-operation is one whose **only subject and only object are the caller**. Connecting a system fails the second half — the object is the workspace's. Leaving passes both: the object is your own membership.
>
> **Stated as a rule:** *an operation requires no policy tuple only when the thing it changes would cease to exist if the caller did.* A membership would. A CRM connection would not.

**With that boundary the principle survives every case tested**, and it is worth generalising: it removes a Casbin entry from four future features and prevents the *"my"* mistake — treating something a person created as something they own.

### Challenge 5 · Does existing capability already solve part of this? — **Yes, three things, and one of them is the whole invitation flow**

| | |
|---|---|
| **Email verification** | **Solves invitation acceptance outright**, via a claim already on every token |
| **`useWorkspaceMembers` · `queryKeys.members` · `Membership`** | Shipped, uncalled, and exactly the list this needs |
| **`lib/auth/email.ts`** | A delivery port with a transport and an event, needing **one more `purpose` value** rather than a new mechanism |

### Challenge 6 · Anything to reuse rather than extend? — **`policy.csv`'s `member:remove`, which already exists and is unhonoured**

**The grant is there and reviewed.** Removal needs **no policy change at all** — only the endpoint, use case and domain method the grant already assumes. **The authorization half of TM-02 is done and has been since M1.**

### Challenge 7 · Is there a simpler design? — **Yes, and it is the one this section arrived at**

**§6 recommended enabling a vendor plugin: a new dependency, a new schema, a two-tier acceptance path, and an ADR amendment.**

**What the evidence supports instead:** one Signora-owned table, one new `purpose` on an existing port, and an acceptance rule that reads a claim already required on every request. **No new dependency. No frozen-file change. No plugin.**

> **The simpler design was reachable in §6 and was missed because the vendor was the obvious answer to *"do not build authentication"*.** It is still not built here — **email ownership is proved by Better Auth**, exactly as the rule requires. What changed is noticing that the proof already arrives.

---

## 12 · The invitation lifecycle, completely — before any code

**Documented first on the product owner's direction.** The exercise paid twice: it collapsed a long list of scenarios into **four states**, and it found the one thing that stops half the slice.

### There are four states, and only one of them is stored as a state

| State | How it is known |
|---|---|
| **`pending`** | **Derived** — none of the three below |
| **`accepted`** | `accepted_at` is set |
| **`revoked`** | `revoked_at` is set |
| **`expired`** | **Derived** — `expires_at < now()` |

> **Expiry is computed, never flipped by a job.** A stored `expired` flag needs something to write it, and until that thing runs the row is wrong — the same reasoning that makes `evidence_state` derived and `release` derived from evaluations. **`expires_at` is the fact; `expired` is the reading.**

**All three terminal states are permanent.** An expired invitation is not revived by extending a date; a new intent is a new row.

### Every scenario, resolved against those four

**Most of the product owner's list are not states — they are *events arriving at a state*, which is why the table is long and the state machine is short.**

| Scenario | Resolution |
|---|---|
| **Sent twice** | **Refused.** One `pending` invitation per `(workspace, email)`, enforced by a **partial unique index** `WHERE accepted_at IS NULL AND revoked_at IS NULL`. Two live invitations to one address is two ways in (D2) |
| **Resent** | **The same row, delivered again.** Not a new invitation — that is what the partial index makes structurally true rather than merely intended |
| **Sent again after expiry or revocation** | **A new row**, and correct: the old one records that somebody was invited and did not come |
| **Already accepted** | Refused, and the wording is *"you are already in this organization"* — not an error, a fact |
| **Accepted while already a member** | **Not an error either.** The customer's intent — *be in this workspace* — is already satisfied. The invitation is marked accepted, **the membership is untouched**, and its `created_at` stays the original |
| **Accepted after the role on the invitation changed** | **The row is the truth at acceptance.** An administrator who edits a pending invitation is changing what they are offering, and the offer is what gets accepted |
| **Accepted after revocation** | **Refused.** State is checked at acceptance, never at delivery — so an email opened before a revocation still cannot be used after it |
| **Revoked after the email was opened** | **Revocation wins**, by the same rule. There is no window |
| **Accepted after expiry** | Refused, with *"ask for a new invitation"* — the one message here that needs to offer a next step |
| **Accepted after the inviter left** | **Succeeds.** See below — it is the most interesting one |
| **Accepted after ownership transfer** | **Succeeds.** An invitation is the organization's intent, not the inviter's personal act |
| **Accepted after the workspace is deleted** | The row is gone with it — `ON DELETE CASCADE`, the same as `membership`. Acceptance finds nothing and says so |
| **Accepted after the workspace is archived** | **No archive concept exists.** Recorded so the next lane does not assume one |
| **Replay** | **Structurally impossible.** There is no token to replay — acceptance matches on the verified email claim, and the state check makes a repeat a no-op |
| **Multiple invitations, different workspaces** | Orthogonal. Each is its own row |
| **One verified email accepting several** | Each accepted separately. **Already supported** — `list_user_workspaces` and the workspace selector exist |

### Who owns an invitation after the inviter leaves — **nobody, and that is the point**

**The product owner's question, and the repository already answers it.**

> **`invited_by` is an immutable historical fact, exactly like `decided_by` on a workflow state.** It records *who did this*, and **it never transfers.**

| | |
|---|---|
| **Does acceptance still succeed?** | **Yes.** The organization invited this person; a departure does not withdraw that. **Withdrawal is an act, and it has a column** |
| **Should attribution move?** | **Never.** A record of the past that is rewritten to match the present is the failure `CLAUDE.md` §2 names in the same breath as documentation drift |
| **Does audit change?** | **No — and this is why D3 keeps ended memberships.** *"Ana invited Sam"* stays readable after Ana leaves, because Ana's membership row still exists |
| **Should ownership transfer?** | **There is no ownership to transfer.** An invitation belongs to the workspace. The inviter is provenance, not an owner — the same distinction as `Opportunity.owner_id` versus `decided_by` |

**A pending invitation from somebody who has left is therefore valid and slightly odd to look at**, which the design handles the way it handles everything else: it says so. *"Invited by Ana, who has since left"* is more useful than silently reattributing it to whoever is administering today.

---

## 13 · The invariants, and which aggregate each one names

**On the product owner's direction, and because *"the invariant determines the aggregate"* is only useful if the invariants are written down.**

| Invariant | Spans | Aggregate |
|---|---|---|
| **A workspace always has at least one owner** | **Every membership in the workspace** | **Workspace** |
| **One live membership per `(workspace, user)`** | Two memberships | **Workspace** |
| **One pending invitation per `(workspace, email)`** | Two invitations | **Workspace** |
| **A membership's role is one of the declared roles** | One membership | **Membership** |
| **An ended membership is never re-opened** | One membership | **Membership** |
| **An invitation reaches exactly one terminal state** | One invitation | **Invitation** |
| **Acceptance creates a membership** | **Invitation and Membership together** | **Workspace** — it is the only thing that sees both |
| **Permissions** | Nothing. **Casbin evaluates a role, and roles are values** | *No aggregate* |
| **Audit · Timeline · Notifications** | Nothing — they **cite** a membership and constrain nothing | *No aggregate* |
| **Billing seats** *(M14b)* | **Every live membership in the workspace** | **Workspace** — and it lands where the count already lives |

> **Three invariants span a set, and all three name Workspace. Three constrain one row each, and name their own entity.** That is the whole aggregate map, and it explains the existing code's split rather than overturning it.
>
> **The useful prediction:** billing seats will need exactly the count the last-owner rule already needs. **A capability two milestones away lands on machinery this slice builds** — which is what an aggregate boundary is for.

---

## 14 · What stops acceptance, and it is not a decision — it is RLS

**Found while planning the endpoint, and it splits TM-03 in two.**

**Inviting, listing and revoking are ordinary workspace-scoped operations.** They need **no new authorization at all**: inviting *is* `member:add`, revoking *is* `member:remove`, listing *is* `member:read` — **three grants that already exist in `policy.csv`**, because an invitation is a deferred membership and the policy already describes it. **No new `Resource`, no new `Action`, no frozen-platform change.**

**Acceptance is different, and the reason is structural:**

| | |
|---|---|
| **The accepter is not a member yet** | `CurrentWorkspace` verifies membership before any handler runs. **It will refuse them — correctly** |
| **The invitation row is workspace-owned** | Every RLS policy in this repository is `workspace_id = current_setting('app.workspace_id')`, and [`session.py:32`](../../backend/signora_platform/db/session.py) sets exactly one variable. **There is no user-scoped session setting** |

> **So a person cannot read the invitation addressed to them**, because reading it requires a workspace context that membership grants and they do not have. **The row is theirs to act on and invisible to them.**

**This is not [C-207](../LANE_COORDINATION.md).** That is about *authorizing* an action on yourself. This is about **tenant-scoped data whose legitimate reader is, by definition, outside the tenant** — a new shape, and the first time the tenancy model has met it.

**Raised as [C-208](../LANE_COORDINATION.md)**, and **it blocks only acceptance.** The invitation aggregate, its lifecycle, persistence, the partial index, inviting, listing and revoking are all buildable now — which is how the slice is being taken.

---

## 15 · Seven challenges before TM-03a

### D7 · Events before states — a principle worth keeping

> **A new customer scenario is an *event against an existing state* until proven otherwise. Only add a lifecycle state when no existing one can absorb the event.**

**Sixteen scenarios in §12 produced zero new states.** The pressure to add them is real and comes from the wording — *"invitation revoked after email opened"* sounds like a state, and it is `revoked` plus a fact about when somebody read something.

**The test:** does the scenario change what is *true of the record*, or only what *happened to it*? The first is a state; the second is an event. **Notifications, billing, approvals, playbooks and feature flags will each meet this**, and each will be tempted by a `SENT_BUT_NOT_YET_SEEN`.

### Challenge A · Tokenless acceptance, stress-tested — **it is stronger on security and weaker on flexibility, and that is the right trade**

| Scenario | Tokenless | With a token |
|---|---|---|
| **Email forwarded to somebody else** | **Refused.** Their verified address does not match | **Accepted.** Whoever holds the link gets in |
| **Shared mailbox** (`sales@acme.com`) | Works — whoever controls the mailbox controls the address. **A Better Auth property, not an invitation one** | Same |
| **Alias** (`sam+signora@` vs `sam@`) | ❌ **Refused, and this is the real cost** | Accepted |
| **Address changed between invite and accept** | ❌ Refused — same cost | Accepted |
| **Multiple browser sessions** | No effect. The claim is on the token, not the session | Same |
| **Account linking · SSO takeover** | No effect **unless the primary email changes**, which is the same case as above | Same |
| **Multiple verified identities** *(Better Auth has one `email` today)* | ⚠️ **The one that would force a change** — an invitation to a secondary address would not match. The fix is small: match against a list if the claim ever carries one | Unaffected |

> **The security direction is the decisive one.** *"An invitation link that works for whoever holds it"* is **a credential sitting in an inbox**, and email is forwarded, archived, and synced to devices nobody remembers owning. **Tokenless makes forwarding fail closed.**
>
> **And the costs are asymmetric in recoverability.** An alias mismatch is fixed by an administrator re-inviting the right address — **annoying and reversible.** The wrong person accepting a forwarded link is **already inside**, and no correction undoes what they saw.

**The design holds, and the failure must be legible:** *"This invitation was sent to `sam@acme.com`. You are signed in as `sam+signora@acme.com`."* — the address is shown, so the refusal is a fact rather than a mystery.

### Challenge B · Is `revoke` really `member:remove`? — **Sufficient, not fundamental**

**They are semantically different and today's mapping hides it:**

| | |
|---|---|
| **`member:remove`** | **Ends a relationship.** Takes access from somebody who has it, and interrupts their work |
| **Revoking an invitation** | **Withdraws an offer.** Nobody has access; nothing is interrupted |

**The blast radius is not comparable**, and the same is true one step earlier: `member:add` *creates* a relationship, while inviting *proposes* one. **Today they coincide because there is exactly one way in and one way out.**

> **Recorded as sufficient with its trigger stated: the first role that may invite but not remove.** A sales manager who can bring an SDR onto the team but not remove a colleague is an ordinary enterprise need, and on that day the two split. **Not before** — a permission introduced for a role that does not exist is speculative (§6).

### Challenge C · Editable, or revoke-and-create? — **Immutable, and the index already enforces it**

**Changing the role on a pending invitation, three ways:**

| | Audit | Customer understanding |
|---|---|---|
| **Edit in place** | ❌ The offer originally made is **gone.** The row shows only its final shape | ❌ The email said *member*; acceptance grants *owner*. **The product told them one thing and did another** |
| **Revoke and create** | ✅ *"Invited as member · withdrawn · invited as owner"* — the whole story | ✅ A new offer, and a new email that matches it |

**Revoke-and-create, and it is the repository's existing discipline**: every declaration in Commercial Profile is versioned and immutable, a change is a new version, and *"an editable record of the past is a record nobody can cite"* (§2).

**The partial unique index makes it the only available path** — a second pending invitation cannot exist until the first is revoked. **The constraint and the principle are the same mechanism**, which is what §2 means by a violation being unrepresentable rather than discouraged.

**Resend stays the same row**, and is consistent: **it changes nothing about the offer.** Extending an expiry *does* change the offer, so it is also revoke-and-create.

### Challenge D · C-208 stress-tested — **it survives, and it is smaller than it looked**

**Nine scenarios, all against the single-tenant rule:**

| | |
|---|---|
| **From another logged-in workspace** · **after switching organizations** | The path names workspace B; the session's `active_workspace_id` says A. **§13 already rules: the claim is a routing hint, never a grant.** Context is set from the path. **One tenant** |
| **Logged out** | Sign in, return. Unchanged |
| **Logged into a different account** | Refused — verified email does not match. **Message names the invited address and offers to sign out** |
| **Expired · revoked · workspace deleted** | Checked inside the workspace context, like every other read |
| **Organization renamed** | A name is not an identity; the path carries the id |
| **Inviter removed** | Succeeds — §12 |

> **All nine hold, and none reads outside a tenant.**

**And it needs no platform change, which is smaller than [C-208](../LANE_COORDINATION.md) itself claimed.** `set_workspace_context` is already a public function in [`signora_platform/db/session.py`](../../backend/signora_platform/db/session.py):69. **The acceptance endpoint needs a dependency that verifies the token and sets context from the path without requiring membership** — that is a new dependency **in this module's interface layer, composed from platform functions that already exist.** Using the platform, not changing it.

**What remains for the product owner is one sentence:** *may a request establish workspace context from a path parameter when the caller is not yet a member?* **Everything else follows.**

### Challenge E · A sender that is not a person — **the pressure point is not here**

**`invited_by` is a user id, and SCIM, imports and automation have none.** But the Phase 2 stress test already found the answer: **SCIM does not invite. It provisions memberships directly**, bypassing invitations entirely — so the pressure lands on **Membership not requiring an invitation id**, which §4 already recorded.

**Bulk invite and CSV import are still human acts** through a different door; `invited_by` stays a person.

**The genuine gap is an admin API or automation that invites**, and the repository has already solved that shape **twice**: `Opportunity.opened_by` is `automatic | manual`, and `WorkflowState.decided_by is None` means *Signora authored it*. **An actor is a person or the system, and the schema says which.** Today's design should follow that pattern rather than invent a third — **noted, not built.**

### Challenge F · Is *"pending relationship"* the better aggregate? — **No, and the test is nullability**

**Tested against every example given:**

| | |
|---|---|
| **Pending membership** *(invitation)* | Counterparty is **not yet a user.** Needs an address, delivery, verification, expiry |
| **Pending ownership transfer** | Counterparty **already is a member.** Needs no address, no delivery, no verification |
| **Pending role change** | **Does not exist.** A role change is immediate |
| **Pending billing seat** | **Not a relationship** — a quantity |
| **Pending feature enablement** | **Not a relationship** — a flag |
| **Pending org merge · external collaboration** | **Do not exist**, in the roadmap or anywhere else |

**Two of seven are genuinely pending relationships, and they differ in the load-bearing way:** one counterparty is a stranger and one is a colleague. **That single difference drives the address, the delivery, the verification and the expiry** — everything the aggregate is made of.

> **A generalized aggregate would carry a nullable email, a nullable target user, a nullable role and a nullable expiry — and a nullable column is a state the type cannot refuse.** That is directly against *types should make incorrect architecture impossible* (§2), and it would buy reuse of a table at the cost of every invariant the type currently enforces.

**Invitation stays, and the trigger for revisiting is stated: a third pending relationship with the same shape** — email-addressed, expiring, delivered. **Two is a coincidence; three is a pattern.**


---

## 16 · TM-03a — as built, 2026-08-02

**An organization can grow.** Until this shipped, every workspace was permanently whoever created it.

| | |
|---|---|
| **Customer capability** | An administrator invites a colleague by email, sees every invitation in every state, and withdraws one. Reached from **Settings → Your team** |
| **Migration** | `0031` — `invitation`, RLS enabled and forced, registered in `tenancy_policy.py`, **reversible** (verified down and up) |
| **The partial index** | `uq_invitation_live_email` on `(workspace_id, invited_email) WHERE accepted_at IS NULL AND revoked_at IS NULL`. **The design, not an optimisation** — it makes *resend is the same row* and *a change is revoke-and-create* unrepresentable to violate |
| **Authorization** | **No policy line added.** `member:add` · `member:read` · `member:remove` already described these operations, because an invitation is a deferred membership (§14) |
| **Delivery** | A port with a console adapter, mirroring `lib/auth/email.ts`. **It cannot fail the invitation** — an offer recorded and undelivered is recoverable by resending; one refused because a mail server blinked makes a customer repeat themselves |
| **Tests** | **+26 domain, +15 component.** Backend 2594, frontend 717 |

### What was reused rather than built

| | |
|---|---|
| `policy.csv`'s three grants | **Unchanged.** The authorization for this capability has existed since M1 |
| The `workspace_role` enum, migration `0001` | The invitation's role column is the same type — `create_type=False` |
| `membership`'s `ON DELETE CASCADE` shape | Copied exactly, for the same reason |
| `SqlAlchemyRepository`, `CurrentWorkspace`, `build_use_cases`, the error envelope | Untouched |
| `Table` · `Dialog` · `Badge` · `EmptyState` · `Select` · `Input` · `Button` · `SkeletonText` · `useToast` | **Nothing new in `components/ui`** |
| CX-01's Settings card pattern | A third card, identical in shape |
| `tests/components/settings-index.test.tsx` | **Caught the new route automatically** — the census asserts every `/settings/*` has a link, and it went from 6 tests to 7 without being edited |

### Two things deliberately absent from the screen

| | |
|---|---|
| **The list of people** | `GET /members` carries no address. Rendering UUIDs would be a table of identifiers pretending to be a team, so **the section is absent rather than wrong.** It arrives when memberships created by acceptance carry the address the organization typed |
| **Accepting** | [C-208](../LANE_COORDINATION.md). Every administrator operation here is workspace-scoped and needed none of it |

### Found while building, and not worked around

**`sa.Enum(..., create_type=False)` is ignored inside `create_table`.** Alembic re-issues `CREATE TYPE` and the migration fails against an existing enum; only the dialect's `postgresql.ENUM` honours the flag. **Fixed in the migration with the reason in a comment**, because the next module to reference `workspace_role` will meet it.


---

## 17 · TM-02 — a membership ends, 2026-08-02

**`policy.csv` has granted owners `member:remove` since M1 and nothing could perform it.** This is the operation that grant assumed.

### The customer's action, not the technical one

**Somebody leaving the company, a contractor's engagement ending, an invitation sent to the wrong address, access withdrawn after an incident** — every one is *this person no longer belongs here*, and none of them is *delete a row*. The endpoint is `POST …/remove`, the response returns the **ended** membership rather than `204`, and the reason is free text kept verbatim.

**A reason is optional.** An administrator correcting a mistaken invitation should not be made to justify it.

### The four verifications, on migration `0032`

| | |
|---|---|
| **Data preservation** | **Additive only** — three nullable columns. The dropped unique constraint is replaced by a partial index that is strictly weaker, so nothing valid became invalid |
| **Behaviour preservation** | Every existing membership has `ended_at IS NULL` and is live under every new predicate. **Membership verification, the roster and RLS behave exactly as before** |
| **Capability expansion** | An owner can end a membership, and the record says who, when and why |
| **Rollback safety** | **Verified down and up while clean.** Once a membership has ended the downgrade **refuses, loudly** — restoring the total constraint would refuse a legitimate re-join, and the only way to force it is to delete audit history. *A migration that silently dropped audit rows to satisfy a constraint would be worse than one that refuses.* **Confirmed by ending a membership and watching it raise** |

### The audit questions it already answers

**Nothing was built for reporting; the facts are simply kept.**

| | |
|---|---|
| *Who invited this person?* | `invitation.created_by` — and it never moves |
| *Who removed them?* | `membership.ended_by` |
| *Why?* | `membership.ended_reason`, verbatim |
| *When?* | `membership.ended_at` |
| *Were they ever re-added? How many times?* | **The partial index makes this answerable**: one live membership per person, and every ended one survives — so the count is the number of rows |

### The pressure point future offboarding will meet, documented not built

**Ending a membership today touches nothing else, and that is correct** — no notifications, assignments, approvals or billing seats exist to cascade to. **When they do, each will want to react to a departure**, and there is no `membership.ended` event on the bus.

**Not published now**, because an event with no consumer is speculative (§6) and [C-012](../LANE_COORDINATION.md) means no module handler is subscribed anyway. **The pressure point is named so the next lane adds one deliberately** rather than discovering the need at slice four.

### A defect in TM-03a, found by reading its own copy

**The forgotten-invitation banner said *"You can send it again, or withdraw it below"* and there was no *Send again* control.** A control that goes nowhere costs more trust than an absent one — and here the product described an action it could not perform.

**Fixed in this slice**: `ResendInvitation` re-delivers **the same row**, and *Send again* sits before *Withdraw* because an administrator chasing a forgotten invitation reaches for the recoverable action first.

**`require_pending` became public** so resend could reuse the domain's own refusal rather than re-express it — a use case reaching into a private method would be the boundary leaking rather than the rule being shared.


---

## 18 · TM-01 — the roster, 2026-08-03

**The Team page names people.** Removal and the invitation lifecycle stop being headless capabilities and become things a customer can see and do.

### How the roster became possible without waiting for acceptance

**§9 concluded the members list had to follow TM-03b, because no membership carried an address.** That was true of memberships created by `POST /members`. **It was not true of the founder's.**

`create_workspace` runs under a verified token, and **`AuthenticatedPrincipal.email` has carried the address since M1.2.** So the one person who is certainly in every organization can be named today, and everybody after them gets theirs from the invitation they accepted.

> **The correction to §9's correction:** the narrowing was right, the sequencing was wrong, **and the sequencing was wrong in a second way** — the address has two sources, and only one of them waits on C-208.

**Nullable, and no backfill.** Memberships added by identifier have none, and inventing one is what migration `0029` refused. They render as *"Somebody here"* — D23's wording, which the product has used for exactly this since M12.2.

**Why this stays inside §13:** the address is **a fact about how the membership came to exist**, not a mirror of a profile. A display name is Better Auth's and goes stale; *the address this membership was created with* is historical and stays true.

### The UX questions, answered

| | |
|---|---|
| **What an owner understands first** | **How many people, and how many can administer Signora** — before any row. The second is what makes the last-owner refusal comprehensible *before* somebody meets it |
| **Table or cards** | **Table, and it is not a default.** Today a row is address · role · one action, and a card would be a table with more whitespace. **The trigger to revisit is stated**: the first row-level fact that is not a single value — an avatar, a last-active reading, a badge set. **Responsive is [C-205](../LANE_COORDINATION.md)'s**, and cards are what that answer will probably want |
| **Row actions** | **One today, and the shape is chosen for six.** *Change role · Remove · Transfer ownership · Suspend · Audit · Activity* do not fit as six buttons; the trigger for a per-row menu is **the third action**, and the column exists to receive it |
| **Pending invitations** | **A separate card, as §10 argued.** *Who is here* and *who is on their way in* are different questions, and a `Status: pending` column would invite sorting a person next to a not-yet-person |
| **Where removal is offered** | **Absent, never disabled — for two different reasons.** A member is not shown a control the server would refuse; **nobody is shown one on their own row**, because leaving is a different operation with a different invariant ([C-207](../LANE_COORDINATION.md)) |
| **The confirmation** | **Names the person and the consequence**, and adds the reassurance only this design can make: *"What they have already decided stays on the record."* That is D3 being true, said out loud |

### Enterprise growth — what today's layout does not block

**Nothing here is built.** The question is only whether the shape refuses it.

| | |
|---|---|
| **Hundreds of users · search · filters · sorting** | The endpoint is already **cursor-paginated**; the screen reads one page. **The trigger is a list that does not fit on one screen** |
| **Bulk actions** | A selection column and a toolbar. **The domain methods are per-member either way** |
| **Departments · teams · cost centres · grouping** | **Multiple workspaces already**, and a grouped roster is a rendering change |
| **SCIM users · guests · external collaborators** | A membership with a different provenance. **`member_email` is nullable and `created_by` already distinguishes who acted** |
| **Seats · licences** | **Lands on the owner count this page already computes** — the prediction §13 made, arriving one slice later than expected |

### Future events — recorded so nobody rediscovers them

**None is implemented.** [C-012](../LANE_COORDINATION.md) means no module handler is subscribed anyway, and an event with no consumer is speculative (§6).

| Event | Why it will exist | Producer | Expected consumers | Why not today |
|---|---|---|---|---|
| `membership.ended` | A departure must reach everything that names a person | Workspace & Tenancy | Notifications · assignments · approvals · billing seats · integrations | **None of those exists.** Nothing would receive it |
| `membership.role_changed` | An entitlement change must reach anything caching a capability | Workspace & Tenancy | Billing · notifications · audit | TM-04 is unbuilt, and nothing caches a role |
| `invitation.accepted` | The moment an organization grows | Workspace & Tenancy | Onboarding · notifications · seat counting | Acceptance is [C-208](../LANE_COORDINATION.md) |
| `workspace.owner_transferred` | Ownership is the highest-consequence change a workspace has | Workspace & Tenancy | Audit · notifications · billing contact | Transfer is unbuilt |

**`workspace.created` and `workspace.member_added` already exist** in [06-events.md](06-events.md) and are published today — so the catalog entry for any of the above is an extension of a pattern rather than a new one.

### If Signora ever builds a People Profile — one pressure point, and it is small

**The question: does a membership-centric design make a person-centric one impossible?**

**No, and the reason is that this module never claims to own a person.** `user_id` is Better Auth's identifier, unmodified; `member_email` is a fact about an act rather than a profile field; **nothing here would become a second home for identity.**

> **A People Profile would sit beside this module, not above it.** A person's memberships, notifications, approvals, sessions and connected identities are five different modules' facts about one Better Auth identity — and joining them is a *projection*, exactly as §11 concluded when it refused "person within a workspace" as an aggregate.

**The one pressure point.** `member_email` would then exist in two places: here, as *the address this membership was created with*, and in a profile, as *this person's current address*. **They can legitimately differ** — somebody changes their address after joining — and a future engineer will read that as duplicated truth.

**It is not.** One is historical and one is current, which is the same relationship `ai_narration` has to today's evidence. **Recorded so the difference is found in this document rather than reasoned out from scratch**, and the fix if it ever confuses anybody is a rename — `joined_as_email` — not a schema change.


---

## 19 · TM-04 — role management, 2026-08-03

**Organizational authority, not a field.** Promoting a colleague hands them the ability to invite, remove and administer; demoting one takes it away while they may be mid-task.

### The questions, answered

| | |
|---|---|
| **May an owner demote themselves?** | **Yes, when another owner exists.** Refusing it would mean an administrator handing over could not then step back, and the last-owner rule already protects what matters. **The dialog says *"That includes you — you will not be able to undo this yourself"***, because it is the one irreversible-by-you action on the page |
| **Can two tabs race it?** | **They could, and it is fixed here.** See below |
| **Can ownership disappear?** | **No.** Demoting the last owner is refused by the *same* invariant that refuses removing them — two ways to one failure, refused in one place |
| **May every administrator promote another owner?** | **Yes.** Two roles, and `member:add` already grants it |
| **Confirmation?** | **Yes, and it explains rather than asks.** A gain then a loss, and the loss sentence appears only when true |
| **Audit history?** | **Yes — the table below** |
| **Timeline · notifications?** | **No.** Timeline projects account activity; a role change is organizational, and putting it there would make the account feed a place two unrelated stories are told. Notifications are M14a's, and the event is deferred (§18) |
| **Sessions invalidated?** | **Not needed.** The role is re-read from `membership` on every request, so a change takes effect on the next one — **no token carries a role**, which is why [ADR-0026](adr/0026-jwt-boundary-architecture.md)'s claim set deliberately carries no permissions |
| **Somebody editing while their permissions change?** | **The write is refused by Casbin and the screen says so.** The client cache is invalidated by the mutation, so the person who *performed* the change sees it immediately; a **concurrent** demotion leaves stale controls for up to five minutes, which fail loudly rather than silently |

### The race, and the fix reaches TM-02 as well

**Counting is not enough.** Two owners demoted concurrently each read *two owners*, each compute *one remaining*, and both succeed — leaving an organization nobody can administer. **Neither transaction did anything wrong; the check simply is not atomic across them.**

> **`SELECT workspace.id … FOR UPDATE` before the count.** Locking the **workspace** row is [§13](#13--the-invariants-and-which-aggregate-each-one-names) made executable: *Workspace is the aggregate root for anything that changes the shape of the membership set*, and this is what that means at runtime. It serialises only those operations, and only per workspace.

**TM-02 had the same race and now takes the same lock.** Found by asking the product owner's question — *"should two browser tabs race ownership changes?"* — against code that was already merged.

### The history is a record, not an event

**`membership_role_change` is append-only**, and it exists because a role change *overwrites* `membership.role`: without it, *"who made Ravi an owner, and when?"* is unanswerable by anything, including replay. **§2 — a system cannot be improved using information it never recorded, and the record cannot be added retroactively.**

**The distinction from §18's deferred events, stated because they look alike:** an event with no consumer is speculative; **a fact that becomes unrecoverable if unwritten is the opposite case.** One is deferred, the other is built, and the test is whether waiting destroys anything.

### What the Security Invariants caught

**Two registrations, and the suite refused both.** The table went into `TENANT_OWNED_TABLES` and the policy check demanded an `UPDATE` policy it must not have; registered as immutable, the check then demanded a `DELETE` **grant**.

**The second refusal was the interesting one.** Every immutable table in the repository grants `DELETE`, and the reason is a distinction worth keeping: **immutability is about *editing*, not about permanence.** Erasability is a property of the tenancy model, so deleting a workspace must be able to delete its history. **The invariant knew the convention better than I did**, and the fix was to match it rather than to argue with it.

### Beyond Day One — where the pressure begins

| | Absorbed? |
|---|---|
| **Custom roles · department administrators · temporary administrators · delegated administration** | ✅ **A role is a Casbin subject.** Adding one is a `policy.csv` line and a `WorkspaceRole` value; the history table already stores *from* and *to* as roles rather than as a boolean |
| **External consultants · guests** | ✅ A role with fewer grants, plus the time-bounded membership §4 already identified |
| **Multiple owners** | ✅ **Already true today** |
| **Suspended users** | ⚠️ Deferred with its trigger (D5). **A suspension is not a role**, and modelling it as one would make *"what can they do"* and *"can they sign in"* the same field |
| **SCIM · SSO · Azure AD · Okta · Google Workspace** | ⚠️ **Where the pressure begins, and it is not the role model.** A directory *asserts* roles, so `membership.role` becomes a **projection of an external system** rather than a fact Signora owns — and `membership_role_change` then records *"the directory said so"*, whose actor is not a person. **The `opened_by` pattern is the answer** (§11, Challenge E), and the pressure point is `created_by` being a user id, not the roles themselves |
| **Organization mergers** | ⚠️ **Genuinely unabsorbed**, and the honest answer: two workspaces merging means two membership sets, two role histories and two owners' claims over one organization. **Nothing here prevents it; nothing here anticipates it either.** It needs a design when somebody asks |

### The future Team experience, checked not built

**Profile cards · presence · activity summaries · workload · approvals · assignments · mentions · comments · ownership history · onboarding progress.**

**All of them attach to a membership or to a Better Auth identity, and both already exist.** The roster row is the natural anchor: it has a stable id, an address, a role and a lifecycle. **The one that would strain today's layout is presence** — a per-row live indicator implies subscriptions the frontend has no mechanism for, and it is the first of these that is not simply another column.


---

## 20 · TM-05 — roles explained as capabilities, 2026-08-03

**§5 called this the weakest part of the design, on the assumption it meant rendering thirty Casbin tuples. It did not.** Customers think in capabilities, and the difference between two roles is four sentences.

### One reviewed catalog

[`components/team/capabilities.ts`](../../frontend/components/team/capabilities.ts) — the only place these sentences exist. **Before it the same distinction was written three times** — the role selector's options, the roster's text, the invitation dialog — and three copies of one fact eventually disagree.

**Deliberately not generated from `policy.csv`.** The least-powerful-author rule: this is *static knowledge a domain expert owns*, like the timeline's headline catalog. **Generating it would climb a rung for no gain** — the output would drift into resource names the moment somebody added a resource, and nobody would notice until a customer read it.

> **The property that makes it worth having: adding `timeline:read` to `member` changes nothing here**, because *"see every account Signora is watching"* was already true and already said. **The explanation is stable while the policy evolves.**

### Where it appears, and where it deliberately does not

| | |
|---|---|
| **A closed disclosure on the Team page** | *"What each role can do."* **Closed by default** — an owner choosing between two roles is the one person who needs nine sentences, and a permanently expanded list is the clutter a matrix was avoided to prevent |
| **Inside the invitation dialog** | The role being offered, explained where the choice is made. **An administrator inviting somebody as an owner should not have to open a disclosure elsewhere** to learn what that grants |
| **To a member, as *who can*** | *"Only owners can invite colleagues, remove them, or change what they can do. Ask somebody who administers this organization."* **A fact they can act on** — they know who to ask. A screen that simply omits the control leaves them wondering whether the feature exists |
| **In onboarding** | **Not yet.** There is no onboarding flow to put it in ([C-007](../LANE_COORDINATION.md)), and inventing one to host a sentence would be building the wrong thing |
| **On a denied action** | **Not needed here, and the reason is the design.** No control the server would refuse is ever rendered — so there is no denial to explain, only an absence, and the absence is what the member-facing line addresses. **It becomes worth building the moment a control cannot be hidden**, which is the trigger |

**A test asserts no platform vocabulary reaches any of it** — `casbin`, `policy`, `permission`, `workspace:`, `member:`, `resource`, `tuple`, `forbidden`, `403`. Same terms `vocabulary.test.tsx` applies to every screen, applied to the one place a matrix would have leaked.

---

## 21 · Ownership transfer — challenged, and it is one operation

**The question: does a customer think in two operations or one?**

**One.** *"Hand over the organization"* is a single intent with a single reason — somebody is leaving, or changing role, or the wrong person set it up. **Nobody thinks *"promote Ravi, then demote myself"***; that is the mechanism, and today the product asks the customer to know it.

**And composing it from two operations is not merely inelegant — it is unsafe in a way one operation would not be.** Between the promote and the demote there are **two owners**, and if the second step fails, is abandoned, or the browser closes, the organization is left in a state nobody chose. **A transfer that half-happens is worse than one that is refused.**

> **So it deserves its own workflow**, and the evidence is the intermediate state rather than the click count.

**What it needs, and it is small:** one use case taking both memberships, inside the transaction and the workspace lock TM-04 already added — so the two role changes are atomic and the invariant is never momentarily satisfied by an owner nobody meant to create. **Two `membership_role_change` rows, which is correct**: two people's authority changed.

**Not built in this slice.** It is a genuine capability rather than polish, it is unblocked, and it is recorded here as the next one.

---

## 22 · TM-06 — audit history, designed before it is built

**Every fact it needs is already stored.** The challenge is presentation, and one question decides most of it.

### The single place a customer answers *"what happened?"*

| Source | Already stored |
|---|---|
| Invited · resent · withdrawn · expired | `invitation`, with `created_by` and all four states |
| Accepted | `invitation.accepted_at` *(pending [C-208](../LANE_COORDINATION.md))* |
| Role changed | `membership_role_change` — from, to, by, when |
| Removed | `membership.ended_at` · `ended_by` · `ended_reason` |
| Rejoined | A second live membership after an ended one |

**Chronology, newest first, one entry per fact.** Grouping by day, as the account timeline already does — **the same component shape, deliberately**: a customer who has read one history should not have to learn a second layout.

**Filtering and search are deferred with the trigger stated:** a history that does not fit on one screen. An organization of four generates perhaps twenty entries a year.

### The question that decides the design: **whose name, and from when?**

**A person renames themselves. Should an entry say the name they have now, or the one they had then?**

| | |
|---|---|
| **Current name** | Reads naturally, and **silently rewrites history**: *"Raj promoted Anita"* when the record says Ravi did, and the audit no longer matches an export taken last year |
| **Historical snapshot** | Truthful, and **confusing** — a reader who knows Raj cannot find Ravi |
| **Both** | *"Ravi (now Raj)"*. Truthful, findable, and slightly heavy |

**Signora's answer follows from what it already does.** `member_email` is *the address a membership was created with* — **already a historical snapshot**, chosen for exactly this reason. So the entry says what was true then, **and the roster says what is true now**, and the two are reconciled by the reader rather than by the product guessing.

> **The pressure point, recorded now because it reaches nine surfaces:** audit, timeline, comments, mentions, notifications, approvals, assignments, AI summaries and exports **will each face this question independently**, and they must answer it the same way. **The first one to answer it sets the convention** — and this document is the first, which is why the reasoning is here rather than in a component.

**Not built.** The reading is TM-06; the facts are kept, which is the half that cannot be added retroactively.

### Future pressure, checked

**Absorbed:** bulk invitations and role changes *(more entries, same shape)* · delegated administration *(a role)* · organization rename *(the workspace's name is not in an entry)* · temporary access · guests · consultants · read-only users *(all roles)* · workspace deletion *(cascades)*.

**Where pressure begins:** **SCIM and directory synchronisation** — the actor stops being a person, and the `opened_by` pattern is the answer (§11). **Legal holds and retention** — an append-only table with a `DELETE` grant is exactly the shape a hold has to override, and nothing today expresses one. **Organization merge or split** — two histories over one organization, and §19 already records it as genuinely unabsorbed.


---

## 23 · Ownership transfer, as built — 2026-08-03

**One operation, and the domain says so.** `transfer_ownership(outgoing, incoming, by, at)` mutates both memberships; the use case performs it inside one transaction under the workspace lock TM-04 added.

**The last-owner invariant is deliberately not consulted.** It protects against ending with nobody, and this ends with exactly one — **checking it mid-operation would refuse the very thing that satisfies it.**

**Two `membership_role_change` rows**, because two people's authority changed and an audit showing one would leave the other's unexplained.

### The scenarios, and where each one landed

| | |
|---|---|
| **Recipient removed while the dialog was open** | **Checked before anything is mutated.** Otherwise they are promoted and *then* found to have left |
| **Outgoing owner lost ownership first** *(concurrent demotion)* | Refused — the transaction finds a member, not an owner. **This is the race the lock exists for, seen from the losing side** |
| **Two tabs transferring simultaneously** | The lock serialises them; the second finds a member and is refused |
| **Racing organization deletion** | The workspace row is the lock target and the FK parent. **A deletion holding it blocks the transfer; a transfer holding it blocks the deletion** |
| **Audit write succeeds, role update fails** | **Impossible — one transaction.** Both roles and both rows commit together or not at all |
| **Handing over to yourself** | Refused |
| **Transactional notifications later** | **Absorbed**: they would be published from the same transaction via the outbox, which is what the outbox is for |
| **Transfer eventually requiring approval** | ⚠️ **Where pressure begins.** An approval makes this a *pending* operation, and §11 Challenge F already rejected a generic pending-relationship aggregate — **this would be the third instance that reopens it**, which is the stated trigger |

### A guard was written and removed

**`outgoing.workspace_id != incoming.workspace_id` could never fire.** Both memberships are fetched scoped to one workspace, and RLS scopes them again beneath that.

> **A guard that cannot fail is documentation pretending to be code** (§2). It was found by a test expecting `OwnershipTransferError` and getting `MembershipNotFoundError` — **the failing test was right and the code was wrong.** The test now asserts the protection that is real.

---

## 24 · Historical identity — one convention for the whole repository

**Recorded here because this module answered it first, and every collaborative feature after it must answer the same.**

> **Persistence stores immutable facts. Presentation resolves identity.**

| | |
|---|---|
| **An event stores** | `actor_id` · `membership_id` · the **email snapshot** as it was · the timestamp |
| **A screen decides** | current name · historical name · or both |

**Why the split, in the product owner's framing and this repository's terms:** a stored *rendering* is a stored copy of a derivable fact (§2), and it goes wrong the moment somebody renames themselves — **the audit stops matching an export taken last year.** A stored *snapshot with an id beside it* keeps both options open forever, because the id resolves and the snapshot does not move.

**Signora already does this**, which is why the convention is a recognition rather than a decision: `member_email` is *the address a membership was created with*, and `decided_by` is an id the screen renders as *"Somebody here"*.

**The convention, stated so nine surfaces can share it:**

1. **Store the id and the snapshot. Never store the rendering.**
2. **Default to the snapshot** — *what was true then* is the truthful answer for a historical entry.
3. **Resolve the id when a reader needs to act**, not merely to read. A mention must reach the person who exists now.
4. **Show both only where finding somebody matters** — *"Ravi (now Raj)"* in a search result, not in every audit line.

**It binds:** audit · timeline · comments · mentions · notifications · approvals · assignments · decision history · activity feeds · AI summaries · exports.

> **Team Management is not coupled to today's representation.** When User Profile introduces display names, **nothing here changes**: the snapshot stays the historical fact and the profile becomes a second resolver the *screen* may call. That is the whole point of keeping presentation and persistence apart, and it is why this convention is recorded before the other workstream needs it.

### Future pressure, checked once more

**Absorbed:** bulk ownership transfer *(a loop over one operation)* · delegated administration · department hierarchy · temporary access · guests · external collaborators · just-in-time provisioning *(a membership with a different creator)* · organization archival · workspace deletion.

**Where pressure begins:** **SCIM and directory sync** — the actor stops being a person, and the `opened_by` pattern answers it. **Emergency owner recovery** — every rule here assumes an owner is reachable; nothing expresses *"the only owner has left the company"*, and support intervention is currently the only path. **Legal hold and retention** — an append-only table with a `DELETE` grant is exactly what a hold must override. **Organization merge or split** — still genuinely unabsorbed, and now with a second reason: two role histories over one organization.


---

## 25 · TM-06 — *"what happened?"*, 2026-08-03

**A read model over three tables, and deliberately not a projection into a fourth.** The facts are already durable and already correct; a copy would be a second representation to keep in step (§2).

### The reuse question, answered by checking rather than assuming

**The account timeline groups by day, renders newest first, and translates a `kind` through a reviewed catalog — the same shape.** Reuse was the obvious move.

> **It is the wrong abstraction, and one difference decides it.** The account timeline answers *what happened to this account* and **names nobody**. This answers ***who did what to whom***, so an actor and a subject are **structural rather than fields inside `detail`.** Bending the feed to carry two people would make every account entry pay for a pair it never has.

**And extracting a shared framework now would be generalising from two instances** — the same *two is a coincidence* rule that refused a generic pending-relationship aggregate (§11). **The trigger is stated: a third history surface.**

### Every question, answered

| The question | The entry |
|---|---|
| *Who invited this person?* | *"ana@acme.com invited sam@acme.com as somebody who works accounts"* |
| *Who removed them, and why?* | *"ana@acme.com removed jo@acme.com — Left the company"* |
| *Who promoted them?* | *"ana@acme.com made jo@acme.com able to administer Signora"* |
| *What role before, what now?* | Both, in the sentence |
| *Who transferred ownership?* | **Two entries** — the promotion and the step back, at the same instant |
| *When?* | To the minute, grouped by day |

**Said as a move rather than a demotion.** *Demoted* is a judgement, and somebody handing over has not been demoted — asserted by a test.

**And it is honest about what it does not know.** An invitation withdrawn today records no actor, so the entry says *"Somebody withdrew…"* rather than attributing it to the inviter, **who may not be who withdrew it.** That is a gap worth closing when revocation gains an actor column; it is not one worth guessing about.

**Everybody in the organization can read it**, deliberately: *a history only administrators may read is a history that cannot be used to hold administrators accountable.*

### The identity convention, applied

**No rendered sentence crosses the wire.** The API sends `kind`, two `(id, snapshot)` pairs and the roles; **the words are a reviewed catalog at the frontend edge** — so improving one is a deploy rather than a migration, and an export can phrase the same entry differently.

**Actor addresses are resolved at read time** from the actor's own membership. **An actor whose membership has since ended still resolves**, because D3 kept the row — which is the first time that decision paid for itself somewhere other than where it was made.

---

## 26 · Emergency owner recovery — the pressure point, documented not built

**Every rule in this module assumes an owner is reachable.** The last-owner invariant guarantees one *exists*; nothing guarantees anybody can *use* it.

### What breaks

| | |
|---|---|
| **The founder leaves the company** | Their membership is live, their account is unreachable, and **nobody else can be made an owner** — only an owner can promote |
| **The sole owner's account is compromised** | The correct response is to remove them, and **only they can do it** |
| **The invariant is doing its job** | It refuses to leave an organization with nobody. **It cannot tell "nobody" from "somebody unreachable"**, and that distinction is the whole problem |

### The questions, with what today's design already implies

| | |
|---|---|
| **Who becomes responsible?** | **Nobody, today.** No support role, no platform administrator, no break-glass path exists — and `signora_app` deliberately cannot bypass RLS, so there is no back door either. **That is correct security and an unsolved product problem** |
| **Can support intervene?** | Only by database access under the migration identity, which is **exactly what the tenancy model exists to prevent.** If it becomes the answer it needs designing, not tolerating |
| **Do multiple owners prevent it?** | **Largely, and it is the only mitigation that exists today.** Ownership transfer (§23) makes a second owner cheap; **the product does not yet ask for one**, and an organization of one is the default |
| **Should enterprises configure recovery owners?** | A recovery owner is **a membership with a purpose**, which today's model absorbs — it needs no new aggregate |
| **Should SSO or SCIM influence it?** | **This is where it becomes tractable.** A directory that asserts who works at a company can assert that the founder no longer does — **which is the one authority outside the workspace that is not Signora's support desk** |
| **Should billing owners differ from workspace owners?** | **Almost certainly yes, eventually**, and it is a second recovery path: whoever pays has a claim nobody inside the workspace can revoke. **M14b's territory** ([C-200](../LANE_COORDINATION.md)) |

### What today's implementation does *not* make harder

**Nothing here needs undoing.** Recovery would be a new *authority* — a directory, a billing relationship, a support procedure — granting a membership. **The membership model, the audit trail and the transfer operation all absorb it**: recovery is an ownership transfer whose actor is not a member, and `membership_role_change.created_by` already records an actor rather than assuming a colleague.

**The one thing that would make it harder is a guard checking that an actor is a member of the workspace they are acting on** — which does not exist, and **should not be added without this in mind.**

---

## 27 · Module handover

**Everything remaining in Team Management is a ruling, not engineering.**

| Slice | State |
|---|---|
| TM-01 roster · TM-02 removal · TM-03a invitations · TM-04 roles · TM-05 capabilities · ownership transfer · TM-06 history | ✅ **Shipped** |
| **TM-03b acceptance** | 🔴 [C-208](../LANE_COORDINATION.md) — *may a request establish workspace context from a path parameter when the caller is not yet a member?* One sentence |
| **TM-02b leaving** | 🔴 [C-207](../LANE_COORDINATION.md) — *is acting on yourself an authorization question?* One paragraph in §7 |

### Behaviour preservation, audited

**No existing behaviour changed.** Four migrations, all additive: `0031` a new table, `0032` three nullable columns and a *weaker* constraint, `0033` one nullable column, `0034` a new table. **Every pre-existing row reads exactly as it did**; every pre-existing endpoint returns what it returned, with `MembershipResponse` gaining one nullable field.

**Two reads narrowed deliberately** — `get` and `list_page_for_workspace` now exclude ended memberships, **which is the security property TM-02 exists to create** and cannot happen to a row that predates it.

### Customer journey, audited

```
  Settings → Your team
     ├ who is here, and how many can administer      → roster
     ├ bring somebody in                             → invite · resend · withdraw
     ├ change what they can do                       → role control + explanation
     ├ take access away                              → remove, with the reason
     ├ hand the organization over                    → one act, never two owners
     └ what happened                                 → history, newest first
```

**Every transition lands somewhere.** Inviting adds a row to *Invited* and toasts the address. Removing returns to a roster one shorter. Transferring leaves the actor a member with the control gone. **The only journey that does not complete is the invitee's**, which is C-208.

### Repository reuse, audited across the module

**Nothing new in `components/ui`. No new `Resource`, no new `Action`, no policy line.** Reused: `policy.csv`'s three grants · `AuthenticatedPrincipal.email` · the JWT's verified claim · Better Auth's email verification · `WorkflowState`'s who/when/why shape · `Opportunity.opened_by`'s actor pattern · D23's *"Somebody here"* · the `evidence_state` derived-state discipline · Commercial Profile's versioned-immutable rule · the immutable-table convention and its `DELETE` grant · `set_workspace_context` · `lib/auth/email.ts`'s port shape · CX-01's Settings card · the route census, which caught the new page unedited.

**Created only where nothing existed:** the invitation aggregate, the role-change record, one domain function, six use cases, four migrations, two components, seven hooks.

---

## Leaving — TASK-437, 2026-08-05

**§2 of this document complained that `member:remove` was *"a reviewed authorization grant for an operation the system cannot perform."*** [TASK-418](../BACKLOG.md) capability ④ then shipped `Action.LEAVE` and its two policy grants, which is that shape a second time. **This row is what stopped it becoming one.**

**`POST /workspaces/{workspace_id}/membership/leave`.** No target, no body, no reason.

### It takes no target, and that is a security property

`remove` names a `membership_id` because an administrator is pointing at somebody. **Nothing here points at anybody** — the membership is found from the workspace and the verified token — so there is no identifier to substitute and **no ownership check that could be written wrongly.** The safest parameter is the one that does not exist, and a test asserts the command carries exactly two fields.

**That is also why the two grants need no self-scoping.** `Action.LEAVE`'s own comment says it: *"the scoping to self is the endpoint's, not the policy's… identity never enters the request tuple."*

### The invariant is the application layer's

**An owner may leave. A workspace may never become ownerless.** [ADR-0404](adr/0404-platform-composition.md) ruled it there rather than into the authorization engine, because *"a workspace invariant hidden in the policy model is invisible to anyone reading the workspace"* — and `Membership.end` already enforced it for `remove` and `change_role`, so leaving reuses it rather than restating it. **Two ways to end a membership with two implementations would eventually disagree about the one rule that matters.**

### No reason is recorded, and that is deliberate

`remove` records why, because it is somebody's sentence about a colleague. **A person leaving owes the organization no explanation**, and `ended_by == user_id` is exactly what distinguishes a departure from a removal afterwards — derived rather than stored (§2).

### Two defects the slice found in its own module

| | |
|---|---|
| 🔴 **[B-206](../BUGS.md) — removal did not revoke access** | `WorkspaceQueryService.get_membership`, which powers the request-time membership check, **never filtered ended memberships.** `SqlMembershipRepository.get` did, and documented exactly this outcome as its reason. **Two reads of one fact and only one filtered**, with authorization consulting the unfiltered one. Found by an acceptance test that expected `404` and got `200` |
| 🟠 **`LastOwnerCannotLeaveError` was mapped to no status code** | So the platform's fail-closed handler turned *"Make somebody else an owner first"* into **500 "An unexpected error occurred."** The domain has raised it since M1, from `end` and from `change_role`. Now `409 last_owner_cannot_leave`, and **the mapping repairs `remove` and `demote` as a side effect** |

**`MembershipResponse` also gained `ended_at`**, because `remove`'s own docstring claimed *"the response returns the ended membership rather than `204`"* and the schema could not say so — an ended membership was byte-for-byte indistinguishable from a live one.

### Still open in this document's §2

**The `remove` endpoint's own gap is closed** — it exists. **What §2 raised and this row deliberately did not take** is membership suspension and notification, both out of scope and neither blocked.

## The history becomes queryable — 2026-08-06 (Lane A, TASK-443)

**Attribution was complete and the query was missing.** `actor_id` is carried across the repository and every write already records who did it; `GET /workspaces/{id}/history` has assembled the organization's own facts since Team Management. **What it could not do was answer the question in pages** — it returned every entry there had ever been, which is a contract a client cannot work with once a workspace has been running a year, and the collection [§7](../../CLAUDE.md) requires to be cursor-paginated.

**The keyset is `(occurred_at, source_id)`.** `source_id` is new and is the row an entry was derived from — a membership, an invitation, a role change. **Entries are computed rather than stored, so there is no identifier of their own to page on**, and two things happening in one microsecond would otherwise put a page boundary between them and drop one. It is deliberately **not unique**: one membership yields both a `joined` and a `removed`, so it pairs with `kind` and `occurred_at` rather than standing alone.

⚠️ **The response is bounded and the fetch is not yet** — [C-231](../LANE_COORDINATION.md), raised by this lane against its own slice. Bounding the fetch needs six queries, one per kind, each ordered on its own timestamp: an entry is derived, so *"the newest fifty rows"* is a question no single table can answer. **Recorded rather than implied**, and the urgency is low because the sources are a workspace's people rather than its pipeline.

### ⚠️ The endpoint had no test, and that is how the shape could change unnoticed

**It shipped with none.** Changing the response from a bare list to a paged envelope broke nothing, because nothing asserted anything about it. **`tests/integration/test_api_organization_history.py` now covers it** — what it records, newest-first ordering, the cursor walking without repeating or dropping an entry, that a member sees it and a stranger gets `404`, and that one organization never appears in another's history.

**Every fact in those tests is produced through the API** — invitations sent and accepted, people leaving — because a history assembled from rows inserted behind the product would prove the assembly and not the recording (§20e).

## The saved view's contract, and nothing else — 2026-08-06 (Lane A, TASK-449)

**[R-02](../DOMAIN_DISCOVERY_REGISTER.md) is measured as the highest-leverage capability in the product** — four screens wrote its definition independently, and sixteen inherit the shell that needs it. **It was blocked on one word**, and [D-112](../DECISION_REGISTER.md) ruled it: ✅ **`SavedView`**, with ⛔ **`Segment` left alone** as `commercial_profile`'s ICP cohort rather than overloaded.

**This module publishes four types and stops there** — `SavedViewView`, `SavedViewListView`, `SavedViewReader`, `SavedViewWriter`. **No table, no endpoint, no implementation**, and that is the deliverable rather than a staging post: a consumer lane can compile, type-check and test against the port **before a row is ever persisted**, while `lint-imports` proves the coupling never forms in the wrong direction.

**The edge already runs.** `opportunity_engine/application/transition.py` imports `WorkspaceQueryPort` from `workspace_tenancy.public` today, so **no import contract needed amending** for this.

### What the contract refuses, and why each refusal is in the types

| | |
|---|---|
| **The declaration is opaque** | ⛔ *Never parses, validates, executes, ranks or optimises it, and never learns what `filter` or `sort` mean.* **The moment this store could call a declaration invalid, `workspace_tenancy` would be responsible for another module's semantics** — the boundary `commercial_profile` keeps by never reading the pipeline. Asserted by a test that fails if a `filters` or `sort` field ever appears |
| **No results, ever** | A saved view is a question somebody wrote down; running it belongs to whichever module owns the answer |
| **No `update` on the writer** | **The absence is the design.** A change is `save` with `supersedes` — `IcpDeclaration`'s shape for its reason: a colleague who acted on a view last week needs it to still mean what it meant. **A port offering `update` would make immutability a rule somebody remembers rather than one the contract cannot express** |
| **Reader and writer are separate** | Every member reads what their workspace shares; creating one is an act with an author. **One port would make every reader a writer** |
| **No events** | **[P-C](../DOMAIN_DISCOVERY_REGISTER.md): an event exists when a consumer appears, and none has.** A context definition is exactly where a speculative event catalog is otherwise born |

**Ten tests hold those refusals**, because a `Protocol` nothing asserts is a suggestion — and these are the non-responsibilities that erode *"one reasonable exception at a time"*.


## The capability layer — 2026-08-15 (Lane A, [TASK-1479](../BACKLOG.md) ⓸)

📁 **[ADR-0410](adr/0410-authorization-capability-layer.md), ratified as [C-1429](../LANE_COORDINATION.md).** ⚡ **§7 delegates the vocabulary, the role sets, the schema, the API shape and the UI to this lane; what follows is what was decided and why.**

### 🔴 §6 said *"two roles remain two"*, and that is still true

⛔ **`WorkspaceRole` is unchanged.** ⚡ **`OWNER` and `MEMBER` are tenancy membership** — *does this person belong here, and may they administer it* — and **a capability role is a different question sitting above it**: *may this person perform this action on this resource.* 📁 ADR-0410 §1.

> **The enum did not widen, and §6's own reasoning is why.** ⛔ **Widening it would have made every new screen a change to a tenancy primitive.**

### ⚡ The mechanism already existed, and finding that was most of the slice

📁 `Authorizer.is_allowed(role: str, …)` **takes a free string**, and `model.conf`'s `sub` is *"the caller's workspace role, already resolved from a server-side-verified membership"* — **deliberately not the user id.**

✅ **So a capability role needed no change to `signora_platform/**` at all.** **It is another role string, resolved server-side exactly as the membership role already is, and its grants are `policy.csv` rows** — 📁 the registry [§20e](../../CLAUDE.md) says every lane extends. ⛔ **One line of composition is the whole wiring**, and it is in `apps/api/main.py`.

### 🔴 The one genuine decision — a capability role REPLACES the membership role

⚠️ **It does not add to it, and four things in the design require that.**

| | |
|---|---|
| 📁 ***"Effective permissions"*** | **ADR-0410 §3 calls it *the resolved answer for a person*.** ⛔ **One answer** — a union of *what my membership allows* and *what my role allows* is two answers a customer has to combine themselves |
| 📁 ***"Change to Analyst"*** | **The design's own words**, and ⚡ **a change is not an addition** |
| 🔴 **Narrowing must be representable** | **`Analyst` is drawn as narrower than `Admin`.** ⛔ **A role that could only add makes a narrower one unbuildable** — *a design that cannot express the product* |
| ✅ **The safe direction survives** | 📁 §5: *"a capability that is not yet granted denies."* **An unlisted pair is denied for a capability role exactly as it is for `member`** |

⛔ **And §5's migration guarantee is untouched, because assignment is opt-in.** **Nobody holds a capability role until somebody assigns one**, so *"every current OWNER and every current MEMBER keeps exactly the authority it has today"* is **true by construction rather than by care.**

### ⛔ The invariant that is not negotiable, expressed as a type

📁 **ADR-0410 §5: *"a member must not acquire an owner's capability through the new layer."***

⚡ **`CapabilityRole` cannot be constructed with a name that collides with a membership role**, and `key` prefixes every subject with `cap:` — **so the two namespaces are disjoint by construction rather than by a list somebody maintains.** ⛔ **A role named `owner` would be handed to `is_allowed` as the string `owner` and would match all 46 of that role's policy rows.**

⚠️ **The enforcement is a Security Invariant as well** — `tests/security_invariants/test_capability_layer.py`, **nine of them, against the real enforcer and the real `policy.csv`**, because a type stops this module and the policy file is edited by every lane. **One of them asserts that no `cap:` subject appears in `policy.csv` at all**: this slice ships the layer and grants nothing through it, and **the day somebody adds a row that test fails and they have to say what they granted and to whom.**

### 📁 What reaches the API, and the two shapes worth arguing about

| | |
|---|---|
| `GET · POST /workspaces/{id}/capability-roles` | The list, and *New role*. **A member may read and may not change** — Team Management shows a colleague's role to everyone; **defining roles is administration** |
| `PATCH …/capability-roles/{role_id}` | 🔴 **A rename moves the subject `policy.csv` keys on**, so **a rename without a matching policy edit denies everything, silently, for everyone holding the role.** ⚠️ Stated at the type, the repository, the use case and the route |
| `PUT …/members/{user_id}/capability-role` | ⛔ **`PUT` and `204`.** There is one field, **`role_id: null` IS *change back***, and *"I did not mention it"* is not a state a customer can be in. **What they may now do is a different question**, answered by *Effective permissions* rather than guessed from the response |
| `GET …/members/{user_id}/effective-permissions` | 📁 **§3 — computed, never stored.** ⛔ **A `404` for a non-member, never an empty permission list**: an absence and *"a member who may do nothing"* are different facts |
| `GET …/members/{user_id}/capability-role/preview` | 📁 **The design's *Change role* trade** — see below |
| `GET …/capability-assignments` | **Who holds which role, for the whole roster in one answer.** ⛔ **Separate from `GET /members`, deliberately**: a capability role on a membership response would put an authorization fact inside a tenancy contract |

⚠️ **`Resource.CAPABILITY_ROLE` governs *managing* roles and never what a role permits.** 🔴 **There is deliberately no resource meaning *"authorization itself"*** — **a grant that could edit grants is the one this model must not have.**

### 🔴 *Change role* is a trade, and the preview is what makes the screen honest

📁 **The design: *"Both directions are shown, because a role change is a trade rather than a promotion."***

⛔ **`EffectivePermissions` answers about a person as they are.** **It cannot answer *what would they be able to do as Analyst*, and without that the dialog either omits *Gains* — not design compliant — or invents it.** ✅ **So the preview resolves BOTH subjects through the same enforcer**, and the screen derives *gains* and *loses* as the set difference — ⛔ **not a third field on the wire** ([§2](../../CLAUDE.md)).

⚠️ **Today every capability role grants nothing, so *Gains* honestly says so and *Loses* is everything.** ⚡ **It stops saying that on its own** the day somebody adds a `cap:` row: **computed, so there is no second place to update.**

⛔ **A `role_id` naming a role that is not in the workspace RAISES rather than falling back.** ⚠️ `subject_for`'s fallback is right for a role that vanished *under* somebody; **here it would render *"nothing changes"* for a change the `PUT` would refuse** — and the dialog would have said the act was safe.

### ⚠️ The screen may not say what the enforcer says, and that needed a catalog

🔴 **The server answers in `(resource, action)` pairs and NONE of them may reach a screen.** 📁 `workspace`, `target_account`, `commercial_focus` and `action_batch` are platform vocabulary ([ADR-0034](adr/0034-ubiquitous-language.md)) — ⛔ **and `vocabulary.test.tsx` structurally cannot catch them**, because it reads source literals and these arrive at runtime.

✅ **`components/team/capabilities.ts` gains `CAPABILITY_AREAS`** — **a resource maps to an area a salesperson would name**, and several fold into one. ⛔ **Not generated from `policy.csv`**, on the same reasoning the role catalog beside it already records: **generating it would put `commercial_focus` on a screen the day somebody added a grant.**

⚠️ **`policy.csv` grants 34 tuples to `member` and 46 to `owner`** — **eighty lines is the *lie by compression* that file already warns about.**

⛔ **An unrecognised resource is COUNTED, never named and never dropped.** **Dropping it would under-report what somebody may do — the worst failure this panel has, because a reader acts on the absence — and naming it would put the platform's vocabulary on the screen.** ⚡ **A line reading *"and 2 more"* is what tells the next engineer the catalog needs an entry.**

⚠️ **Two levels, not the design's five.** 📁 The design draws *Full · Team-scoped · Own only · Read · None*, and ⛔ **three of those describe scoping by team or by ownership, which nothing enforces today.** **Rendering *Team-scoped* would be a claim no enforcement point makes.**

### ⚠️ One test was corrected rather than worked around

📁 `frontend/tests/components/team.test.tsx` **forbade the word `permission` on this screen.** 🔴 **Too wide, and this slice is what showed it**: the finalized design's own labels are ***"Roles & permissions"*** and ***"Effective permissions"***, and **ADR-0410 §6 releases both by name.** ⛔ **Keeping the entry would have made the guard forbid the design.**

✅ **The guard got stricter where the risk actually moved** — the raw resource names are now in the forbidden list, and they are the ones only a rendering assertion can catch.

### 🔴 Where the slice is reachable, and the one test that proves it

**Settings → Your team.** ⚡ **The roles card sits beside the people it applies to**, and the roster gains a *Limited to* column, a *Change role* trade and an *Effective permissions* panel.

⛔ **Every other test in the slice would pass against a capability layer that was stored, read back and never consulted.** ✅ **One does not:**

```
a member reads the roles list                    200
the owner changes them to a role with no grants
the member reads the roles list again            403
```

⚡ **Fire-tested**: reverting the one line of wiring in `apps/api/main.py` fails **exactly that test** and leaves the other eleven green. **Storage and refusals still work; only reachability breaks** — which is the guard against the unreachable-primitive class.

### ⚠️ What is deliberately not built

| | |
|---|---|
| **Grants for any role** | 📁 **ADR-0410 §2 — they are `policy.csv` rows, and a reviewed change.** ⛔ **A rules UI is what choosing Casbin over a vendor was avoiding** ([ADR-0010](adr/0010-identity-and-access.md)) |
| **Deleting a role** | ⚡ `holders` is on the response so a control could ask first; **migration `0057`'s `ON DELETE RESTRICT` refuses to remove a role somebody holds**, and a control the database would reject is one that goes nowhere |
| **Field-level permissions** | 📁 **ADR-0410 §4 records it as this layer's question and does not choose the mechanism.** ⛔ Not decided here |
| **The design's role matrix** | ⚠️ **The Team Management design says *"Custom roles are deliberately absent — they become unauditable within a year"*, and the Settings design has *New role* and *"Five roles"*.** 🔴 **The two halves of one snapshot disagree**, and **ADR-0410 §6 rules it by naming *New role* explicitly.** 📁 Raised as [C-1513](../LANE_COORDINATION.md) so the design says one thing rather than two |
