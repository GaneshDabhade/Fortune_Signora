# Lead ownership, assignment and collaboration — design

> **Assigned to Lane A by the product owner on 2026-08-03.** The brief was eighteen deliverables and a warning not to think in tables. **The audit changed what the milestone is**, so this document leads with that rather than with a model.

---

## 1 · Repository Reuse Audit — the capability is built, and it has no UI

**Measured before anything was designed.**

| What the brief asks for | What already exists |
|---|---|
| **Who owns an opportunity** | `WorkflowState.owner_id` — `None` until a human takes it up |
| **Who changed ownership** | `WorkflowState.actor_id` — **required**, and the domain refuses a state without one unless it is the single machine-authored `TRACKING` |
| **Why** | `WorkflowState.reason` — **required and non-empty**, refused otherwise |
| **When, in order** | `WorkflowState.sequence` — monotonic from 0, *"ordering that does not depend on clock resolution"* |
| **Append-only history** | Every transition is a new row. **The record is already immutable** |
| **Assigning to somebody else** | **`POST /workspaces/{w}/opportunities/{o}/states` accepts `owner_id`** |
| **Refusing a non-member assignee** | `MembershipError` → `422 owner_not_a_member`, with the reasoning already written: *"naming the wrong person is a fault in the request rather than in their permissions"* |
| **Naming the person** | **TM-01**, last cycle |

> **The one line that decides this milestone is in `workflow.tsx`:**
>
> ```
> { stage, reason, ...(claiming ? { owner_id: viewerId } : {}) }
> ```
>
> **The UI has only ever sent the viewer's own id.** A seller can take an account on. **Nobody can hand one to a colleague** — and the backend that does it has been built, authorized, validated and tested since M6.

**This is the fourth instance of the pattern the capability census exists to find**, after Timeline's mount, the Connection Center's entrance, and the members endpoint. **And it is the first where the missing piece was another slice rather than a decision** — you could not assign to a colleague because the product could not name one, and TM-01 fixed that.

### What is therefore *not* being built

**No new aggregate. No new table. No new endpoint. No new event. No new permission.** Assignment is a `WorkflowState` with an `owner_id`, and that is already true.

**`assignment`, `assignee`, `lead` and `claim` do not enter the codebase.** They would be a second vocabulary for `owner_id` and `WorkflowState`, and §4's rule is explicit: *never invent a synonym.* **The customer word is *owner*, the platform word is *owner*, and they are deliberately the same.**

---

## 2 · The customer journey — Monday morning

**Eight questions a seller arrives with, against what the product answers today.**

| | Today |
|---|---|
| *Which ones are mine?* | 🟠 **Corrected 2026-08-03, see §11.** The list has said `Yours` since M12.2 — what it could not say is *who else*. It still cannot be **filtered** |
| *Which changed overnight?* | 🔴 R9-04 · [TASK-016](../BACKLOG.md), blocked on per-user read state |
| *Which were reassigned?* | 🟠 **The fact is recorded and unreachable** — `WorkflowState` holds every owner change and only the account brief renders history |
| *Which need attention today?* | ✅ The attention list, ranked by buying score |
| *Which are blocked?* | ⚫ No such concept, and **probably correctly** — see §4 |
| *Which need my manager?* | ⚫ No escalation, no manager relationship |
| *Which are waiting on the customer?* | ⚫ No such state |
| *Can I organize my day?* | 🔴 **Not by ownership.** Everything else, yes |

> **The gap is not the lifecycle. It is that ownership is invisible.** Four of the eight are answered or correctly absent; the three that hurt are all *"who holds this"*, and none needs a new state to fix.

---

## 3 · The ownership model — one owner, and the evidence for it

**`WorkflowState.owner_id` is a single nullable id. The brief lists sixteen ownership models. This adopts one and records the triggers for the rest.**

