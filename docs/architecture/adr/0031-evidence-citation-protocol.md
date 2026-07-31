# ADR-0031 — The renderer and the parser disagree about the citation protocol

> Status: **PROPOSED — 2026-07-31.** Recorded at T128 during M9. **Amended 2026-07-31 after T137–T138**, and **recommended for ratification** — see the amendment at the end of this document. Still not implemented.
> Deciders: Product Owner · Architecture Review Board
> Supersedes: nothing. Amends: nothing.
> Anchors: [28-ai-platform.md](../28-ai-platform.md) · [29-ai-reasoning-engine.md](../29-ai-reasoning-engine.md) (T128) · [ADR-0028](0028-model-runtime-by-environment.md) · [ADR-0030](0030-the-decision-package.md) · CLAUDE.md §10, §20a
>
> **Everything from here to *Consequences* is the record as it stood at T128, on the evidence available then. It is left unedited. The amendment supersedes its Decision and revises two of its option assessments.**

## Context

A grounded output is a set of statements, each carrying **citation tokens** that must resolve to facts in the closed evidence set. The token is the shared protocol between two pieces of code that never call each other:

- **The renderer** (`ai_platform/application/render.py`) turns an `EvidenceSet` into the text a model is shown.
- **The parser** (`EvidenceRef.parse`, via `grounding.py`) reads back what the model cited and resolves it.

They disagree about the protocol, and the disagreement is invisible until a model takes its instructions literally.

### Current behaviour

`render.py::_fact` presents every fact **wrapped in square brackets**:

```python
def _fact(fact: EvidenceFact) -> str:
    lines = [f"[{fact.ref.token}] {fact.summary}"]
    lines.extend(f"  {name}: {value}" for name, value in fact.attributes)
    return "\n".join(lines)
```

So a model sees:

```
[signal_contribution:3f40f486-98e5-5ff7-812d-feca5aa54af7] A retired system suggests …
  signal_type: displacement_opportunity
  relevance: primary
  contribution: 30
```

`EvidenceRef.token` produces, and `EvidenceRef.parse` accepts, the **bare** form:

```python
return f"{self.kind}:{self.id}"
```

And `reasoning@1` instructs:

> **Every statement must cite the facts it rests on**, by their exact reference strings.

**There is no form of "the exact reference string" visible to the model that the parser accepts.** The only rendering it ever sees is bracketed. A model that follows the instruction precisely emits `[signal_contribution:3f40…]`, `parse` reads `3f40…]` as the UUID, and the citation is rejected as `MALFORMED_CITATION`.

### Repository evidence

Five models were run against `reasoning@1` on 2026-07-31. The benchmark, dataset, rubric, schema, timeout and release criteria were **identical** in every run; only `SIGNORA_OLLAMA_MODEL` changed.

| Model | Resident | Processor | Result | Failure |
|---|---|---|---|---|
| `llama3.1:8b` | 5.6 GB | 58% CPU / 42% GPU | **UNMEASURABLE** | 60 s timeout, all cases |
| `qwen3:4b` | 3.2 GB | 27% CPU / 73% GPU | **UNMEASURABLE** | 60 s timeout, all cases |
| `qwen2.5:7b-instruct-q3_K_M` | 4.2 GB | 46% CPU / 54% GPU | **REFUSED** | 2 grounding failures |
| `qwen2.5:3b` | 1.9 GB | mostly GPU | **REFUSED** | 1 grounding failure |
| `llama3.2:3b` | 2.6 GB | 10% CPU / 90% GPU | **REFUSED** | 1 grounding failure |
| `granite3.3:2b` | 1.9 GB | **100% GPU** | **EARNED** ×8 | — |

**Every one of the three REFUSED runs failed on citation form, not on reasoning.** The rejected citations, quoted from the runs:

```
'[signal_contribution:346ae5cb-0147-52d8-8c81-55f43f0e45a2]'
'[signal_contribution:3f40f486-…]: contribution: 12, relevance: supporting, signal_type: modernization_underway'
'signal_contribution:a2529736-…:contribution=30 observed_on=2026-01-11'
```

Read them against the rendering above. The first is the bracketed line verbatim. The second and third are the bracketed line **plus its indented attribute block**, flattened. In all three cases the model reproduced what it was shown, which is what it was told to do.

