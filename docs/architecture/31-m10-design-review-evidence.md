# 31 — M10 Design Review: may a research artifact become evidence?

> Status: **OPEN — 2026-07-31.** Analysis for a ruling. **No option is recommended in §1–§6**; the recommendation is deliberately held to §7 so the analysis can be read without it.
> Audience: the product owner, and whoever implements M10.
> **Reordered 2026-07-31: [32-knowledge-ontology.md](32-knowledge-ontology.md) is now the first question.** The product owner's judgement was that this review asked the right question *second* — so the ontology classifies every knowledge type Signora holds before anything is decided about research. It excludes options B and D, and the synthesis half of C, **by classification rather than by preference**. The options below stand unchanged; read the ontology first.
> Anchors: [28-ai-platform.md](28-ai-platform.md) · [29-ai-reasoning-engine.md](29-ai-reasoning-engine.md) · [ADR-0030](adr/0030-the-decision-package.md) · [ADR-0031](adr/0031-evidence-citation-protocol.md) · [30-m9-retrospective.md](30-m9-retrospective.md) · CLAUDE.md §2, §10

---

## The question

**M10 produces research: inference, synthesis, interpretation, open-ended reasoning over public sources. M9 consumes a closed Evidence Set of deterministic facts. What is the epistemic status of a research artifact, and may it be cited?**

This is not an implementation detail. It decides whether M10 **extends** Deterministic Explainability or **ends** it.

## Why it is urgent — the repository makes the wrong answer easy

Three facts, verified in the repository rather than assumed:

**1 · `EvidenceRef.kind` is an unconstrained string.**

```python
kind: str
def __post_init__(self) -> None:
    if not self.kind.strip():  raise EvidenceError(...)
    if ":" in self.kind:       raise EvidenceError(...)
```

No enum, no allowlist, no registry. `research_finding:uuid` is constructible **today, with zero platform change.**

**2 · `EvidenceFact` declares itself true.** Its docstring opens: *"One thing that is **true**, addressed and attributed."* Nothing enforces that; it is a statement of intent that every consumer has so far been entitled to rely on.

**3 · Grounding cannot help here, by construction.** `verify()` checks that a citation **resolves inside the set** — malformed, unresolved, uncited, ungrounded quantity, workspace escape. **Not one of the five checks asks whether a fact in the set is true.** M9's retrospective already recorded the sharper form of this: *grounding confirms a conclusion cites real facts and invents no figures; it says nothing about whether the conclusion follows.*

Put together: **if a model-authored research finding enters the Evidence Set, every downstream check passes and the Decision Package presents it to a customer as evidence they can check.** What they would actually be checking is one model's claim against another model's claim.

That is the failure mode this architecture was built to prevent, arriving through the one door left unlocked.

## What is genuinely at stake

M9's value proposition, in the product owner's own framing:

> **Customers should never be asked to trust the AI. They should be shown enough to reach their own judgement.**

Twelve of fifteen Decision Package parts are derived precisely so a customer can check them. Research is the **most powerful author in the system** — agentic, multi-step, open-ended, unverifiable, and unrepeatable. Routing its output into the Evidence Set would make the most powerful author an input to the module built to minimise model authorship.

There is also a second-order effect worth naming: **`SupportBasis` would silently mis-report.** Support derives from *distinct corroborating providers* and `EvidenceState`. A research finding has neither. Left alone, research contributes to a package while contributing nothing to Support — so a conclusion resting largely on research could read `CORROBORATED` on the strength of two pipeline providers that supported a different claim.

---

# The options

Five, spanning the realistic space. Each is assessed against the eight dimensions requested.

---

## Option A — Research artifacts are **not** evidence and are never cited

Research produces a stored artifact. It is **never** placed in an Evidence Set and never citable. It surfaces to a customer, if at all, as a clearly separated *"what we found while researching"* panel with its own provenance, adjacent to the Decision Package rather than inside it.