| Model | Verdict |
|---|---|
| **Single owner** | ✅ **Today.** One person is accountable, and *"nobody has taken it yet"* is a first-class state the product already says out loud |
| **Manual assignment** | ✅ **Today** — the slice below |
| **Manager assignment** | ✅ **Today, and it needs nothing.** An owner assigning to somebody else *is* manager assignment; the roles differ, the operation does not |
| **AI recommendation** | ⚠️ **Deliberately not.** *Intelligence suggests; humans commit* is the module's founding rule, and `TRACKING` is the only machine-authored stage. An AI-assigned owner would be the first machine-authored *commitment* — see §7 |
| **Primary + secondary · collaborative · shared** | ⚠️ **Trigger: two people working one account and needing to see each other.** Today a second person is *watching*, not owning, and watching is a different concept that does not exist |
| **Round-robin · load balancing · territory · regional · industry · product · strategic** | ⚠️ **All the same shape: a rule that picks an owner.** None changes the ownership *model* — each is an input to the same assignment. **Trigger: the first customer with more sellers than they can assign by hand** |
| **Temporary ownership · vacation coverage** | ⚠️ **Trigger: the first customer who asks.** It is an owner with an end date, which the state record already expresses as *a later state* |
| **Customer success · partner ownership** | ⚫ **Not this product yet.** No CS or partner concept exists anywhere |

**The single-owner model is not a simplification — it is a decision the domain already documents.** An account with two accountable people is an account nobody is accountable for, and the state record's whole shape is *one owner at a time, with a reason for each change.*

---

## 4 · The lifecycle — most of the brief's states are events or derivations

**Seventeen proposed states, against five that exist.**

| Proposed | Verdict |
|---|---|
| **Unassigned** | ✅ **Exists** — `TRACKING` with `owner_id: None`, and the brief already renders it as *"nobody has taken it yet"* |
| **Assigned · Claimed · Accepted · Working** | ✅ **All one state: `ENGAGED`.** Four words for *somebody is working this*, and the difference between them is *who* acted — which is `actor_id`, not a stage |
| **Converted** | ✅ `CLOSED_WON` |
| **Rejected · Lost** | ✅ **Two states, and the distinction is load-bearing**: `DISMISSED` is feedback about Signora's judgement, `CLOSED_LOST` is a sales outcome. *"Collapsing them would destroy the only signal the platform gets about its own qualification quality"* |
| **Transferred · Reassigned** | **Events, not states.** A transfer is a new `WorkflowState` with a different `owner_id`; the account is still `ENGAGED`. **Making it a state would mean an account stops being worked while it changes hands** |
| **Reactivated** | **An event.** A new state naming the one it follows — the sequence already carries it |
| **Dormant** | **Derived.** *Nothing has happened for N days* is a reading of `occurred_at`, and storing it needs a job that makes the row wrong until it runs — the reasoning that made invitation expiry derived |
| **Needs review · Escalated · Waiting · Blocked** | ⚠️ **Genuinely absent, and genuinely different**: each says *somebody else must act*. **They are one concept — a hand-off that is not an ownership change** — and adding four stages would be four words for it. **Trigger: a customer describing an account they cannot progress** |
| **Archived** | ⚫ Closed states already remove an account from the attention list |

> **Thirteen of seventeen already exist, are events, or are derivations. One real gap remains — *waiting on somebody else* — and it is one concept rather than four.**

---

## 5 · What ownership does *not* propagate to, and why

**The brief asks whether reassignment should cascade. It must not, and the repository already says so.**

| | Owned by | Moves on reassignment? |
|---|---|---|
| **The opportunity** | The person in `owner_id` | **Yes — that is the operation** |
| **The account · signals · buying score · research · evidence** | **Nobody.** They are *derived intelligence about a company*, rebuildable from evidence | **No.** A company does not belong to a salesperson |
| **The buying committee · ICP · products** | **The organization**, as customer-authored declarations | **No** |
| **Decision history** | **Nobody — it is the record.** `decided_by` is provenance | **Never.** Moving it would rewrite who decided what |
| **The timeline** | The account | **No** |

