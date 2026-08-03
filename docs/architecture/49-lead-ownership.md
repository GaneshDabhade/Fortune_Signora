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

---

## 14 · LO-05 — the lifecycle walked as a customer, 2026-08-03

**Not a workflow review.** The product was walked end to end as an SDR, an AE, a manager and somebody returning after three months, with the implementation deliberately forgotten. Every finding below is **evidence from the running code**, not a guess about what might be missing.

### The verdict, first

**The lifecycle is coherent from discovery to closure, and it ends badly.** Everything up to *won* explains itself; the moment an account closes, three of the customer's most ordinary questions have no answer, and one of them — *"I clicked the wrong button"* — has no answer at all.

### The walk

| The customer's moment | What Signora does today | Verdict |
|---|---|---|
| **An opportunity appears** | The attention list ranks it, the badge says why it moved, the brief says *Signora suggested this* and *nobody has taken it yet* | ✅ Understandable and trustworthy |
| **They want to know why** | Score, contributions, evidence drawer, narration, research, validation | ✅ The strongest part of the product |
| **A seller takes it on** | Ownership is recorded with a reason and an actor; the line says *you hold this* | ✅ |
| **A seller hands it over** | LO-04. Named colleague, reason, both directions | ✅ |
| **A seller ignores it for three weeks** | The list surfaces *Cooling* and *Evidence expired* — **facts about Signora's evidence, not about the seller** | ⚠️ **F-1** |
| **Ownership changes** | LO-04's trail, in both directions, naming both people | ✅ |
| **The deal is won** | The brief now says why nothing can be done (fixed here). It stays reachable under *accounts already decided* | ✅ *after this slice* |
| **The deal is lost or dismissed** | Reopening is offered, with its own reason and actor | ✅ |
| **They closed the wrong account** | **Nothing.** A won deal is terminal, correctly — and the recourse the domain names does not exist | 🔴 **F-2** |
| **They want to add an account themselves** | **No route.** `Qualification.MANUAL` exists in the domain, is rendered on the brief, and **nothing can produce it** | 🔴 **F-3** |
| **A manager arrives** | Nothing a manager can answer that a seller cannot | ⚠️ **F-4** |
| **An SDR joins halfway** | The decision history and the account timeline both read from the start | ✅ |
| **They return after three months** | Everything is there; **nothing says what changed while they were gone** | ⚠️ **F-5** |

### The findings, classified the way the product owner asked

| | Finding | Class | Evidence |
|---|---|---|---|
| **F-1** | **A stalled account looks identical to a fresh one.** *Cooling* and *Evidence expired* describe Signora's evidence ageing, never *"you took this on three weeks ago and nothing has happened"* | **Missing.** The fact is derivable from the `engaged` state's `occurred_at` and nothing renders it | `attention.tsx` badges are keyed to `evidence_state` only |
| **F-2** | **An accidental win is unrecoverable, and always will be** | **Missing recourse, correct rule.** `CLOSED_WON: frozenset()` is right — the next deal is genuinely a new opportunity — but the *product* offers no way to reach that new opportunity | `_ALLOWED[CLOSED_WON]` is empty; there is no opening endpoint |
| **F-3** | **A human cannot open an opportunity.** `Qualification.MANUAL` is modelled, tested, and rendered as *"somebody here added it"* — **and is unreachable in production** | **Implemented but disconnected.** `QualifyOpportunity` has exactly one caller: the buying-score event handler, which never passes `opened_by` | `interface/handlers.py`; no POST route exists |
| **F-4** | **No manager view exists**, so *"where should my team focus?"* has no screen | **Missing**, and blocked on a manager relationship that does not exist | Already recorded at §12 |
| **F-5** | **"What changed since I was last here?"** has no answer | **Missing**, and it is the same per-user read state as [TASK-016](../BACKLOG.md) | §12 |
| **F-6** | *"N accounts **you** have decided about"* over a **workspace-wide** query | **Confusing.** Fixed in this slice | `decided_page` has no owner predicate |
| **F-7** | **A won brief offered nothing and explained nothing** | **Unpolished.** Fixed in this slice | `WorkflowActions` returned `null` |

**F-3 is the seventh instance of this milestone's recurring shape** — built, and unreachable. It is also the *cause* of F-2: the domain's answer to a mis-click is *"open a new opportunity"*, and that is exactly the route nobody can take.

### Two fixed inline, because they were wording and a missing sentence

**F-7 — a won brief now says what happens instead.** *"Won deals stay won. If this company comes back, Signora opens a new opportunity — this one keeps its history."* **Every word of that is checkable**: a new qualifying score after a closure opens a new generation, which is asserted in the module's suite. It is the one screen in the lifecycle where a reader can do nothing, so it is the one screen that has to say why.

**F-6 — the decided section no longer claims a colleague's judgement as the reader's own.** True when written, when every workspace had one member; **Team Management made it false without anything here changing**, which is the exact failure mode §12 of `CLAUDE.md` describes.

### Challenging the inherited CRM

**Asked deliberately: if Signora were invented today, with AI from day one, what would this look like?**

