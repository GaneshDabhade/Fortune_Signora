# ADR-0031 — The renderer and the parser disagree about the citation protocol

> Status: **PROPOSED — 2026-07-31.** Documented, deliberately **not implemented**.
> Deciders: Product Owner · Architecture Review Board
> Supersedes: nothing. Amends: nothing.
> Anchors: [28-ai-platform.md](../28-ai-platform.md) · [29-ai-reasoning-engine.md](../29-ai-reasoning-engine.md) (T128) · [ADR-0028](0028-model-runtime-by-environment.md) · [ADR-0030](0030-the-decision-package.md) · CLAUDE.md §10, §20a

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