> **One rule covers all of it: ownership attaches to the *commitment*, never to the *knowledge*.** An opportunity is a person's undertaking; everything else is what the platform found out, and findings have no owner.

**CRM synchronisation is the one place this gets hard** — a CRM's owner field is on the *account*, and Signora's is on the *commitment*. **Recorded as M13's problem, with the mapping stated: `WorkflowState.owner_id` is the field a CRM's account owner corresponds to.**

---

## 6 · Collaboration — one concept exists, the rest need a customer

**Watching · followers · mentions · delegation · escalation · ownership requests · transfer requests · queues · comments · approvals · presence · out-of-office.**

**None exists. One is close:** an owner change already carries a `reason`, which is the smallest possible hand-off note — *"passing to Ravi, he knows their CTO"*.

> **The honest ordering: every item on that list needs somebody to be notified**, and Signora has no notification capability (M14a, not started). **Building any of them first would be building the half a customer cannot feel.**

**Trigger for the whole group: M14a ships.** Recorded rather than sequenced, because it is the product owner's ordering.

---

## 7 · AI participation — the boundary already exists

**`TRACKING` is the only machine-authored stage, and the domain enforces it**: a state without an `actor_id` is refused unless it is `TRACKING`.

> **So an AI-assigned owner is structurally impossible today, and that is correct.** *Intelligence suggests; humans commit.*

| Where AI helps | Where it must not |
|---|---|
| **Suggesting an owner** — a name pre-selected in the dialog, which a human still confirms | **Assigning one.** That would be the first machine-authored commitment |
| **Detecting a neglected account** — nothing has happened for weeks | **Reassigning it** |
| **Detecting an overloaded seller** — a count against a workload nobody has declared | **Rebalancing** |

**Every one of those is a *reading*, and every reading needs the ownership data to be visible first.** None is buildable before §8's slice.

---

## 8 · The roadmap, ordered by what a customer feels

| | | |
|---|---|---|
| **LO-01** | **Hand an account to a colleague** | The backend exists; the UI sends only the viewer. **Unblocked — this cycle** |
| **LO-02** | **The attention list says who holds each account** | *"Which are mine?"* — the question that hurts most. Needs the list to carry `owner_id`, which the opportunity response already does |
| **LO-03** | **Filter the list to mine** | Follows LO-02 directly |
| **LO-04** | **Ownership changes reach the account history** | The facts are in `WorkflowState`; the brief renders stage changes and not owner changes |
| **LO-05** | *Waiting on somebody else* | ⚠️ **A new stage.** Needs a customer describing it — §4 |
| **LO-06+** | Watching · escalation · queues · AI suggestion | ⚠️ **Blocked on M14a** — §6 |

---

## 9 · Enterprise readiness, and where pressure begins

**Absorbed without change:** territories, regions, business units, industries and strategic accounts are **all rules that pick an owner**, and none changes the model. Multi-country and matrix organizations are **multiple workspaces**, which already work.

**Where pressure begins:**

| | |
|---|---|
| **A rule that assigns automatically** | The first thing that would write an `owner_id` **without an `actor_id`** — and the domain refuses that. **The rule needs an identity**, which is the `opened_by` pattern again, and it is the same pressure point SCIM creates in Team Management |
| **Two owners** | The state record holds one. A second is a schema change *and* a change to *"one person is accountable"*, which is a product decision rather than a technical one |
| **Ownership analytics · manager dashboards** | **Read models over `WorkflowState`**, which is append-only and complete. **Nothing blocks them; nothing has been built** |
| **100k accounts · millions of signals** | The attention list is already cursor-paginated and ranked. **Ownership filtering is an indexed predicate on a column that exists** |
| **Channel partners · resellers · distributors** | **Not this product.** No concept of an organization acting on another's behalf, and §11's *cross-workspace* problem is the same one |


