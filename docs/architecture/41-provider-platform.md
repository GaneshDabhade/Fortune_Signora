# 41 — Provider Platform: how evidence enters, and what stops it entering twice

> **The module design doc, started 2026-08-02 — four milestones after the module.** Provider Platform was built in M2.0 and M2.1 and has had no design document since; the modules documented in `22`–`29` all arrived later and all got one. This is the gap closed, and the circumstance is recorded rather than tidied away: under rotating assignment a module's design doc is the next assignee's only inherited context (`CLAUDE.md` §12), and this module — the one every other module's data passes through first — had none.
>
> **What this document covers, honestly.** The synchronization model as it stands today and the target-account contract being built on it. It is **not** a retrospective reconstruction of M2: the Provider Port, the adapter contract and the simulation framework are specified in [20-provider-simulation.md](20-provider-simulation.md) and [21-intelligence-pipeline.md](21-intelligence-pipeline.md), and this document references them rather than restating them (§2, *truth has exactly one authoritative representation*).

## What the module owns

**Synchronization — entirely** ([ADR-0036](adr/0036-target-account-contract.md) §1): cadence, polling policy, cost, provider selection, failover, backoff, deltas.

**None of it is a customer's to configure**, ruled 2026-08-01. A customer says *watch this company*; everything about how often, from whom, at what cost and in what order is Signora's. That is the boundary most likely to be taken by a neighbour, which is why the ADR states it as a permanent ownership rule rather than a design preference.

**What it deliberately does not own:** intent (Commercial Profile), understanding (Knowledge Graph), intelligence (Signal Engine). A `subject` arrives unresolved and **stays** unresolved — resolution happens downstream, in the module whose competence it is.

## The synchronization state

| | What it records | Why it is separate |
|---|---|---|
| `provider_sync` | One run: when, how many pages, how many records, how it ended | The history of what happened |
| `provider_watermark` | **How far one subject has been read** | Resetting it is the standard recovery from a bad run, and **recovery must not destroy the record of what went wrong** |
| `raw_provider_record` | What arrived, before interpretation | Evidence. Immutable, and cited by every conclusion downstream |

### A watermark belongs to one subject — PP-01, B-004 *(2026-08-02)*

**The key was `(workspace_id, provider, capability)` and carried no subject**, so a workspace watching two accounts shared one position between them.

> Sync Acme to Tuesday. Sync Initech. Initech's run reads Acme's position, asks the provider for everything *since* it, and **every Initech record older than Tuesday is never requested.**

**No error, no log, no failed sync.** Evidence that never becomes a signal, on an integration that looks healthy — which is why it gets a suite of its own rather than an assertion inside an existing test.

**It was latent, and PP-02 is what ends that.** Nothing outside the Provider Simulation Framework has ever supplied a `subject` — `RunProviderSync` has taken one since M2.1 and no caller has filled it — so no workspace has yet had two. The consumer gives every declared account one. [ADR-0036](adr/0036-target-account-contract.md) therefore names this *"one defect that must be fixed before the consumer is built"*, and the ordering is the whole reason it is slice 1.

**`subject` is part of the identity, not a label on it.** `SyncWatermark` gives it no default: a watermark that cannot name its account **is** the defect, so the type refuses to construct one, and `get_watermark` requires it rather than accepting `None`. A caller that could omit it would get another account's position — silently, which is the property that made the original bug expensive.

**Rows written before the column keep an empty subject** (migration `0026`). Which account an old position belongs to is not recoverable, and inventing an attribution would be worse than admitting none. An empty subject matches no real one, so those rows are inert and the first sync of each subject requests a full snapshot — **which is what an absent watermark already means**, so nothing new exists to handle it.

**The downgrade discards watermarks and says so.** Narrowing the constraint means collapsing many rows into one and there is no correct choice of which to keep; it keeps the furthest-advanced position, which is safe for the *constraint* and unsafe for *coverage*. Recorded in the migration rather than left for someone to discover — the honest recovery afterwards is to reset the affected watermarks, which destroys no history because syncs and raw records are separate tables.

## The target-account contract — what PP-02 and PP-03 build

**Specified in full by [ADR-0036](adr/0036-target-account-contract.md); the shape is repeated here only as far as a lane needs to navigate it.**

```
  commercial_profile                        provider_platform
  ──────────────────                        ─────────────────
  target_accounts_changed  ──trigger──▶     the consumer
   (workspace_id, declaration_version)          │
                                                │ calls
  TargetAccountReader      ◀──payload───────────┘
   (the whole list, never a delta)               │
                                                 ▼
                                          delta vs provider_watermark
                                                 │
                                                 ▼
                                          RunProviderSync per subject
```

**The event triggers; the port supplies.** Not a choice between them — events carry identity, ports carry payload.

**Provider Platform computes its own delta**, because a delta from Commercial Profile is a delta between two *declarations*, and what matters is the delta against **what has actually been synced**. Re-adding an account that was declared before and never successfully fetched is *"no change"* to a declaration and real work here.

**`declaration_version` orders what idempotency cannot.** Idempotency on `event_id` handles redelivery; it does not handle two declarations in quick succession arriving out of order. An event older than the version already acted on is ignored — compared locally, with no coordination.

**Removal stops polling and deletes nothing** (§6). Raw records are evidence that conclusions a customer has already read and acted on still cite. *Erasability is a property of the tenancy model* — it belongs to deleting a workspace, not to un-watching a company. **The watermark stays**, so re-adding resumes incrementally.

## Slices, and where this document was written

| Slice | Task | State |
|---|---|---|
| **PP-01** — a watermark belongs to one subject | [TASK-015](../BACKLOG.md) / [B-004](../BUGS.md) | Built 2026-08-02 |
| **PP-02** — the consumer | [TASK-018](../BACKLOG.md) | Next |
| **PP-03** — un-watching stops the spending | [TASK-019](../BACKLOG.md) | After PP-02 |

**PP-02 is what [TASK-014](../BACKLOG.md) and [C-007](../LANE_COORDINATION.md) are blocked on** — the guided first run ends by publishing a declaration nothing consumes, and *"a guided first run is the most prominent place in the product to make a promise."*
