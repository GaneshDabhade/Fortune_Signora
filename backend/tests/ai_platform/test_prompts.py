"""Prompts as engineering artifacts: identity, immutability, release rules.

The registry that ships in the repository is exercised directly rather than
through fixtures — a manifest that is valid in a test and broken on disk
would be the exact failure this machinery exists to prevent.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

import pytest

from modules.ai_platform.domain.prompt import (
    Evaluation,
    PromptError,
    PromptNotFoundError,
    PromptNotReleasableError,
    PromptRegistry,
    PromptTamperedError,
    PromptVersion,
)
from modules.ai_platform.infrastructure.prompt_loader import (
    MANIFEST,
    PROMPT_DIR,
    load_prompt_registry,
)

#: Every prompt version in the repository, pinned.
#:
#: This is the content-hash lockfile. It does not make an in-place edit
#: *impossible* — nothing in a repository can — but it makes one impossible
#: to perform **quietly**: changing a prompt now requires editing this
#: literal, which is a deliberate, reviewable act rather than a diff nobody
#: reads. Draft versions are pinned too: a version number is a promise from
#: the moment it is committed, because an evaluation may already name it.
PINNED_FINGERPRINTS = {
    "explanation_narration@1": "be511c4152c898ce466b0e4f632d35d4b68aab8661d6da5e6bd04d3f8f276dbb",
}


def a_prompt(**overrides: object) -> PromptVersion:
    kwargs: dict[str, object] = {
        "name": "narration",
        "version": 1,
        "owner": "AI Platform",
        "text": "Restate the facts.",
    }
    kwargs.update(overrides)
    return PromptVersion(**kwargs)  # type: ignore[arg-type]


def an_evaluation(**overrides: object) -> Evaluation:
    kwargs: dict[str, object] = {
        "model": "llama3.1",
        "dataset": "baseline",
        "dataset_version": 1,
        "rubric_version": 1,
        "evaluated_on": date(2026, 7, 30),
        "sample_size": 20,
        "grounding_failures": 0,
        "schema_failures": 0,
        "coverage": 1.0,
    }
    kwargs.update(overrides)
    return Evaluation(**kwargs)  # type: ignore[arg-type]


class TestTheShippedRegistryIsIntact:
    def test_the_repository_registry_loads(self) -> None:
        assert load_prompt_registry().versions

    def test_every_shipped_prompt_matches_its_pinned_fingerprint(self) -> None:
        """Editing a prompt without editing this test is not possible. That
        is the whole mechanism: a silent change becomes a visible one."""
        actual = {v.reference: v.fingerprint for v in load_prompt_registry().versions}
        assert actual == PINNED_FINGERPRINTS

    def test_the_narration_prompt_is_not_yet_usable(self) -> None:
        """It has passed no evaluation, so the release rule refuses it. Not
        an oversight — T120 is what earns it a release, and until then the
        rule working is the system working."""
        prompt = load_prompt_registry().get("explanation_narration", 1)
        assert not prompt.is_released
        with pytest.raises(PromptNotReleasableError, match="nothing yet"):
            prompt.require(model="llama3.1", dataset="baseline")

    def test_every_manifest_entry_has_a_file_and_every_file_an_entry(self) -> None:
        declared = {
            f"{p['name']}@{p['version']}" for p in json.loads(MANIFEST.read_text())["prompts"]
        }
        on_disk = {path.stem for path in PROMPT_DIR.glob("*.md")}
        assert declared == on_disk


class TestContentIdentityOutranksVersionIdentity:
    def test_the_fingerprint_covers_the_text(self) -> None:
        assert a_prompt().fingerprint != a_prompt(text="Say something else.").fingerprint

    def test_the_fingerprint_covers_name_and_version(self) -> None:
        base = a_prompt().fingerprint
        assert a_prompt(name="other").fingerprint != base
        assert a_prompt(version=2).fingerprint != base

    def test_the_fingerprint_ignores_evaluations(self) -> None:
        """Evaluations are observations *about* a prompt, not part of it. A
        fingerprint that moved every time the prompt was measured could not
        identify anything."""
        assert a_prompt().fingerprint == a_prompt(evaluations=(an_evaluation(),)).fingerprint

    def test_the_fingerprint_ignores_the_owner(self) -> None:
        """Reassigning ownership does not produce a different prompt."""
        assert a_prompt().fingerprint == a_prompt(owner="Someone Else").fingerprint

    def test_the_fingerprint_is_stable_across_runs(self) -> None:
        # Computed from the implementation, verified identical across three
        # processes with differing PYTHONHASHSEED. A change here means the
        # identity scheme changed, invalidating every recorded
        # prompt_version — a migration, not a refactor.
        assert a_prompt().fingerprint == (
            "ba6ef7889b9e854df09b2b793a243ac03c4e3275d57d236bdcaa8c4d41f7596c"
        )


class TestATamperedPromptFailsAtStartup:
    def test_text_that_disagrees_with_the_manifest_is_refused(self, tmp_path: Path) -> None:
        """Not at the first inference — by then every result recorded
        against the version was produced by text nobody can recover."""
        (tmp_path / "sample@1.md").write_text("Edited after release.\n")
        (tmp_path / "manifest.json").write_text(
            json.dumps(
                {
                    "prompts": [
                        {
                            "name": "sample",
                            "version": 1,
                            "owner": "AI Platform",
                            "fingerprint": "0" * 64,
                            "evaluations": [],
                        }
                    ]
                }
            )
        )
        with pytest.raises(PromptTamperedError, match="never edited in place"):
            load_prompt_registry(tmp_path)

    def test_a_declared_prompt_with_no_file_is_refused(self, tmp_path: Path) -> None:
        (tmp_path / "manifest.json").write_text(
            json.dumps(
                {
                    "prompts": [
                        {
                            "name": "ghost",
                            "version": 1,
                            "owner": "AI Platform",
                            "fingerprint": "0" * 64,
                            "evaluations": [],
                        }
                    ]
                }
            )
        )
        with pytest.raises(PromptError, match="is missing"):
            load_prompt_registry(tmp_path)

    def test_a_malformed_manifest_is_refused(self, tmp_path: Path) -> None:
        (tmp_path / "manifest.json").write_text('{"prompts": [{"name": "x"}]}')
        with pytest.raises(PromptError, match="malformed"):
            load_prompt_registry(tmp_path)

    def test_a_missing_manifest_is_refused(self, tmp_path: Path) -> None:
        with pytest.raises(PromptError, match="no prompt manifest"):
            load_prompt_registry(tmp_path)


class TestReleaseIsEarnedNotDeclared:
    def test_a_prompt_with_no_evaluation_supports_nothing(self) -> None:
        assert not a_prompt().is_released
        assert not a_prompt().supports(model="llama3.1", dataset="baseline")

    def test_a_passing_evaluation_earns_exactly_its_own_pairing(self) -> None:
        prompt = a_prompt(evaluations=(an_evaluation(model="llama3.1", dataset="baseline"),))
        assert prompt.supports(model="llama3.1", dataset="baseline")
        assert not prompt.supports(model="claude-x", dataset="baseline")
        assert not prompt.supports(model="llama3.1", dataset="contested")

    def test_a_failing_evaluation_earns_nothing(self) -> None:
        """Grounding is deterministic, so a single failure means the prompt
        does not hold on that pairing — there is no partial credit."""
        prompt = a_prompt(evaluations=(an_evaluation(grounding_failures=1),))
        assert not prompt.is_released
        assert not prompt.supports(model="llama3.1", dataset="baseline")

    def test_requiring_an_unearned_pairing_names_what_was_earned(self) -> None:
        prompt = a_prompt(evaluations=(an_evaluation(model="llama3.1", dataset="baseline"),))
        with pytest.raises(PromptNotReleasableError) as caught:
            prompt.require(model="claude-x", dataset="baseline")
        assert "llama3.1/baseline" in str(caught.value)

    def test_requiring_an_earned_pairing_returns_quietly(self) -> None:
        a_prompt(evaluations=(an_evaluation(),)).require(model="llama3.1", dataset="baseline")

    def test_resolve_refuses_an_unearned_pairing(self) -> None:
        registry = PromptRegistry(versions=(a_prompt(),))
        with pytest.raises(PromptNotReleasableError):
            registry.resolve("narration", 1, model="llama3.1", dataset="baseline")

    def test_resolve_returns_an_earned_prompt(self) -> None:
        registry = PromptRegistry(versions=(a_prompt(evaluations=(an_evaluation(),)),))
        resolved = registry.resolve("narration", 1, model="llama3.1", dataset="baseline")
        assert resolved.reference == "narration@1"


class TestEvaluationsAccumulate:
    def test_evaluations_are_held_in_a_stable_order(self) -> None:
        """Two manifests recording the same history in different orders are
        the same history."""
        first = an_evaluation(model="a")
        second = an_evaluation(model="b")
        assert (
            a_prompt(evaluations=(first, second)).evaluations
            == a_prompt(evaluations=(second, first)).evaluations
        )

    def test_the_same_evaluation_recorded_twice_is_refused(self) -> None:
        """A repeat means one overwrote another rather than appending."""
        with pytest.raises(PromptError, match="same evaluation twice"):
            a_prompt(evaluations=(an_evaluation(), an_evaluation()))

    def test_re_evaluating_on_a_later_date_is_an_addition(self) -> None:
        prompt = a_prompt(
            evaluations=(
                an_evaluation(evaluated_on=date(2026, 7, 1)),
                an_evaluation(evaluated_on=date(2026, 8, 1)),
            )
        )
        assert len(prompt.evaluations) == 2

    @pytest.mark.parametrize(
        ("overrides", "expected"),
        [
            ({"model": " "}, "name both a model and a dataset"),
            ({"dataset": ""}, "name both a model and a dataset"),
            ({"sample_size": 0}, "measured nothing"),
            ({"grounding_failures": -1}, "cannot be negative"),
        ],
    )
    def test_a_meaningless_evaluation_is_refused(
        self, overrides: dict[str, object], expected: str
    ) -> None:
        with pytest.raises(PromptError, match=expected):
            an_evaluation(**overrides)


class TestTheRegistryRefusesAmbiguity:
    def test_two_versions_sharing_a_reference_are_refused(self) -> None:
        """Provenance recording that reference would not identify one
        artifact."""
        with pytest.raises(PromptError, match="appears twice"):
            PromptRegistry(versions=(a_prompt(), a_prompt(text="different")))

    def test_an_unknown_prompt_fails_loudly_rather_than_falling_back(self) -> None:
        """No silent "latest": a result recording version 3 must be
        reproducible from version 3."""
        registry = PromptRegistry(versions=(a_prompt(),))
        with pytest.raises(PromptNotFoundError, match="narration@1"):
            registry.get("narration", 3)

    @pytest.mark.parametrize(
        ("overrides", "expected"),
        [
            ({"name": " "}, "has no name"),
            ({"version": 0}, "versions start at 1"),
            ({"text": "   "}, "has no text"),
            ({"owner": ""}, "has no owner"),
        ],
    )
    def test_an_incomplete_prompt_is_refused(
        self, overrides: dict[str, object], expected: str
    ) -> None:
        with pytest.raises(PromptError, match=expected):
            a_prompt(**overrides)


class TestTheRegistryKnowsNothingAboutVendors:
    def test_no_vendor_concept_appears_in_the_prompt_domain(self) -> None:
        """A prompt declares what it requires — a model and a dataset.
        Which vendor serves that model is resolved at runtime, from
        configuration (CLAUDE.md §10)."""
        import modules.ai_platform.domain.prompt as prompt_module

        source = Path(prompt_module.__file__).read_text().lower()
        for word in ("ollama", "anthropic", "claude", "openai", "gemini", "aivendor"):
            assert word not in source, f"the prompt domain mentions the vendor '{word}'"