---

## 10 · LO-01 — an account can be handed to a colleague, 2026-08-03

**One line changed, and it was the milestone.**

```
- { stage, reason, ...(claiming ? { owner_id: viewerId } : {}) }
+ { stage, reason, ...(newOwner !== null ? { owner_id: newOwner } : {}) }
```

**No endpoint, no migration, no permission, no event, no new vocabulary.** `WorkflowState` already carried the owner, the actor and the reason; the API already validated the assignee's membership; TM-01 already made a person nameable. **The whole slice is a picker, a default and a sentence.**

### The decisions inside it

| | |
|---|---|
| **Default to *You*** | The commonest case by far — somebody deciding about an account is usually taking it on. **A required choice would tax the common path to enable the rare one** |
| **Only on *Take it on*** | Closing and dismissing leave ownership where it was, and a control there would invite a change nobody asked for |
| **Absent when nobody else exists** | A one-person organization gets no picker. **An empty control teaches a reader to distrust the ones that work** |
| **Named or not offered** | A membership with no address is skipped — *"Somebody here"* in a picker is a row nobody can choose between, the rule the account sequence already applies |
| **The roster is passed in, not fetched** | Same rule `next` follows: a presentational control that reached for a query would make every test of a decision mount a client. **And it costs no request** — the Team page's query, same cache key |

### A defect this slice introduced, and caught

**The confirm button said *"Take it on"* while handing the account to somebody else.** It is the last thing a person reads before committing, and **a button describing a different act than the one it performs is precisely what a confirmation exists to prevent.**

**It now says *"Hand it to ravi@acme.com"***, and falls back to *"Hand it over"* if the name has not resolved — rather than *"Hand it to "* with nothing after it.

> **Found by writing the test, not by reviewing the diff.** The assertion needed the button's name, and the name was wrong.

### What a seller can now do that they could not

**Hand an account to the colleague who should work it, with the reason recorded against both of them** — because a `WorkflowState` carries `actor_id` *and* `owner_id`, so the history already says *Ana gave this to Ravi, and why.*

**LO-02 is next**: the attention list still does not say who holds each account, which is the question that hurts most.


---

## 11 · LO-02 — a held account says who holds it, 2026-08-03

### A correction to my own audit, made before writing anything

**§2 said the attention list *"shows no owner"*. That was wrong.** `Ownership` has been mounted on every row since M12.2, with its D23 reasoning written out, rendering **`Yours`** or **`Taken`**.

> **I grepped the component file for its own strings and concluded it was unmounted.** The list imports it at `page.tsx:10` and renders it at `199`. **A search that looks in one file cannot tell you what imports it** — and the census's own method is what should have been applied.

**So LO-02 is smaller than the roadmap said**: the list already answers *"which are mine?"*. What it could not do is say **who** the somebody else is.

### `Taken` was right, and stopped being right

**D23 chose *taken* because the Python tier verifies tokens without learning who anybody is** — so an identifier nobody could read was worse than an honest absence. **TM-01's `member_email` changed the premise**, and the badge now names the colleague.

**`Taken` survives as the fallback** for a membership added by identifier before invitations existed. Still honest, and now rare.

### The design questions, answered

| | |
|---|---|
| **Avatar?** | **No.** There are no display names and no images — an avatar would be a coloured initial derived from an email, which is decoration standing in for information |
| **Name, chip or badge?** | **The badge that already exists.** A chip beside a badge beside a badge is three shapes for one row |
| **Primary or secondary?** | **Secondary, and unchanged.** It sits with contested and evidence, where a seller's eye goes when they pause on a row — not with the score, which is why the row is ranked |
| **Two questions, one badge** | *Which are mine* is **binary**, and `Yours` is the whole answer. *Who holds this* needs the name. **The badge answers whichever the reader has** |
| **Highlight a recent change?** | ⚠️ **Not built. It needs *since when you last looked*, which does not exist** — the same per-user read state that blocks [TASK-016](../BACKLOG.md). Recorded rather than approximated with *"changed in the last 24 hours"*, which is a different question wearing the same badge |
| **Presence · workload · availability?** | ⚫ **None exists**, and each needs a capability rather than a rendering. §6's trigger applies: all of them need M14a |
| **Manager ownership differently?** | ⚫ **No manager relationship exists.** An owner is an owner |

