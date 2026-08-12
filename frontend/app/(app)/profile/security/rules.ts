/**
 * **The Security Center's rules, separated from its markup** —
 * [TASK-1414](../../../../../docs/BACKLOG.md), Workflow 23, against 📁
 * [`Fortune Signora Security Center.dc.html`](../../../../../docs/design-snapshot/screens/)
 * ([D-138](../../../../../docs/DECISION_REGISTER.md)).
 *
 * ## 🔴 Why these are here and not inside a component
 *
 * 📁 **The design states its rules as sentences a customer reads** — *"methods
 * are ordered by how well they resist phishing, and the order is stated rather
 * than implied"*, *"below three remaining, Signora prompts you to
 * regenerate"*. ⚡ **A sentence a customer reads is a claim the product makes**,
 * and a claim that lives inside JSX can only be tested by rendering a screen.
 *
 * ⛔ **Nothing here renders anything**, so each rule can be fire-tested on its
 * own: remove it and exactly one assertion goes red.
 */

/**
 * 📁 **The design's own resistance classes, in the design's own order** —
 * *"methods are ordered by how well they resist phishing, and **the order is
 * stated rather than implied**"*.
 *
 * ⚡ **Stated means the reader sees the class beside the method**, which is why
 * this is data rather than an array sorted somewhere and hoped about.
 */
export const RESISTANCE = ['phishing-resistant', 'codes', 'last-resort', 'vulnerable'] as const;

export type Resistance = (typeof RESISTANCE)[number];

/** 📁 The words the design prints, never a slug shown to a customer. */
export const RESISTANCE_LABEL: Readonly<Record<Resistance, string>> = {
  'phishing-resistant': 'Phishing-resistant',
  codes: 'Codes',
  'last-resort': 'Last resort',
  vulnerable: 'Vulnerable to SIM swap',
};

export interface SecondFactor {
  readonly id: string;
  readonly name: string;
  /** 📁 The design's state chip — *Primary*, *Active*, *7 remaining*. */
  readonly state: string;
  readonly resistance: Resistance;
  /** Why it resists what it resists, in the design's words. */
  readonly explanation: string;
}

/**
 * 🔴 **Ordering by resistance, and the comparison is the rule.**
 *
 * ⛔ **Not `sort()` on a `strength` number** — a number invites *"is 3 better
 * than 2?"*, and 📁 the design's list is a fixed vocabulary of four classes.
 */
export function byResistance(factors: readonly SecondFactor[]): readonly SecondFactor[] {
  return [...factors].sort(
    (a, b) => RESISTANCE.indexOf(a.resistance) - RESISTANCE.indexOf(b.resistance),
  );
}

/**
 * 🔴 **The design's §03 refusal, and why this product must NOT implement it.**
 *
 * 📁 ***"Removing your last phishing-resistant factor is refused, not warned
 * about. The button explains which method would have to be added first."***
 *
 * ⛔ **Two of that rule's three inputs do not exist here.**
 *
 * | The rule needs | This repository has |
 * |---|---|
 * | **A workspace policy requiring a phishing-resistant factor** | ⛔ **Nothing declares one.** No module, no contract, no setting |
 * | **A phishing-resistant factor to protect** | ⛔ **None.** `better-auth@^1.1.0` ships no passkey plugin, and the only enrollable method is TOTP, which the design itself files under *Codes* |
 *
 * ⚡ **So a refusal here would be a policy this lane invented**, enforced on a
 * customer's own account, sourced from a mockup — **and it would be
 * unfalsifiable code besides**: a branch that cannot be reached is
 * [§2](../../../../../CLAUDE.md)'s Decorative Logic, and the fire test for it
 * fails by construction.
 *
 * ✅ **What ships instead is the blast radius**, which the design demands of
 * every destructive control on this page — *"every destructive control states
 * its blast radius before it fires"*. ⛔ **It never refuses.**
 *
 * ⚠️ **Recorded rather than silently dropped**: this is the row's *"the
 * strength meter REPORTS and never gates"* one control along, and the moment a
 * phishing-resistant method exists the refusal becomes implementable and
 * testable on the same day.
 */
