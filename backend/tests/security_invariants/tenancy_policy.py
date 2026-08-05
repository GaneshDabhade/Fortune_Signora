"""The Tenant Isolation Policy — what makes a table safe to hold tenant data.

Every table in the application schema is exactly one of two things, and the
distinction is declared here rather than inferred:

* **Tenant-owned** — holds a workspace's data. Subject to the full policy
  below, without exception.
* **Platform infrastructure** — owned by platform services, spanning every
  workspace by design (the relay cannot sweep the outbox one tenant at a
  time). Isolated by *privilege* instead of by RLS, and unreachable from
  business modules (migration 0006).

Declaring the split explicitly is the point. Inferring "tenant-owned" from
the presence of a ``workspace_id`` column — the earlier approach — meant a
new table that simply forgot the column was silently classified as platform
infrastructure and exempted from every check. The failure mode of a
misclassification is now a build failure rather than a silent exemption:
a table appearing in neither list fails ``test_every_table_is_classified``.

The policy, per docs/architecture/11-tenancy.md:

1. A tenant identifier column exists and is ``NOT NULL``.
2. Row-Level Security is **enabled and forced** — ``FORCE`` matters
   separately, because without it the table's owner is exempt from its own
   policies.
3. The required policies exist, covering read and write separately: a table
   with only a ``SELECT`` policy silently permits no writes, and one with a
   permissive ``ALL`` policy usually means the write path was never
   considered.
4. No runtime role can bypass RLS.
5. Enforcement is proven by regression tests that fail when the policy is
   removed — not merely asserted to be configured.
"""

from typing import Final

TENANT_IDENTIFIER: Final = "workspace_id"