### Nothing new was written

**No endpoint, no field, no migration, no component.** One optional prop, one fallback, and a map threaded from a query that was already cached by two other screens — so **it costs no request**.

**LO-03 follows directly**: the list now shows ownership, and filtering to *mine* is a predicate over a field the row already carries.


---

## 12 · LO-03 — whose work the list is showing, 2026-08-03

### The pagination question decided the slice

**The attention list is a `CursorPage`.** So filtering the returned rows would mean **"mine on this page"** — which reads correctly at twelve accounts and **silently becomes a lie at two hundred**: nine of somebody else's followed by two of mine returns a page of two while claiming to be a page of ten.

> **The predicate is in the page query**, so the cursor walks the filtered set. **One `where` clause, and the semantics are correct at any size.** A test asserts exactly that arrangement.

### And it had to travel on the link, or *next* would break

**The brief reads the same query to offer the next account (D41).** A seller filtered to *Mine*, who decides and is then handed **somebody else's** account, has been dropped out of the list they were working — silently, at the one moment the product is certain they are ready to continue.

**So the scope lives in the URL and rides the row's `href`.** Three properties fall out of that, and all three were asked for: **it survives a refresh · it survives browser back · it opens in a second tab as a different view.** A `useState` would lose all three.

**`all` is left out of the URL**, because a clean address is the one a seller copies.

### The filter set — three, not ten

| | |
|---|---|
| **All · Mine · Unassigned** | **Built.** The two questions a seller actually asks on a Monday, plus the default |
| **Team** | ⚫ **No manager relationship exists.** *Everybody's* is `All` |
| **Following · Watching** | ⚫ **Not concepts.** §6 |
| **Recently changed · Recently assigned** | ⚠️ **Needs *since when you last looked***, which does not exist — the same per-user read state blocking [TASK-016](../BACKLOG.md). **Not approximated with 24 hours**, which is a different question |
| **Mentioned me · Needs my review** | ⚠️ Mentions need M14a; *needs my review* needs the hand-off state LO-05 is waiting on a customer to describe |

**Each absent one has a trigger rather than a stub.**

### Rendered as links, not as a control

A link is **bookmarkable, openable in a new tab, and keyboard-reachable without a widget** — and the scope has to be in the URL regardless. `aria-current="page"` marks the active view. **The filter appears only once an organization exists**: a control over nothing is furniture.

**An unrecognised `?owner=` reads as `all` rather than failing.** It is a view preference, not a security boundary; there is nothing to protect by refusing, and a stale link should show a seller their accounts.

### Reuse

**`useSearchParams`, the convention `/settings/connections` already established.** No state library, no persisted preference, no new component. **One new module** — `lib/state/owner-scope.ts` — because reading, writing and naming the scope in one place is what stops the list and the brief disagreeing about what `?owner=mine` means.

**One backend enum, one query parameter, one `where`.** No migration, no table, no new endpoint.

### The fake was changed to match the query

`FakeOpportunityRepository.open_page` now applies the owner predicate **before the limit**, exactly as the SQL does. **A fake that filtered afterwards would agree with an implementation that returns short pages** — which is the precise defect this design exists to prevent, and it would have made the test that proves it pass against broken code.

---

## 13 · LO-04 — an account being worked can change hands, 2026-08-03

### The slice was assigned as *ownership changes reach the account history*. The audit found the question before it