| Dimension | Assessment |
|---|---|
| **Ownership** | Cleanest. M10 owns its artifact end to end; M9 unchanged; `ai_platform` unchanged |
| **Explainability** | Strongest. Every cited premise remains pipeline-derived and reproducible |
| **Auditability** | Strongest. The Evidence Set stays a closed set of deterministic facts, exactly as documented |
| **Customer trust** | Highest *per claim*, but the customer must reconcile two panels themselves. Research becomes decoration next to the conclusion rather than part of it |
| **Deterministic guarantees** | Fully preserved. The digest still covers only deterministic facts, so replay is unaffected |
| **Impact on M9** | **None.** No change to reasoning, grounding, Support, or the package |
| **Impact on Decision Package** | None structurally — and that is the criticism: research cannot strengthen or challenge a conclusion, which is most of why it was commissioned |
| **Future extensibility** | Low. Any later attempt to let research inform reasoning reopens this question with more code in the way |

**The honest objection:** `05-module-dependencies.md` states M10 exists so *"AI Reasoning Engine consumes it as additional context."* Option A declines to build the edge the architecture was designed around. It is safe by not doing the thing.

---

## Option B — Research findings enter the Evidence Set as an ordinary kind

`research_finding:uuid` becomes a kind like `signal_contribution`. Reasoning cites it identically. Requires no platform change.

| Dimension | Assessment |
|---|---|
| **Ownership** | Blurred. M10 becomes a producer of "facts" that M9 treats as pipeline-equivalent |
| **Explainability** | **Damaged.** A premise citing a research finding is not reproducible; re-running research produces different words |
| **Auditability** | **Damaged.** The evidence digest — the identity a customer cites — would cover model output, so two runs over identical pipeline state produce different digests. *Determinism outranks convenience* is directly violated |
| **Customer trust** | **Actively harmful.** A customer told *"here is the evidence, check it"* receives generated content indistinguishable from derived fact |
| **Deterministic guarantees** | **Broken.** Replay, regression testing and *"the same declared inputs produce the same result"* all fail |
| **Impact on M9** | None visible — which is precisely the danger. No test fails, no contract breaks |
| **Impact on Decision Package** | Silently inverts it. `supporting_evidence` would mix derived and generated premises with no way to tell them apart |
| **Future extensibility** | Superficially highest, actually lowest: once shipped, the distinction can never be recovered from stored rows |

**Included because it is the path of least resistance, and would be chosen by default if nobody rules.** It requires no design work and no platform change. That is exactly what makes it dangerous.

---

## Option C — Research yields **sourced findings only**; synthesis is discarded

M10 may run open-ended agentic research, but **only findings anchored to an external source survive** into anything citable. A finding is `(claim, source_url, retrieved_at, verbatim_excerpt)`. The agent's *synthesis* — its narrative, its conclusions — is recorded as operational history and **never becomes evidence**.

The evidence kind is distinct (`research_finding`), and the fact's summary is *what the source says*, not what the model concluded.

| Dimension | Assessment |
|---|---|
| **Ownership** | Clear. M10 owns retrieval and attribution; the **source** owns the claim; M9 owns what to do with it |
| **Explainability** | Strong. A customer can open the URL. *"TechCrunch reported X on this date"* is checkable in the way a pipeline fact is checkable — by looking |
| **Auditability** | Strong, with one caveat: the external source may change or vanish, so the verbatim excerpt and `retrieved_at` must be stored. This is the same reasoning that makes catalog content snapshotted and immutable history referenced |
| **Customer trust** | High, and arguably **higher than pipeline facts** for some claims — a named public source is often more persuasive to a seller than a derived score |
| **Deterministic guarantees** | Preserved *downstream*. Research itself is non-deterministic, but its **output is a fixed set of sourced facts**, so reasoning over them replays exactly. The non-determinism is quarantined at the boundary and time-stamped |
| **Impact on M9** | **Real and must be raised, not absorbed.** The Decision Package must distinguish derived premises from sourced ones, and `SupportBasis` must decide whether an external source counts toward corroboration |
| **Impact on Decision Package** | Additive: a new premise class, visibly labelled. `answers()` gains genuine strength on *"which evidence supports it?"* |
| **Future extensibility** | High. Adding source classes (filings, job boards, news) is data, not architecture |