| Inherited assumption | Challenge | Answer |
|---|---|---|
| **Won / Lost captures the outcome** | It captures *whether*, never *why now* or *against whom* | **Keep the stages; the reason field already carries it.** A competitor field is a CRM instinct — it is a *fact about the account*, and the Knowledge Graph owns facts about accounts |
| **Waiting should be a stage** | ⚫ **No.** *Waiting on the customer* is not a state of the opportunity, it is a state of **the most recent activity**. Making it a stage means somebody must remember to leave it — and every CRM that did this has a pipeline full of accounts stuck in *Waiting* since March | **Activity, not stage.** It belongs to the timeline, and the honest surfacing of it is F-1: *nothing has happened here in three weeks* |
| **Blocked should be first-class** | Same shape, stronger pull — a manager genuinely wants *what is blocked*. But *blocked* is a **claim with an owner and an expected resolution**, not a stage | **Deferred with a stated trigger**: a customer describing what unblocks it. Recorded as LO-06 |
| **Needs customer response · Waiting for contract** | These are **five stages that are really one question**: *what is this waiting on, and since when?* | **One concept, not five stages.** Five would multiply the transition table by five and answer nothing the timeline cannot |
| **An opportunity has a close date and an amount** | Absent, and deliberately so — both are **forecasting**, and neither is knowable by inference | Not this milestone. **Trigger: the first forecasting requirement** |
| **A stage means the same thing to everyone** | This one is *worth* inheriting: the five stages are small, explained in the customer's words, and each maps to exactly one recorded value | **Keep** |

> **The through-line: a CRM turns every question into a stage, because a stage is the only thing it can render.** Signora has a timeline, a decision history, evidence and a score — so a question should become a *fact it already holds*, and the stage table should stay small enough that a seller can hold it in their head.

### Explainability, scored against the seven questions

| Question | Answered? |
|---|---|
| **Why did this happen?** | ✅ Reason on every state, and it leads the entry |
| **Who did it?** | ✅ Since LO-04, by name |
| **When?** | ✅ |
| **What changed?** | ✅ Stage and ownership, read pairwise |
| **Why now?** | ✅ `BuyingScore.trigger`, on the list |
| **What happens next?** | ⚠️ Only on a won deal (this slice). **Elsewhere the product never says what it expects next** |
| **What should I do?** | ⚠️ The ranked list answers it *across* accounts; no brief answers it *for* one |
| **Can I undo it?** | 🔴 **F-2** |
| **Can I recover it?** | ✅ except after a win |

### Playwright scenarios — the plan, not the suite

**Written as customer behaviour**, per the product owner's instruction, and deliberately not implemented yet.

| # | Scenario | Covers |
|---|---|---|
| **P-1** | Discover → understand → take on → work → win | The spine |
| **P-2** | Discover → take on → lose → reopen → win | Recovery through the legal path |
| **P-3** | Dismiss → find it again under *already decided* → reopen | R4-04 |
| **P-4** | Hand an account over mid-work; the colleague sees it as theirs | LO-04 |
| **P-5** | Take over an account somebody else holds; both trails agree | LO-04 |
| **P-6** | Filter to *Mine*, decide, and be offered the next **of mine** | LO-03 · D41 |
| **P-7** | Refresh mid-hand-over; nothing is half-applied | Not optimistic, deliberately |
| **P-8** | Two tabs hand the same account to different people | Last write wins, and the trail shows both |
| **P-9** | A member loses their role while a dialog is open | Server refuses; the message is the domain's |
| **P-10** | Return after a week and understand what happened | F-5 — **expected to fail today**, and that is its value |
| **P-11** | Open a won account and understand why nothing can be done | F-7 |
| **P-12** | Six months of history read by somebody who has just joined | The trail from `sequence 0` |

**P-10 is written to fail.** A scenario that documents a known gap is worth more than one that documents what already works, and it converts F-5 from a paragraph into a check.

### Future pressure — trigger, pressure, direction

| Trigger | Pressure | Possible direction |
|---|---|---|
| **A workspace passes ~500 open accounts** | The attention list is cursor-paginated and correct, but *"what needs attention"* stops being answerable by ranking alone | Saved views over the existing scope parameter — **no new concept** |
| **A second seller shares a territory** | Two people work the same account and only the trail records it | Watching, which needs M14a |
| **A manager with ten reports** | F-4. Needs a manager relationship, which is a Team Management concern rather than this module's | An owner relationship on membership, then a scope value — **the LO-03 filter already has the shape** |
| **Bulk reassignment** | Thirty hand-overs after one departure | **Deliberately unbuilt** until somebody has been watched doing it slowly |
| **Auto-assignment or AI-recommended owners** | *Intelligence suggests; humans commit* holds — a recommendation must arrive as a **suggestion on the existing control**, never as an owner written by a machine | The `Choice` type already separates the act from the stage |
| **SLAs and escalation** | Both need F-1's *"nothing has happened since"* first | F-1 is the prerequisite for four of these rows |
| **Territories, business units, partner ownership** | Ownership becomes a *relationship* rather than a person | Not until a customer has two of them |

**F-1 is load-bearing for SLAs, escalation, queues, stale-ownership surfacing and manager health.** It is the smallest of the open findings and unlocks the most.

### What LO-05 recommends next, in order

| | | |
|---|---|---|
| **LO-06** | **Nothing has happened here since…** | F-1. Derived from state the module already holds; no schema change; unblocks five future rows |
| **LO-07** | **A human can add an account** | F-3, and therefore F-2's recourse. One endpoint, one control, one already-modelled `Qualification` |
| **LO-08** | *Blocked* / *waiting on* | Needs a customer describing it. **Do not invent a stage** |

