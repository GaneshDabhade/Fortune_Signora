"""Where this module's prompt artifacts live.

**Owned here, not by the AI Platform** — a module owns its own artifacts
(`CLAUDE.md` §2), and `load_prompt_registry(directory)` has been per-directory
since M9 precisely so a second, third and now fourth owner needs no platform
change. Nothing is reimplemented: manifest parsing, fingerprint enforcement,
tamper detection and registry identity are the platform's, reused whole.

**What this module does *not* reuse is the release derivation**, and
`domain/release.py` states why in full: one field on `Evaluation` means the
Commercial Context Protocol here and the evidence rendering protocol
everywhere else.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

from modules.ai_platform.infrastructure.prompt_loader import load_prompt_registry
from modules.ai_platform.public import PromptRegistry

PROMPT_DIR: Final = Path(__file__).resolve().parent.parent / "prompts"
MANIFEST: Final = PROMPT_DIR / "manifest.json"


def prompts() -> PromptRegistry:
    """Every synthesis prompt this process can serve.

    Read once and validated: a manifest disagreeing with the files on disk
    **fails at startup rather than at the first synthesis**, because a prompt
    whose text has drifted from its recorded hash makes every result claiming
    that version unreproducible, and there is no way to notice that afterwards.
    """
    return load_prompt_registry(PROMPT_DIR)
