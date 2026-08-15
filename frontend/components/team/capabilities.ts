/**
 * What each role lets somebody do, in the customer's words.
 *
 * **One reviewed catalog, and it is the only place these sentences exist.**
 * Before it, the same distinction was written three times — in the role
 * selector's options, in the roster's text, and in the invitation dialog — and
 * three copies of one fact eventually disagree (`CLAUDE.md` §2).
 *
 * ### It describes capabilities, not permissions
 *
 * `policy.csv` holds thirty tuples across twelve resources. **A customer does
 * not think in tuples and cannot act on one.** They are deciding whether a
 * colleague should be able to bring people in and change how the organization
 * works — which is one sentence, not a matrix.
 *
 * **A tooltip listing `member:add`, `member:remove`, `workspace:update` would
 * be a lie by compression**: it looks complete, omits twenty-seven rows, and
 * uses engineering's vocabulary on the one screen where a customer is making a
 * decision about a person.
 *
 * ### It is deliberately not generated from the policy
 *
 * **The least-powerful-author rule** (`CLAUDE.md` §2): this is *static
 * knowledge a domain expert owns*, like the timeline's headline catalog and
 * the signal taxonomy's `why_it_matters`. Generating it would climb a rung for
 * no gain — the output would drift into resource names the moment somebody
 * added a resource, and nobody would notice until a customer read it.
 *
 * **So it stays stable when permissions evolve internally**, which is the
 * property that makes it worth having: adding `timeline:read` to `member`
 * changes nothing here, because *"see everything Signora finds"* was already
 * true and already said.
 *
 * ### Reviewed like code
 *
 * A change is a diff somebody approves. `frontend/tests/components/team.test.tsx`
 * asserts that no platform vocabulary reaches these strings, on the same terms
 * `vocabulary.test.tsx` applies to every screen.
 */

export type TeamRole = 'owner' | 'member';

export interface RoleCapabilities {
  /** The one-line answer to *"what is this person?"*, used wherever a role is
   * shown as a value rather than explained. */
  readonly summary: string;
  /** What they can do, each a complete sentence a customer could act on. */
  readonly can: readonly string[];
  /** What they cannot — **stated only for the role that lacks something**, so
   * the list is a genuine difference rather than a symmetrical table. */
  readonly cannot: readonly string[];
}

export const ROLE_CAPABILITIES: Record<TeamRole, RoleCapabilities> = {
  owner: {
    summary: 'Can administer Signora',
    can: [
      'Everything a member can do',
      'Invite colleagues, and withdraw an invitation',
      'Remove somebody from this organization',
      'Change what a colleague is allowed to do',
      "Change your organization's settings and what it sells",
    ],
    cannot: [],
  },
  member: {
    summary: 'Works accounts',
    can: [
      'See every account Signora is watching, and why it matters',
      'Read the evidence behind any conclusion',
      'Decide on an account — take it on, close it, or disagree',
      'Ask Signora to research an account properly',
    ],
    cannot: [
      'Invite or remove colleagues',
      "Change what anybody else is allowed to do",
      "Change your organization's settings",
    ],
  },
};

/** The role selector's options, derived so the words cannot drift from the
 * explanation beside them. */
export const ROLE_OPTIONS = (['member', 'owner'] as const).map((role) => ({
  value: role,
  label: ROLE_CAPABILITIES[role].summary,
}));

/**
 * Why a control is absent, said in terms of who *can* do it.
 *
 * *"Only owners can invite colleagues"* is a fact a customer can act on — they
 * know who to ask. **`403 Forbidden` is a fact about a request**, and a screen
 * that simply omits the control leaves them wondering whether the feature
 * exists at all.
 */
export function onlyOwnersCan(action: string): string {
  return `Only owners can ${action}. Ask somebody who administers this organization.`;
}

/* ── What a permission means, in the customer's words ──────────────────────
 *
 * 📁 **[TASK-1479](../../../docs/BACKLOG.md) ⓸** — the design's *Effective
 * permissions* (*"every line names where it comes from"*) and its *Change
 * role* dialog's *Gains* / *Loses*.
 *
 * 🔴 **The server answers in `(resource, action)` pairs and NONE of them may
 * reach a screen.** 📁 `workspace`, `target_account`, `commercial_focus` and
 * `action_batch` are platform vocabulary ([ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)),
 * and ⛔ **`vocabulary.test.tsx` cannot catch them** — it reads source
 * literals, and these arrive at runtime. **The guard has to be this catalog.**
 *
 * ## ⛔ Grouped, because eighty lines is the *lie by compression* above
 *
 * ⚠️ **`policy.csv` grants 34 tuples to `member` and 46 to `owner`.** 📁 The
 * argument at the top of this file applies unchanged: **a customer does not
 * think in tuples and cannot act on one**, and a panel listing eighty rows is
 * the matrix `ROLE_CAPABILITIES` exists to avoid.
 *
 * ✅ **So a resource maps to an AREA a salesperson would name**, and several
 * resources fold into one — *account*, *account_tag*, *account_assignment*,
 * *account_segment* and *target_account* are all *"the companies you watch"*
 * to the person reading it.
 */