---

## 15 · LO-06 — how long an account has been sitting there, 2026-08-03

### What counts as activity? The question decided the whole slice

**Signora records workflow decisions. It cannot see a call, an email or a meeting.**

That single fact rules out almost every design a CRM would reach for. *"Stalled"*, *"neglected"*, *"at risk"*, *"no activity in 30 days"* — **every one of them is a claim the platform has no way to make**, and a seller who spoke to the customer yesterday would be told they had not, by a product that could not know.

> **So the product states the fact it owns and grades nothing.** *"Taken on 3 weeks ago."* The clock is real, checkable and the seller's own; what it means is the seller's to decide.

**This is the least-powerful-author rule applied to a sentence.** The database owns *when*; nobody owns *too long*.

### What resets it, and what deliberately does not

| | |
|---|---|
| **A workflow decision** | ✅ **The one act by a human that Signora can see** |
| **A new signal, a score move, a research run** | ⚫ **No.** That is *Signora* working, not the seller — and letting the platform's own activity reset the count would let it hide a seller's inactivity behind its own |
| **Ownership changing** | ✅ Already a workflow decision (LO-04). A hand-over restarts the clock for the person who now holds it, which is correct: Ravi has had it two days |

### No threshold, and that is a decision rather than an omission

A number at which an account becomes *too* old is a per-customer judgement — a 30-day cycle and a 6-month one are not the same product.

**The obvious home refused it, and its own docstring is the argument.** `OpportunityPolicy` is versioned *because every opportunity records the policy version that qualified it*; adding an unrelated setting there would mint a new policy version and churn the recorded explanation of every historical opportunity — **exactly the reasoning that kept qualification out of the scoring model.**

> **The threshold arrives with the thing that needs one**, which is a notification, and that needs M14a. Until then a threshold would be a number nothing acts on.

### Where it appears

| | |
|---|---|
| **The brief** | Folded into the holder clause — *"you took this on 3 weeks ago"* replaces *"you hold this"*, which was the same sentence on an account taken on this morning and one taken on in March. **Read from the last history entry**, not a new field: the entry *is* the current state, and a second copy of a derivable fact will eventually disagree with it |
| **The list** | `since` on the attention row — **already loaded**, because `_page` returns each opportunity beside its current state. The row has carried that state's `stage` and `owner_id` since M12.2 and left *when* behind |
| **A tracked account** | ⚫ Silent. Its age is *Signora's* suggestion ageing, which the brief already states and the evidence badge already grades |
| **A closed account** | ⚫ Silent. The clock stopped, and measuring it would report a duration that means nothing |

**`since` is not `opened_at`, and a test asserts both.** One says when Signora suggested this account, the other when a person last acted on it. Collapsing them would answer neither.

---

## 16 · LO-07 — a human can open an opportunity, 2026-08-03

### The finding it closes, and the one it closes *because* of that

**F-3.** `Qualification.MANUAL` has been in the domain since M12.1, is covered by a test called *"a human may open one the policy would decline"*, and is rendered on every brief as *"somebody here added it"*. **Nothing could produce one:** `QualifyOpportunity` had exactly one caller — the buying-score event handler — which never passes `opened_by`. **A string that could never appear.**

**F-2 follows from it.** A won deal is terminal, and correctly: *the next deal at that account is genuinely a new opportunity, and conflating them distorts every win-rate figure computed later.* But the recourse that sentence names **had no route into the product**, so *"I clicked the wrong row"* had no answer at all.

> **One endpoint closed both**, because the second was never a separate problem — it was the first one wearing a customer's clothes.

### What was already there, and what was actually missing

| | |
|---|---|
| **The use case** | ✅ `QualifyOpportunityInput` already took `opened_by` and `reason`, already bypassed the policy for a manual opening, already incremented `generation`, already refused a second open opportunity |
| **The domain** | ✅ `Qualification.MANUAL`, `Opportunity.created_by`, an opening state that names its actor |
| **The route** | ❌ **The only thing missing.** One `POST`, one composition dependency, two policy tuples |

**Nothing in the domain or the application layer changed.** The audit found the shape and the shape was correct; it had no door.

### Deliberately narrow, and the boundary is somebody else's

**This opens an opportunity on an account Signora already knows.** It does **not** create a company.

- **A company Signora has never heard of** is what [Target Accounts](../BACKLOG.md) is for — the customer declares it, and the pipeline discovers, scores and qualifies it. That declaration exists and works.
- **There is no entity browser or search**, so an account with no opportunity cannot be named by a seller anyway. Adding one would be a Knowledge Graph endpoint, and that is another bounded context.

**So the reachable case is exactly the one the audit found: a closed account, which is already navigable under *accounts already decided*.**

### Two things it refuses, and both are provenance

| | |
|---|---|
| **404 when the account has no score at all** | A manual opening bypasses the *policy* and never the *score*. **`why does this exist` has two halves**, and a human answering the first does not remove the second — an opportunity with no provenance is a record nobody could defend |
| **409 when one is already open** | The same account arriving twice, not an error the caller can fix |

### The mistake is preserved rather than erased

**There is no undo, and there will not be one.** A one-click undo would edit the past — the one thing this module refuses — and it would quietly remove a false win from a figure somebody may already have reported.

