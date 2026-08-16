"""Inbound machine credentials — a third party authenticating TO Signora.

⛔ **Not [`integrations`](../integrations/), which is the near-miss.** 📁
[ADR-0414](../../../docs/architecture/adr/0414-machine-credentials-bounded-context.md)
§2: that module owns credentials for the OPPOSITE direction, and
[§13](../../../CLAUDE.md) forbids exactly this class of reuse — *"a sign-in
OAuth token must never be reused as an integration OAuth token"*.
"""