Two independent model families — Qwen and Llama — produced the same defect on the same evidence. **A failure that reproduces across vendors is a property of the prompt or the platform, not of a model.**

### Why Granite currently succeeds

`granite3.3:2b` strips the brackets and emits the bare token. That is a **stylistic habit**, not a capability: nothing in the protocol asks for it, no instruction states it, and no test constrains it. The same is true of `llama3.1:8b` under M8's `explanation_narration@1`, which earned READY for the same accidental reason — the narration schema is flat and short enough that the model's bracket-stripping habit held.

So the platform's grounding has been **passing on luck since M8**. M9 exposed it because `ReasonedOutput` is nested and 1307 bytes against narration's 866, which puts the model under enough schema pressure that its formatting habits give way.

### Why this is severe rather than untidy

**It penalises instruction-following.** The models that failed were the ones that followed *"cite by their exact reference strings"* most literally. A grounding checker that rejects obedience is measuring the wrong thing — and `REFUSED` is a durable, recorded verdict, so a model can be recorded as unfit for Signora on the basis of a protocol Signora never stated.

**It silently narrows the field of usable models**, in a way that reads as a capability finding. Nothing in the record would tell a future engineer that the refusals were formatting. This ADR exists so that record is not lost.

**It contradicts a ratified principle.** *Evaluation measures compatibility with Signora's contract, not general model quality.* That only holds if the contract is stated. Here it is stated one way and enforced another.

### What is *not* wrong

- **`EvidenceRef.token` is correct.** A flat opaque string is the right shape, for the reason its docstring gives.
- **The grounding checker is correct.** An unresolvable citation *should* be a violation; that is what makes the evidence set closed.
- **`reasoning@1` is correct.** Requiring exact reference strings is right. It cannot know it is describing a form the parser will reject.
- **The bracketed rendering is defensible.** Delimiters make a citation visually separable from prose, which is likely why it was written that way.
- **No model tested was defective.** Every refusal was a faithful transcription.

**The defect is that two components share a protocol and neither owns it.** The renderer decides the presentation; the parser decides the grammar; nothing reconciles them, and no test compares them.

## Decision

**None yet — this ADR documents the finding and does not implement a fix.**

It was discovered inside M9, and the M9 boundary forbids changing the AI Platform's grounding. Correcting it would alter how every prompt renders evidence, which would change the conditions under which `explanation_narration@1` earned its release. **That is an M8 change, and it needs its own evaluation.**

## Options

| | Option | Assessment |
|---|---|---|
| **A** *(recommended)* | **Render the bare token; keep a delimiter that is not part of it.** e.g. `signal_contribution:3f40… — A retired system suggests …`. The string the model sees is exactly the string the parser accepts, so literal obedience becomes the winning strategy | Removes the trap at its source and makes the protocol one thing rather than two. Requires re-evaluating both released prompts, because the rendered text changes |
| **B** | **Make the parser tolerant** — strip surrounding brackets and trailing attribute text before parsing | Cheapest, and it would have passed all five models. But it makes the parser guess at intent, and every tolerance added to a validator is a rule nobody stated. It also leaves two protocols, with one quietly repairing the other |
| **C** | **State the citation form explicitly in the prompt**, e.g. *"cite the reference without its surrounding brackets"* | Keeps rendering and parsing as-is, but puts the burden on every prompt author forever, and a prompt that forgets reintroduces the defect silently. It also solves it per-prompt rather than once |
| **D** | **Assert the round trip in a test** — for every fact, the rendered citation must parse back to the same `EvidenceRef` | Not an alternative but a **complement**: whichever of A–C is chosen, this is what stops the two drifting apart again. Recommended alongside A |

**Recommended: A + D.** A removes the inconsistency; D makes its return a build failure. Together they change the protocol from a convention held in two places into one representation with an executable check — *truth has exactly one authoritative representation*.

## Consequences

**If A is adopted**, both `explanation_narration@1` and `reasoning@1` must be re-evaluated, because the prompt text a model receives will have changed. Neither release survives automatically, and that is correct: the release rule binds a measurement to the exact conditions that produced it.

