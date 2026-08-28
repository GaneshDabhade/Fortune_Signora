/**
 * **The Settings screen's sections and its navigation, in the design's order.**
 *
 * 📁 **`Design Documents/Fortune Signora Settings.html`** — eleven anchored
 * sections and a four-group navigation over them. ⛔ **This file is the only
 * place either list is written**, for the same reason
 * [`lib/accounts/sections.ts`](../accounts/sections.ts) is: a screen that
 * spells its own navigation is a screen whose rail and sections drift.
 *
 * ## ⚠️ Eleven sections, and three of them have a producer
 *
 * **Measured against the repository, not estimated.** Every route the backend
 * publishes was searched for each capability the design names:
 *
 * | Section | Producer |
 * |---|---|
 * | **General** · **Users** · **Audit log** · **Integrations** | ✅ shipped |
 * | Branding · Billing · Feature flags · Roles & permissions · SSO · SCIM · API keys · Webhooks · Security · Data retention | ⛔ **none — no route, no hook, no contract** |
 *
 * ⚡ **So the design names fourteen navigation items and ten of them lead to a
 * capability this product does not have.** 📁 **The established answer is
 * Account 360's**, where the rail lists every section *including* the seven
 * nothing can fill — *"a map that hides the empty rooms is one nobody can
 * trust"* — **each with a sentence saying what is missing and why.**
 *
 * ⛔ **What is NOT done here**: a control that looks operational, a figure with
 * no source, or a section quietly omitted so the screen looks finished. 📁
 * [§20c](../../../CLAUDE.md) — *a screen without a shipped module behind it
 * ships a designed absence.*
 */

/** ⚡ **Where a section's content comes from**, and the absence is a value. */
export type SettingsSupply = 'supplied' | 'absent';

export interface SettingsSection {
  /** 📁 The design's own anchor — `#workspace`, `#users`, `#roles`… */
  readonly id: string;
  /** 📁 The design's section title, verbatim. */
  readonly title: string;
  /** 📁 The design's meta line, beneath the title. */
  readonly meta: string;
  readonly supply: SettingsSupply;
  /**
   * ⛔ **Why nothing can fill it**, in the customer's words — 📁 the same
   * contract `AccountSection.absence` carries. **Required when `absent`.**
   */
  readonly absence?: string;
}

/**
 * 📁 **The design's eleven sections, in the design's order.**
 *
 * ⚠️ **The order is the design's and not a judgement** — `#workspace` first and
 * `#integrations` last is how the page reads, and reordering it to put the
 * producer-backed ones together would be this lane redesigning the screen.
 */
export const SETTINGS_SECTIONS: readonly SettingsSection[] = [
  {
    id: 'workspace',
    /**
     * ⛔ **`Organization`, not the design's `Workspace`** — 📁
     * [ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md):
     * *"a customer says Organization; the platform says workspace."* ⚡ **The
     * translation lives at the frontend edge**, so the anchor stays `#workspace`
     * — it is addressing, not prose — **and only what is READ changes.**
     *
     * 🔴 **This shipped as `Workspace` and rendered as a section heading.**
     * ⚠️ **`vocabulary.test.tsx` walks `app` and `components`; this string
     * lives in `lib`**, so the guard never saw it.
     */
    title: 'Organization',
    meta: 'Identity, region and fiscal calendar',
    supply: 'supplied',
  },
  {
    id: 'users',
    title: 'Users',
    // ⛔ **The design's meta is *"312 seats · 288 active · 6 provisioned this
    // week"*.** ⚡ **Seats and provisioning are billing and SCIM facts and
    // neither has a producer**, so the line states what the product can count.
    meta: 'Everyone who can reach this organization',
    supply: 'supplied',
  },
  {
    id: 'roles',
    title: 'Roles & permissions',
    meta: 'Permissions are additive, never subtractive',
    supply: 'absent',
    absence:
      'Roles are fixed for now — owner, admin and member. Signora cannot yet let you define your own or change what each one may do.',
  },
  {
    id: 'sso',
    title: 'SSO',
    meta: 'Single sign-on and directory provisioning',
    supply: 'absent',
    absence:
      'Signing in through your identity provider, and adding or removing people automatically when your directory changes, are not available yet.',
  },
  {
    id: 'api',
    title: 'API keys & webhooks',
    meta: 'Scoped, rotatable, and logged per call',
    supply: 'absent',
    absence:
      'Signora has no public API keys or webhooks yet, so there is nothing here to issue, rotate or point at your own systems.',
  },
  {
    id: 'security',
    title: 'Security',
    // ⛔ **ADR-0034** — the meta line is read, so it takes the customer word.
    meta: 'Organization-wide',
    supply: 'absent',
    // ⚠️ **Deliberately names where the real control IS.** ⛔ A section saying
    // only *"not available"* on a screen whose subtitle promises attribution
    // would read as *this product has no security*, which is false.
    absence:
      'Organization-wide security rules are not something you can set yet. Your own sign-in security — passwords, two-factor and active sessions — is under your profile.',
  },
  {
    id: 'branding',
    title: 'Branding',
    meta: 'Exports & shared links only',
    supply: 'absent',
    absence:
      'Putting your own mark on exports and shared links is not available yet. The product interface itself is not themeable by design.',
  },
  {
    id: 'flags',
    title: 'Feature flags',
    // ⛔ **ADR-0034** — same rule; `section: 'workspace'` below is an ANCHOR
    // and stays, because addressing is not prose.
    meta: 'Opt in per organization',
    supply: 'absent',
    absence:
      'There is nothing to opt into yet. When a capability ships behind a flag it will appear here, with what turning it on changes.',
  },
  {
    id: 'billing',
    title: 'Billing',
    meta: 'Plan, seats and invoices',
    supply: 'absent',
    absence:
      'Signora does not handle billing yet, so there is no plan, seat count or invoice to show you here.',
  },
  {
    id: 'audit',
    title: 'Audit log',
    meta: 'Immutable · every change is attributed',
    supply: 'supplied',
  },
  {
    id: 'integrations',
    title: 'Integrations',
    meta: 'The systems Signora reads from',
    supply: 'supplied',
  },
] as const;