> **The closed deal keeps its history, its reason and its outcome. The new opportunity carries the sentence saying why it exists.** A test asserts the won deal is still on the decided list, unchanged, after the recovery.

### It opens at `tracking`, owned by nobody

A human opening an opportunity is **still a suggestion becoming a record**. Taking it on is a separate, deliberate act, and one that arrived already owned would collapse the distinction the module rests on.

### A finding this slice did not fix, and must not paper over

**`qualify_from_buying_score` is not subscribed in the production worker.** `apps/worker/subscriptions.py` registers two consumers — research and Timeline projections — so **no opportunity is opened automatically in a running deployment**; the score-to-opportunity chain runs only in `tests/pipeline.py`. That is the runtime-composition gap `make runtime-composition` already reports, and it belongs with the dispatch direction ([C-021](../LANE_COORDINATION.md)) rather than to this module.

**It makes manual opening more important, not less — and it is not a reason to pretend the pipeline works.**

### Playwright scenarios added

| # | Scenario |
|---|---|
| **P-13** | Win the wrong account → work it again → the win is still on the record |
| **P-14** | Open an account Signora scored below the threshold |
| **P-15** | Open one that is already open → told plainly, not duplicated |

---

## 17 · The walk, repeated — and why LO-08 stops, 2026-08-03

### The findings, re-checked against the shipped product

| | Finding | Then | Now |
|---|---|---|---|
| **F-1** | A stalled account looks identical to a fresh one | ⚠️ | ✅ **LO-06.** The list and the brief both say how long, and neither grades it |
| **F-2** | An accidental win is unrecoverable | 🔴 | ✅ **LO-07.** *Work this account again*, with the win left on the record |
| **F-3** | A human cannot open an opportunity | 🔴 | ✅ **LO-07.** `Qualification.MANUAL` is reachable, and names the person |
| **F-4** | No manager view | ⚠️ | ⚠️ **Open.** Needs a manager relationship, which is Team Management's to model |
| **F-5** | *"What changed since I was last here?"* | ⚠️ | ⚠️ **Open.** Per-user read state, the same as [TASK-016](../BACKLOG.md) |
| **F-6** | *"you have decided"* over a workspace query | ⚠️ | ✅ **LO-05** |
| **F-7** | A won brief offered nothing and explained nothing | ⚠️ | ✅ **LO-05**, and LO-07 gave it a way forward |

**Five of seven closed. Both survivors need a concept this module does not own**, and neither is a gap a lane may fill by inventing one.

### The lifecycle, walked again

| | |
|---|---|
| **Discovered → understood → owned → worked** | ✅ Coherent, explained, recoverable |
| **Worked → handed over → worked by somebody else** | ✅ LO-04, in both directions, with the trail naming both people |
| **Worked → sat on for a month** | ✅ LO-06 says so, and says only what it knows |
| **Won → realised it was the wrong account** | ✅ LO-07 |
| **Lost or dismissed → reopened** | ✅ Since M12.3 |
| **Returning after three months** | ⚠️ F-5 |
| **A manager asking where the team should focus** | ⚠️ F-4 |

### LO-08 — *waiting on somebody* — stops here, and this is the reasoning

**First principles, as asked, rather than a pipeline stage.** *"What am I waiting for?"* decomposes into four things, and only one of them exists:

| Part | Does Signora have it? |
|---|---|
| **Since when** | ✅ **LO-06** |
| **What** — a signature, a security review, a callback | ❌ Nothing models it |
| **From whom** — the customer, legal, our own team | ❌ Nothing models it |
| **Until when** — *"they said Friday"* | ❌ Nothing models it |

> **Waiting is not a state, a relationship or a timer. It is an *expectation*: a thing, owed by somebody, by a date.** Three of its four parts are facts a seller would have to *tell* Signora, and the product has **no note, no activity and no task** — it has decisions, and a decision is not an expectation.

**So LO-08 is not a lifecycle slice at all. It is the first activity model**, and that is a new concept with a real boundary question — is an expectation the Opportunity Engine's, or a note on the account that Timeline owns? **That is architectural pressure, and it stops.**

**What must not be built to fill the gap:**

| | |
|---|---|
| **A `waiting` stage** | ⚫ Every CRM that shipped one has a pipeline full of accounts stuck in it since March — somebody has to remember to leave, and nobody does |
| **`waiting_on` on the state row** | ⚫ A stage by another name, on an immutable snapshot, carried by every row that has no expectation |
| **Inferring it from silence** | ⚫ Silence is what LO-06 reports and refuses to interpret. *Waiting* and *forgotten* look identical from here, and they are opposites |

**The trigger is a customer describing one.** Not a request for *"a waiting stage"* — the words for what they are owed, from whom, and by when.

---

## 18 · LO-09 — the screen audit, 2026-08-03

**Every Lead Lifecycle surface walked as a seller rather than as its engineer**, asking one question of each: *does it answer what the reader came to ask, and does it hide anything?* Three surfaces failed, and one of the failures was **introduced two slices earlier by this lane**.

### The empty list lied, and LO-03 is what made it lie

**Filter to *Mine*, hold nothing, and the product said *"Nothing needs your attention."***

Twenty accounts may need attention. **None of them are yours.** The sentence is not merely unhelpful — it is *false*, and it is exactly the confident wrong answer this page's own comment says it refuses when the target declaration has not loaded.

