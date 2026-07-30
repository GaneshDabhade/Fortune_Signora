"""The Evidence Set — the closed universe a model is permitted to reference.

**The architectural foundation of grounding.** Everything the AI Platform
guarantees rests on one property: at the moment of an inference, the set of
facts that may legitimately be referred to is *known, finite, and fixed*.
A model may phrase those facts however it likes. It may not add to them.

> **It may generate language. It must never generate facts.**
> (``docs/architecture/28-ai-platform.md``, ratified 2026-07-29)

Six properties, each chosen so that violating it is *unrepresentable*
rather than merely discouraged (CLAUDE.md §2):

**Closed.** A set is built once and never added to. Grounding validates a
response against the universe the model saw; a universe that can grow
afterwards is not a universe, it is a suggestion.

**Single-workspace by construction.** Every fact carries its workspace and
the builder is opened *for* one — so a cross-tenant prompt is not forbidden,
it cannot be assembled. Belt and braces, matching RLS plus explicit
filtering: the set re-verifies at construction even though the builder
already refused.

**Typed.** Values are a closed union of scalars, never nested JSON. This is
not tidiness — it is what makes grounding's quantity check *exact*. The
legitimate numbers in a response are enumerable from the evidence rather
than scraped out of prose with a regular expression, so *"headcount grew
40%"* against evidence saying 12 fails on arithmetic, not on a heuristic.

**Provenanced.** Every fact is addressed by an :class:`EvidenceRef` — a kind
and the identifier the pipeline already minted. A citation therefore resolves
all the way back to a raw provider record, and it keeps resolving after a
rebuild, because upstream identity is derived from evidence rather than
allocated.

**Deterministic.** Facts are held in canonical order and the digest is stable
across processes and runs. **Insertion order is deliberately not preserved:**
order is not information about evidence, and letting it survive would make
the rendered prompt depend on how the caller happened to loop — a hidden
input, which statelessness forbids. A narrative that needs chronology sorts
on a fact's own timestamp, explicitly.

**Silent about language.** There is no ``render``, no ``to_prompt``, no
template anywhere in this module. **Evidence is truth; prompts are
language**, and the moment a fact knows how it will be phrased, changing the
wording becomes a change to the evidence model.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator, Mapping, Sequence
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

#: What a fact's attribute may hold.
#:
#: Deliberately no ``float``: its text form is unstable across platforms,
#: which would make the digest unstable, and the pipeline already works in
#: integers and ``Decimal`` for exactly the reproducibility reasons recorded
#: in the Buying Score Engine. Deliberately no nested structure either — a
#: fact whose value is another object has smuggled a second fact in without
#: a ref, and that one could never be cited.
EvidenceValue = str | int | bool | Decimal | datetime | date


class EvidenceError(ValueError):
    """An evidence set was assembled that could not be a closed universe."""


class WorkspaceMismatchError(EvidenceError):
    """A fact from another workspace was offered to a set.

    The most serious error in this module. Everything else here produces a
    bad explanation; this one would produce a **cross-tenant leak** — and it
    is caught at assembly, before a prompt exists, let alone a vendor call.
    """


@dataclass(frozen=True, slots=True, order=True)
class EvidenceRef:
    """The address of one fact: what kind of thing, and which one.

    A pair rather than a bare identifier, so a citation is resolvable
    without the reader knowing which table to look in, and so two kinds
    sharing an identifier can never collide.
    """

    kind: str
    id: UUID

    def __post_init__(self) -> None:
        if not self.kind.strip():
            raise EvidenceError("an evidence ref has no kind, so nothing could resolve it.")
        if ":" in self.kind:
            raise EvidenceError(
                f"evidence kind '{self.kind}' contains ':', which is the token separator. "
                "A kind that can contain the separator makes a citation ambiguous to parse."
            )

    @property
    def token(self) -> str:
        """The form a model cites and a validator parses.

        Deliberately a flat string: a model asked to reproduce a nested
        object gets it wrong far more often than it gets a short opaque
        token wrong, and every citation that fails to parse is a usable
        response thrown away.
        """
        return f"{self.kind}:{self.id}"

    @classmethod
    def parse(cls, token: str) -> EvidenceRef:
        """Read a citation back. Raises rather than returning ``None`` —
        an unparseable citation is a grounding failure, not an absence."""
        kind, separator, raw_id = token.partition(":")
        if not separator:
            raise EvidenceError(f"citation '{token}' is not a reference: expected 'kind:uuid'.")
        try:
            return cls(kind=kind, id=UUID(raw_id))
        except ValueError as exc:
            raise EvidenceError(f"citation '{token}' does not address anything: {exc}") from exc


@dataclass(frozen=True, slots=True)
class EvidenceFact:
    """One thing that is true, addressed and attributed.

    Built by the caller from its own domain objects. The AI Platform never
    imports a pipeline type — it could not, and should not: this module is
    infrastructure, and a substrate that knows what a buying score is has
    started to become a pipeline stage.
    """

    ref: EvidenceRef
    workspace_id: UUID
    #: A short human-readable summary — *"Raised 24M USD in a Series B"*.
    #: Language chosen by the module that owns the concept, so the AI
    #: Platform never has to name a domain thing it does not understand.
    summary: str
    #: Typed attributes, held in canonical order. Sorted at construction so
    #: two callers building the same fact produce the same digest.
    attributes: tuple[tuple[str, EvidenceValue], ...] = ()

    def __post_init__(self) -> None:
        if not self.summary.strip():
            raise EvidenceError(
                f"fact {self.ref.token} has no summary. A fact a model cannot read is a fact "
                "it will not cite, and an uncitable fact is dead weight in the prompt."
            )
        names = [name for name, _ in self.attributes]
        if len(names) != len(set(names)):
            raise EvidenceError(
                f"fact {self.ref.token} repeats an attribute name. Two values under one name "
                "makes the grounding check depend on which one is read."
            )
        object.__setattr__(self, "attributes", tuple(sorted(self.attributes, key=lambda a: a[0])))

    def canonical_form(self) -> str:
        """A stable text form, for hashing only. Not for prompts."""
        rendered = "|".join(f"{name}={_canonical(value)}" for name, value in self.attributes)
        return f"{self.ref.token}\x1f{self.summary}\x1f{rendered}"


def _canonical(value: EvidenceValue) -> str:
    """One text form per value, **tagged with its type**.

    The tag is not decoration. Without it, values of different types
    collapse onto the same text and two different facts digest identically:
    ``True`` and the string ``"true"``, ``1`` and ``"1"``, a ``date`` and its
    own ISO string. A digest that cannot tell those apart cannot be used to
    decide whether two inferences saw the same evidence.

    ``bool`` is a subclass of ``int`` and ``datetime`` is a subclass of
    ``date``, so each subtype is tested before its parent. Reversing that
    would not create a *collision* — each value's own text still differs —
    but it would tag a bool as an integer, and a canonical form that
    mislabels a type is one nobody can reason about later.
    """
    if isinstance(value, bool):
        return f"b:{'true' if value else 'false'}"
    if isinstance(value, int):
        return f"i:{value}"
    if isinstance(value, Decimal):
        return f"n:{value}"
    if isinstance(value, datetime):
        return f"t:{value.isoformat()}"
    if isinstance(value, date):
        return f"d:{value.isoformat()}"
    return f"s:{value}"


@dataclass(frozen=True, slots=True)
class EvidenceSet:
    """A closed, single-workspace universe of facts.

    Construct through :class:`EvidenceSetBuilder`. Direct construction is
    possible and validated identically — the builder exists because it makes
    the workspace impossible to get wrong, not because this type trusts it.
    """

    workspace_id: UUID
    facts: tuple[EvidenceFact, ...]
    assembled_at: datetime

    def __post_init__(self) -> None:
        if not self.facts:
            raise EvidenceError(
                "an evidence set contains no facts. A model given nothing to reference can "
                "only produce something ungrounded, so this fails here rather than at "
                "validation, where it would look like a model problem."
            )
        foreign = {f.ref.token for f in self.facts if f.workspace_id != self.workspace_id}
        if foreign:
            raise WorkspaceMismatchError(
                f"evidence set for workspace {self.workspace_id} contains facts belonging to "
                f"another workspace: {sorted(foreign)}. A prompt assembled from more than one "
                "workspace is a cross-tenant leak, not a formatting error."
            )
        refs = [f.ref for f in self.facts]
        if len(refs) != len(set(refs)):
            raise EvidenceError(
                "an evidence set repeats a reference. A citation must resolve to exactly one "
                "fact, and a duplicate would make the grounding check depend on scan order."
            )
        object.__setattr__(self, "facts", tuple(sorted(self.facts, key=lambda f: f.ref)))

    def __iter__(self) -> Iterator[EvidenceFact]:
        return iter(self.facts)

    def __len__(self) -> int:
        return len(self.facts)

    def resolve(self, ref: EvidenceRef) -> EvidenceFact | None:
        """The fact at this address, or ``None`` if the universe does not
        contain it. **An unresolvable citation is the definition of an
        ungrounded statement**, so this returning ``None`` is what grounding
        is built on."""
        for fact in self.facts:
            if fact.ref == ref:
                return fact
        return None

    def contains(self, ref: EvidenceRef) -> bool:
        return self.resolve(ref) is not None

    @property
    def refs(self) -> frozenset[EvidenceRef]:
        return frozenset(f.ref for f in self.facts)

    @property
    def digest(self) -> str:
        """SHA-256 over the canonical form — the reproducible half of an
        inference's input.

        Recorded against every inference so the *inputs* to a result are
        exactly reconstructable even though the output is not. Two callers
        assembling the same facts in different orders produce the same
        digest, because order is not information about evidence.

        ``assembled_at`` is deliberately excluded: it records when the set
        was gathered, not what it contains, and including it would give the
        same evidence a different identity every time it was assembled.
        """
        canonical = "\x1e".join(fact.canonical_form() for fact in self.facts)
        return hashlib.sha256(f"{self.workspace_id}\x1d{canonical}".encode()).hexdigest()


class EvidenceSetBuilder:
    """Assembles a set for exactly one workspace.

    The workspace is named once, at the start, and every fact is checked
    against it as it arrives. A caller drawing from two sources is stopped at
    the fact that crosses the line — naming it — rather than at the end,
    where the only available message would be *"something does not match"*.
    """

    def __init__(self, workspace_id: UUID) -> None:
        self._workspace_id = workspace_id
        self._facts: list[EvidenceFact] = []

    @property
    def workspace_id(self) -> UUID:
        return self._workspace_id

    def add(
        self,
        *,
        kind: str,
        id: UUID,
        summary: str,
        attributes: Mapping[str, EvidenceValue] | None = None,
    ) -> EvidenceRef:
        """Record one fact. Returns its ref, so a caller can relate facts to
        each other without reconstructing the address."""
        fact = EvidenceFact(
            ref=EvidenceRef(kind=kind, id=id),
            workspace_id=self._workspace_id,
            summary=summary,
            attributes=tuple((attributes or {}).items()),
        )
        self._facts.append(fact)
        return fact.ref

    def include(self, fact: EvidenceFact) -> EvidenceRef:
        """Record a fact built elsewhere, refusing a foreign workspace.

        The path a real assembler takes when translating another module's
        published views, and the one place a cross-tenant mistake could
        physically arrive.
        """
        if fact.workspace_id != self._workspace_id:
            raise WorkspaceMismatchError(
                f"fact {fact.ref.token} belongs to workspace {fact.workspace_id}, but this set "
                f"is being assembled for {self._workspace_id}. Evidence is never combined "
                "across workspaces."
            )
        self._facts.append(fact)
        return fact.ref

    def extend(self, facts: Sequence[EvidenceFact]) -> None:
        for fact in facts:
            self.include(fact)

    def build(self, *, assembled_at: datetime) -> EvidenceSet:
        """Close the universe. The builder may be reused, but the set it
        produced is fixed."""
        return EvidenceSet(
            workspace_id=self._workspace_id,
            facts=tuple(self._facts),
            assembled_at=assembled_at,
        )
