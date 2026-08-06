# 462 · C-332 · An account's observed attributes — architectural proposal

**Lane C · Product Office · 2026-08-06.** **[D-095](../DECISION_REGISTER.md): *"prepare the architectural proposal… Do not implement until the dependency review is complete."***

**Prepared, not implemented. No lane named, no code written, no contract added.**

> **The question**: `evaluate(icp, observed)` is `PROMOTED` and correct. **Nothing constructs an `ObservedAttributes`, and the module ruled to measure cannot reach the module that could.** [C-332](../LANE_COORDINATION.md).

---

# 0 · ⚡ The finding that reshapes the proposal

**An existing public contract very nearly satisfies this, and measuring it changed the recommendation.**

> **`knowledge_graph/public/` already exports `GraphQueries` and `ClaimSet`**, and the read is published today:
>
> **`async def claim_set(workspace_id, entity_id, attribute) -> ClaimSet`**

**So the naïve reading is that no new contract is needed at all — `opportunity_engine` calls it three times, for `INDUSTRY`, `COUNTRY` and `EMPLOYEE_COUNT`, and builds the value object itself.**

**That is wrong, and the reason is the whole proposal.**

---

# 1 · Why the existing public contract cannot satisfy the requirement

**`ClaimSet` is *"everything known about one attribute of one entity"* — a set of competing claims from different providers, with `providers` and `latest_by_provider` as its two views.**

> ## **It hands the caller a disagreement and no rule for settling it.**

| What the caller receives | What the caller must then decide |
|---|---|
| **Three providers say the industry is `SaaS`, `Computer Software`, `Technology`** | **Which one is *the* industry** |
| **`latest_by_provider` — one claim per provider, by `observed_at`** | **Whether newest wins, or most-corroborated, or a named provider** |
| **An empty set** | **Whether that means *unknown* or *not yet fetched*** |

**Every one of those is a resolution decision, and `knowledge_graph` is the module that owns resolution** — `ResolutionRule`, `MatchStrength`, `IdentityState`, *"a property of the rule, not a belief"*.

> ⛔ **A consumer projecting `ClaimSet` into a single value is a second resolver.** **And the repository has already refused exactly this, twice, in writing:**
>
> **`commercial_profile/domain/competitors.py`:** *"**This module could not resolve one even if it should**… matching *'Salesforce'*, *'salesforce.com'* and *'SFDC'* to one technology is exactly the job the graph exists to do, and **a second resolver here would be free to disagree with it.**"*
>
> **And [443](443-account-matching-capability.md) §1 refused the same thing for `commercial_profile`.**

**With eight consumers of [R-00](../DOMAIN_DISCOVERY_REGISTER.md), *"the caller projects it"* means up to eight rules for what an account's industry is** — **and the disagreements would be invisible, because each caller's answer looks correct in isolation.**

> **So the existing contract is not insufficient in *shape*. It is insufficient in *authority*.** **`ClaimSet` publishes evidence; what a consumer needs is a resolved fact, and only its owner may resolve it.**

---

# 2 · The proposal

> ## **`knowledge_graph` publishes a projection: one canonical value per attribute per entity, with its provenance and an explicit *unknown*.**

| | |
|---|---|
| **Owner** | **`knowledge_graph`** — it owns identity resolution, the `entity_id → SubjectRef` binding, the claims, and the vocabulary. **No other module holds any of the four** |
| **Shape** | **A `Reader` in `public/`**, on the `View · Reader` triple this module and `commercial_profile` both already publish. **One call per entity, not three** — a caller assembling three reads is a caller with three chances to mismatch them |
| **The value** | **Per attribute: the resolved value, the providers that agreed, and `unknown` as a first-class outcome** — ⚡ **`unmeasured` is already in [TASK-434](../BACKLOG.md)'s type, and this is the same word arriving from the other end of the same call** |
| ⛔ **What it must not do** | **Never score, rank or weight a provider.** **Never return a *best guess* without saying it is one.** **Never expose `SubjectRef`** — a provider identity crossing this boundary would let a consumer do resolution after all |