> **An empty view is not an empty workspace**, and LO-03 made the two indistinguishable by adding a filter without teaching the empty state about it.

Each view now says what is actually true, and — the part that matters more — **offers the way back**. A dead end a reader arrived at *by clicking* is the one kind this surface must never leave them in.

| View | What it says |
|---|---|
| **All**, nothing declared | *"Signora does not know which companies to watch yet"* — unchanged |
| **All**, declared | *"Nothing needs your attention"* — unchanged, and now only said when it is true |
| **Mine** | *"You are not working any accounts"* · *other accounts may still need attention* · **Show everything** |
| **Unassigned** | *"Every account here has somebody on it"* · **Show everything** |

### The dialog never mentioned that a dismissal is recoverable

**The product built the recovery and told nobody at the moment it mattered.** The decided section exists precisely so a seller can find a dismissed account again — and a rep who does not know that will not dismiss anything, which is what a Sales Manager said out loud during R4-04: *"I'd tell my reps not to dismiss anything."*

> **A rep who will not dismiss produces no qualification-quality signal at all**, which is the one thing `dismissed` exists to capture. The sentence that makes the decision safe belongs on the dialog, not on the screen a reader reaches afterwards.

Every decision now states its consequence before it is committed:

| | |
|---|---|
| **Dismiss · Lost** | *"This leaves your list. You can find it again under the accounts you have already decided…"* |
| **Won** | *"…Won deals stay won — if the company comes back, that is a new opportunity."* |
| **Take it on** | *"This account will be assigned to you"* — unchanged, because the assignment *is* the consequence |

**A statement of consequence, never reassurance.** A win is told plainly that it does not come back, because that one genuinely is not recoverable and **pretending otherwise would be the more expensive kindness.**

### A judgement with no author

The decided row said **`· yours`**, meaning *you held it*. **An account nobody ever took on can still be dismissed** — dismissal is reachable straight from `tracking` — so on those rows the mark never appeared at all, and a colleague's judgement was anonymous on the one surface whose entire purpose is showing a customer a judgement back.

`decided_by` was **already loaded** — the state is read beside the opportunity — and simply left off the response, the same shape as `since` in LO-06 and `owner_id` in M12.2. The row now names the decider, which answers the question in strictly more cases and reads identically in the one `yours` covered.

### Surfaces that passed

| | |
|---|---|
| **The account brief** | Score, contributions, evidence, narration, research, validation, workflow, history — *why is this here* is the strongest thing the product does |
| **The decision history** | Reason-first, named, ordered as recorded, never re-sorted |
| **The account timeline** | Days, prominence, a reviewed catalog, and LO-04's hand-over correction |
| **Workflow controls** | Exactly `allowed_next`, plus the two controls that are deliberately not stage moves |
| **The decided section** | Absent rather than empty; closed by default; the customer's own words on the row |
| **Reopening** | Offered from the brief of any lost or dismissed account, with its own reason and actor |

### Five-year pressure recorded, not built

| Trigger | Pressure | Direction |
|---|---|---|
| **50 sellers** | *Mine* stops being the interesting filter; *my team's* starts | One more `OwnerScope` value once a manager relationship exists |
| **500 sellers · 50,000 accounts** | The attention list's ranking is global; nobody reads past the first screen | Territory or business-unit scoping **above** the filter, not another filter |
| **Territories · business units · regions** | Ownership stops being *a person* and becomes *a person within a boundary* | A scope on the workspace, not a second owner field |
| **Vacation coverage · temporary ownership** | LO-04 hands over permanently; coverage is a hand-over **with an end date** | The first genuine case for an expectation (§17) — **the same model** |
| **Shared ownership · account teams · overlay specialists** | One `owner_id` cannot express *two people, different roles* | A participation relation beside ownership; **`owner_id` stays** as *who is accountable* |
| **AI agents · auto-assignment** | *Intelligence suggests; humans commit* must survive | A suggestion **on the existing control**, never an owner written by a machine |
| **Enterprise approvals** | A decision becomes a request | Would put an approval state between intent and record — **the first real pressure on the stage table**, and worth resisting hard |
| **Partner · channel selling** | The owner is not a member of the workspace | Breaks the membership check LO-04 relies on; **needs an ADR before anything is built** |

**Every row is a note. None is a design.**

### Playwright scenarios added

| # | Scenario |
|---|---|
| **P-16** | Filter to *Mine* with nothing owned → understand why the list is empty → get back |
| **P-17** | Dismiss a first account, having been told it is recoverable → find it → track it again |
| **P-18** | A colleague's dismissal is attributable on the decided list |

---

# Part II · The ownership contract and handover, 2026-08-03

> **Written for a session that has never seen this module.** Under rotating assignment the next lane inherits this document, the ADRs and the commit messages — nothing else (`CLAUDE.md` §12). Everything below exists so nobody has to rediscover the reasoning.

## 19 · What Lead Lifecycle owns, and what it deliberately does not

### It owns

| | |
|---|---|
| **The opportunity aggregate** | Its identity, its generation, the score and policy that justified it, who opened it and when |
| **The workflow state sequence** | Append-only, one complete statement per row. **The status *is* the audit trail**, not something kept beside it |
| **The transition table** | Which stage may become which. Five stages, and the set is closed |
| **Ownership** | Who holds an account. Assignment, hand-over, take-over, and the membership check behind each |
| **Qualification policy** | The customer's threshold, versioned immutably, recorded on every opportunity |
| **Attention ordering** | Which open accounts a seller sees, and in what order |
| **`evidence_state`** | Derived at read time from the live score. **Never stored** |