**The cost:** it discards the most impressive part of agentic research — the synthesis — from the customer-visible path. It also requires a **verification step**: a model can fabricate a URL as readily as a number, so a finding must be checked against a retrieved document, which is real engineering.

---

## Option D — A separate, explicitly-typed *interpretation* channel

Research findings enter as a **distinct type**, not as `EvidenceFact` — say a `ResearchContext` alongside the Evidence Set in `ReasoningContext`. The model may **read** it but is **forbidden from citing it**; only pipeline evidence is citable. Grounding is unchanged and would reject a research citation as `UNRESOLVED_CITATION` automatically.

| Dimension | Assessment |
|---|---|
| **Ownership** | Clear, and expressed in the type system — the strongest form available here |
| **Explainability** | **Ambiguous, and this is its weakness.** Research *influences* the conclusion without appearing in its premises. A customer sees a conclusion whose stated evidence does not fully account for it |
| **Auditability** | Partial. The artifact is stored and linked, so an auditor can reconstruct — but the package does not *say* research shaped it |
| **Customer trust** | **Risky.** A hidden input is an architecture defect by this repository's own ratified principle: *any input that influences behaviour without being part of the declared contract*. This option deliberately creates one |
| **Deterministic guarantees** | Preserved for citations; **broken for behaviour**. Same inputs plus different research produce different conclusions with an identical evidence digest |
| **Impact on M9** | Moderate — a new context field, and a grounding rule that already holds for free |
| **Impact on Decision Package** | Weakens it. The package would no longer fully explain itself |
| **Future extensibility** | Moderate |

**Included because it is the intuitive compromise** — *"let the model see it but not cite it"* — and because the repository already has a principle that rules against it. Worth stating explicitly so it is not re-proposed.

---

## Option E — Research is a **hypothesis generator**, not an evidence source

The most radical reframing, and it aligns with existing precedent. Research does not produce facts at all: it produces **candidate signals** which re-enter the pipeline at the Signal Engine, where they are subject to the same grounding rules, catalog definitions, profile weighting and supersession as any other hypothesis.

A research finding becomes commercially meaningful **only if it survives the machinery that already decides what a signal is**. It then reaches M9 as an ordinary contribution, with a provider attribution of "research" and everything downstream unchanged.

| Dimension | Assessment |
|---|---|
| **Ownership** | Strong and principled. M10 proposes; the **Signal Engine disposes** — mirroring *intelligence suggests, humans commit* one layer down |
| **Explainability** | Strong. A researched signal is explained exactly like any other, through `SignalExplanation` |
| **Auditability** | Strong. The full supersession and profile machinery applies, and `catalog_version` records the rules used |
| **Customer trust** | High. A customer sees *"a signal, sourced from research"* — a category they already understand |
| **Deterministic guarantees** | Preserved downstream; non-determinism quarantined at the point of proposal, exactly as in Option C |
| **Impact on M9** | **Zero.** M9 needs no change at all — the strongest signal that this fits the existing architecture |
| **Impact on Decision Package** | None structurally; strictly richer input |
| **Future extensibility** | Highest. Any future intelligence source plugs in the same way |

**The serious objections, stated fairly:**

1. **It inverts the ratified dependency graph.** `ARE → AIR` is documented; this makes it `ARE → Signal Engine`, a backwards edge into an upstream module. `05-module-dependencies.md` forbids *"a downstream module publishing an event an upstream module subscribes to as a hidden feedback loop"* — though it permits **new forward-flowing events**, and cites exactly this precedent: `recommendation.status_changed` feeding the Signal Engine.
2. **Signal types are a closed, reviewed catalog.** A workspace *cannot invent a signal type* — that is unrepresentable by design. Research that can only produce catalogued types is far less open-ended than "agentic research" implies.
3. **It may be the wrong shape for the actual product need.** *"This company just hired a CISO and posted three security roles"* is a signal. *"Their 10-K says they are consolidating vendors in FY27"* is context that no catalogued signal type captures.

**Objection 3 is the strongest**, and it suggests C and E may be complementary rather than exclusive: sourced findings that match a catalogued hypothesis become signals; those that do not remain sourced context.

---

## Comparison