## Dependency direction

**`opportunity_engine → knowledge_graph.public`, and nothing else.**

| | |
|---|---|
| ⛔ **Forbidden today** | `pyproject.toml` names **`modules.knowledge_graph` in full** in `opportunity_engine`'s forbidden set, and [05](05-module-dependencies.md) agrees |
| ✅ **The precedent is exact** | **[ADR-0403](adr/0403-signal-engine-reads-a-declaration.md)** added `signal_engine → commercial_profile.public` for the same shape: **a consumer needing a fact the owner already holds, reached through `public/` only, with no inner layer touched** |
| ✅ **And the direction is the safe one** | **Downstream reading upstream.** ⚡ **The dangerous direction is already forbidden and stays forbidden**: [C-328](../LANE_COORDINATION.md) ruled `commercial_profile` may not read the pipeline, and **nothing here changes that** |

## Why this is the minimum change

| Alternative | Why not |
|---|---|
| **The caller projects `ClaimSet`** | ⛔ **A second resolver, up to eight times over** — §1 |
| **`commercial_profile` reads the graph** | ⛔ **[C-328](../LANE_COORDINATION.md) ruled it shut, and correctly** |
| **The attributes travel on an event** | ⚠️ **More machinery, and it makes a *measurement* depend on *delivery*.** A backtest that silently omits an account because its projection has not arrived is [P-A](../DOMAIN_DISCOVERY_REGISTER.md)'s failure with no way to see it |
| **`buying_score_engine` carries them** | ⛔ **Refused in its own code**: *"no name, no domain, no industry"* — deliberately, so a score row never becomes an account record |
| **A new bounded context** | ⛔ **For a read over facts one module already holds** |
| ✅ **This** | **One reader, in a module that already publishes fifteen types. One edge, `public/` only. No new module, no new table, no migration, no event, and no existing contract weakened** |

---

# 3 · What this proposal does not settle

**⬜ Which resolution rule applies to an attribute value.** **`knowledge_graph` resolves *identities* today; resolving *attribute values* — newest, most-corroborated, or a declared provider precedence — is a rule nobody has written.** ⚡ **It is the same gap [443 §M1](443-account-matching-capability.md) named as vocabulary agreement, arriving one layer down.**

> **Stated rather than assumed, because it is the part most likely to be decided by accident inside the first implementation.** **The reader can ship with the simplest defensible rule — most recent, with the agreeing providers named — provided the rule is *stated in the contract* rather than buried in a query.**

---

# 4 · Governance

| | |
|---|---|
| **Change Budget** | 🔴 — **a new cross-module dependency edge.** **Product owner + ADR** |
| **ADR** | **Required, and not drafted.** [443](443-account-matching-capability.md) and [451](451-workflow-automation-traceability-audit.md) both showed an ADR written ahead of a ruling gets its sizing wrong |
| **Import contract** | **`pyproject.toml` needs `modules.knowledge_graph` removed from `opportunity_engine`'s forbidden set and replaced with the inner-layer form** — the shape [ADR-0403](adr/0403-signal-engine-reads-a-declaration.md) used |
| **Unblocks** | **[TASK-406](../BACKLOG.md), both halves** · **[R-00](../DOMAIN_DISCOVERY_REGISTER.md) becomes usable rather than merely implemented** |

---

# 5 · What this document did not do

**Nothing implemented · no ADR drafted · no lane named · no contract added · no import contract amended · no backlog row created.**

⚡ **And it changed its own recommendation once, at §0.** **The first reading was *"knowledge_graph has no reader for this"*. It has one, published, and the argument had to move from *the contract is missing* to *the contract publishes evidence where a resolved fact is needed*** — which is a better argument and was only available by reading the code.
