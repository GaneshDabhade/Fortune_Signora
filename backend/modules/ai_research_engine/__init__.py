"""AI Research Engine — the pipeline's agentic, open-ended stage.

**The module that looks outward.** Every stage before it derives conclusions
from what providers already told Signora; this one goes looking for what they
did not. That makes it the first module whose latency is measured in minutes,
whose cost is variable, and whose failure mode is *partial completion* rather
than a retryable error (ADR-0025).

It is deliberately **not** a blocking dependency of the pipeline. The AI
Reasoning Engine must produce a valid — if less informed — Decision Package
whether research completed, timed out, or was never started.

**What it is permitted to know is governed by the Knowledge Contract**
(34-knowledge-contract.md), not by this module's convenience:

* A **research synthesis** is INFERRED. It is never citable and never enters
  an evidence set, however well sourced it appears.
* A **research finding** anchored to an external source is ATTESTED. Whether
  ATTESTED knowledge may be cited at all is an **open product ruling**.
* **Retrieval, rankings and embeddings are not knowledge.** They may decide
  what is looked at; they may never decide what is true.

The rule that makes this module architecturally possible at all:

    Inference may direct attention. It may never confer status.
"""