| | A — never evidence | B — ordinary kind | C — sourced findings | D — read-only channel | E — hypothesis generator |
|---|---|---|---|---|---|
| Determinism preserved | ✅ | ❌ | ✅ | ⚠️ behaviour only | ✅ |
| Customer can check a premise | ✅ | ❌ | ✅ | ⚠️ | ✅ |
| Introduces a hidden input | No | No | No | **Yes** | No |
| Evidence digest stays deterministic | ✅ | ❌ | ✅ | ✅ | ✅ |
| Requires M9 change | No | No | **Yes** | Yes | **No** |
| Requires graph change | No | No | No | No | **Yes** |
| Research can strengthen a conclusion | ❌ | ✅ | ✅ | ⚠️ | ✅ |
| Reversible after shipping | ✅ | **❌** | ✅ | ✅ | ✅ |

**The reversibility row deserves emphasis.** Every option except B can be changed later. B cannot: once generated content is stored as evidence and cited by shipped packages, the distinction between derived and generated premises is unrecoverable from the rows.

## Questions a ruling should answer

1. **Is a sourced external claim "evidence" in Signora's sense?** Everything currently in an Evidence Set is *derived by Signora from provider data*. A newspaper article is checkable but not derived. This is a definitional question the architecture has never had to answer.
2. **Does an external source count toward corroboration?** If yes, `SupportBasis.corroborating_providers` needs a concept of source class. If no, a well-sourced conclusion can read `LIMITED`.
3. **Must a research finding be verified before it is citable?** A model can fabricate a URL as easily as a number, and `UNGROUNDED_QUANTITY` does not cover *"this source does not say that"*.
4. **Is unsourced synthesis ever customer-visible?** Or is it strictly operational history — valuable for debugging, never shown?

---

# §7 · Recommendation on sequencing

*Held separately, and deliberately not a recommendation between A–E — that is the ruling being requested.*

**A short M9.5 should precede M10.** The argument rests on repository evidence, not preference.

**1 · ADR-0031's cost grows monotonically.** Correcting the citation protocol changes what every prompt renders, so every released prompt must be re-evaluated. Today that is **two** prompts (`explanation_narration@1`, `reasoning@1`). After M10 it is three. There is no version of this that gets cheaper.

**2 · M10 is the milestone most likely to be misled by it.** Measured this week: three of five models were REFUSED on citation *form*, not reasoning — across two independent model families. M10 is agentic and multi-call, exercising grounding far harder than a single-call module. It would generate more of these refusals and, without ADR-0031 in front of the engineer, record them as capability findings about models.

**3 · Freezing a substrate with a known defect is the worst outcome.** `ai_platform` freezes once M10 consumes it. Running M10 first means freezing a platform whose citation protocol is documented as inconsistent — after which correcting it needs a freeze exception.

**4 · F-1 is already real and M10 makes it worse.** Two certified prompts already cannot be served by one process configuration. Discovering that mid-M10 is worse than settling it deliberately.

**Proposed M9.5 (~2–3 ew):** ADR-0031 Option A + D (render the bare token; assert the render→parse round trip) · re-evaluate both prompts · resolve F-1 · re-run the model comparison, since the usable local field is very likely wider than currently recorded.

**What M9.5 is not:** an opportunity to start M10 early, or to fix F-2. The Evidence Set question needs a ruling, not a workaround.

## A dissenting view, recorded so it is not lost

**M10 may not be the right next milestone at all.** The pipeline runs **nine stages ahead of any user-visible surface** — the Decision Package is produced, stored and announced, and no human can see it until M12. M10 adds the most expensive, slowest, least deterministic capability in the system to a pipeline whose output nobody can read.

M11 (Recommendation, 6–8 ew) and M7 (Timeline, 6–8 ew) are cheaper and closer to a visible surface, and either would give the Decision Package a consumer.

**The counter-argument, which is why this is a dissent and not a recommendation:** M10 is the only remaining consumer needed to freeze `ai_platform`, and a substrate left unfrozen accumulates exceptions. Deferring M10 defers that.

It is a genuine trade, and it belongs to the product owner rather than to a design review.