export interface SettingsNavItem {
  readonly label: string;
  /** ⚡ **The section it scrolls to.** Two items may share one. */
  readonly section: string;
}

export interface SettingsNavGroup {
  readonly label: string;
  readonly items: readonly SettingsNavItem[];
}

/**
 * 📁 **The design's four navigation groups, verbatim** — `navGroups`.
 *
 * ⚠️ **Two pairs share an anchor and that is the design's own doing**: *SSO*
 * and *SCIM* both point at `#sso`, and *API keys* and *Webhooks* both at
 * `#api`. ⛔ **Not deduplicated** — the design lists both because a customer
 * looks for either word, and collapsing them would answer a different question
 * from the one the reader asked.
 *
 * ⛔ **The design's badges are NOT carried**: `312` seats, `3` flags, `2` API
 * keys, `4` webhooks and two `!` warnings are all counts of things this product
 * does not have. ⚡ **A badge is a measurement** — 📁
 * [B-1054](../../../docs/BUGS.md) — **and none of these has been measured.**
 */
export const SETTINGS_NAV: readonly SettingsNavGroup[] = [
  {
    // ⛔ **ADR-0034 again** — this is the navigation group a customer reads.
    label: 'Organization',
    items: [
      { label: 'General', section: 'workspace' },
      { label: 'Branding', section: 'branding' },
      { label: 'Billing', section: 'billing' },
      { label: 'Feature flags', section: 'flags' },
    ],
  },
  {
    label: 'Access',
    items: [
      { label: 'Users', section: 'users' },
      { label: 'Roles & permissions', section: 'roles' },
      { label: 'SSO', section: 'sso' },
      { label: 'SCIM', section: 'sso' },
    ],
  },
  {
    label: 'Developer',
    items: [
      { label: 'API keys', section: 'api' },
      { label: 'Webhooks', section: 'api' },
      { label: 'Integrations', section: 'integrations' },
    ],
  },
  {
    label: 'Governance',
    items: [
      { label: 'Security', section: 'security' },
      { label: 'Audit log', section: 'audit' },
      { label: 'Data retention', section: 'security' },
    ],
  },
] as const;

/** ✅ The sections a shipped module can fill. */
export function suppliedSettings(): readonly SettingsSection[] {
  return SETTINGS_SECTIONS.filter((section) => section.supply === 'supplied');
}

/**
 * ⛔ **The sections nothing can fill**, each with what a customer is told.
 *
 * ⚡ **Exported so the gap is countable** — 📁 the same reasoning
 * `lib/accounts/sections.ts` gives: a repository that can measure *"eight of
 * eleven"* can prioritise it.
 */
export function absentSettings(): readonly SettingsSection[] {
  return SETTINGS_SECTIONS.filter((section) => section.supply === 'absent');
}