**The model comparison above should be re-run afterwards.** Three of the four models refused for formatting rather than reasoning, so the field of locally-usable models is very likely wider than the table suggests. Until then, `granite3.3:2b` is the **currently certified** evaluation model for `reasoning@1`, not the preferred one, and not a permanent pin.

**Until this is resolved, a REFUSED verdict citing `MALFORMED_CITATION` should be read as suspect** and checked against this ADR before being recorded as a finding about a model.

---

# Amendment — 2026-07-31, after T137 and T138

> The record above was written inside M9, from one prompt's failures. M10 has since authored two more prompts, attempted Option C twice, and measured the result. Three findings follow. The first two change how the options are assessed; the third changes the order the work must be done in.

## Finding 1 — Option C has been exercised twice, and its record is one in two

M10 wrote both of its prompts **with Option C already applied.** Neither was an experiment; the instruction was included because T128 had already identified the trap.

[`research_planning@1`](../../../backend/modules/ai_research_engine/prompts/research_planning@1.md), rule 5:

> **Cite the exact reference, without the square brackets.** … The brackets are display only, and a citation that includes them addresses nothing.

[`research_synthesis@1`](../../../backend/modules/ai_research_engine/prompts/research_synthesis@1.md), rule 2:

> **Every statement must cite the findings it rests on**, using the exact reference inside the square brackets, **without the brackets**. A finding is shown as `[research_finding:2f7c9a10-...]`; write `research_finding:2f7c9a10-...`.

Both name the defect. Both give a worked example. Both were evaluated against **the same model, `llama3.1:8b`, through the same renderer, in the same milestone, days apart.**

| Prompt | Option C applied | Result | Failure |
|---|---|---|---|
| `research_planning@1` | yes, rule 5 | **RELEASED**, 0 grounding failures, coverage 1.0 | — |
| `research_synthesis@1` | yes, rule 2 | **REFUSED** ×3 consecutive runs | citation emitted as a **bare UUID** |

**The synthesis failure is the inverse of the defect this ADR was written about.** The T128 evidence is models copying *more* than the citation — the bracket transcribed along with it. Here the model copied *less*: told to remove the brackets, it removed the brackets **and the `research_finding:` kind prefix**, leaving a bare UUID. `EvidenceRef.parse` finds no separator, and reports `MALFORMED_CITATION`. Grounding behaved correctly, as it did in every case above.

Identical across three consecutive runs, and — the detail that matters most — **it happened on one of the two cases and not the other, from the same prompt, in the same run.** Not a model that cannot follow the instruction. A model that follows it inconsistently, within a single inference.

### What this establishes, and what it does not

It does not disprove Option C statistically; two prompts is two prompts. It establishes something more specific and more damaging:

**Option C does not remove a failure mode. It trades one for another.** Before it was applied, every observed failure was *over-copying*. After it was applied, an *under-copying* failure appeared that had never been seen — on the only prompt in the repository whose kind prefix is long enough to read as a label rather than as part of an address. The instruction that says *"remove the brackets"* is an instruction to remove characters, and a model deciding how many to remove is a model that can decide wrongly in either direction.

**The two prompts that pass do so for reasons nothing in the repository states.** `research_planning@1` passes with the workaround; `explanation_narration@1` and `reasoning@1` pass *without* it, on `granite3.3:2b`'s and `llama3.1:8b`'s bracket-stripping habits. Three of four prompts are held up by behaviour no instruction requests and no test constrains — and the fourth, the one where the workaround was applied most explicitly, is the one that failed.

That is the disqualifying property. **A strategy every prompt author must apply forever, which works for reasons nobody can state and fails for reasons nobody predicted, is worse than no strategy** — because it also makes the problem look handled.

## Finding 2 — nothing in the repository records the bytes the model was shown

Two artifacts are recorded against every inference, and **neither covers the rendered prompt**:

- **`PromptVersion.fingerprint`** — SHA-256 over `name`, `version` and **template text**. The template contains `{facts}`, not the facts.
- **`EvidenceSet.digest`** — over the facts' `canonical_form()`, which is documented in that module as *"a stable text form, for hashing only. **Not for prompts**."*

`render.py` is what joins them, and it is covered by neither. So:

> **Two inferences carrying identical `prompt_fingerprint` and identical `evidence_digest` may have been shown different text.** All that is required is that `render.py` changed between them.

