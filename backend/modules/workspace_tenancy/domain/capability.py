"""What a person may do, above what their membership says they are.

📁 **[ADR-0410](../../../../docs/architecture/adr/0410-authorization-capability-layer.md),
ratified as [C-1429](../../../../docs/LANE_COORDINATION.md)** —
[TASK-1479](../../../../docs/BACKLOG.md) slice ⓸.

> ✅ ***"Use a capability/permission layer ABOVE the existing `WorkspaceRole`
> enum. Do NOT simply expand `WorkspaceRole` from OWNER/MEMBER into every UI
> role shown by the designs."***

## 🔴 The mechanism already existed, and finding that is most of this slice

⚡ **`Authorizer.is_allowed(role: str, …)` takes a free string**, and
`model.conf`'s `sub` is *"the caller's workspace role, already resolved from a
server-side-verified membership"* — **deliberately not the user id**, because
mirroring membership into Casbin's grouping policy would duplicate a source of
truth that lives in PostgreSQL under RLS.

✅ **So a capability role needs no change to `signora_platform/**` at all.**
**It is another role string, resolved server-side exactly as the membership
role already is, and its grants are `policy.csv` rows** — 📁 the registry
[§20e](../../../../CLAUDE.md) says every lane extends.

⛔ **That is what ADR-0410 §2 means by *"adds no new mechanism; it says which
mechanism these belong to"*, and it is why this slice touches no frozen file.**

## ⚠️ A capability role REPLACES the membership role; it does not add to it

🔴 **The one genuine decision here, and
[ADR-0410](../../../../docs/architecture/adr/0410-authorization-capability-layer.md)
§7 delegates it** — *"the named role sets and their contents"*.

**Four reasons, and the design drew each of them.**

📁 ***"Effective permissions"*** — **ADR-0410 §3 calls it *the resolved answer
for a person*.** ⛔ **One answer.** A union of *what my membership allows* and
*what my role allows* is two answers a customer has to combine themselves.

📁 ***"Change to Analyst"*** — **the design's own words in Team Management**,
and ⚡ **a change is not an addition.**

🔴 **Narrowing must be representable.** **`Analyst` is drawn as narrower than
`Admin`**, and ⛔ **if a capability role could only add, a narrower one would be
unbuildable.** §2 prefers a violation that is unrepresentable over one that is
discouraged, and that cuts both ways: **a role that cannot narrow is a design
that cannot express the product.**

✅ **The safe direction is preserved.** 📁 §5: *"a capability that is not yet
granted denies."* **Replacement keeps that** — an unlisted `(resource, action)`
is denied for a capability role exactly as it is for `member`.

⛔ **And §5's migration guarantee is untouched, because assignment is opt-in.**
**Nobody holds a capability role until somebody assigns one**, so *"every
current OWNER and every current MEMBER keeps exactly the authority it has
today"* is true by construction rather than by care.

## 🔴 The invariant that is not negotiable

📁 **ADR-0410 §5: *"a member must not acquire an owner's capability through the
new layer."*** ⚡ **Expressed here as a type rather than a rule to remember:
`CapabilityRole` cannot be constructed with a name that collides with a
membership role**, so `Admin` can never be spelled `owner` and quietly inherit
44 policy rows.

⛔ **The enforcement is a Security Invariant as well**, because a type stops
this module and the policy file is edited by every lane.
"""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from modules.workspace_tenancy.domain.entities import WorkspaceRole
from modules.workspace_tenancy.domain.exceptions import WorkspaceTenancyError

#: Long enough for *"Revenue Operations"*, short enough that a sentence is
#: obviously the wrong field. The design draws `Admin` and `Analyst`; a
#: customer naming their own is what *"New role"* in Settings is for.
MAX_ROLE_NAME = 40

#: ⛔ **The names a capability role may never take**, because `sub` is one
#: string and a collision would silently inherit that membership role's grants.
#: 📁 Derived from `WorkspaceRole` rather than listed, so a future membership
#: role cannot be shadowed by a capability role somebody named first.
RESERVED_ROLE_NAMES: frozenset[str] = frozenset(role.value for role in WorkspaceRole)


class CapabilityError(WorkspaceTenancyError):
    """A capability role cannot be recorded as the customer stated it."""


