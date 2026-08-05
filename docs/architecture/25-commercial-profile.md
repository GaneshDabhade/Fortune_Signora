
---

## TASK-434 — an account can be asked whether it matches a criterion

**Delivered 2026-08-05 by Lane B.** **The capability [C-330](../LANE_COORDINATION.md) asked for**, and the loop that produced it is worth recording because it is the governance working rather than a lane being clever.

This lane claimed TASK-406, found that lift needs a predicate nothing could supply, and **refused to invent one inside a slice**. The product owner declined the framing and broadened it — *"a foundational platform capability that multiple future product areas will depend upon"*. Product Office assessed it in [443](443-account-matching-capability.md) and found it is three problems, not one. [D-077](../DECISION_REGISTER.md) sequenced it ahead of its dependent. **No workaround was built at any point, and the interim one that was permitted was never needed.**

### Why the matcher lives in the module that records the declaration

**The criterion vocabulary is defined here** — `industries`, `countries`, `EmployeeRange`, `validate_criterion_list`. A matcher built anywhere else needs a second copy of it, and the copy nobody maintains is the one that decides whether an account is in its own ICP.

**And it does not breach the contract this module lives under.** `pyproject.toml` forbids `commercial_profile` from importing the pipeline — *"commercial_profile declares; it never reads the pipeline"*. `evaluate` **reads nothing**: it imports no module, queries no repository, opens no session and knows no caller. **The prohibition is on reaching for the pipeline, and being handed a value is not reaching** — which is what lets the ruled dependency direction hold while the comparison stays where the vocabulary is.

### Two invariants, both in the type rather than the prose

**A verdict is a category with a reason and never a number.** `MatchStrength` established this in resolution; the same door would open here. A number invites a weight, a weight invites a threshold, and a threshold is a propensity judgement this module has no standing to make. **There is no score, confidence or weight on anything in `matching.py`**, and `test_boundary.py`'s domain scan would fail if there were.

**`UNMEASURED` is never `NO`.** The customer declares free text; the pipeline observes canonical values. Under string equality `SaaS` against `Computer Software` returns *no match*, and the account **silently drops out of its own ICP** — a wrong answer that looks decided. Absence of an observation and absence of a match are different facts, which is the same distinction the product owner ruled for search groups at TASK-408 on the same day.

### What is deliberately not here

**No overall verdict.** Rolling three answers into *"matches"* needs a rule for `UNMEASURED`, and every available rule is a judgement — treat it as a pass and an unmeasured account looks qualified, as a fail and it looks disqualified. **That rule belongs to whichever consumer has a reason for it**, stated where a customer can see it.

**No synonym catalog.** Case and spacing are folded, which is not interpretation — the same string typed twice. Anything cleverer decides what two different words mean, and 443 records that as a **reviewed catalog** to build *"when `UNMEASURED` shows it is losing accounts"*. **The limitation is asserted in a test** so it stays visible rather than being discovered by a customer.

**No lift and no backtest.** That is TASK-406, which is sequenced behind this.

### The published surface

`IcpReader` is the module's **third published read and its thirteenth view** — and the first that carries the criteria. Until it existed no module could read them at all, which is how sixteen consumers accumulated behind a capability nobody could build. `notes` is **not** published: it exists to be read by a human and is explicitly *"never parsed"*, so publishing it would invite exactly the parsing it forbids.

*+23 tests. 3600 backend passed, coverage 95.37%; `icp_reader.py` 100%, `matching.py` 95%.*