This is a hidden input in the exact sense CLAUDE.md §2 forbids — *an input that influences behaviour without being part of the declared contract* — and it has been present since M8. It has three consequences that bear directly on this ADR:

1. **A renderer change silently invalidates every release** while every recorded artifact continues to assert it. The loader catches prompt-text drift by fingerprint; the dataset catches its own drift by fingerprint; nothing catches this.
2. **It is the reason the fix cannot be landed as a one-line change.** Correcting `_fact` without a mechanism to invalidate the measurements taken under the old rendering would leave the repository asserting three releases that no longer describe it — the failure mode CLAUDE.md §2 names last and treats as most damaging, because it is trusted.
3. **It explains why this defect survived two milestones.** Nothing recorded the one thing that would have shown the renderer and the parser disagreeing.

### The reproducibility contract, stated

A prompt evaluation is a measurement of a **system**, and the system has four inputs: the prompt text · the rendered evidence · the model · the dataset. Three are bound to the measurement today. The fourth is not bound and, uniquely among the four, **its change is undetectable.**

**The rendered form must therefore become part of the reproducibility contract.** Not because rendering is important, but because a measurement whose conditions can change without notice is not a measurement.

## Finding 3 — the refusals this ADR rests on are not in the repository

Found while gathering evidence for this amendment, and not previously recorded.

`release.py` was written on the principle that failures are recorded too:

> *"A manifest that recorded only passes would show a prompt with a clean history and no way to see it had been measured and found wanting — and the second engineer to evaluate it would repeat the work."*

But `--record` is opt-in, the evaluation harness's recorder is `RunLog`, which is **in memory**, and no refusal has ever been written to a manifest. The five-model table in this document, and the three consecutive `research_synthesis@1` refusals, exist **only as prose in documents and commit messages.**

`research_synthesis@1` therefore shows `"evaluations": []` — indistinguishable, to any tool, from a prompt nobody has ever measured. That is precisely the state `release.py`'s docstring says the design exists to prevent.

> **Resolved by M9.5 Step A, 2026-07-31.** Three refusals are now recorded: `research_synthesis@1` on `llama3.1:8b`, and `reasoning@1` on `qwen2.5:3b` and `llama3.2:3b`. All three reproduced live, and the rejected citations are the ones this document quotes. **`qwen2.5:7b-instruct-q3_K_M` could not be recorded**: it returned UNMEASURABLE today where T128 recorded REFUSED, because one of its two cases exceeded the timeout on this machine. An unmeasurable run yields no `Evaluation` by construction, which is correct — a partial average is how a verdict gets granted on the cases that happened to finish. It is left unrecorded rather than reconstructed from the T128 prose.

**This changes the order of the work.** The whole value of the fix is a before/after comparison, and the "before" is currently anecdote. **The refusals must be recorded to their manifests before the renderer changes** — otherwise the repository loses the only evidence that the change was justified, and this ADR becomes unfalsifiable.

## Revised assessment of the options

| | Option | Assessment at T128 | **Revised, 2026-07-31** |
|---|---|---|---|
| **A** | Render the bare token | recommended | **Recommended, unchanged in substance and strengthened in argument.** It is the only option under which the citation requires no transformation. Both observed failure modes — over-copying and under-copying — are errors in *how much to transform*; an option that asks for zero transformation has no mechanism for either |
| **B** | Tolerant parser | rejected on principle | **Rejected on evidence.** Stripping brackets recovers information that was *present and decorated*. Nothing recovers a kind that was **never emitted**. B would not have fixed the failure actually in front of us — see the analysis below |
| **C** | State the form in the prompt | rejected as a burden on authors | **Rejected as measured.** No longer a prediction: applied twice, failed once, and the failure was a mode the workaround itself introduced |
| **D** | Assert the round trip in a test | complement | **Required, and the gap is now precise.** `test_evidence.py` asserts `parse(ref.token) == ref` — the round trip over the *token*. Nothing asserts it over what `render` emits. **That gap is the defect, stated exactly** |
| **E** | *(new)* Version the rendering, and bind releases to it | — | **Required.** Finding 2. Without it, A cannot be landed truthfully |

### Why B remains insufficient, in detail

