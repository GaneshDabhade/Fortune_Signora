"""What every commercial declaration has in common.

A customer's declaration — what they sell, who buys it, who decides, which
accounts matter — is always the same *kind* of statement: complete, made by
somebody, at a moment, superseding the one before it.

**This file exists now and did not before, because there are two of them.**
The version a workspace reports when it has declared nothing is one fact, and
a second copy of it under a second name is how two aggregates begin
disagreeing about what *nothing* means.

**Deliberately a constant and an error, not a base class.** What the two
aggregates share is those two things; a `Declaration` superclass would be an
abstraction over two instances, generalising ahead of the evidence. The
duplication that *is* left — read current, compare version, build, save —
stays duplicated until a third aggregate shows what the shape really is.
"""

from typing import Final


class CommercialProfileError(Exception):
    """Something a customer declared cannot be recorded as stated."""


UNDECLARED: Final = 0
"""The version reported when a workspace has declared nothing.

**Not a stored row.** A new workspace has declared nothing, and answering with
an empty statement at version 0 means every caller gets the same shape whether
or not anything has been declared — no `None` branch, no 404, and no seeding
write that would tie this module to workspace creation.
"""