# Tables holding workspace data. Every one is subject to the full policy.
TENANT_OWNED_TABLES: Final[frozenset[str]] = frozenset(
    {
        "workspace",
        "membership",
        # Provider Platform (M2.1). Each carries workspace_id with forced
        # RLS and the full policy set, created in migration 0007.
        "provider_sync",
        "provider_watermark",
        "raw_provider_record",
        # Provider Platform's target-account consumer (PP-02), migration 0030.
        "target_sync_state",
        # Workspace & Tenancy — an organization can grow (TM-03a), migration
        # 0031. **Tenant-owned like `membership`**, and the one table whose
        # legitimate reader is, at acceptance, not yet in the tenant — which is
        # C-208 and is why acceptance is not built here.
        "invitation",
        # Role-change history (TM-04), migration 0034. **Append-only** — the
        # grant carries no UPDATE, which is the enforcement rather than the
        # convention.
        "membership_role_change",
        # Provider Normalization (M2.2), migration 0008.
        "claim",
        "normalization_outcome",
        # Knowledge Graph (M3A), migration 0009.
        "entity",
        "identity_binding",
        "resolution_decision",
        "relationship",
        # Observation Engine (M3B), migration 0010.
        "observation",
        # Business Event Engine (M4), migration 0011.
        "business_event",
        # Signal Engine (M5A), migration 0012. `signal_profile` is the first
        # **customer-authored** table in the platform — not derived data.
        "signal",
        "signal_profile",
        # How a signal leaves the queue (TASK-405), migration 0039. A record
        # *beside* the signal, never a column on it: the signal states what
        # Signora concluded from evidence, and a person disagreeing with it
        # later has not changed what was concluded.
        "signal_resolution",
        # Buying Score Engine (M5B), migration 0013. `workspace_scoring_model`
        # is the **second** customer-authored table — a workspace's own
        # weighting, which cannot be regenerated from anything.
        "buying_score",
        "workspace_scoring_model",
        # Opportunity Engine (M6), migration 0014. The platform's **first
        # workflow tables**: not derived intelligence and not configuration,
        # but the accumulated record of work a human performed. A pipeline
        # rebuild regenerates intelligence and must not touch these.
        "opportunity",
        "opportunity_state",
        "workspace_opportunity_policy",
        # AI Platform (M8), migration 0015. The platform's first **operational
        # record**: not intelligence, not configuration, not workflow, but
        # Signora's account of its own behaviour when it called a model. It is
        # workspace-owned all the same — the evidence digest and refs it holds
        # address one workspace's facts, and the ungrounded rate is a fact
        # about that workspace's data.
        "ai_inference",
        # AI Platform (M8), migration 0016. The platform's first **materialized
        # AI artifact** — a fifth category. Not derived intelligence, not
        # configuration, not workflow, not operational history: a grounded
        # explanation deliberately persisted for auditability, user experience
        # and provenance, and the first row in the platform holding text a
        # customer reads.
        "ai_narration",
        # AI Reasoning Engine (M9), migration 0017. The **Decision Package** —
        # also a materialized AI artifact, and the first row a customer will
        # read in order to *disagree* with Signora rather than merely to learn
        # from it. Its own table rather than a discriminator on `ai_narration`:
        # different shape, different consumers, and a shared table with a
        # `kind` column would be one representation serving two truths.
        "ai_reasoning",
        # AI Research Engine (M10), migration 0018. **Three tables because
        # there are three data categories**, not because there are three
        # types: `research_task` is operational history, `research_finding` is
        # derived intelligence rebuildable from the rows it cites, and
        # `research_synthesis` is a materialized AI artifact. They inherit the
        # storage rules of their category, and a pipeline rebuild treats each
        # differently — it regenerates findings, must never fabricate a
        # synthesis, and records tasks.
        "research_task",
        "research_finding",
        "research_synthesis",
        # Commercial Profile (M12.5), migration 0019. **Customer-authored
        # declaration** — the second table in the platform that cannot be
        # regenerated from anything, after `signal_profile`. A pipeline
        # rebuild must leave it untouched.
        "product_catalog",
        # Commercial Profile (M12.5 slice 2), migration 0020. Who buys each
        # product, as the customer described them — customer-authored on the
        # same terms, and the one whose leak would be the most commercially
        # damaging in the platform: it states a company's whole go-to-market
        # position in its own words.
        "icp_declaration",
        # Commercial Profile (ICP-01), migration 0031. **The same customer
        # declaration, given an identity.** Four tables because each answers a
        # question the others must not: `icp_segment` is what every future
        # citation points at and holds nothing else, `icp_segment_version` is
        # published content, `icp_segment_product` is which products a segment
        # buys — versioned with the content — and `icp_segment_state` is the
        # append-only lifecycle whose rows *are* the audit log. Every one is
        # customer-authored and unregenerable, on `icp_declaration`'s terms
        # (ADR-0041).
        "icp_segment",
        "icp_segment_version",
        "icp_segment_product",
        "icp_segment_state",
        # AI Research Engine (M12.4), migration 0021. **Workflow state**, the
        # same category as `opportunity` — a person asked Signora to spend a
        # model call, and nothing reproduces that. Deliberately not columns on
        # `research_task`: an artifact records what a run produced and exists
        # only when one succeeded, while a request survives a failure and is
        # the only record that anybody wanted this.
        "research_request",
        "research_request_state",
        # Commercial Profile (M12.5 slice 3), migration 0021. Who decides
        # about each product — job titles the customer typed, never people:
        # person entities are deferred platform-wide, and this table names
        # none.
        "buying_committee",
        # Commercial Profile (M12.5 slice 4), migration 0023. What the
        # customer is pushing right now — the fastest-changing of the four
        # declarations, and the one whose staleness a customer notices first.
        "commercial_focus",
        # Commercial Profile (M12.5 slice 5), migration 0025. The companies a
        # customer wants watched — **the pipeline's input**, and the only
        # declaration anything downstream reads. A leak here tells a
        # competitor exactly which accounts a company is pursuing.
        "target_account_list",
        # Commercial Profile (Epic D phase 1), migration 0036. Which
        # technologies a customer competes against — **the fact only the
        # customer has**, and a leak here tells a competitor exactly who a
        # company believes it is losing to.
        "declared_competitors",
        # Timeline (M7 slice 1), migration 0026. **The first table that is a
        # projection**: every row is derived from an event whose source of
        # truth is another module's table, so losing it loses an index over
        # facts rather than any fact. It is still tenant-owned and still
        # forced-RLS — a projection of workspace-scoped facts is workspace-
        # scoped, and being rebuildable is not an isolation argument.
        "timeline_entry",
        # Integrations (M13 slice 1), migration 0027. **The customer's own
        # systems**, as opposed to Signora's suppliers — a distinction
        # `04-modules.md` calls permanent. `integration_grant` holds a
        # `secret_ref` and never secret material: a token in a replicated,
        # backed-up table is an incident, and the vault arrives behind a port.
        # A leak of `connected_account` alone would tell a competitor which
        # systems a company runs.
        "connected_account",
        "integration_grant",
        # Integrations (M13 slice 4), migration 0028. **The only table in the
        # platform holding customer credential material**, encrypted at rest
        # with a key injected as configuration. Its own table rather than a
        # column on the grant: the grant is read on every connections screen
        # and this is read only when a call is about to be made.
        "integration_secret",
        # Integrations (TASK-407), migration 0038. **What happened when the
        # platform actually tried to use a connection** — the only evidence
        # that a credential still works, as opposed to still looking right.
        # Tenant-owned because a probe names one workspace's connection, and
        # its `detail` describes that customer's system.
        "connection_probe",
    }
)

