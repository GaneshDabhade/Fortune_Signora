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
