# ADR-0409 — Signora owns commercial account facts

| | |
|---|---|
| **Status** | ⚠️ **DRAFT — Lane C, 2026-08-12.** ⛔ **Ratification is the product owner's** ([§20e](../../../CLAUDE.md)) |
| **Decision** | ✅ **Ruled by the product owner, 2026-08-12, as C-209 option A: *Signora owns commercial account facts — Open ACV, Renewal, and commercial/opportunity stage.*** |
| **Scope** | ⛔ **The ruling is OWNERSHIP ONLY.** **This ADR is the minimum contract that makes it implementable, and nothing more** |
| **Supersedes** | Nothing. **It extends the closed vocabulary by the route that vocabulary names** |

## 1 · Why an ADR and not a code change

📁 [`provider_normalization/domain/vocabulary.py`](../../../backend/modules/provider_normalization/domain/vocabulary.py):1

> *"**Adding or changing an attribute is an architectural decision requiring an RFC**; adding or updating a **mapper** is routine engineering. **That asymmetry is what lets provider integrations evolve while the platform's language stays stable.**"*

⚡ **This ADR is the whole of the architectural half. Everything below the vocabulary is routine engineering and belongs to Lane A.**

## 2 · A sixth `ClaimDomain`

`ClaimDomain` groups attributes *by the kind of question they answer*: `FIRMOGRAPHIC` · `TECHNOGRAPHIC` · `CAPITAL` · `WORKFORCE` · `BEHAVIOURAL`.

> ✅ **Add `COMMERCIAL` — *what this account is worth to us, and where it stands*.**

⛔ **Not folded into `CAPITAL`.** Capital is what happened to the *company*; commercial is the state of *our relationship with it*. **Different subject, different provenance, and a consumer filtering on domain would get the wrong set.**

## 3 · Three attributes, and each takes a shape the vocabulary already uses

⚡ **No new modelling idiom is introduced. Each attribute reuses an existing precedent, named.**

| Attribute | Value | Precedent |
|---|---|---|
| **`OPEN_ACV`** | **A frozen value carrying `amount` and `currency`** — never a bare number | 📁 `FundingValue` and `AcquisitionValue` both carry `amount: int \| None` beside `currency: str \| None`. ⚡ **A figure without its currency is not a fact** |
| **`RENEWAL_DATE`** | **A `date`** | 📁 `FundingValue.announced_on` |
| **`COMMERCIAL_STAGE`** | **A closed canonical position, carrying the tenant's own label beside it** | 📁 **`RevenueBand`** bands a continuous value into a closed enum; **`TechnologyValue.name`** carries the raw vendor string beside the canonical `category` |

### ⛔ Why `COMMERCIAL_STAGE` is the one that needed a decision

**Every CRM names its stages differently, and a tenant renames them again.** ⚠️ **A free string would be a `value: Any` in disguise** — the file's opening rejects exactly that: *"by the Signal Engine nobody would remember what an `employee_count` actually is."*

> ✅ **So the canonical value is a small closed set of pipeline positions, and the tenant's own wording travels beside it as provenance.**
>
> ⛔ **Reasoning reads the canonical position. A screen may show the customer's word.** ⚡ **This is [ADR-0034](0034-ubiquitous-language.md) inside a single attribute: the customer's language reaches the screen and never travels inward.**

⛔ **The members of that closed set are NOT fixed here.** **They are the smallest set that supports the consumers in §6, and Lane A proposes them from the design and the CRM adapters it can see.** ⚠️ **Naming them from this office, without a mapper in front of me, would be the invention this ADR exists to avoid.**

## 4 · Ownership, and the mapping boundary

| | |
|---|---|
| **Vocabulary** | **`provider_normalization/domain/vocabulary.py`** — ⛔ **the only place the canonical language is defined.** Extending it again needs another ADR |
| **Mapping** | **Each provider's mapper**, e.g. `infrastructure/mappers/crm.py`. ✅ **Routine engineering** |
| **Consumers** | **Read the canonical form only.** ⛔ **No consumer parses a vendor's stage name, and none may branch on which CRM supplied a fact** ([§10](../../../CLAUDE.md), vendor neutrality) |

⚡ **`crm.py`'s refusal is discharged by this ADR, not overridden.** 📁 It said the facts *"have no canonical attribute, and `ClaimAttribute` says an RFC extends it"*. ✅ **This is that RFC. The comment should be updated to cite it rather than deleted** — it records why the gap existed.

## 5 · Normalization expectations

- **`VOCABULARY_VERSION` increments to `2`.** 📁 It exists to be incremented; a vocabulary change that leaves it at `1` is a stored fact disagreeing with the code that wrote it.
- **A claim is only produced where the provider supplies the fact.** ⛔ **Absence is never inferred, defaulted or zero-filled** — a missing ACV is missing, and [P-A](../../DOMAIN_DISCOVERY_REGISTER.md) already forbids rendering an absent read as an empty one.
- **Currency is carried, never converted.** ⚠️ **Conversion is a rate applied at a moment, which is [§10](../../../CLAUDE.md)'s *operational facts and commercial policy stay separate* — a converted figure stored on a claim is correct briefly and wrong permanently.**
- **The tenant's stage label is provenance and is never reasoned over.**

## 6 · What this releases

**All three consume the same canonical model. ⛔ None may define its own.**

| | |
|---|---|
| **Companies remainder** | *Open ACV* and *Renewal* columns, excluded from [TASK-1475](../../BACKLOG.md) pending this ruling |
| **[TASK-1469](../../BACKLOG.md)** | The deal record |
| **[C-297](../../LANE_COORDINATION.md)** | Forecast — ⚠️ **the concept it needs is stage, not probability.** ⛔ **`buying_score_engine`'s refusal of probability is untouched by this ADR and still stands** |

## 7 · What this ADR deliberately does not decide

⛔ **Field names in any schema · table or column design · API shape · the migration · which CRM fields map to which attribute · the members of the stage enum · retention · any UI.**

⚡ **All of it is Lane A's, as routine engineering under the asymmetry in §1.**