export function removalConsequence(
  factors: readonly SecondFactor[],
  removing: string,
): string {
  const remaining = factors.filter((factor) => factor.id !== removing);
  const target = factors.find((factor) => factor.id === removing);
  const name = target?.name ?? 'this method';

  if (remaining.length === 0) {
    return (
      `Removing ${name} leaves your account with a password and nothing else. ` +
      'Your backup codes stop working at the same moment, because they are codes ' +
      'for a second factor you would no longer have.'
    );
  }

  const survivors = remaining.map((factor) => factor.name).join(' and ');
  return `Removing ${name} leaves ${survivors}. You can still sign in.`;
}

/**
 * 📁 ***"Below three remaining, Signora prompts you to regenerate."***
 *
 * ⛔ **Three is the design's number and it lives here once.** ⚡ **`< 3`, not
 * `<= 3`** — the design says *below three*, and a rule that fires one code
 * early teaches a customer the number is approximate.
 */
export const BACKUP_CODE_FLOOR = 3;

export function backupCodesAreLow(remaining: number): boolean {
  return remaining < BACKUP_CODE_FLOOR;
}

/**
 * 📁 ***"Regenerating invalidates all ten immediately — including any you have
 * printed — and that sentence appears in the confirmation, not in a help
 * article."***
 *
 * ⚡ **So the sentence is a value, and the confirmation cannot be written
 * without it.**
 */
export const REGENERATE_CONSEQUENCE =
  'Regenerating invalidates every code you currently hold, immediately — including any you have printed or saved.';

/**
 * 🔴 **§01 · a posture cell either knows something or says it does not.**
 *
 * ⚡ **[P-A](../../../../../docs/DOMAIN_DISCOVERY_REGISTER.md) one level up.**
 * 📁 *A failed read must never render as an empty result* — and on this screen
 * the empty result would be **`Open alerts: none`**, which is the single most
 * dangerous false sentence the product could print. **A person who has been
 * compromised would read it and stop looking.**
 *
 * ⛔ **So an unreadable cell states that it is unreadable, and says why.**
 */
export type PostureReading =
  | { readonly known: true; readonly value: string; readonly meta: string; readonly tone: PostureTone }
  | { readonly known: false; readonly because: string };

export type PostureTone = 'positive' | 'attention' | 'risk';

export interface PostureCell {
  readonly label: string;
  readonly reading: PostureReading;
}

export interface PostureInput {
  /** How many second factors are enrolled. `null` when the read failed. */
  readonly factors: number | null;
  /** How many sessions the account holds. `null` when the read failed. */
  readonly sessions: number | null;
}

/**
 * 📁 **The design's five cells, in the design's order** — Open alerts · Second
 * factors · Active sessions · Backup codes · Recovery.
 *
 * ⛔ **Three of the five are not readable today, and they are still rendered.**
 * ⚡ **Dropping them would report a posture the product cannot see as a posture
 * it has checked**, which is the same false reassurance in a quieter voice.
 */
export function posture(input: PostureInput): readonly PostureCell[] {
  return [
    {
      label: 'Open alerts',
      reading: {
        known: false,
        because:
          'Signora records security events but nothing reads them back yet, so it cannot tell you whether anything is open. It will not say “none”.',
      },
    },
    {
      label: 'Second factors',
      reading:
        input.factors === null
          ? { known: false, because: 'Your factors could not be read just now.' }
          : {
              known: true,
              value: input.factors === 1 ? '1 active' : `${input.factors} active`,
              meta:
                input.factors === 0
                  ? 'A password is your only factor'
                  : 'Authenticator app, with backup codes',
              tone: input.factors === 0 ? 'risk' : 'positive',
            },
    },
    {
      label: 'Active sessions',
      reading:
        input.sessions === null
          ? { known: false, because: 'Your sessions could not be read just now.' }
          : {
              known: true,
              value: input.sessions === 1 ? '1 session' : `${input.sessions} sessions`,
              meta: 'Every issued token, including this one',
              tone: input.sessions > 1 ? 'attention' : 'positive',
            },
    },
    {
      label: 'Backup codes',
      reading: {
        known: false,
        because:
          'How many codes you have left is not something Signora can read — it stores hashes, and counting them is not a capability it has today.',
      },
    },
    {
      label: 'Recovery',
      reading: {
        known: false,
        because:
          'Recovery contacts are not built yet, so there is nothing to report about them.',
      },
    },
  ];
}