# Platform infrastructure. Spans workspaces by design; isolated by grant
# rather than by RLS, and readable only by platform identities.
#
# Adding a table here is a deliberate architectural act, not a way to make a
# failing test pass. It asserts that the table holds no data a tenant could
# read that belongs to another — or that the only roles able to read it are
# platform services.
PLATFORM_INFRASTRUCTURE_TABLES: Final[frozenset[str]] = frozenset(
    {
        "outbox_event",
        "processed_event",
        "dead_letter_event",
        "alembic_version",
    }
)

# `workspace` is the tenancy root and cannot have a `workspace_id` pointing
# at something else — its own `id` *is* the tenant identifier. Its policies
# are split INSERT/SELECT/UPDATE to break the bootstrap circularity of
# creating the first workspace before any membership exists.
TENANCY_ROOT: Final = "workspace"

# Commands every tenant-owned table must have a policy for. DELETE is not
# required: a table with no delete path is a legitimate design, and
# demanding a policy would encourage adding one that is never used.
REQUIRED_POLICY_COMMANDS: Final[frozenset[str]] = frozenset({"SELECT", "INSERT", "UPDATE"})

# Tables whose rows are **immutable by design**. These legitimately have no
# UPDATE policy and no UPDATE grant — requiring one would mean weakening
# immutability to satisfy a test, which is exactly backwards.
#
# `claim` holds evidence. Evidence is never edited: new information is a new
# claim. Timeline, the Observation Engine, and AI Reasoning all depend on
# being able to see what was believed *when*
# (docs/architecture/20-provider-simulation.md; M2.2 ruling).
#
# `resolution_decision` holds knowledge's history. A decision that can be
# edited is a decision whose history cannot be trusted, so a correction is a
# new decision naming the one it supersedes — which is also why its
# supersession pointer points backwards (migration 0009; M3A ruling).
#
# `observation` records what changed. A late-arriving claim makes an earlier
# observation *less precise*, never false, so the finer observations name the
# coarser one they refine and it stays readable as what was believed then
# (migration 0010; M3B ruling).
#
# `business_event` is durable business history. A phenomenon that extends
# or a conclusion that is corrected produces a new event naming the one it
# replaces — future intelligence modules are expected to reason over
# complete historical sequences, which requires the sequence to exist
# (migration 0011; M4 ruling).
#
# `signal` holds commercial hypotheses; a hypothesis that gains evidence
# becomes a new signal naming the one it replaces. `signal_profile` is
# customer-authored configuration: an edit in place would make every
# historical signal unexplainable, because the reason it exists would have
# changed underneath it (migration 0012; M5A ruling).
#
# `signal_resolution` records one person's decision about one signal. Changing
# your mind is a *new* row naming the one it supersedes, so the queue can show
# what is true now while the history of how it got there stays readable — and a
# dismissal somebody regretted cannot quietly cease to exist. Editable, it
# would be the one record of what a customer decided that nobody could cite
# (migration 0039; TASK-405).
#
# `ai_inference` is Signora's account of its own behaviour. The ungrounded
# rate read from an editable table would be a number nobody could defend —
# and the rows worth editing are exactly the embarrassing ones (migration
# 0015; M8).
#
# `ai_reasoning` is the same category as `ai_narration` and for the same
# reason: it records the conclusion a customer was actually shown, with the
# evidence, support and limits that accompanied it. A better conclusion is a
# new package naming a later score (migration 0017; M9).
#
# `ai_narration` is a **historical fact, not current truth** (ratified
# 2026-07-30). It records what the platform produced at one moment, against
# one prompt, one model and one evidence set. Prompt evolution produces a new
# narration; editing one would destroy the only record of what a customer was
# actually shown, and silently invalidate every evaluation and audit citing it
# (migration 0016; M8).
#
# `research_task` is immutable **before it has a lifecycle**, deliberately.
# Budget, timeout and resumability arrive with the orchestrator; withholding
# UPDATE now decides that progress is recorded as append-only state rows, the
# way `opportunity_state` records workflow, rather than as columns mutated in
# place (migration 0018; M10).
#
# `research_finding` is derived and content-addressed: recomputing it produces
# the same key, so a correction is a different finding rather than an edit to
# this one. `research_synthesis` is the same category as `ai_narration` and
# `ai_reasoning` — what a model actually produced, at one moment, against one
# prompt and one set of findings (migration 0018; M10).
#
# Adding a table here is a deliberate architectural act. The immutability it
# claims is separately asserted in test_tenancy_policy.py.
IMMUTABLE_TENANT_TABLES: Final[frozenset[str]] = frozenset(
    {
        "claim",
        "resolution_decision",
        "observation",
        "business_event",
        "signal",
        "signal_profile",
        "signal_resolution",
        "buying_score",
        "workspace_scoring_model",
        "opportunity",
        "opportunity_state",
        "workspace_opportunity_policy",
        "ai_inference",
        "ai_narration",
        "ai_reasoning",
        "research_task",
        "research_finding",
        "research_synthesis",
        # A revision is a new version naming the one it supersedes; no
        # `UPDATE` grant exists. `DELETE` deliberately does — erasability is
        # a tenancy property, and the first draft of migration 0019 withheld
        # it until this suite refused.
        "product_catalog",
        # Migration 0020, on identical terms: no `UPDATE` grant, `DELETE`
        # granted because erasability is a tenancy property.
        "icp_declaration",
        # Migration 0038. **A probe records a moment and is never
        # corrected** — a later probe supersedes it by being later, and
        # health is derived from the run rather than stored. `DELETE` on the
        # same erasability grounds as every other table here.
        "connection_probe",
        # Migration 0031, and the whole aggregate is append-only: content is
        # superseded, lifecycle is appended, and nothing is edited. `DELETE`
        # is granted on the same erasability grounds as every other table
        # here.
        "icp_segment",
        "icp_segment_version",
        "icp_segment_product",
        "icp_segment_state",
        # A request is written once and its progress is appended, exactly as
        # `opportunity`/`opportunity_state` are — which is the shape migration
        # 0018 committed to when it withheld UPDATE from `research_task`
        # *before* research had a lifecycle. The status **is** the audit
        # trail, so the two cannot disagree (migration 0021; M12.4).
        "research_request",
        "research_request_state",
        # Migration 0021, likewise.
        "buying_committee",
        # Migration 0023, likewise.
        "commercial_focus",
        # Migration 0025, likewise.
        "target_account_list",
        # Migration 0036, likewise.
        "declared_competitors",
        # Migration 0026. A projected entry records what an upstream module
        # said at one moment; a correction is a new entry naming the event it
        # came from. No `UPDATE` grant, `DELETE` granted on the same terms.
        "timeline_entry",
        # Migration 0028. Credential material is never edited: rotating writes
        # a new `secret_ref` and the old one is purged. Editing in place would
        # destroy the previous value at exactly the moment a rotation is being
        # diagnosed.
        "integration_secret",
        # Migration 0034. What somebody was allowed to do, and when it changed.
        # A role that can be edited in place is a role whose history cannot be
        # trusted, and *"who made Ravi an owner?"* becomes unanswerable — which
        # is the whole reason this table exists rather than the role column
        # simply being overwritten.
        "membership_role_change",
    }
)

# Runtime roles. None may bypass RLS, whatever else they are permitted.
RUNTIME_ROLES: Final[tuple[str, ...]] = ("signora_app", "signora_auth", "signora_relay")
