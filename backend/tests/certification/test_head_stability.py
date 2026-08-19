"""**A certification names one commit, and B-1025 is what happens when it does not.**

Cycle 249 committed a documentation change while the gates were running. The
tree stayed clean, every gate passed, and the run recorded a commit that did
not exist when it started — beside an attempt log naming the one that did.
"""

from __future__ import annotations

import pytest

from tests.certification.__main__ import refuse_if_head_moved
from tests.certification.record import CertificationError


def test_an_unmoved_head_is_accepted() -> None:
    refuse_if_head_moved(started="12c21acb6866", finished="12c21acb6866")


def test_a_moved_head_is_refused_before_anything_is_recorded() -> None:
    with pytest.raises(CertificationError) as refusal:
        refuse_if_head_moved(started="12c21acb6866", finished="0d61c30a107a")

    #: **Both SHAs, because one of them alone does not identify the problem.**
    message = str(refusal.value)
    assert "12c21acb6866" in message
    assert "0d61c30a107a" in message
