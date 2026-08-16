# Lane C — Operating Mode

**The first document a Lane C session reads, and the only one it reads unconditionally.**
Created 2026-08-12 on the product owner's directive, after repeated context exhaustion mid-investigation.

> **Conversation context is temporary. Repository state is persistent.**
>
> A Lane C session must never depend on remembering what a previous session discovered. If a finding, ruling, mapping, audit result or design authority matters for future work, **it lives in a register — not in a transcript.**

⛔ **This document is a navigation layer. It restates no rule and no design.** [`CLAUDE.md`](../../../CLAUDE.md) is the repository's operating system; [`PRODUCT_OFFICE.md`](../../PRODUCT_OFFICE.md) is Lane C's method. **Both remain authoritative and neither is summarised here.**

---

## 1 · Responsibilities

**Lane C governs · audits · reviews · prepares decisions · decomposes workflows · creates and routes tasks · reviews architecture · maintains coordination integrity.** Plus **Platform Foundation** ([D-022](../../DECISION_REGISTER.md)) — `infra/`, the `Makefile`, environment tooling, `signora_platform/simulation/`.

**Lane C must not:**

- ⛔ **implement product surface work** — that is Lane A's, always, unless governance explicitly says otherwise;
- ⛔ **duplicate an existing task.** Three duplicates landed in three days (TASK-1459, TASK-1472, TASK-206). **Read the actual row before writing a new one**;
- ⛔ **invent a design requirement**, or **treat existing implementation as design authority** ([D-138](../../DECISION_REGISTER.md));
- ⛔ **mark its own work verified** where governance names another lane — QE verifies; **Lane C may not verify governance it authored**;
- ⛔ **close a decision because closing it unblocks Lane C**;
- ⛔ **assert runtime behaviour without runtime evidence.** *A contract that exists and a contract that is callable are different findings* — this office has confused them twice;
- ⛔ **treat conversation history as state.**

## 2 · Authority hierarchy

**Recorded, not invented.** Each row names where the rule already lives.

| Rank | Authority | Where |
|---|---|---|
| 1 | **Product owner rulings** | [`DECISION_REGISTER.md`](../../DECISION_REGISTER.md) |
| 2 | **Governance** | [`CLAUDE.md`](../../../CLAUDE.md) · [`ENGINEERING_LAWS.md`](../../../ENGINEERING_LAWS.md) |
| 3 | **Architecture + ratified ADRs** | [`docs/architecture/`](../../architecture/) `01`–`21`, `adr/` |
| 4 | **Design** | [`design-snapshot/`](../../design-snapshot/MANIFEST.md) — see [DESIGN-AUTHORITY-INDEX.md](DESIGN-AUTHORITY-INDEX.md) |
| 5 | **Module designs** | `docs/architecture/22`–`29`, `33` |
| 6 | **Registers** | `BACKLOG` (scope) · `modules.toml` (ownership) · `LANE_COORDINATION` (dependencies) |
| — | **Projections — never authority** | `coordination.toml` · `queues/*.toml`. ⚠️ **If a projection disagrees with its source, the source wins and the disagreement is a defect** |

## 3 · Session modes — declare one, and do not combine

| | Mode | Loads |
|---|---|---|
| **A** | **Governance / PO decisions** | `LANE_COORDINATION` · `DECISION_REGISTER` · `CLAUDE.md` |
| **B** | **Design audit** | One design document, named sections only · the components it governs |
| **C** | **Workflow decomposition** | `workflows.toml` · that workflow's design document · its `BACKLOG` rows |
| **D** | **Architecture review** | `docs/architecture/` · ADRs · `modules.toml` |
| **E** | **Coordination / queue hygiene** | `BACKLOG` · queues · `state-check` · `coordination.py` |
| **F** | **Routine maintenance** | Whatever the mechanical task names |

## 4 · Every session declares its bounds, before loading anything

```
SESSION OBJECTIVE     one sentence
MODE                  A–F
SCOPE                 exactly what is in it
AUTHORITATIVE SOURCES the documents that decide
EXPECTED OUTPUT       the artifact this session leaves behind
OUT OF SCOPE          named, so the boundary is checkable
```

⛔ **When the objective is complete, stop.** Do not expand into an adjacent audit because it is visible.

## 5 · Loading rules

**Load first, always:** this document · [CURRENT-STATE.md](CURRENT-STATE.md) · [DESIGN-AUTHORITY-INDEX.md](DESIGN-AUTHORITY-INDEX.md).