### It deliberately does not own

| | Why, and who does |
|---|---|
| **What an account *is*** | Knowledge Graph. This module holds an `entity_id` and has never resolved a name |
| **The score** | Buying Score Engine, read through its published port and **never recomputed** — this module decides what to track, not how much anything matters |
| **Hypotheses and their names** | Signal Engine. The attention row carries a **catalog key and never a title**; its import contract forbids reaching that module at all |
| **What happened to an account** | Timeline, which projects this module's events. **One-directional: Timeline reads, this module never calls it** |
| **Who a person is** | Better Auth in the Next.js tier. The Python tier verifies tokens without learning who anybody is (ADR-0026). **Every name on screen comes from the roster at the frontend edge** |
| **Membership** | Workspace & Tenancy, through the one approved synchronous read. **No copy is kept** |
| **Activity, tasks, expectations, notes** | **Nothing owns them yet**, and this module must not start (§17) |
| **Manager relationships** | Team Management's, when it exists |
| **Which companies to watch** | Commercial Profile's Target Accounts |

> **The line that decides every future question: this module answers *what is the state of the work*, never *what is true about the company*.** A field that describes the account belongs upstream; a field that describes the work belongs here.

## 20 · Invariants this module protects

**Each is enforced by code and covered by a test. A future change that breaks one is a defect, not a trade-off.**

| | |
|---|---|
| **Intelligence suggests; humans commit** | `next_state` requires an `actor_id` with no default. **Only `TRACKING` may be machine-authored**, and only as an opening state |
| **Every state carries a reason** | A blank one is refused by the domain. *"Someone changed it"* is not an explanation |
| **Nothing is ever edited** | No `UPDATE` grant, no `UPDATE` policy, no repository method offering one. A change is a new row |
| **A state row that changes nothing is refused** | Noise in an audit trail is worse than a gap |
| **A won deal never reopens** | The next deal is genuinely a new opportunity, and conflating them distorts every win-rate figure computed later |
| **One open opportunity per account** | Enforced on creation; a lost race leaves exactly one |
| **An owner is a verified member** | Checked server-side on every assignment, never trusted from the request |
| **No derived intelligence is stored** | `evidence_state` is computed on read. A falling score cannot revoke a seller's commitment |
| **Ownership is not a stage** | A hand-over is a same-stage row with a different owner. **No `transferred` stage exists, and none may be added** |
| **Provenance always exists** | Every opportunity records the score and policy version that justified it — including a manual one |

## 21 · Contracts in and out

| Direction | What |
|---|---|
| **Publishes** | `opportunity.created` · `opportunity.stage_changed` (v1, transactional outbox, `workspace_id` + `correlation_id` + `causation_id`) |
| **Consumes** | `buying_score.updated` → `qualify_from_buying_score`. **⚠️ Not subscribed in the production worker** (§16) |
| **Reads synchronously** | `buying_score_engine.public` · `workspace_tenancy.public` — and nothing else, ever |
| **Read by** | `ai_reasoning_engine` · `ai_research_engine` · `ai_platform` — all through `public/`, all read-only |
| **Projected by** | Timeline, from the two events above. **It reads; this module never calls it** |
| **Depended on by the frontend** | The attention list, the account brief, the decided section, the workflow controls |

> **`opportunity.stage_changed` carries a hand-over with `previous_stage == new_stage`.** Any future consumer must handle that; the name predates the capability. **Renaming it is a breaking change and is not worth it** — the payload has always described state rather than a delta.

## 22 · Five users, walked

### Seller
**Morning** ✅ the ranked list, the reason, the score movement. **Lunch** ✅ decide, and be offered the next account *within the view they were working*. **End of day** ✅ *Taken on 3 weeks ago* answers *what have I been sitting on*. **Vacation** ✅ hand over, with a reason, in one act. **Returning after two weeks** ⚠️ **F-5** — everything is there and nothing says what moved while they were gone.

### Sales Manager
**Sees**: every account, who holds each, how long, every judgement and its author. **Does not see**: workload across the team, ownership distribution, aging as a *set*, decision consistency. **Should care about**: all four. ⚠️ **F-4** — the data exists on every row; **no screen aggregates it**, and aggregating needs a manager relationship to know whose accounts are *theirs*.

### Organization Owner
**Pipeline** ✅ readable account by account. **Workload** ❌ not without F-4. **Accountability** ✅ **the strongest answer in the product** — every decision names a person, a reason and a time, and nothing can be edited afterwards.

### New employee
✅ **The vocabulary is the customer's** (ADR-0034) and every stage is spelled out on the brief. The decision history reads from `sequence 0`, so six months of context arrives without asking anybody. **The one thing that needs explaining is `dismissed` vs `lost`** — and the dialog now asks the distinguishing question rather than a generic *Reason*.

### Enterprise customer
✅ Append-only history · server-side authorization · tenant isolation · a reason on every act · **an immutable record of a mistake rather than a quiet correction**. ⚠️ Would ask for: manager reporting, bulk reassignment, SLAs, approvals. **All four are recorded as pressure and none is built.**

## 23 · What happens if — the pressure test

