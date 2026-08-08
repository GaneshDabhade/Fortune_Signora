import { AuthLink, AuthShell } from '../../auth-shell';

/**
 * **Screen `10 · Password updated`** — [TASK-488](../../../../../docs/BACKLOG.md).
 *
 * ⚡ **Its own route rather than a state of screen `09`.** The reset token is
 * spent once the password changes, so re-rendering `09` with a success flag
 * would leave a form on screen whose submit could never work again — the
 * false affordance this lane has now refused four times.
 *
 * ⛔ **It does not claim other devices were signed out.** Nothing was:
 * `revokeSessionsOnPasswordReset` is unset, so other sessions survive —
 * [C-244](../../../../../docs/LANE_COORDINATION.md). **A success screen that
 * overstated what happened would be the worst place in the product to do it.**
 */
export default function PasswordUpdatedPage() {
  return (
    <AuthShell
      title="Password updated"
      description="You can sign in with your new password now."
      footer={<AuthLink href="/sign-in">Back to sign in</AuthLink>}
    >
      <p className="text-sm leading-6 text-content-muted">
        If you did not make this change, ask for another reset link straight away and contact
        whoever administers your organization.
      </p>
    </AuthShell>
  );
}