def fold(name: str) -> str:
    """The form two role names are compared in. **Never the form anybody sees.**

    ⚡ **`casefold` over collapsed whitespace**, the same rule the account tag
    and segment vocabularies use — and for the same reason: `Analyst` and
    `analyst` are one role to the person who typed them, and two rows to a
    database.
    """
    return " ".join(name.split()).casefold()


@dataclass(frozen=True, slots=True)
class CapabilityRole:
    """One named set of capabilities.

    ⛔ **The contents are NOT here.** 📁 They are `policy.csv` rows keyed on
    `key`, because ADR-0410 §2 forbids *"a second independent authorization
    model"* — **and a copy of the grants in this module would be exactly
    that**, drifting from the file the enforcer actually reads (§2).

    ⚡ **`key` is what reaches Casbin**, and `name` is what a customer sees.
    """

    id: UUID
    name: str

    def __post_init__(self) -> None:
        stripped = " ".join(self.name.split())
        if not stripped:
            raise CapabilityError("A role needs a name.")
        if len(stripped) > MAX_ROLE_NAME:
            raise CapabilityError(
                f"A role name is at most {MAX_ROLE_NAME} characters; "
                f"this one is {len(stripped)}."
            )
        if fold(stripped) in RESERVED_ROLE_NAMES:
            # 🔴 **ADR-0410 §5's invariant, made unconstructable.** A role named
            # `owner` would be handed to `is_allowed` as the string `owner` and
            # would match all 44 of that membership role's policy rows —
            # **which is precisely "a member acquiring an owner's capability
            # through the new layer".**
            raise CapabilityError(
                f"“{stripped}” is a membership role and cannot name a capability role."
            )
        object.__setattr__(self, "name", stripped)

    @property
    def key(self) -> str:
        """**The subject Casbin is asked about**, and what `policy.csv` keys on.

        ⚡ **Prefixed, and the prefix is load-bearing.** ⛔ Without it a
        customer could create a role whose folded name equals a *future*
        membership role — `RESERVED_ROLE_NAMES` can only refuse the ones that
        exist today — **and the prefix makes the two namespaces disjoint by
        construction rather than by a list somebody maintains.**
        """
        return f"cap:{fold(self.name)}"

    def renamed(self, name: str) -> CapabilityRole:
        """The same role, said differently.

        ⚠️ **The id does not move and the KEY does**, which is the one place
        this differs from a tag or a segment: the key is what `policy.csv`
        holds, so **a rename is a policy edit as well as a row update.**
        📁 That is stated rather than hidden because the grants live in a file
        this module does not own.
        """
        return CapabilityRole(id=self.id, name=name)


@dataclass(frozen=True, slots=True)
class CapabilityAssignment:
    """The capability role one person holds in one workspace.

    ⛔ **At most one**, which is what makes *"Effective permissions"* a single
    answer rather than a union the customer has to reason about.

    ⚡ **`role_id` is `None` for *no capability role*, and that is the ordinary
    state** — everyone is in it until somebody assigns one, which is how
    ADR-0410 §5's *"every current OWNER and MEMBER keeps exactly the authority
    it has today"* holds by construction.
    """

    user_id: UUID
    role_id: UUID | None = None


def subject_for(
    membership: WorkspaceRole, assignment: CapabilityAssignment | None, role: CapabilityRole | None
) -> str:
    """**The one string handed to `Authorizer.is_allowed`.**

    🔴 **The whole capability layer is this function.** ⚡ **A capability role
    REPLACES the membership role in the tuple** — see the module docstring for
    why the design's *"Change to Analyst"* and *"Effective permissions"* both
    require replacement rather than a union.

    ⛔ **Falls back to the membership role whenever the assignment is absent OR
    the role it names cannot be resolved.** ⚠️ **The second half matters and is
    not defensive coding**: a role deleted between two reads must not leave a
    person with *no* subject, which would deny everything including reading the
    screen that would let somebody fix it. **Falling back to membership is the
    state they were in before anybody assigned anything.**

    ✅ **Pure**, so the rule is testable without Casbin, a database or a
    request — and it cannot be quietly re-implemented inside a dependency
    (§2, behaviour exists exactly once).
    """
    if assignment is None or assignment.role_id is None or role is None:
        return membership.value
    if role.id != assignment.role_id:
        # ⛔ **A mismatched pair is a caller defect, not a fallback.** Silently
        # using the membership role here would hide a resolution bug behind a
        # working screen — and the screen would show the wrong permissions.
        raise CapabilityError("That role is not the one this person is assigned.")
    return role.key