| | |
|---|---|
| **I click twice** | The confirm disables on `isPending`. The domain refuses a second identical row anyway — **two defences, one of which is the database's** |
| **My browser refreshes mid-decision** | Nothing is optimistic. **The screen is never briefly wrong** |
| **The API is slow** | The dialog stays open and disabled; the list shows skeletons. ⚠️ **No timeout wording** — a 30-second request looks the same as a stuck one |
| **The owner leaves** | ⚠️ **Their accounts stay assigned to a departed membership.** LO-04 makes reassignment possible; **nothing surfaces the need for it.** A trigger, not a defect |
| **Ownership changes while I am reading** | My decision uses the id I loaded. The server refuses nothing — **last write wins, and the trail shows both.** Correct for a sales team, and deliberate |
| **A score changes while I am reading** | The brief shows *then* beside *now*; a moved score never alters a commitment |
| **Two people decide at once** | Both rows land, in order, each naming its actor. **No lock, and none wanted** |
| **A decision arrives from AI** | Structurally impossible: `next_state` demands an `actor_id` |
| **The account disappears upstream** | ⚠️ **Untested.** The opportunity survives; the name resolves to nothing and `EntityName` falls back. **Worth a test** |
| **The ICP or buying committee changes** | No effect. **Opportunities outlive the score that created them**, which is the module's founding decision |
| **Signals disappear** | The score expires, `evidence_state` reads `stale`, the opportunity stays open. **Signora never closes anything** |
| **A CRM sync changes ownership** | ❌ **No CRM sync exists.** When it does, it must arrive through this module's endpoint as a named actor — **never a direct write** |
| **The company merges, splits, or duplicates** | ❌ Knowledge Graph's identity problem. **Two entities means two opportunities, and this module cannot tell** |
| **50,000 accounts imported** | The list is cursor-paginated and ordered server-side ✅. **The ranking is global** — see §18 |

## 24 · Explainability, audited

| Question | Answer |
|---|---|
| **Why did this become an opportunity?** | ✅ The score, the policy version, the contributions, the evidence |
| **Why am I the owner?** | ✅ The decision history names who assigned it and why |
| **Why did ownership change?** | ✅ LO-04, in both directions, with the reason leading |
| **Why is this score lower?** | ✅ Contributions and the evidence drawer |
| **Why is this ranked higher?** | ✅ Score, contested state, and the trigger |
| **Why was this reopened?** | ✅ Its own reason and actor |
| **Why can't I do this?** | ✅ **Only on a won deal**, which is now stated — and it is the only place the product refuses something |
| **Why is this disabled?** | ⚠️ **The confirm button disables silently** on an empty reason and an unnamed assignee. A reader who has not noticed the field gets no explanation |
| **Why am I waiting?** | ⛔ §17 |
| **Why isn't this happening?** | ⚠️ **The weakest answer in the product**, and not this module's: `qualify_from_buying_score` is unsubscribed, so *"why has no opportunity appeared?"* has no answer anywhere |

## 25 · Premium experience — observations, not work

**Recorded rather than built.** None is a defect; each is where the product would feel more considered.

| | |
|---|---|
| **A disabled confirm says nothing** | The one *"why is this disabled?"* the product does not answer. **The smallest premium win available** |
| **No bulk anything** | Thirty hand-overs after one departure. **Correctly unbuilt** until somebody is watched doing it slowly |
| **Filters are not saved, recent or pinned** | Three views is few enough that saving is premature; **the trigger is a fourth** |
| **No keyboard path through the list** | `j`/`k`/`enter` is the shape a daily triage surface eventually wants |
| **No undo anywhere** | **Deliberate.** Every recovery is a recorded act with a reason, which is the module's central claim |
| **Nothing animates** | Calm by default. A decision landing without any acknowledgement is the one place a small transition would help |
| **Context is preserved** | The scope rides the account link (LO-03) and *next* stays inside the filtered list (D41). ✅ **Already right** |

## 26 · Repository reuse — the rule of three, applied to this milestone

**Everything introduced, checked for a third consumer.**

| Introduced | Consumers | Verdict |
|---|---|---|
| `components/team/people.ts` | **Four** — the picker, the workflow line, the decision history, the decided row | ✅ **Already extracted, and this milestone is why**. Two would have been a coincidence |
| `lib/state/owner-scope.ts` | **Two** — the list, the brief | **Leave it.** It exists to stop the two disagreeing, not because a third asked |
| `HeldSince` | One | **Leave it** |
| `CONSEQUENCE` / `STAGE_PAST` / `ACTION_WORDING` | One each, and **deliberately separate** | **Never merge.** They are the same stage in four different sentences, and one shared table would force a wording change in four places at once |
| `Choice` (stage + handover) | One | **Leave it** |
| `movement()` in the decision history | One | **Leave it.** Timeline's feed answers a different question and names nobody |
| `nameOf` fallbacks | Four | ✅ Extracted |

> **Nothing else qualifies.** Three history-rendering surfaces now exist — organization history, decision history, account timeline — and **they still must not share a framework**: one names two people, one names one, one names nobody. **The differences are structural, not cosmetic**, which is precisely the case where a shared abstraction costs more than it saves.

## 27 · AI pressure — where it inserts, and where it must not

