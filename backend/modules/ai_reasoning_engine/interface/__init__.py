"""The AI Reasoning Engine's HTTP surface.

**One endpoint, and it is a read.** The module concludes; it does not conclude
on request. `Reason` is dispatched by the pipeline after a buying score moves,
and a `POST` here would put a model call inside a request — which §7 forbids
and Principle 13 puts in a background worker.

**The module has had a complete domain and application layer and no way to be
read since it was built** ([417 §2c](../../../docs/architecture/417-executable-slice-audit.md)).
That is what this layer changes and all it changes: no new conclusion, no
second inference path, no cross-account ranking. The `public/` contract stays
empty, deliberately — **nothing outside this module consumes a Decision
Package**, and an interface layer serving its own module's use cases is not a
consumer (`15-project-structure.md`).
"""