/**
 * 📁 **§02 · *"What Signora never does"*** — **the section the row is really
 * about**: *"the design has an explicit section stating the product's own
 * limits, and it must be built as content the product commits to, not as
 * filler."*
 *
 * ⚡ **Four sentences, the design's own, verbatim.** ⛔ **Not paraphrased** —
 * each one is a commitment a support agent can be held to, and rewording a
 * commitment is how it stops being one.
 */
export const NEVER_DOES: readonly string[] = [
  'Ask for your password by email, in chat, or in a support call.',
  'Show a password you have already set, in any form, to anyone including support.',
  'Send a one-time code that you did not just request from a screen you are looking at.',
  'Let an administrator read your session tokens, backup codes or connected-app credentials.',
];

/**
 * 🔴 **§04 · a recovery route states what it proves, how long it takes — and
 * whether it exists.**
 *
 * 📁 ***"Recovery is the weakest link in every account system: it is, by
 * definition, the path that works without your factors. Signora treats it as
 * an attack surface rather than a convenience, so each route states what it
 * proves and how long it takes."***
 *
 * ⛔ **`built` is this repository's addition to the design's shape, and it is
 * the honest half.** 📁 The design draws four routes as though all four work.
 * ⚠️ **Two of them do**: a backup code and a second enrolled factor are Better
 * Auth calls that exist. ⛔ **Admin-assisted recovery is not built** — no
 * request, no two-approver flow, no 24-hour hold, nothing.
 *
 * ⚡ **A recovery route a frightened person tries and finds absent is worse
 * than one they were told about honestly**, which is the design's own argument
 * against the SSO dead end — *"saying this plainly is better than a recovery
 * flow that ends in a dead end after four steps."* **It applies to this
 * product's own gaps exactly as it applies to Okta's.**
 */
export interface RecoveryRoute {
  readonly rank: number;
  readonly title: string;
  readonly tag: string;
  readonly time: string;
  readonly body: string;
  readonly proves: string;
  /** ⛔ **Whether a person can actually take this route today.** */
  readonly built: boolean;
  /** Required when `built` is false: what is missing, in the customer's words. */
  readonly absent?: string;
}

export const RECOVERY_ROUTES: readonly RecoveryRoute[] = [
  {
    rank: 1,
    title: 'A backup code',
    tag: 'Works offline',
    time: 'Immediate',
    body: 'The only route that survives losing your phone and your laptop on the same day, and the only one that needs no third party.',
    proves: 'Proves possession of something issued to you before the incident.',
    built: true,
  },
  {
    rank: 2,
    title: 'A second enrolled factor',
    tag: 'Preferred',
    time: 'Immediate',
    body: 'Your authenticator app on a replacement phone, restored from a backup you already had.',
    proves: 'Proves possession of a factor bound to your identity.',
    built: true,
  },
  {
    rank: 3,
    title: 'Recovery through your identity provider',
    tag: 'Identity provider',
    time: 'Minutes to hours',
    body: 'Your IT department resets your factors at the source. Signora honours the new sign-in.',
    proves: 'Proves whatever your IT department chooses to verify — Signora cannot see that process.',
    built: true,
  },
  {
    rank: 4,
    title: 'Admin-assisted recovery',
    tag: 'Not built',
    time: '—',
    body: 'Two administrators approving out of band, with a mandatory hold during which every channel on your account is alerted.',
    proves: 'It would prove a human vouched for you. Nothing proves that today.',
    built: false,
    absent:
      'This route does not exist yet. There is no way to request it, and no administrator can grant it — so do not plan on it.',
  },
];

/**
 * 📁 ***"There is no self-service reset for SSO accounts. Your identity lives
 * at Okta, so Signora cannot restore access it never granted. Saying this
 * plainly is better than a recovery flow that ends in a dead end after four
 * steps."***
 *
 * ⚡ **Generalised off Okta by name**, because the provider is whichever one a
 * customer uses and the sentence is true of all of them.
 */
export const NO_SELF_SERVICE_RESET =
  'There is no self-service reset for accounts that sign in through an identity provider. Your identity lives there, so Signora cannot restore access it never granted.';