| Tomorrow | Insertion point | Cost |
|---|---|---|
| **AI recommends an owner** | The hand-over picker gains a suggested row | **None.** `Choice` already separates the act from the stage, and the actor is still the human who confirms |
| **AI recommends the next action** | Beside `allowed_next`, never inside it | **None**, provided the recommendation cannot *become* a state |
| **AI recommends reassignment** | Same as the first | **None** |
| **AI explains a recommendation** | The brief already renders narration beside evidence | **None** |
| **AI records a decision** | ⛔ **Structurally impossible, and must stay so.** `next_state` demands an `actor_id`; only `TRACKING` may be machine-authored |

> **No redesign is required for any of them**, and that is not luck: *intelligence suggests, humans commit* was expressed in the **type system** rather than in a convention, so the boundary holds without anybody defending it.

## 28 · Enterprise pressure — recorded, not designed

| Scale | What breaks first |
|---|---|
| **1 → 10 sellers** | Nothing |
| **100** | *Mine* stops being interesting; *my team's* starts. **F-4** |
| **500** | Global ranking. Needs scoping **above** the filter, not another filter |
| **5,000** | The attention list stops being a list and becomes a queue with assignment rules |
| **Territories · regions · business units** | Ownership becomes *a person within a boundary*. **A scope on the workspace, not a second owner field** |
| **Partners · resellers · channel** | **The owner is not a member.** Breaks the membership check LO-04 depends on — **needs an ADR before any code** |
| **Multi-owner · account teams · overlay** | One `owner_id` cannot express *two people, two roles*. **A participation relation beside ownership; `owner_id` stays as who is accountable** |
| **Temporary · vacation · assistant ownership** | A hand-over **with an end date** — the same expectation model §17 stopped on |
| **Emergency reassignment** | Bulk, plus a reason applied once |
| **Acquisitions · subsidiaries · cross-workspace** | ⛔ **Tenancy, not workflow.** RLS is the isolation boundary; cross-workspace selling would reopen it, and that is a platform decision |

## 29 · Handover package

### Functional summary
**A seller discovers an account Signora surfaced, understands why, takes it on, works it, hands it over or takes it over, decides an outcome, and recovers from every mistake except a win — which is explained rather than hidden.** Every act names a person, carries a reason, and cannot be edited afterwards.

### Customer journeys — the Playwright specification

| # | Journey | Status |
|---|---|---|
| **P-1** | Discover → understand → take on → work → win | Specified |
| **P-2** | Discover → take on → lose → reopen → win | Specified |
| **P-3** | Dismiss → find it under *already decided* → reopen | Specified |
| **P-4** | Hand over mid-work; the colleague sees it as theirs | Specified |
| **P-5** | Take over an account somebody else holds | Specified |
| **P-6** | Filter to *Mine*, decide, be offered the next **of mine** | Specified |
| **P-7** | Refresh mid-hand-over; nothing half-applied | Specified |
| **P-8** | Two tabs hand the same account to different people | Specified |
| **P-9** | A role changes while a dialog is open | Specified |
| **P-10** | Return after a week and understand what happened | **Written to fail** — F-5 |
| **P-11** | Open a won account and understand why nothing can be done | Specified |
| **P-12** | Six months of history read by somebody who just joined | Specified |
| **P-13** | Win the wrong account → work it again → the win is still recorded | Specified |
| **P-14** | Open an account scored below the threshold | Specified |
| **P-15** | Open one already open → told plainly, not duplicated | Specified |
| **P-16** | Filter to *Mine* with nothing owned → understand → get back | Specified |
| **P-17** | Dismiss, having been told it is recoverable → find it → track it again | Specified |
| **P-18** | A colleague's dismissal is attributable | Specified |

### QE validation checklist
**Tenancy** — every query workspace-scoped; an opportunity from another workspace is a 404, never a 403 · **Authorization** — `opportunity:read/add/update` enforced before application code · **Immutability** — no `UPDATE` grant on `opportunity_state`; a mutation attempt fails · **Reason** — every state has one; a blank is refused · **Actor** — every non-opening state names one · **Membership** — an owner outside the workspace is refused · **Won terminality** — `closed_won` offers no transition, and the manual route creates a *new* opportunity rather than editing it · **Pagination** — the owner filter is applied before the limit; a filtered page is a full page · **Vocabulary** — no screen says workspace, tenant, entity, stage enum or identifier.

### Regression checklist
The five stages and their transitions · the opening state names nobody on an automatic qualification and names a person on a manual one · a hand-over does not move the stage · the trail reads ownership pairwise · the clock resets only on a workflow decision · `since` and `opened_at` move independently · the empty states differ by scope · every consequence sentence matches what the transition actually does.

### Known limitations
**F-4** no manager view · **F-5** no *since you were last here* · no entity search, so manual opening is reachable only for closed accounts · no release-to-nobody (`owner_id: null` means *unchanged*) · no bulk anything · no *waiting* (§17) · **`qualify_from_buying_score` is unsubscribed in production**.

### Future milestones that will extend this
Manager workflows (needs a manager relationship) · notifications (M14a) · the expectation model (§17) · CRM sync (must arrive through the endpoint as a named actor) · forecasting (close date and amount, deliberately absent).

### What must never be modified directly
**The transition table** without an ADR · **the actor requirement** on `next_state` · **the immutability of `opportunity_state`** · **`evidence_state` becoming stored** · **any write to this module's tables from another module** · **a fifth stage for anything that is an event.**
