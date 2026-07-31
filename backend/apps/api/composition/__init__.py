"""Where the API wires modules together.

**The composition boundary, and the only place that may see two modules'
infrastructure at once.** A module's own composition root takes its neighbour's
query surface as a *parameter* rather than constructing it, so the assembling
happens here, at the entry point, exactly as §6 requires.

**Split per module, and the split is not cosmetic.** A single shared module here
was the first shape tried, and import-linter refused it: a router importing it
inherits *every* import it makes, so `knowledge_graph`'s router acquired a
transitive dependency on `opportunity_engine` — an upstream module reaching
downstream, which is a cycle waiting to happen. **One file per read surface
means a router depends only on what it actually composes.**

Nothing is re-exported from here. A router imports the module it needs.
"""