**An account being worked could not be handed to anybody.**

`allowed_next` is the domain's **stage** table, and it is what the brief's controls are drawn from. From `engaged` it contains `closed_won`, `closed_lost` and `dismissed` — so a seller working an account was offered *Won*, *Lost* and *Not a real opportunity*, **and no way to give it to a colleague.**

> **A seller going on leave had to close their accounts to get them off their name.** Every one of the pressure points a real revenue team lives with — leave, resignation, a territory change, a manager inheriting thirty accounts — arrived at the same dead end.

**Rendering ownership changes in the history without this would have rendered a fact that can occur exactly once per opportunity** — at the moment somebody first takes it on. The two are one slice because neither is worth much alone.

### The domain has permitted it since M6. Nothing needed to change

`next_state` refuses a row only when **the stage *and* the owner are both unchanged** — *"a state row that changes nothing is noise in the audit trail."* A same-stage row with a different owner has always been legal, `TransitionOpportunity` has always verified the new owner's membership, and the endpoint has always accepted an arbitrary `owner_id`.

**No migration, no new endpoint, no new event, no domain change.** The capability was built; **the control was missing**, which is the sixth time this milestone has found that shape.

### Ownership is not a stage, and the type is where that is enforced

The obvious implementation is a fifth stage — `transferred`. **It is wrong**, and the reason is the one this module already states about a won deal: a stage is a **state**, a hand-over is an **event**, and a stage that exists to record an event distorts every figure computed from the table afterwards.

So the control carries a `Choice`:

```ts
interface Choice {
  stage: Stage;
  handover: boolean;   // ownership is the change; the stage is going nowhere
}
```

**Two independent facts, because a single enum could only hold one of them.** The hand-over control is therefore deliberately **not** driven by `allowed_next` — that list is about stages, and it structurally cannot express this.

### Where it is offered, and where it is deliberately not

| | |
|---|---|
| **Being worked, held by you** | **Hand it over** — a colleague is chosen, and the confirm stays disabled until one is |
| **Being worked, held by somebody else** | **Take it over** — the reader becomes the owner, and the dialog says so before they commit |
| **Nobody holds it** | ⚫ Not offered. *I'm working this* already asks who is taking it; two controls for one act would be two ways to answer one question |
| **Closed — won, lost, dismissed** | ⚫ Not offered. There is no live work to move, and a won deal is terminal |
| **A one-person organization** | ⚫ Not offered. **A control that cannot complete is not offered** rather than offered and refused |

**Taking an account somebody else holds is allowed, on purpose.** *"Two people both think they own this"* is a real thing that happens, and the product settles it in the open: the taker is the actor, a reason is required, the previous holder appears on the row before it, and nothing is silently overwritten. **Preventing it would push the conversation outside the product**, where the record cannot follow it.

### The picker has no default, which is the opposite of the take-on control

Taking an account on defaults to *you* because that is overwhelmingly the commonest case. **Handing one over has no commonest case the product may assume** — the first colleague in a list is not a guess, it is a person — so the placeholder is unselectable and the confirm is disabled until somebody is named.

### The history had to change, or a hand-over would have read as its opposite

**The stage alone cannot say what an entry was.** A row recorded at `engaged` is *"took it on"* when the owner arrived with it and *"handed it to Ravi"* when the stage never moved. **Reading only the stage would have told a seller that Ana took on an account she had just given away.**

So each entry is rendered against **the one before it**:

| Entry, compared with its predecessor | Reads as |
|---|---|
| Owner arrived, from nobody | *took it on* |
| Owner changed, stage did not | *handed it to ravi@acme.com* |
| Owner changed to the actor, stage did not | *took it over from ravi@acme.com* |
| Stage moved into `engaged`, owner is somebody else | *handed it to ravi@acme.com* |
| Stage moved anywhere else | the stage wording, unchanged |

