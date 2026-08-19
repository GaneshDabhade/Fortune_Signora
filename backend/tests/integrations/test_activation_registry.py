"""The steps this module asks a customer to take, and what it refuses to ask.

📁 `Fortune Signora Home.dc.html` contract 5 — *"The activation registry is
fetched from the server; card order comes from its priority integer, not from
array position."* ⚡ **This is the half the connections module owns.**
"""

from __future__ import annotations

import pytest

from modules.integrations.domain.catalog import (
    ACTIVATION_STEPS,
    CATALOG,
    Capability,
    CatalogEntry,
    activation_registry,
)


def test_the_registry_is_ordered_by_priority_and_not_by_declaration() -> None:
    """📁 *"card order comes from its priority integer, not from array position."*

    ⛔ **The two agree today**, which is exactly why the assertion is about the
    integers rather than about the tuple: a step inserted in the wrong place
    later must still come out in the right one.
    """
    steps = activation_registry()

    assert [step.priority for step in steps] == sorted(step.priority for step in steps)


def test_the_crm_comes_before_meetings() -> None:
    """📁 *"CRM 100, calls 200, invite 300. Lower is earlier."*"""
    steps = activation_registry()
    order = [step.capability for step in steps]

    assert order.index(Capability.CRM_ACTIVITY) < order.index(Capability.MEETINGS)


def test_both_steps_this_module_owns_are_blocking() -> None:
    """📁 *"Calls is blocking; invite is not."* ⚡ Invite is the other module's."""
    assert all(step.blocking for step in activation_registry())


def test_a_step_nothing_in_the_catalog_supplies_is_not_published(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """⛔ **The product must not ask for something it cannot receive.**

    ⚡ A capability whose every supplying system left the catalog is a step
    with no way to complete it, and asking for it would leave a customer
    hunting for a button that does not exist.
    """
    # ⚠️ **Every supplier, and there are four** — the first draft of this test
    # blanked three and passed for the wrong reason, because `outlook_calendar`
    # still supplied the capability.
    suppliers = [
        slug
        for slug, entry in CATALOG.items()
        if Capability.MEETINGS in entry.live_capabilities
    ]
    assert len(suppliers) > 1, "one supplier makes this test weaker than it looks"
    for slug in suppliers:
        monkeypatch.setitem(CATALOG, slug, CatalogEntry(slug, (), connectable=False))

    assert Capability.MEETINGS not in {step.capability for step in activation_registry()}
    assert Capability.CRM_ACTIVITY in {step.capability for step in activation_registry()}


def test_an_empty_registry_is_representable(monkeypatch: pytest.MonkeyPatch) -> None:
    """🔴 **`AC-H09` needs this to be possible.**

    📁 *"Return the activation registry as an empty array: HM-COPY-11 renders
    and no progress bar is present."* ⛔ **A registry that cannot be empty
    makes state 12 untestable and unreachable** — which is what a hard-coded
    client-side list produced, and why the design puts the registry on the
    server.
    """
    monkeypatch.setattr("modules.integrations.domain.catalog.CATALOG", {})

    assert activation_registry() == ()


def test_every_declared_step_names_a_capability_the_platform_can_act_on() -> None:
    """⛔ **The catalog's own rule, and this is the reader that could break it.**

    ⚡ `LIVE_CAPABILITIES` exists so the product never advertises what the
    pipeline cannot execute. A step declared against a dead capability would
    be that promise wearing a different hat.
    """
    from modules.integrations.domain.catalog import LIVE_CAPABILITIES

    assert all(step.capability in LIVE_CAPABILITIES for step in ACTIVATION_STEPS)
