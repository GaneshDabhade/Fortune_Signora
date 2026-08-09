import { authMode, environmentName, type AuthMode } from '@/lib/auth/config';

import { Badge, type BadgeTone } from './badge';

/**
 * **Which authentication mode is running, said out loud** —
 * [TASK-473](../../../docs/BACKLOG.md), on
 * [ADR-0406](../../../docs/architecture/adr/0406-authentication-execution-modes.md).
 *
 * > 📁 **[D-131](../../../docs/DECISION_REGISTER.md): *"These modes must be
 * > explicit and never silently imitate production behavior. A user or
 * > developer should always know which mode is active."***
 *
 * ## 🔴 A server component, and that is a security property rather than a
 * rendering preference
 *
 * ⛔ **`SIGNORA_ENVIRONMENT` is not a `NEXT_PUBLIC_` variable and must not
 * become one.** ⚡ **Resolving the mode on the server and shipping only the
 * rendered word means the browser learns *development*, never the deployment
 * configuration that produced it.** **A client component would have needed the
 * variable exposed**, and exposing a deployment variable to make a badge is a
 * cost nobody would accept if it were stated that way.
 *
 * ## ⛔ It renders nothing when the mode is `production`
 *
 * 📁 **The row: *"the indicator is absent in production builds, asserted by a
 * test."*** ⚠️ **And *production* here is `authMode()`'s, not `NODE_ENV`'s** —
 * **the file this reads from already documents why, and the distinction was
 * found by a build failing**: 📁 ***"`NODE_ENV=production` means 'an optimised
 * build', not 'deployed to production'"***, so Next sets it while compiling on
 * a laptop. ⚡ **Keyed to `NODE_ENV`, this badge would vanish from `make demo`
 * and from human review — the two places its stated failure actually
 * happens** — while still rendering in a deployed environment configured with
 * a development build. ✅ **Both halves backwards.**
 *
 * ## ⚠️ This is the FACT. The treatment is not this row's
 *
 * 📁 **[D-129](../../../docs/DECISION_REGISTER.md)'s rule, and the row states
 * it: *"How the mode is displayed — a banner, a badge, a startup line — the
 * treatment is the approved design's, and [410](../../../docs/architecture/410-approved-ui-specification.md)
 * is the authority. This row delivers the fact and refuses to invent the
 * presentation."***
 *
 * ⛔ **So this composes `Badge` and adds no visual language of its own** — no
 * position, no placement, no colour outside the token set, and no opinion
 * about where a caller mounts it. ⚡ **When 410 rules on the treatment, what
 * changes is this file's markup; `authMode()` does not move.**
 *
 * ## 🔴 What it is NOT, because it sits next to the thing §13 forbids
 *
 * ⛔ **`CLAUDE.md` §13 bars a *"skip auth in development"* flag by name, and
 * ADR-0406 §2 says this ADR *"is where somebody would reach for one."***
 * ⚡ **This is its opposite: it makes the mode VISIBLE, never PERMISSIVE.**
 * 📁 **`requireEmailVerification` is `true` in all three modes and nothing
 * here touches it** — **and no authentication path reads `authMode()`**, which
 * is ADR-0406 §5's falsifiable claim kept true.
 */

/**
 * ⚡ **Tone carries the warning, and `demo` is the one that earns amber.**
 * ⛔ **A seeded demonstration looks exactly like a real workspace** — that is
 * what makes it useful and what makes mistaking it expensive
 * ([C-320](../../../docs/LANE_COORDINATION.md)). **`development` is neutral
 * because a developer already knows where they are.**
 */
const TONE: Record<Exclude<AuthMode, 'production'>, BadgeTone> = {
  development: 'neutral',
  demo: 'warning',
};

/**
 * ⛔ **The customer's vocabulary, not the platform's** ([ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)).
 * ⚠️ **A developer is not a customer, so this is the narrower rule**: the word
 * says what is *true of the data*, because that is the question being asked —
 * ⚡ ***"did I sign in as a seeded account or create one?"***
 */
const LABEL: Record<Exclude<AuthMode, 'production'>, string> = {
  development: 'Development',
  demo: 'Demo data',
};

export function AuthModeIndicator({ className }: { className?: string }) {
  const mode = authMode();

  // 📁 *"absent in production builds"* — and absent means ABSENT: no wrapper,
  // no empty element, nothing a stylesheet could bring back.
  if (mode === 'production') return null;

  return (
    <Badge
      tone={TONE[mode]}
      className={className}
      // ♿ The badge is two words with no surrounding sentence, so the
      // accessible name has to carry the question it answers.
      aria-label={`Authentication mode: ${LABEL[mode]} (${environmentName()})`}
      data-auth-mode={mode}
    >
      {LABEL[mode]}
    </Badge>
  );
}