**Ownership leads only where it is the news.** A win that also reassigned reads as *"closed it won"* — that is the fact, and the assignment beside it is bookkeeping.

### D23 was true when it was written, and stopped being true

The workflow line said **"held by someone else"** for three milestones, and the comment beside it said Signora *can say nobody else's name*. That was correct: the Python tier verifies tokens without ever learning who anybody is ([ADR-0026](adr/0026-jwt-boundary-architecture.md)).

**TM-01 changed the fact underneath it.** A membership now carries the address it was created with, and the roster is already in the cache on every screen that needs one.

> **"Someone else" on the one line whose job is to say who holds an account was the product knowing and not saying.**

The decision history's own doc comment predicted this and named the wrong mechanism — it expected [C-024](../LANE_COORDINATION.md) to settle name resolution. **TM-01 settled it first.**

**Three surfaces resolve a name** — the hand-over picker, the workflow line, the decision history — which is what makes `components/team/people.ts` a module rather than an expression written three times. **Two would have been a coincidence** (the rule that refused a shared history framework, [46-team-management.md](46-team-management.md) §11); three is the pattern it named as the trigger. The real argument is not repetition but agreement: **a picker offering *ana@acme.com* whose trail then says *"somebody here"* describes two people to a reader who knows there is one.**

**The honest absence survives as the fallback**, for a membership added by identifier and for somebody who has since left — *a name the roster no longer holds is a fact about today, and the record is about then.*

### What the hand-over would have projected onto the timeline

**Asked before it shipped rather than after somebody saw it.** A hand-over publishes `opportunity.stage_changed` with **both stages equal**, and the account timeline renders `previous_stage` → `new_stage`:

> **"Opportunity moved — Working it to Working it"** — a sentence that says nothing, twice, on the feed a seller uses to understand an account.

It now reads **"Account handed over"**, with **the reason** as its detail — which is already on the wire and is exactly what a colleague opening the account next week needs.

**No owner is named there, and that is the feed's own rule rather than a gap.** That surface answers *what happened to this account* and names nobody; *who did what to whom* is the decision history's question, and it has the whole state to answer it with. **The timeline's projection is unchanged** — no `owner_id` was added to `detail_keys`, because nothing on that surface would render it.

### Two defects found by writing the test rather than by reading the diff

**The success panel said *"You're working this"* to somebody who had just given the account away** — the same defect as LO-01's confirm button, one screen later.

**And the fix had a second one inside it.** Recording the decision invalidates the brief, so by the time the panel renders **the account already belongs to somebody else** — asking *"do I hold this?"* then answers about the world *after* the act. The wording is about the act, so what was held at the moment of deciding is captured with the decision.

### A branch that could not fail, removed

`actor()` in the decision history read `state.decided_by === null ? (opened ? 'Signora' : 'Signora')` — **both arms identical.** Decorative Logic (`CLAUDE.md` §2): it looked like it distinguished the opening entry and could not. The `opened` argument is gone.

### What LO-04 deliberately did not build

| | |
|---|---|
| **Releasing an account back to nobody** | ⚠️ **Not representable.** `owner_id: null` on the request means *leave ownership unchanged*, so there is no way to express *unassign*. A real need — a rep leaves and nothing should silently inherit their pipeline — and it needs a request shape that can distinguish *absent* from *null*. **Trigger: the first customer who asks to unassign** |
| **Acknowledgement by the new owner** | ⚫ Nothing to acknowledge with until M14a. A hand-over is currently a fact the trail records, not a message |
| **Notifying the previous owner** | ⚫ Same. M14a |
| **Bulk reassignment** | ⚫ **A manager inheriting thirty accounts does thirty hand-overs today.** Deliberately not built: the shape of the bulk operation should be decided by watching somebody do it slowly, not before |
| **A required reason vocabulary** | ⚫ The free sentence is the record, and a dropdown of *leave · territory · resignation* would collect less than the sentence does |
