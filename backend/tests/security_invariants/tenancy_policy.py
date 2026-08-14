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
        # Saved View (R-02, 455 §4), migration 0041. **Not append-only, and
        # the difference is deliberate**: `membership_role_change` records
        # what *was* true, while a saved view is still in use and retiring one
        # changes its present state. `UPDATE` is granted and only retirement
        # uses it — a revision is an INSERT naming the version it replaces.
        "saved_view",
        # Person preferences (TASK-470, Workflow 9), migration 0044.
        # 🔴 **The first table in the platform whose ROWS are filtered by
        # `app.user_id`** — 492 §0's *narrowing of tenant-owned, never a
        # parallel to it*. It is fully tenant-owned (non-nullable
        # `workspace_id`, RLS forced, separate read and write policies) **and
        # then narrower**: every policy also requires
        # `user_id = current_setting('app.user_id')`.
        #
        # ⚠️ **TASK-470's row calls these preferences *account*-scoped and this
        # disagrees with it**, on 418: *"a profile preference, a notification
        # matrix and a session belong to a person within a workspace."*
        # ⛔ **Account-global has no lawful home today** — a table without
        # `workspace_id` could only be platform infrastructure, which a
        # business module may never query, and a profile panel queries this on
        # every render. Recorded at C-247 rather than settled here.
        "person_preferences",
        # Onboarding (TASK-469, Workflow 8), migration 0043. **Every answer
        # column is nullable and the table is still tenant-owned** — a
        # skippable step is a nullable column, not an exempt table, and the
        # confirmations a person gave about their company are as much theirs
        # as anything else in the workspace. `UPDATE` is granted because
        # autosave is an update: *"every step saves on advance and on blur."*
        "onboarding_run",
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
        # The People bounded context (TASK-427), migration 0040. **Two tables,
        # and `person` is deliberately almost empty** — an identity with no
        # name, no contact channel and no provider identifier (C-221). It is
        # tenant-owned rather than shared because two customers tracking the
        # same real human hold two unrelated rows: one workspace's evidence
        # must never become another's.
        "person",
        # Where somebody has worked, as an interval that closes rather than a
        # field that is overwritten (ADR-0400). **The one tenant table in this
        # module that carries an UPDATE grant**, and the reason is in the
        # migration: `ended_on` moves exactly once, from NULL to a date, and
        # nothing else in the row is ever touched.
        "affiliation",
        # The Action Batch context (TASK-463), migration 0042. **Two tables,
        # and the split is what keeps them append-only**: `action_batch` is the
        # identity, written once, and every lifecycle event afterwards is a row
        # in `action_batch_transition`. A single table carrying `state` and
        # `applied_at` would need UPDATE on both.
        "action_batch",
        # The log the current state derives from. Tenant-owned rather than
        # infrastructure despite looking like an event stream: it records one
        # workspace's decisions about one workspace's work, and an approval
        # visible across tenants is the defect the platform exists to refuse.
        "action_batch_transition",
        # The security event stream (TASK-492), migration 0046. **One
        # append-only record every module writes to** — 493 §5. Tenant-owned
        # and not platform infrastructure, and the distinction is the whole
        # reason it is here: `outbox_event` spans every workspace and carries
        # no RLS because the GRANT separates tenants there, whereas this
        # records ONE workspace's activity and a row visible across tenants
        # would be a customer reading another customer's sign-ins.
        "security_event",
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
        # Commercial Profile (TASK-466), migration 0051. A customer's own
        # labels, ratified as ADR-0411. **A leak here reads a company's
        # private opinion of its own accounts** — "Champion lost", "At risk",
        # "M&A" — which is a sharper disclosure than any provider fact beside
        # it, because nobody but the customer knows it.
        "account_tag",
        # Migration 0051. Which accounts wear which tag. **Tenant-owned in its
        # own right and not by association**: it carries `workspace_id`
        # explicitly rather than reaching the tag's, so a policy here does not
        # depend on a join (§8, defense in depth).
        "account_tag_assignment",
        # Commercial Profile (TASK-1479 slice ⓶b), migration 0055. What a
        # customer named their own saved groupings — ADR-0411's third
        # capability. **A leak here reads the customer's private working
        # vocabulary**: "Board reporting set", "Competitive watch" and
        # "Dormant enterprise" say what a company is worried about before any
        # account is attached to them.
        "account_segment",
        # Migration 0055. Which accounts are in which segment. **Tenant-owned in
        # its own right and not by association**: it carries `workspace_id`
        # explicitly rather than reaching the segment's, so a policy here does
        # not depend on a join (§8, defense in depth) — the same reasoning
        # `account_tag_assignment` records above.
        "account_segment_member",
        # Commercial Profile (TASK-1479 slice ⓶b), migration 0056. What one bulk
        # "Add to segment" asked for and what it added.
        "account_segment_batch",
        # Commercial Profile (TASK-1479 slice ⓶), migration 0054. What one bulk
        # owner change asked for and what it moved — the same shape 0052 holds
        # for tags. **A leak here reads a company's account-coverage decisions
        # together with the people they were assigned to.**
        "account_assignment_batch",
        # Commercial Profile (TASK-1479 slice ⓶), migration 0053. Who owns an
        # account and who looks after it — ADR-0411's second capability.
        # **Tenant-owned, and the leak this classification prevents is a
        # commercial one**: who a company has put on which account is its
        # account-coverage strategy, readable in one query.
        "account_assignment",
        # Commercial Profile (TASK-466), migration 0052. What one bulk batch
        # asked for and what it changed — the half `ActionBatchView`
        # deliberately does not publish, because "what each item means belongs
        # to the domain that proposed it". **A leak here reads a company's
        # private labelling decisions together with which accounts they were
        # applied to**, which is more than either table says alone.
        "account_tag_batch",
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
        # `person` holds no mutable fact at all — it is an id and its tenant —
        # so it takes the ordinary immutable grant. **`affiliation` is
        # deliberately absent from this set**: closing an interval is the one
        # legitimate in-place change in the module, and it is not an edit of a
        # fact. See migration 0040, which argues it rather than assuming it.
        "person",
        # Both Action Batch tables, and neither argues an exception. An
        # approval that can be edited is an approval nobody can cite, and
        # nothing here has `affiliation`'s shape — every row is a fact about a
        # moment, and a fact about a moment is never corrected in place
        # (migration 0042; TASK-463).
        "action_batch",
        "action_batch_transition",
        # The security event stream (TASK-492), migration 0046. **An account's
        # history is the one thing that must not be editable** — the rows most
        # worth changing are always the inconvenient ones, and a stream a
        # workspace owner could revise is a stream compliance cannot cite. No
        # UPDATE grant and no UPDATE policy, both withheld rather than one.
        "security_event",
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
        # Migration 0051. **An assignment is made or it is removed; there is
        # no third thing to say about it**, so the join row carries no
        # `UPDATE` grant. ⚠️ **`account_tag` itself is deliberately NOT here**
        # — a rename is a correction to a customer's own label rather than a
        # new published statement, and versioning it would keep a history
        # nobody would cite while turning a rename into four writes. The two
        # tables of one capability differ, and the migration says why.
        "account_tag_assignment",
        # Migration 0055, and on exactly the terms above. **An account is in a
        # segment or it is removed from it; there is no field on the join row a
        # customer can change**, so no `UPDATE` grant exists. ⚠️ **`account_segment`
        # itself is deliberately NOT here**, for the reason `account_tag` is
        # not: renaming *"Board reporting set"* to *"Quarterly pack"* is a
        # correction to a customer's own filing, and versioning it would keep a
        # history nobody would cite while turning one rename into four writes.
        #
        # 🔴 **Registered because the invariant refused the change without it**,
        # which is the pair of mistakes this list catches in both directions: in
        # slice ⓶ this lane registered a table here while granting `UPDATE`, and
        # here it withheld `UPDATE` without registering. **Neither is reachable
        # by reading the migration alone.**
        "account_segment_member",
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
