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

## 6 · Workflow → task mapping

⛔ **Never map by substring, title similarity, keyword or approximate name.** `TASK-1418` *"AI Research"* matched Global Search because ***"research"* contains *"search"***.

✅ **[`workflows.toml`](../workflows.toml) is the authoritative registry and already names each workflow's design document.** Map from there, then **read the actual task row** and confirm from its stated workflow reference and scope. **If the evidence is absent, record `UNRESOLVED MAPPING`. Do not guess.**

## 7 · Re-investigation

**Settled items are indexed in [CURRENT-STATE.md](CURRENT-STATE.md) § *Do not re-investigate*, pointing at the authoritative register — never re-recorded here.**

✅ **It becomes eligible again when the source changed, the design changed, the ruling was superseded, the implementation changed, or new evidence contradicts it.** *Settled* is not *sealed*.

## 8 · Stopping

**If context runs short: stop, write the handoff into [CURRENT-STATE.md](CURRENT-STATE.md), end.**

⛔ **Never trade correctness for completion.** A shallow audit produced to finish a session is worse than an unfinished one, because the next session believes it.
