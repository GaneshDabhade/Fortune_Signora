import { MINIMUM_PASSWORD_LENGTH } from '@/lib/auth/password';

/** One rule, and whether the password in hand satisfies it. */
export interface PasswordRule {
  readonly label: string;
  readonly met: boolean;
}

/**
 * The rules this meter can answer **from the string alone**, in the design's
 * own words and order.
 *
 * ⚠️ **The design enumerates a fourth — *Not found in a breach corpus* — and
 * it is deliberately absent.** It is not absent because it is hard: Better
 * Auth 1.6.25 **already ships** `haveIBeenPwned`, which checks
 * `api.pwnedpasswords.com` by SHA-1 prefix so the password never leaves the
 * server. **It is absent because it is a *server* check** — the plugin hooks
 * `password.hash` — and [TASK-485](../../../docs/BACKLOG.md) states in terms
 * that *"nothing in this row touches `lib/auth/server.ts` … or any route"*.
 *
 * ⛔ **So it is raised rather than faked.** A fourth row that a client could
 * only ever guess at would be a rule the product does not check, drawn as one
 * it does — and [D-156](../../../docs/DECISION_REGISTER.md) ④ is explicit that
 * **a state whose business rule is missing is not built at all.**
 */
export function evaluatePassword(password: string): PasswordRule[] {
  return [
    { label: `At least ${MINIMUM_PASSWORD_LENGTH} characters`, met: password.length >= MINIMUM_PASSWORD_LENGTH },
    { label: 'Upper and lower case', met: /[a-z]/.test(password) && /[A-Z]/.test(password) },
    { label: 'A number or symbol', met: /[^A-Za-z]/.test(password) },
  ];
}

/**
 * The segmented bar and the rule list from screen `06 · Create account`.
 *
 * ### ⚡ This is a *strength* meter, and the distinction is the whole design
 *
 * **[TASK-485](../../../docs/BACKLOG.md) calls it *"the four password strength
 * list"*, and the platform means it.** `lib/auth/password.ts` records a
 * reviewed position — *"**Length is the only requirement** — composition rules
 * push people toward `Passw0rd!`, which is less entropy in a longer costume"*
 * — so **only the first rule is enforced**, by Better Auth's
 * `minPasswordLength`. The other two describe the password rather than gate
 * it.
 *
 * ⛔ **Which is why nothing here disables the submit button.** Drawing an
 * unmet row and then refusing the form would invent a business rule the
 * product never adopted; drawing it as a *requirement* while letting the form
 * through would be the list lying about itself. **It reports strength, it says
 * so in its accessible name, and enforcement stays where it already lives.**
 *
 * ⚠️ **The bar is three segments where the design draws four**, because it
 * counts the rules that exist rather than a number transcribed from a mock.
 * **A fourth empty segment would be the missing breach check drawn as though
 * it were merely unmet.**
 *
 * ⚡ **Announced politely, never as an alert** — it changes on every keystroke,
 * and `role="alert"` would interrupt a screen-reader user mid-word.
 */
export function PasswordStrength({ rules }: { rules: PasswordRule[] }) {
  const met = rules.filter((rule) => rule.met).length;

  return (
    <div className="mt-2 flex flex-col gap-2">
      <div
        className="flex gap-1"
        role="meter"
        aria-valuenow={met}
        aria-valuemin={0}
        aria-valuemax={rules.length}
        aria-label="Password strength"
      >
        {rules.map((rule) => (
          <span
            key={rule.label}
            className={[
              'h-1 flex-1 rounded-full transition-colors',
              rule.met ? 'bg-success' : 'bg-surface-sunken',
            ].join(' ')}
          />
        ))}
      </div>

      <ul aria-live="polite" className="flex flex-col gap-1.5">
        {rules.map((rule) => (
          <li
            key={rule.label}
            className={[
              'flex items-center gap-2 text-xs',
              rule.met ? 'text-content-muted' : 'text-content-subtle',
            ].join(' ')}
          >
            {/* ⚡ **The tick is knocked out of the dot, not painted white.**
                `text-surface` is the colour of the card the dot sits on — 255
                in light, `21 32 39` in dark — so the mark stays legible when
                the theme inverts. **The first draft named Tailwind's white
                keyword directly and `design-tokens.test.tsx` refused it**,
                which is the guard TASK-491 added doing its job on the next
                screen. ⚠️ **It refused the reworded comment too**, because the
                check reads source text and cannot tell prose from a class —
                **the same trade `globals.css` already documents**, and the
                right one: a guard that skipped comments would skip the place a
                banned value is most likely to be pasted back in from.

                **Drawn rather than typed** for the same reason: an `8px`
                glyph is an arbitrary type size, and the scale check refuses
                those too. An `svg` has no font size to escape the scale. */}
            <span
              aria-hidden
              className={[
                'grid h-3.5 w-3.5 flex-none place-items-center rounded-full',
                rule.met ? 'bg-success text-surface' : 'bg-surface-sunken',
              ].join(' ')}
            >
              {rule.met ? (
                <svg viewBox="0 0 10 10" className="h-2 w-2" fill="none" stroke="currentColor" strokeWidth={2.2} strokeLinecap="round" strokeLinejoin="round">
                  <path d="M1.5 5.2 4 7.5 8.5 2.5" />
                </svg>
              ) : null}
            </span>
            {/* The rule reads the same to a screen reader as it looks, rather
                than leaving the ✓ to carry meaning it cannot carry. */}
            <span className="sr-only">{rule.met ? 'Met:' : 'Not yet:'}</span>
            {rule.label}
          </li>
        ))}
      </ul>
    </div>
  );
}
