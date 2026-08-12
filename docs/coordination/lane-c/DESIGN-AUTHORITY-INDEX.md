# Design Authority Index

**Navigation only. It tells Lane C *where* the design authority lives and reproduces none of it.**

⛔ **If the design changes, the design document is authoritative and this index is stale.** A gap between them is a defect in this file, never in the design.

> **Why this is not a duplicate of [`MANIFEST.md`](../../design-snapshot/MANIFEST.md).** The manifest answers *"is this snapshot intact, and where did it come from?"* — hashes, bytes, provenance, refresh record. **It does not answer *"which document governs Navigation?"*** This file answers only that, and defers to the manifest for identity and integrity.

## The rule that outranks every row below

📁 **[D-138](../../DECISION_REGISTER.md): the Claude Design project is the upstream authority; [`docs/design-snapshot/`](../../design-snapshot/MANIFEST.md) is the *implementation* authority, and implementation reads only the snapshot.** ⛔ **Never reconnect upstream during implementation. Never compare against upstream. A refresh is a deliberate act by Product Office and a new baseline.**

📁 **[D-137](../../DECISION_REGISTER.md): never write a copied specification, exported checklist, summarised design artifact or intermediate implementation guide.** ⚡ **A task references the snapshot path; it does not restate the design.**

## Status of the snapshot

| | |
|---|---|
| **Snapshot date** | **2026-08-06**, partially refreshed 2026-08-08 |
| **Contents** | **31 files · 29 screen designs**, re-measured 2026-08-10 by TASK-1455 |
| **Identity** | ⚠️ **The upstream project exposes no version. The content hashes in [`MANIFEST.md`](../../design-snapshot/MANIFEST.md) are the identity** |
| **Authority level** | ✅ **Finalized for this wave.** Immutable until Product Office records a refresh |

## Index

**All paths are relative to [`docs/design-snapshot/screens/`](../../design-snapshot/screens/) unless stated.**

| Product area | Canonical document | Notes |
|---|---|---|
| **Application Shell** | `Fortune Signora App Shell.dc.html` | ⚡ **The largest and most-cited — 135 KB.** Rail, top bar, utility panel, responsive bands, keyboard. **Open named sections, never the whole file** |
| **Design System / UI foundation** | `Fortune Signora Design System v2.dc.html` · [`design-system/styles.css`](../../design-snapshot/design-system/) | Tokens. ⛔ **[§20c](../../../CLAUDE.md): no literal colours, no Tailwind palette utilities** |
| **Navigation** | `Fortune Signora App Shell.dc.html` | ⚠️ **Not a separate document.** Rail and destinations live in the shell |
| **Responsive behaviour** | `Fortune Signora App Shell.dc.html` | The four bands with `railW` / `panelW` / `filterOpacity` |
| **System / empty / error states** | `Fortune Signora System States.dc.html` | ⚡ **[P-A](../../DOMAIN_DISCOVERY_REGISTER.md): a failed read must never render as an empty result** |
| **Authentication** | `Fortune Signora Authentication.dc.html` | The 400 px card, all 24 screens |
| **Entry / routing** | `Fortune Signora Authenticated Entry.dc.html` · `Entry Coverage Review.dc.html` | Added 2026-08-08 / 08-09 |
| **Onboarding · Workspace Setup** | `Fortune Signora Onboarding.dc.html` · `Workspace Setup.dc.html` | ⚠️ **Two files share the Workspace Setup name — check the manifest hashes** |
| **Security Center** | `Fortune Signora Security Center.dc.html` | |
| **Account 360** | `Fortune Signora Account 360.dc.html` | |
| **Companies · People** | `Fortune Signora Companies.dc.html` · `People Intelligence.dc.html` | |
| **Signal Center** | `Fortune Signora Signal Center.dc.html` | |
| **Opportunity Intelligence** | `Fortune Signora Opportunity Intelligence.dc.html` | |
| **Global Search** | `Fortune Signora Global Search.dc.html` | ⛔ **Distinct from AI Research. The false positive that produced this rule** |
| **AI Research** | `Fortune Signora AI Research.dc.html` | ⛔ **Distinct from Global Search** |
| **AI Copilot** | `Fortune Signora AI Copilot.dc.html` | ⚡ **The assistant is `Signora`, never `Fortune Signora`** ([§4](../../../CLAUDE.md)) |
| **Team Management** | `Fortune Signora Team Management.dc.html` | |
| **Settings · User Profile · Billing** | `Fortune Signora Settings.dc.html` · `User Profile.dc.html` · `Billing.dc.html` | |
| **Workflow Automation** | `Fortune Signora Workflow Automation.dc.html` | |
| **Notification Center** | `Fortune Signora Notification Center.dc.html` | |
| **CRM Integrations** | `Fortune Signora CRM Integrations.dc.html` | |
| **ICP Builder** | `Fortune Signora ICP Builder.dc.html` | |
| **Reports · Executive Dashboard** | `Fortune Signora Reports.dc.html` · `Executive Dashboard.dc.html` | |
| **Help Center** | `Fortune Signora Help Center.dc.html` | |
| **Design Review** | `Fortune Signora Design Review.dc.html` | ⚠️ **A review artifact, not a screen** |

## Overriding authorities

⚠️ **Where a design conflicts with one of these, the design does not win.**

| | |
|---|---|
| **Customer vocabulary** | [ADR-0034](../../architecture/adr/0034-ubiquitous-language.md) — Organization, not workspace, on screen |
| **Product naming** | [§4](../../../CLAUDE.md) — the product speaks as **Signora** alone |
| **Frontend foundation freeze** | [§20c](../../../CLAUDE.md), as amended by [D-170](../../DECISION_REGISTER.md) §2 |
| **Tenancy · security · API** | [§7](../../../CLAUDE.md), [§8](../../../CLAUDE.md), [§13](../../../CLAUDE.md) — **never overridden by a screen** |

## What is *not* indexed here

⛔ **Section numbers are deliberately absent from most rows.** Recording them would make this file a second copy of each design's table of contents — **which drifts, and is what [D-137](../../DECISION_REGISTER.md) forbids.** ✅ **Open the document and read its own headings.**