/** One thing the server says somebody may do. Mirrors `Permission` on the
 * wire, declared structurally so this catalog imports no API type. */
interface ResourceAction {
  readonly resource: string;
  readonly action: string;
}

/**
 * The areas, in the order a customer would read them — **their own work
 * first, administration last.**
 *
 * ⚠️ **Reviewed like code, and deliberately not generated** — the same rule
 * the role catalog above states. ⛔ **Generating it from `policy.csv` would
 * put `commercial_focus` on a screen the day somebody added a grant**, which
 * is precisely the failure this exists to prevent.
 */
export const CAPABILITY_AREAS: readonly {
  readonly area: string;
  readonly resources: readonly string[];
}[] = [
  {
    area: 'The companies you watch',
    resources: [
      'account',
      'account_tag',
      'account_assignment',
      'account_segment',
      'target_account',
    ],
  },
  { area: 'What Signora finds, and why it matters', resources: ['signal', 'timeline'] },
  {
    area: 'Opportunities, and what to do about them',
    resources: ['opportunity', 'buying_committee', 'action_batch'],
  },
  { area: 'Research on a company', resources: ['research'] },
  { area: 'Saved views', resources: ['saved_view'] },
  {
    area: 'What your organization sells, and who buys it',
    resources: ['product', 'icp', 'commercial_focus', 'competitor'],
  },
  { area: 'Your colleagues, and what they can do', resources: ['member', 'capability_role'] },
  {
    area: "Your organization's settings and connections",
    resources: ['workspace', 'integration'],
  },
  { area: 'Your own profile', resources: ['preferences', 'onboarding'] },
];

/** What somebody may do in one area. */
export interface CapabilityLine {
  readonly area: string;
  /**
   * ⚠️ **Two levels, because two is what this model can honestly express.**
   * 📁 The design draws five — *Full · Team-scoped · Own only · Read · None* —
   * ⛔ **and three of them describe scoping by team or by ownership, which
   * nothing enforces today.** ⚡ **Rendering *Team-scoped* would be a claim no
   * enforcement point makes**, which is the stale-claim class ADR-0410 §3
   * forbids arriving through the UI instead of a table.
   */
  readonly level: 'Can see' | 'Can see and change';
}

/**
 * Turn what the enforcer said into what the screen says.
 *
 * ⛔ **An unrecognised resource is COUNTED, never named and never dropped.**
 * ⚠️ **Dropping it would under-report what somebody may do** — the worst
 * failure this panel has, because a reader would act on the absence — **and
 * naming it would put `commercial_focus` on the screen.** ⚡ **Counting is the
 * only honest third option, and it is visible**: a line reading *"and 2 more"*
 * is what tells the next engineer this catalog needs an entry.
 */
export function describeCapabilities(permissions: readonly ResourceAction[]): {
  readonly lines: readonly CapabilityLine[];
  readonly undescribed: number;
} {
  const byArea = new Map<string, Set<string>>();
  const known = new Set(CAPABILITY_AREAS.flatMap((one) => one.resources));
  const undescribed = new Set<string>();

  for (const permission of permissions) {
    if (!known.has(permission.resource)) {
      undescribed.add(permission.resource);
      continue;
    }
    const area = CAPABILITY_AREAS.find((one) =>
      one.resources.includes(permission.resource),
    )!.area;
    const actions = byArea.get(area) ?? new Set<string>();
    actions.add(permission.action);
    byArea.set(area, actions);
  }

  return {
    // **The catalog's order, not the server's.** A list whose order depended on
    // how the enforcer happened to enumerate resources would reshuffle itself
    // when somebody added one.
    lines: CAPABILITY_AREAS.flatMap(({ area }) => {
      const actions = byArea.get(area);
      if (actions === undefined) return [];
      // ⚡ **Anything beyond `read` is a change**, including `add`, `remove`
      // and `resolve` — a customer reading this is deciding whether somebody
      // can alter their organization, not which verb the API used.
      const changes = [...actions].some((action) => action !== 'read');
      return [{ area, level: changes ? ('Can see and change' as const) : ('Can see' as const) }];
    }),
    undescribed: undescribed.size,
  };
}