⛔ **Never load by default:** every ADR · every design document · every audit · `PRODUCT_OFFICE.md` in full (**158 KB**) · `SESSION_HANDOFF.md` (**107 KB**, and it is QE's) · `BACKLOG.md` in full (**189 rows**). **Open a section when the objective requires that section.**

## 5a · Output budget — ⚠️ the constraint that actually binds

**Added 2026-08-12, same day as this file, after a session exhausted context having loaded almost nothing.** ⛔ **§5's loading rules were not the binding constraint. Lane C's own output was.**

> **Everything Lane C writes, it then carries.** A 700-word peer message costs context twice — once to compose, once for the rest of the session.

| | Budget |
|---|---|
| **Peer message (QE, Lane A)** | ⛔ **Under 150 words.** State the finding, name the evidence, stop. **Agreement needs one line, not a paragraph explaining why you agree** |
| **Report to the product owner** | **One screen.** The [Standard Lane Report](../../../CLAUDE.md) block plus the decision. ⛔ **Detail goes in the register and is linked** |
| **Commit message** | ✅ **Unbudgeted.** This is where reasoning belongs — it is written once, carried never, and travels with the change forever |
| **Reading** | ⛔ **Extract the field, not the section.** `grep` the `Status` line; do not read 3,000 characters to find it |

⚡ **The asymmetry is the whole rule: the repository is free to write to and expensive to talk about.** ⛔ **A finding explained in chat and not committed is a finding that dies with the session.**

## 5b · Handoff and resumption

⛔ **A conversation summary is not a handoff.** A summary narrates what happened; **it arrives as thousands of words of history and reconstructs nothing the repository could not have answered.**

✅ **On resuming, read [CURRENT-STATE.md](CURRENT-STATE.md) and treat any inherited narrative as untrusted.** ⚠️ **It reflects what was believed then** — this session inherited three stale blocker attributions from one, and corrected all three against the rows.

## 5c · Before writing a check, ask what it would report on a real problem

**Recorded 2026-08-12 at QE's suggestion, from an exchange where a guard was the obvious answer and the wrong one.** ⛔ **Not a rule. The sentence a future session will need when it is tempted.**

> **Adding a check would let the contradiction persist behind a green output.**

📁 **[§2](../../../CLAUDE.md) already covers the guard that *cannot* fail.** ⚠️ **This is the other half: a guard that can fail, does fire correctly, and is still wrong** — because it answers a narrower question than the reader believes.

**The worked case:** `--audit-claims` reported *"0 claims awaiting promotion"* on a ref carrying **ten unvalidated commits**. ✅ **The check was correct** — it audits commits whose subject begins `Claim `. ⛔ **B-182 and B-184 are the same family**, which QE named as *"correct about a fact and wrong about whether the fact was a problem."*

⚡ **And the deeper reason a third one would have been worse than none: the condition had an owner.** **Lane A said the slice was not ready; it was on the ref QE certifies from. One of those statements was wrong and only Lane A could say which.** ⛔ **A check cannot resolve a contradiction between two people's claims — it can only make the repository look like it has.**

**The test before building one: *if this check goes green, what will the reader stop asking?*** ⚠️ **If the answer is the actual question, the check is the problem.**

### 🔴 The mutation is under test too — 2026-08-15, QE, from their own near-miss

> ## **Read what the failure says, not that there was one.**

⛔ **QE fire-tested a canonicalisation guard by substituting a name that does not exist. `pytest` printed `Interrupted: 1 error during collection` — `1 error in 0.27s`.** ⚠️ **A red-looking result, which is exactly what a fire test is supposed to produce, and they were one glance from recording it as a pass.**

🔴 **So a BROKEN MUTATION and a WORKING GUARD produce the same colour.** ⚡ **A neuter that fails to import is not a neuter.** ✅ **Their second attempt was a real pass-through and it fired properly.**

📁 **This is [§5g-2](#5g-2--report-a-sha-from-the-shared-ref-never-from-the-one-you-control)'s *absence was the finding* with the sign flipped:** **there the missing output was the signal; here the PRESENT output was the wrong one.** ⛔ **And QE's own framing of it, which is less comfortable than mine: they did not discover this — they made the mistake and the tooling told them, and what is worth keeping is that they almost did not read it.**

### ⚠️ Two from the same slice, both Lane A's

> ## **`json.loads(a) == json.loads(b)` is TRUE of two strings whose keys differ in order.**

⛔ **A vendor-agreement test looked like it compared two vendors' output and actually compared two parse trees.** 📁 **The same shape as *an authorization test where every subject holds the grant* — one module over, same lane, same week.**

> ## **A fixture written in the canonical form makes a canonicalisation guard untestable.**

**The byte-identical test PASSED with the re-serialisation removed, because the fixture happened to be canonical.** ✅ **Lane A's repair is the part worth copying: the fixture's spacing is now deliberately NON-canonical, with an in-place comment forbidding tidying** — **so the next person to "clean up" that string meets the warning where they are standing.**

📁 **Same reason [B-270](../../BUGS.md) carries *"`make -n` shows what the parent sets"* beside the measurement rather than in its correction block.** ⚡ **QE's sentence: *a warning in a register is read by somebody looking for it; a warning in the file is read by the person about to break it.***

### ⚡ When a guard's output is advice, the advice is under test — not just the refusal

**Recorded 2026-08-15, QE's wording, from `refuse-slot-0` in the `Makefile`.**

🔴 **The guard fired correctly and told the reader to run `make $@ ALLOW_SLOT_0=1`. `$@` there is the PREREQUISITE — `refuse-slot-0` — not the target the person actually ran**, so the instruction expanded to a command that does nothing.

⛔ **A green fire test would have confirmed the guard fires and said nothing about whether its instruction works.** ⚡ **And for a refusal, the instruction IS the product** — a guard that stops somebody and then misdirects them has spent its whole budget and delivered nothing.

✅ **Caught by reading the fire test's OUTPUT rather than its exit code.** 📁 **Same family as [§5g-2](#5g-2--report-a-sha-from-the-shared-ref-never-from-the-one-you-control)** — the exit code was the operand that did not matter.

> ⚠️ **The other half of that guard, worth keeping because the shape recurs:** **`demo-seed` against slot 0 is exactly what a reviewer wants and exactly what a lane must never do, and nothing in the environment distinguishes them.** ⛔ **Blocking unconditionally breaks the legitimate use; skipping silently is Decorative Logic.** ✅ **`ALLOW_SLOT_0=1` makes the human state which of two indistinguishable intents they have, at the moment the two diverge** — 📁 **[§2](../../../CLAUDE.md)'s *hidden inputs are architecture defects*, solved by making the input explicit rather than by inferring it.**

⚡ **And the test cuts both ways — added 2026-08-12 after QE applied it to themselves and it came out the other way.** ✅ **Where the reader SHOULD stop asking, and the check genuinely answers it, the check earns its place and gets built.** ⛔ **A note that only ever argues against building is not a test; it is a preference.**

📁 **QE's worked pair, and the asymmetry is the sharper half:**

| | |
|---|---|
| **This office's stale header** | **No checker.** ⚠️ **An absent check leaves a reader uncertain** |
| **QE's stale dashboards** | 🔴 **A checker that passed.** ⛔ **`_is_ancestor(named, HEAD)` fires only on a commit that never merged, so it cannot detect staleness at all** — **and staleness is the condition [§20d](../../../CLAUDE.md) cares about** ([B-195](../../BUGS.md)) |

⛔ **A green check leaves the reader confident and wrong**, ⚡ **and that — not fourteen cycles versus two — is what made QE's instance the worse of the two.**

### ⚠️ And once it is built, reproduce against the real past tree — never a synthetic one

**Added 2026-08-12 from QE's [B-195](../../BUGS.md) build, and it nearly went the other way.**

⛔ **A synthetic revert of the three stale records did not reproduce the bug.** **It left the promoted SHA in `PROJECT_STATUS.md`'s release-summary appendix — a dated record, legitimately there — so an older rule fired first and masked the new predicate.** 🔴 **A red line would have appeared, the check would have looked proven, and the shipped predicate would have done nothing.**

✅ **`git checkout <the stale cycle's commit> -- <the records>` fires; with the records current it is silent.** ⚡ **The generalisation is this office's own arriving from an unexpected direction: *read the artifact, not the report about it* — including when the artifact is a past state of the repository and the report is a reconstruction of it.**

⚠️ **A third direction, 2026-08-13, and it is the one where being wrong was destructive rather than merely misleading.** ⛔ **QE ran its required patch-id survival check before a force-push and it printed *"everything survives"* — against a stale `origin/integration`, fetched afterwards.** 🔴 **True of the ref compared against, false of the repository, and eleven commits were one push away.** ⚡ **A stale ref is a report about the repository, not the repository.** ⛔ **A verification against a stale operand is not a weaker verification — it is a confident wrong answer guarding a destructive operation**, ✅ **which is the green-output half of the asymmetry above, one level up.**

## 5d · After a rebase, re-derive the queue array. Never trust either hunk.

**Recorded 2026-08-13 after it happened twice in two days, in the same file.** ⛔ **A recurrence worth writing down rather than re-diagnosing each time.**

> **`queues/lane-a.toml`'s `backlog` array and the comment explaining it are separate hunks. A clean rebase can keep the comment and drop the array.**

⚠️ **Mechanism corrected 2026-08-13, third occurrence, and the first two diagnoses were incomplete.** ⛔ **The array is not hand-maintained: `infra/coordination.py` WRITES it.** ⚡ **So after a rebase the committed array is whatever the replayed commits left, and it is stale until the generator runs — which is why *re-derive* is the fix and *restore my version* never was.** ✅ **The prescription below was right for a reason I had not measured; the diagnosis above described the symptom.**

🔴 **Both times the file was left describing a change it no longer carried** — ⚠️ **which is worse than losing the change outright, because the comment is what the next reader believes.** ⚡ **It is the half-landing shape in a different medium: the thing that describes the change survives and the change does not.**

⛔ **A `git rebase` reporting success is a report, not the artifact.** ✅ **Read the array back every time.**

**And do not re-derive it by reading `BACKLOG.md` by hand.** 🔴 **A first-token match on a `Status` cell reported `TASK-466` and `TASK-1416` as `PROMOTED` when they were live** — **these rows carry claim and promotion history in ADDITIONAL table rows, so the first state token found is often a historical one.** ⛔ **Acting on it would have removed two claimable rows from the lane's queue.**

✅ **`python3 infra/coordination.py` resolves the claimable set and names it. Use it.** ✅ **Then let `state-check` judge the result — *"queues X as executable; somebody holds it"* is the check that fires if held work was queued.**

⛔ **No guard is proposed, and §5c's test is why:** **a reader would stop asking whether the array matched its comment, and only re-derivation actually answers that.**

## 5e · A row has one `Status` cell. Stack history under a different label.

**Recorded 2026-08-13, after three rows declared their state two or three times.**

⛔ **Prepending a terminal state is right and preserves history** ([§2](../../../CLAUDE.md)). ⛔ **Leaving the earlier cell labelled `Status` is not** — **the row then answers the state question more than once, and every reader takes the first.**

🔴 **Measured: four call sites parse that cell, and all four take the first match.** 📁 **[`state-check.py`](../../../infra/state-check.py):1151 and :1339 · [`pipeline-dashboard.py`](../../../infra/pipeline-dashboard.py):67 · [`registers.py`](../../../infra/registers.py):87.** ⚡ **So a stacked cell does not merely trip a checker — it changes what four independent readers answer, and it does so silently.**

✅ **The fix is a label, never a deletion:** `📁 **Earlier state — not the row's status**`. **History intact, one `Status` per row.**

⚠️ **The test that separates this from silencing a check**, and QE applied it rather than taking the claim: **re-add one genuine second `Status` row and confirm the check still fires.** ⛔ **A relabel that also stops the check catching a real duplicate has hidden the defect rather than removed it.**

## 5f · An author cannot see the narrowness of their own predicate

**Named by QE, 2026-08-13, after four in one day. ⛔ Not a rule — the reason a second reader is worth the round trip.**

> **A check answers the question its author asked. The failure is that the question was narrower than the one they believed they were asking — and the author is the one person who cannot see the gap, because they wrote both halves to match.**

📁 **Four instances, one day, and every one was found by somebody other than its author:**

| | The narrow question | The real one |
|---|---|---|
| **B-433**, mine | *"does the `Module` cell differ?"* | *"is the row synchronized?"* |
| **QE's degeneracy predicate** | *"is the key empty?"* | *"can two records that should be distinct share it?"* — **6 of 8 became 7 of 8** |
| **Lane A's password check** · **QE's redaction probe** | — | — |
| **QE's disjointness measurement** | *"do the vocabularies intersect?"* — **against the PRE-FIX enum** | **against the ratified one, and the answer is `{demo}` rather than empty** |

⚡ **The fourth is the one this office caught, and only because it was about to put the claim in front of the product owner.** ✅ **`grep`ping the enum took one command; accepting *"intersection EMPTY"* would have cost a ruling made on a false premise.**

⛔ **The practice, and it is cheap: re-measure any figure you are about to relay into a decision, especially one you agree with.** ⚠️ **Agreement is when this fails — a number that confirms what you already believe is the one nobody re-runs.**

### ⚠️ And a comparison has TWO operands. Read both.

**Added on QE's own account of how the disjointness measurement went wrong, which is a different failure from the one above.**

⛔ **The evidence was gathered correctly.** 📁 **QE's terminal printed `BY_NAME` containing `demo` in the same output where it concluded the intersection was empty.** 🔴 **What was wrong was the OTHER set — `development · test · production · production-local`, assembled from a compose file, a lane's prose and an assumption, and never read from [`environment.py`](../../../backend/signora_platform/environment.py).**

⚡ **So *read the artifact, not the report about it* has a second half nobody states: a comparison has two operands, and it is the one you are not investigating that gets remembered instead of read.** ⛔ **The same shape as a survival check run against a stale ref — a correct operation on an operand that was assembled rather than fetched.**

📁 **The detail that makes it worth recording: `development` is the member [ADR-0412](../../architecture/adr/0412-environment-and-secret-safe-logging.md) deliberately REMOVED**, and the ADR's own reason is *"two spellings of one environment is how a guard comes to be written against the spelling somebody happened to use."* ⚠️ **The analysis was written against the spelling somebody happened to use.**

### 🔴 A repair has a scope, and nothing in the repair asks what it is — 2026-08-15

> ## **When you fix an instance, ask where else the class occurs — in the same commit.**

⛔ **Three instances on one day, and each was a correct repair with a scope of one:**

| | the repair | what it missed |
|---|---|---|
| **Lane C** | removed `TASK-1432`'s stale `[[blocked]]` entry, **and wrote a comment explaining why a stale block gives a lane two answers** | ⛔ **Did not sweep the file. `TASK-1401`'s was found by QE hours later, hiding the row released to fix Lane A's floor** |
| **QE** | wrote a script to split a count | ⛔ **Re-expressed `_is_closeout` instead of calling it, and published the wrong figure** |
| **QE** | measured the cost of B-1005 | ⛔ **Counted a narrower predicate than the row needed** |

⚠️ **The tell is that nothing about a correct repair prompts the question.** ⚡ **It works, the instance is gone, and *"where else?"* has to be asked deliberately** — which is why it belongs in the commit rather than in a later sweep.

✅ **And the sweep is only evidence if its result is reported either way.** 📁 **All four `[[blocked]]` entries were checked and three were correct — `TASK-1426` on a genuine missing design, `TASK-422` and `TASK-1434` correctly sequenced.** ⛔ **A sweep that reports only what it found is indistinguishable from one that stopped early.**

📁 **Same family as [§5f](#5f--an-author-cannot-see-the-narrowness-of-their-own-predicate)**, and the harder half: **there the predicate was too narrow; here the predicate was right and applied once.**

### ⚡ Lane A's rule for finding a closed set — 2026-08-15, adopted by QE the same hour

> ## **Grep for an existing MEMBER, never for the type.**
> **A type appears wherever the vocabulary is USED. A member appears wherever it is ENUMERATED.**

**Found implementing `TASK-1477`**: three new `ClaimAttribute` members were added and classified in none of the places that enumerate them, and a Security Invariant caught it — *"a silent default is how a new canonical attribute acquires observation behaviour nobody chose."*

⚡ **It is the operational form of [§5f](#5f--an-author-cannot-see-the-narrowness-of-their-own-predicate).** ⛔ **Searching for `ClaimAttribute` returns every consumer and drowns the four registries; searching for `RENEWAL_DATE` returns exactly the places a new member must also appear.**

📁 **QE adopted it against a gap they had already hit without recognising it: `REQUIRED_GATES` is a closed set whose *runner* lives in a different file, and they found that by reasoning where one member-search would have shown it in a line.**

⚠️ **And the second half of Lane A's finding is the better half: they argued `RENEWAL_DATE` should be `STATE` — *"the date is the VALUE, not the moment of assertion"* — flipped it to `OCCURRENCE`, and two `occurrence_key` tests failed, because a bare date identifies no occurrence.** ✅ **The wrong classification was UNREPRESENTABLE rather than merely wrong** — 📁 [§2](../../../CLAUDE.md), *types should make incorrect architecture impossible*. **Their sentence: *"I would not have known that from reading; the guard told me."***

## 5f-2 · One instance of an output does not tell you the rule that produced it

**Recorded 2026-08-14, from a wrong claim this office made to the product owner.**

🔴 **`TASK-479` was absent from the generated projection. Its `Status` read `DISPOSED`, a token this office had not seen.** ⛔ **I connected the two and reported *"a state token no tool recognises, so the row is invisible to every reader that parses state."***

✅ **Lane A measured instead of reasoning.** 📁 **`coordination.py`:64 — `_CLOSED = frozenset({"DONE", "DISPOSED", "PROMOTED"})`, applied at `:481`; [`state-check.py`](../../../infra/state-check.py) carries it in four places.** ⚡ **`DISPOSED` is recognised everywhere and deliberately filtered.**

🔴 **And the population settles it: the projection omits 137 of 198 rows, almost all `PROMOTED`.** ⛔ **`TASK-479` is absent for the same reason `TASK-466` is.** **I had one data point and inferred a rule from it.**

⚠️ **The failure mode I warned about is impossible by construction, which I would have seen by reading the set rather than the symptom**: **`_CLOSED` is an ALLOW-LIST, so a typo'd state falls through to classification and APPEARS.** ⛔ **An unknown state is never dropped.**

> **The question was never *why is this row absent*. It was *what governs absence, and how many rows does it govern?*** ⚡ **One is a symptom; the other is the rule.**

📁 **Related to [§5f](#5f--an-author-cannot-see-the-narrowness-of-their-own-predicate) and distinct from it: there the predicate was too narrow; here the SAMPLE was.**

### ⚠️ The widening, from the same pair of lanes running the other way — 2026-08-14

> ## **Check the state cell before citing the reasoning. Including your own.**

**Lane A proposed this after making the mistake and catching itself.** ⚡ **It rebuilt [C-1503](../../LANE_COORDINATION.md)'s argument from the source material, sent this office the conclusion as a live question, then found its own item `CLOSED` — ruled by the product owner at [D-235](../../DECISION_REGISTER.md) ② the day before.**

🔴 **This office did the same thing to the same item within the hour, and worse.** ⛔ **I opened `C-1434` for a question `D-235` ② had already answered — a row in a register I write, whose `Blocks` cell I filled in myself.** **I derived a real and correct argument from the design snapshot, eliminated an option on evidence, drafted a recommendation, and none of it was needed.**

⛔ **`C-1435` went the same way in the same commit: I raised a coordination item for [B-131](../../BUGS.md), which has been `OPEN` and QE's since 2026-08-06** — 📁 **[§20e](../../../CLAUDE.md), *a defect is not a dependency*.** ⚠️ **And its title carries the number `sixteen`, which is the figure I "corrected" a lane on without having read the row that states it.**

| | |
|---|---|
| ⛔ **The tell** | **A question whose argument assembles TOO easily.** ⚡ **If the evidence lines up in one pass, ask who assembled it the first time** |
| ✅ **The check, and it is two commands** | **`grep -n "<the subject>" docs/LANE_COORDINATION.md docs/BUGS.md docs/DECISION_REGISTER.md` BEFORE drafting, not after** |
| ⚠️ **Why it recurs** | **Rederiving feels like analysis. It produces the same artifact as analysis. ⛔ Only the register can tell the two apart** |

📁 **[§5e](#5e--a-row-has-one-status-cell-stack-history-under-a-different-label) says a row has one `Status` cell.** ⚡ **This is the reader's half of that rule: a cell nobody reads is the same as a cell that does not exist.**

## 5g · A count compares reachability. Only content compares content.

**Recorded 2026-08-13 after the same trap fired three times in a week, twice on a destructive operation.**

⛔ **Before any `--force-with-lease`, the patch-id survival check reports a NUMBER. The number is never the answer.** ✅ **Map every flagged id back to its commit and classify it**, because *missing* has three meanings and only one is a loss:

| | |
|---|---|
| ✅ **Already upstream** | Dropped by rebase as previously applied. **Not lost** |
| ✅ **Replayed with a resolution** | Same change, new patch-id. **Not lost** — 📁 **QE hit this on a byte-identical certification record: same subject, identical file list, both blobs identical, and the count still said *"1 commit would be lost"*** |
| 🔴 **Reachable from nothing** | **The only real one** |

⚡ **Reading only the count, all three look the same** — **and the two safe ones are far more common, which is exactly what trains a reader to dismiss the number.**

⛔ **Do it before the push, not after.** 📁 **QE's near-miss earlier the same week was eleven commits, and `--force-with-lease` was the only thing between the branch and them.**

### ⚠️ The general form, which is QE's sentence and better than the heading above

> ⛔ **A number consumed without its mapping.**

📁 **A second instance, same day, different count:** **`git rev-list --left-right --count A...B` prints *&lt;only in A&gt; &lt;only in B&gt;*, and *left* is the first ref rather than *the branch*.** ⛔ **QE read `15 10` and `9 1` as branch totals and reported cycle 228 as *"your 10 plus Lane A's 9"*; measured explicitly it is 5 and 2**, with Lane A **11 behind**.

⚡ **So the family is wider than survival checks: *missing* has three meanings, and a count has two sides.** ⚠️ **Both look equally authoritative, and reading the wrong one inverts the answer without any sign that it has.**

✅ **The practice covers both: never consume a number whose columns or members you have not resolved** — `--left-right` gets `ahead` and `behind` named explicitly, a survival count gets each id mapped to its commit.

### 🔴 The sharpest case, and the one nothing warns you about — QE, 2026-08-15

> ## **A wrong count announces itself when something disagrees. A right count answering the wrong question agrees with everything.**

**B-1005's cost.** This office measured **45** — *commits touching nothing but a regenerated projection*. ⛔ **Correct, reproduced by QE, and not the number the row needs.** ✅ **The question is *how many commits would have been closeout-exempt but for the `.toml`* — because a commit touching `BACKLOG.md`, `LANE_COORDINATION.md` **and** `coordination.toml` is documentation in substance and is disqualified by one file in it.**

⚡ **At 45 the row reads *"a lane's regenerations are noisy."* At ~157 it reads *"the accumulate rule has a one-in-six hole, concentrated in planning."*** ⛔ **Same defect; only the second justifies the care the fix needs.**

⚠️ **And the two independent measurements did NOT agree: QE got 159, this office got 157 — same window, same intent.** ✅ **Stating the predicate is what let it be resolved in one round trip: 157 is right, and the two extra commits — `99a0e8bb` and `c44a837f` — each carry a `docs/design-snapshot/**.dc.html`, which passes `startswith("docs/")` and fails `endswith((".md", ".json"))`.**

📁 **So a count is reported with the predicate that produced it, not just its value** — the same shape as [§5g-2](#5g-2--report-a-sha-from-the-shared-ref-never-from-the-one-you-control)'s *a measurement is a claim about a ref*. ⛔ **Ref, predicate, mapping: a number needs all three before anybody can check it, and 2026-08-15 produced one failure of each.**

#### ⚡ QE's refinement, which is sharper than *"state your predicate"*

> ## **If you compute a number twice, reconcile it before publishing either. If you computed it once, say which predicate — so somebody else can compute the second.**

🔴 **QE's discrepancy was never with this office. It was between their own two scripts.** **The first called `_is_closeout` and returned 157. The second, written to split A from B, re-expressed the condition in different words — prefix without suffix — and returned 159. ⛔ They ran both and published the one they ran last.**

📁 **That is [B-1002](../../BUGS.md) in miniature: a second implementation of a predicate, diverging from the authoritative one, and the divergence invisible because both returned a plausible number.** ⚠️ **They filed that defect against `certification-guard.py` in the morning and reproduced it in a shell heredoc the same evening.**

✅ **The rule that survives is [§5h](#5h--a-hand-maintained-copy-of-a-registry-is-the-defect-derive-it)'s, applied to a throwaway script: the split should have CALLED `_is_closeout` and partitioned its result, never restated the condition.** ⛔ **A one-off script is exactly where restating feels harmless.**

## 5g-2 · Report a SHA from the shared ref, never from the one you control

**Recorded 2026-08-15, from QE. ⛔ Both halves are this office's, and they compounded.**

🔴 **I reported `b216b2eb`, then `54f2c062`, then `2848f2d7` as this branch's tip. `git ls-remote --heads origin lane-c-sync` said `22b42cf2` the whole time. 57 commits were unpushed.**

⛔ **And the sentence that caused it: *"I cannot push to `integration`, so this is the whole of what I can do about it."*** ⚡ **The second clause does not follow from the first, and I never tested it.** 📁 **[§20e](../../../CLAUDE.md) step 6 is *"Push the lane branch and tell QE"* — QE integrates from a pushed lane branch, and that is the entire mechanism.**

> ⚠️ **The shape is this office's own finding one level up.** **I filed a `Planning-Sync: required` marker about a correction no lane could see — and the marker was itself invisible.** 📁 **The rule already exists and was paid for: *prepared work that has not reached `integration` does not exist for planning purposes*, written after Lane A idled on artifacts living only on a Product Office branch.**

### ⚡ The rule, after it caught the integrator the same day it caught this office

> ## **A SHA in a message is a promise not to move the ref — and its converse, that a ref you have moved locally has not moved.**

### ⚡ Lane A's generalisation, which is the same rule about a different noun

> ## **A measurement is a claim about a ref, and a claim without its ref is not checkable.**

🔴 **Three lanes made three correct measurements of [B-270](../../BUGS.md)'s severity and three claims wider than what they measured.** **Lane A raised it to 🔴 on their branch, with dated reasoning. QE read `integration` and wrote *"reads 🟠 and always has."* This office verified QE's ref, agreed, and repeated *"it has never been anything else"* — ⛔ a claim about all of time from a single snapshot, made while correcting somebody for exactly that.**

```
origin/lane-a-2b   🔴 Raised from 🟠 on 2026-08-15
origin/integration 🟠      origin/lane-qe 🟠      origin/main 🟠
```

✅ **Every reading was right. `state-check` was right on every ref it was pointed at.** ⛔ **The unexamined operand here was neither a process nor a projection but the TREE.**

⚠️ **The repair is not *"check more refs"* — it is that a severity, a count or a status carries the ref it was read from**, and *"escalated 🟠 → 🔴"* becomes *"…on `lane-a-2b`, not yet on `integration`"*. 📁 **Which is the [five states of a decision](../../../CLAUDE.md) applied to a measurement: ruled is not actionable, and measured is not published.**

📁 **Lane A said it first and said it about themselves.**

⛔ **The first version of this section said *read it back with `git ls-remote`*. That is a verification step and it does not hold**: QE *did* read `ls-remote` earlier in the cycle, before their local fast-forwards existed, then trusted `git rev-parse` for the rest. ✅ **An invariant about the sender survives where a chore for the reader does not.**

🔴 **The converse binds the INTEGRATOR harder than the lane, and the asymmetry is the point.** **A lane's stale SHA costs one wrong report. QE reported `integration` fast-forwarded and a Certification Snapshot pinned to `9a01139c` — a commit in no ref `origin` advertised.** ⛔ ***A snapshot naming a commit no other clone can resolve is a record nobody can check***, and it was one step from promotion. ✅ **Caught by this office reading `git ls-remote --heads origin` while checking something else, and fixed within the hour.**

⚠️ **Nobody spots an unpushed ref by being careful.** **The local view is complete, self-consistent and wrong** — which is why the tell has to be behavioural rather than attentional.

### 📁 Eight instances on 2026-08-15, six layers, two lanes

| Layer | The reading | Why it was wrong |
|---|---|---|
| **Register** | **3** `>>>>>>>` in `BUGS.md` | ⛔ **Two were quoted evidence inside fenced blocks, in a row about a stray marker** |
| **Instrument** | **39 `READY`** *(QE)* | ⛔ Matched *"Previously: `READY`"* |
| **Instrument** | **209 commits** *(QE)* | ⛔ **A real measurement of a quantity the audit does not consume** |
| 🔴 **Ref** | **4 refs fast-forwarded** *(QE)* | ⛔ **Locally. `origin` had none of them** |
| 🔴 **Process** | **`certify` sets no database** *(this office)* | ⛔ **True of the PARENT. `__main__.py:446` injects three URLs into the child** |
| **Producer** | **`database.py` returns a disposable-DB dict** *(QE)* | ⛔ **Read the producer and assumed a consumer. The application is a different line** |
| **Document** | **`RUNNING.md` cited as the mitigation** *(QE)* | ⛔ **Cited without opening. Line 64 is a note addressed to QE saying those exact lines are stale** |
| ⚡ **Inverted** | **`--exports` prints `5432`/`signora`** *(QE, reported in passing)* | ⚠️ **The RIGHT operand, read correctly — and stopped early. It is also a hole in this office's own fix** |

⚡ **In seven of the eight the raw reading was correct and the operand was not the one the consumer uses.** 🔴 **The eighth inverts it: the right operand, read correctly, with the narrower conclusion drawn** — ⛔ **and it is the hardest to catch, because nothing about the output looks incomplete.**

> ⚠️ **And one thing that usually goes unsaid, from the same repair:** **a fix can make a hazard *worse* by making it look intentional.** **`DESTRUCTIVE_DB_ENV` named slot 0 explicitly where the old code reached it by accident, so the next reader has less reason to question it than the accident did.** 📁 **Same shape as `certify` gaining the same variable and reading as a fix rather than as redundancy.**

> ## ⚠️ The fifth one cost a certification run, and that is what makes this section load-bearing
>
> **This office wrote *"`make certify` has been truncating whatever database the shell held"* into [B-270](../../BUGS.md).** **QE read `/proc/<pid>/environ`, found the same absence, and killed a valid cycle-232 run.** ⛔ **A false finding that reaches a shared register stops being one person's error.**

| | |
|---|---|
| ✅ **The general form** | **Read around the match rather than counting it** · **read the ref the reader will use, not the one you are standing on** · ⚡ **and a parent that does not need a variable is not evidence its child lacks one** |
| ⚠️ **The tell** | **Any sentence of the form *"I cannot X, so this is all I can do."*** **Test the second clause; it is a claim, not a consequence** |
| 🔴 **QE's reciprocal, and it binds this office equally** | ***A peer's accuracy record is not evidence about a specific claim.*** **QE skipped a one-command check because the claim came from a lane that had been right four times that day.** ⛔ **Weighting the source instead of the assertion, when the assertion was checkable in seconds** |

⚡ **And the repair that generalises is not the correction — it is naming the METHOD that produced it, where the next person will reuse that method.** 📁 **B-270 now carries *"`make -n` shows what the parent sets; it cannot show what a child injects"* beside the measurement, not in the correction block.** ⛔ **A `CORRECTION` tells a reader the claim was false; that sentence tells them why their method would produce it again.**

📁 **Same family as [§5g](#5g--a-count-compares-reachability-only-content-compares-content) — a number reported without the mapping its reader will apply.**

## 5g-3 · A prepared row is not finished until somebody has tried to claim it

**Recorded 2026-08-16, from Lane A's measurement of this office's own output.**

🔴 **Seven rows opened in one day. SIX needed something that was not in them:**

| | what was missing |
|---|---|
| **TASK-1416** | a figure in a report to drill into |
| **TASK-1432** | an importer for `scope.ts` — ⛔ **this office had released it on a text match** |
| **TASK-1424** | to not already be on `main` |
| **TASK-202** | a hosted credential |
| **TASK-1481** | an owner — `modules.toml` and §20e disagree |
| **TASK-1482** | a ruling — deleting the entry meets [D-225](../../DECISION_REGISTER.md) §4 |

✅ **`TASK-480` was the ONE that needed nothing, and the reason is measurable rather than lucky:** ⚡ **Lane A audited it BEFORE claiming, found the tier ambiguity, and the product owner answered it before the row was opened.**

> ## **One message before claiming costs a message. One claim spent finding out costs a poll — and the lane is idle for it.**

⛔ **The uncomfortable half is that this office prepared all seven.** ⚠️ **A row with a Definition of Done, testing metadata and a Change Budget still reads as complete while missing the one fact that decides whether it can start** — **because everything a preparer checks is IN the row, and what is missing is in the repository.**

✅ **So the test before releasing: *what would the implementing lane find in the first ten minutes that this row does not say?*** 📁 **Six of seven had an answer, and five of those were checkable from here.**

## 5h · A hand-maintained copy of a registry is the defect. Derive it.

**Three instances in two days, in three different kinds of artefact.**

| | The copy | What it cost |
|---|---|---|
| **[B-199](../../BUGS.md)** | A byte total and two per-file figures typed beside computed hashes | **Two were never true of their files** |
| **[B-434](../../BUGS.md)** | `state-check`'s literal actor list | **Demanded the one thing [C-213](../../LANE_COORDINATION.md) forbids in that cell** |
| **QE's, cycle 228** | **Six stack names hand-listed in a Security Invariant** where `BY_NAME ∪ UNSLOTTED` holds nine | 🔴 **A future `lane-d`/`lane-e` collision would have passed silently** |

⛔ **The third is the worst and QE named why: in a Security Invariant, a guard that tests a copy still looks like a guard.** ⚡ **The copy is not wrong when written — it is wrong the first time the registry grows, and nothing connects the two events.**

✅ **The practice: when a check needs a set the repository already defines, read the definition.** ⛔ **If a literal list is unavoidable, the check must fail when the registry and the list disagree** — 📁 **that is [§2](../../../CLAUDE.md)'s *truth has exactly one authoritative representation; everything else derives from it*, applied to test code, which is where it is least often applied.**

⚠️ **This office nearly added a fourth**: satisfying [B-434](../../BUGS.md) meant writing `Lane A` into a coordination row's `Owner` cell. ✅ **The fix was a join through [`modules.toml`](../modules.toml), never a wider pattern.**

⛔ **And that near-fourth is the sharpest of the set, on QE's reading: a check whose cheapest satisfaction is the violation it protects against.** 🔴 **The copy would have been created BY the guard** — strictly worse than three that were merely written by hand.

### ⛔ The corollary: derivation, never detection — do NOT build the checker

**QE's, 2026-08-14, and it follows from the sentence above rather than from new evidence.**

⚡ **The instinct after three instances is *"add a check that copies match their registries."*** ⛔ **That check would have to know which literals are copies of which registries — which is itself a hand-maintained mapping. A fourth copy, guarding the first three.**

✅ **So the only reliable defence for this class is derivation, and it is what all three fixes actually did**: a join, a derived set, a measured figure. ⚡ **The fix and the guard are the same act**, which is unusual enough to be worth stating.

📁 **[§5c](#5c--before-writing-a-check-ask-what-it-would-report-on-a-real-problem)'s test settles it: a green result would tell a reader *"no copies have drifted"* when all it can test is *"the copies somebody remembered to list have not drifted."*** ⛔ **The answer to *what will the reader stop asking* is the real question.**

#### ⚠️ Refined 2026-08-15 — *never* was too absolute, and QE produced the counter-case

🔴 **This said *derivation, never detection*. It is right about the general case and wrong as a universal, and B-1003 is where it breaks.**

| | The repair | Why |
|---|---|---|
| **[B-1001](../../BUGS.md)** — `BUGS.md` held its own copy of the identifier table | ✅ **DELETION.** The table became a pointer to `CLAUDE.md` §20e | ⚡ **The reference carries everything the copy did** |
| **[B-1003](../../BUGS.md)** — `RUNNING.md`'s allocation table | ✅ **A CHECK** — `test_runbook_allocation_table.py`, 11 cases | ⛔ **The reference does NOT carry it**: `--exports` answers only for the clone you are standing in and **cannot tell a reader that Lane A is slot 2** |

> ## **The test is not *"is there a registry?"* — it is *"does the registry answer the question the copy answers?"***
>
> ✅ **When it does, delete the copy; the fix and the guard are the same act.** ⛔ **When it does not, the copy has a job, and a check is what stops it being trusted.**

⚡ **And the second case must still refuse to hand-maintain the copy.** **QE's table is GENERATED from `infra/environments.py` rather than typed** — 📁 **written after they had typed one themselves and got `lane-qe`'s slot wrong and omitted `lane-e` entirely, one minute after writing *"no lane types a port."*** ⛔ **So: derive the CONTENT, check the DRIFT. Neither alone was enough here.**

## 6 · Workflow → task mapping

⛔ **Never map by substring, title similarity, keyword or approximate name.** `TASK-1418` *"AI Research"* matched Global Search because ***"research"* contains *"search"***.

✅ **[`workflows.toml`](../workflows.toml) is the authoritative registry and already names each workflow's design document.** Map from there, then **read the actual task row** and confirm from its stated workflow reference and scope. **If the evidence is absent, record `UNRESOLVED MAPPING`. Do not guess.**

## 7 · Re-investigation

**Settled items are indexed in [CURRENT-STATE.md](CURRENT-STATE.md) § *Do not re-investigate*, pointing at the authoritative register — never re-recorded here.**

✅ **It becomes eligible again when the source changed, the design changed, the ruling was superseded, the implementation changed, or new evidence contradicts it.** *Settled* is not *sealed*.

## 8 · Stopping

**If context runs short: stop, write the handoff into [CURRENT-STATE.md](CURRENT-STATE.md), end.**

⛔ **Never trade correctness for completion.** A shallow audit produced to finish a session is worse than an unfinished one, because the next session believes it.
