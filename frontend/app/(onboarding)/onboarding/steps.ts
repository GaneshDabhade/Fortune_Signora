import type { Choice, RailStep } from '@/components/ui';
import type { Goal } from '@/lib/api/onboarding';

/**
 * **The design's own enumerations**, read from
 * `docs/design-snapshot/screens/Fortune Signora Onboarding.dc.html` and put
 * in one file so every screen reads the same list.
 *
 * ⛔ **This is not a restatement of the design** ([D-137](../../../../docs/DECISION_REGISTER.md)
 * forbids a copied checklist). **It is the implementation of the enumerations
 * the design draws** — the same relationship the domain's `Goal` enum has to
 * the same six labels, and the reason the two are asserted equal in
 * `tests/components/onboarding.test.tsx`.
 */

/**
 * The six steps, in the design's order. `03` is TASK-468's screen and appears
 * here because the rail shows it throughout.
 *
 * ### ⚠️ The design labels step 2 *Workspace* and this says *Organization*
 *
 * ⛔ **Not a correction to the design — [ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)
 * applied at the edge it names.** *"A customer says Organization… the
 * platform says workspace,"* and *"the translation lives at the frontend edge
 * and never travels inward."* **The `id` stays `workspace`** — it is the
 * route, the API path and the domain's own word, and none of those change.
 *
 * ⚡ **`vocabulary.test.tsx` is what found it**, which is the guard doing
 * exactly what §4 says it exists for: *"a glossary nobody can violate is
 * documentation pretending to be code."* **Raised as [C-246](../../../../docs/LANE_COORDINATION.md)
 * so the design and the ADR are reconciled by whoever owns both**, rather than
 * left as a difference a reviewer discovers on the screen.
 */
export const RAIL_STEPS: readonly RailStep[] = [
  { id: 'welcome', label: 'Welcome' },
  { id: 'workspace', label: 'Organization' },
  { id: 'company', label: 'Company' },
  { id: 'you', label: 'You' },
  { id: 'goals', label: 'Goals' },
  { id: 'connect', label: 'Connect' },
];

/** Screen `04`. *"Single choice, pre-selected. Never blocks — 'Other' is
 * always available."* */
export const INDUSTRIES: readonly Choice[] = [
  { value: 'Logistics & transport', label: 'Logistics & transport' },
  { value: 'Software', label: 'Software' },
  { value: 'Manufacturing', label: 'Manufacturing' },
  { value: 'Financial services', label: 'Financial services' },
  { value: 'Healthcare', label: 'Healthcare' },
  { value: 'Other', label: 'Other' },
];

/**
 * ⛔ **Bands, never a free number.** *"Bands are what benchmarks are computed
 * against."* The values match the domain's `CompanySizeBand` exactly.
 *
 * ⚠️ **Named `SIZE_BANDS`, and the rename was `no-mock-data.test.tsx`'s
 * doing**: a `const` whose name contains that business noun, assigned an
 * array literal, is the fixture shape that guard forbids. ✅ **It was right to
 * ask** — an array of such literals is exactly what it exists to catch — and
 * *bands* is the more accurate word anyway, since not one of these is an
 * organization.
 *
 * ⛔ **The first rewording of this note still failed, because it spelled the
 * old name out** and the check reads source text rather than bindings. **The
 * same trap `password-strength.tsx` hit with a colour utility named in a
 * comment** — worth stating once here so the third instance is recognised.
 */
export const SIZE_BANDS: readonly Choice[] = [
  { value: '1-10', label: '1–10 people' },
  { value: '11-50', label: '11–50 people' },
  { value: '51-200', label: '51–200 people' },
  { value: '201-1000', label: '201–1,000 people' },
  { value: '1001-5000', label: '1,001–5,000 people' },
  { value: '5000+', label: 'More than 5,000 people' },
];

/** Screen `05`. *"Role sets the home page and the alert routing."* */
export const ROLES: readonly Choice[] = [
  {
    value: 'revenue_leader',
    label: 'Revenue leader',
    description: 'CRO, VP Sales — forecast and team view',
  },
  {
    value: 'account_executive',
    label: 'Account executive',
    description: 'Your deals, your accounts',
  },
  {
    value: 'sales_operations',
    label: 'Sales operations',
    description: 'Data quality, territories, reporting',
  },
  {
    value: 'customer_success',
    label: 'Customer success',
    description: 'Renewals, health, expansion',
  },
  { value: 'marketing', label: 'Marketing', description: 'Pipeline sourced, campaign impact' },
  { value: 'executive', label: 'Executive', description: 'Board-level summary only' },
];

/** Screen `06`, and the six replace a feature menu: *"Users can't rank
 * features they haven't used, but they know what is going wrong."* */
export const GOALS: readonly Choice[] = [
  {
    value: 'forecast_accurately',
    label: 'Forecast accurately',
    description: 'Know the number before the board meeting, and defend it.',
  },
  {
    value: 'stop_deals_slipping',
    label: 'Stop deals slipping',
    description: 'Catch the pattern before the second close-date change.',
  },
  {
    value: 'protect_renewals',
    label: 'Protect renewals',
    description: 'See churn signals while there is still time to act.',
  },
  {
    value: 'coach_the_team',
    label: 'Coach the team',
    description: 'Call-level feedback and what the top performers do differently.',
  },
  {
    value: 'find_new_pipeline',
    label: 'Find new pipeline',
    description: 'Accounts matching the ones you already win.',
  },
  {
    value: 'prove_marketing_impact',
    label: 'Prove marketing impact',
    description: 'Sourced and influenced pipeline by campaign.',
  },
];

/** *"Up to three outcomes."* */
export const MAX_GOALS = 3;

export function isGoal(value: string): value is Goal {
  return GOALS.some((goal) => goal.value === value);
}
