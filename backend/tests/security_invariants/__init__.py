"""Security Invariants — permanent architectural guarantees.

These tests are different in kind from the rest of the suite. A feature test
asserts that a behaviour works; a test here asserts that a *property of the
system* holds, and is expected to remain in place unchanged for the life of
the codebase. They are not refactored away when the feature they touch is
rewritten — they are the reason a rewrite is safe.

Four categories, each stating guarantees the architecture depends on:

* ``test_authentication`` — only correctly-signed, correctly-scoped tokens
  are accepted, and this tier cannot mint one.
* ``test_authorization`` — Casbin decides access, workspaces are isolated,
  and PostgreSQL enforces that isolation rather than application code.
* ``test_database`` — each tier holds a credential that can do its job and
  nothing else.
* ``test_platform`` — accepted work is not lost, is not processed twice,
  and failures end somewhere a human can find them.

**Deliberate overlap with feature tests is intended.** Several invariants
here are also exercised by tests elsewhere. That duplication is the point:
a feature test may legitimately be rewritten or deleted when its feature
changes, and the guarantee would leave with it. These do not move.

Run them alone:

    uv run pytest -m security_invariant

Every test carries the ``security_invariant`` marker, applied in
``conftest.py`` rather than per-test so a new file cannot forget it.

**A failure here is never "just a failing test."** It means a guarantee the
architecture is built on has stopped holding. Diagnose the guarantee before
touching the assertion.
"""