Tolerance would have to operate at one of two places, and both fail against repository guarantees:

**At the parser** — strip `[`, `]` and trailing prose. This handles T128's evidence and does nothing for T138's: `2f7c9a10-…` contains no kind, and no amount of lenience invents one.

**At the resolver** — match a bare UUID against ids in the closed evidence set. This *would* have resolved the synthesis failure, so it deserves the honest answer rather than a dismissal. It is refused on three stated repository guarantees:

- `EvidenceRef`'s own docstring gives the reason it is a pair: *"so two kinds sharing an identifier can never collide."* Resolution by id alone discards that property deliberately.
- `grounding.py` states: *"It validates; it never repairs. … a validator that quietly fixed its input would make the failure rate unmeasurable, which is the one number this platform most needs about itself."*
- It would make the citation protocol **two grammars again** — one written, one accepted — which is the defect, re-created one layer down.

**No repository evidence supports tolerance preserving these guarantees, so the parser stays strict.** The fix is entirely on the producing side.

## Decision

> **Superseding the *"None yet"* recorded above.** That was correct in M9, where the AI Platform was outside the milestone's boundary. It is no longer correct, because M10 has now been blocked by it.

**Adopt A + D + E**, as one change, in a milestone of its own:

**A — the renderer emits the token undecorated**, with a delimiter that is not part of it. The string the model must produce becomes a string it can copy.

**D — the round trip is asserted over the rendered output**, not over the token. A renderer that decorates a citation becomes a test failure.

**E — the rendered form becomes a versioned protocol, and a release is bound to the version it was measured under.** An evaluation conducted under one rendering does not survive a change to the rendering, and `require_model` refuses rather than the repository quietly asserting a release that no longer describes it.

Together these convert the citation protocol from a convention held in two places into **one owned representation with an executable check and a recorded identity** — *truth has exactly one authoritative representation, and hidden inputs are architecture defects.*

### Where the protocol lives

The defect was stated at T128 as *"two components share a protocol and neither owns it."* **The fix is to give it an owner, and the owner already exists.** `EvidenceRef.token` and `EvidenceRef.parse` — the writer and the reader of the citation grammar — are already neighbours in `domain/evidence.py`, which is why *they* have never drifted. What is unowned is the **display form**: the line layout that surrounds the token, invented in `application/render.py`, where the parser cannot see it.

So the display form belongs beside `token` and `parse`, in the domain that owns the grammar, and `render.py` composes facts using it and contributes no formatting of its own. **`render.py` stops being a second author of the protocol and becomes its only caller.**

## Consequences, revised

**Three releases are invalidated** — `explanation_narration@1`, `reasoning@1`, `research_planning@1` — and none survives automatically. That is the release rule working, not collateral damage.

**Prompt immutability is preserved.** Every `@1` stays on disk, unedited, with its evaluations intact: they were true under rendering version 1, and E is what makes that statement precise rather than merely believed. The corrections are `@2`s. **A record of what was true then is dated, not rewritten.**

**The blast radius on the test suite is small.** Pipeline and smoke tests supply their own registries with scripted adapters and do not read the shipped manifests, so an invalidated release breaks no test and no demonstration. Only `make eval-*`, the manifests, and two tests that pin manifest contents are affected.

**The five-model comparison should be re-run afterwards** — unchanged from T128, and now with a second prediction attached: if A is correct, the models that refused `reasoning@1` on formatting should pass `reasoning@2`. **If they do not, this ADR is wrong and should be recorded as wrong.**

**The order is: record the refusals, then change the renderer.** Finding 3.

## Recommendation

**Promote this ADR from PROPOSED to ACCEPTED, and open M9.5 to implement it, before M10 resumes.**

The evidence has changed category. At T128 this was a defect that narrowed the field of usable models — real, but survivable, and outside M9's boundary. It is now the thing preventing a finished milestone from closing, on a prompt that already implements the recommended workaround. Three of the four prompts in the repository are held up by an undeclared model habit; the fourth is refused.

**This is not M10's work.** It changes the AI Platform and re-releases M8's and M9's prompts, and CLAUDE.md §20d forbids a milestone reaching outside what it owns to satisfy its own demonstration. Ratification belongs to the Product Owner and the Architecture Review Board; this document records the recommendation and stops there.
