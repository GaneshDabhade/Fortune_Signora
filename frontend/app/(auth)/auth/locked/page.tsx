import { Lock } from 'lucide-react';

import { AuthLink, AuthShell } from '../../auth-shell';

/**
 * **This account is locked** — [TASK-1467](../../../../../docs/BACKLOG.md),
 * against 📁 `Fortune Signora Authentication.dc.html` §11 *"Account locked"*
 * ([D-138](../../../../../docs/DECISION_REGISTER.md)).
 *
 * ## 🔴 The entry engine has routed here since it shipped, and nothing was here
 *
 * 📁 [`lib/entry/rules.ts`](../../../../lib/entry/rules.ts) rule 05 —
 * *"Account locked — failed attempts"* — **routes to `/auth/locked`.** ⛔ **The
 * route did not exist**, so a locked account was sent to the 404 gate: *"that
 * address does not lead anywhere."* ⚡ **Filed as
 * [B-242](../../../../../docs/BUGS.md)** and fixed here.
 *
 * ⚠️ **It is the worst screen to lose to a 404.** **Somebody who cannot sign in
 * and lands on *"that address does not lead anywhere"* concludes the product is
 * broken rather than that their account needs unlocking** — and there is no
 * second place for them to find out.
 *
 * ## ⛔ What the design draws, and what this screen may honestly say
 *
 * 📁 **The design's card**: *"Five failed sign-in attempts locked the account at
 * 09:02. It unlocks automatically at **09:17**, or you can reset the password
 * now."*
 *
 * 🔴 **None of those three facts is published.** ⚠️ **Measured before writing a
 * line**: [`session.ts`](../../../../lib/entry/session.ts)'s `AccountStanding`
 * is `'locked'` and nothing more — **no attempt count, no lock time, no unlock
 * time, anywhere in `lib/auth` or `lib/entry`.**
 *
 * ⛔ **So they are absent rather than invented** ([§20c](../../../../../CLAUDE.md)):
 * ⚡ **a wrong unlock time is worse than none.** **Somebody told *"it unlocks at
 * 09:17"* waits until 09:17** — and if the number was a guess, they wait for
 * nothing, twice. **The gap is [C-290](../../../../../docs/LANE_COORDINATION.md).**
 *
 * ✅ **What survives is the shape the design is actually about**: **what
 * happened · what it means · one route forward that works today.**
 */
export default function AccountLockedPage() {
  return (
    <AuthShell
      masthead={
        <div
          aria-hidden
          className="flex h-9 w-9 items-center justify-center rounded-lg border border-danger bg-danger-subtle text-danger"
        >
          <Lock className="h-4 w-4" />
        </div>
      }
      // 📁 **The design's heading, verbatim.**
      title="This account is locked"
      footer={
        <>
          {/* 📁 **The design's own second action** — *"or you can reset the
              password now"* — ✅ **and the one route forward that exists
              today.** ⛔ **A *"try again"* link would be a control that does
              nothing**: the account is locked, so signing in is exactly what
              cannot work. */}
          <AuthLink href="/forgot-password">Reset your password</AuthLink>
        </>
      }
    >
      {/* ⚡ **Two sentences, and both are true.** ⛔ **The design's numbers are
          not here and their absence is deliberate** — see the note above.
          ✅ **The lock is stated as temporary and automatic**, which is the
          fact that decides whether somebody waits or acts, and it is the one
          the product does know. */}
      <p className="text-sm leading-6 text-content-muted">
        Too many failed sign-in attempts locked this account. It unlocks on its own after a short
        period — or you can reset your password now and sign in straight away.
      </p>
      <p className="mt-3 text-sm leading-6 text-content-muted">
        {/* ⛔ **The reassurance a locked account actually needs.** ⚡ **The fear
            is not the lock; it is that the data is gone or that somebody else
            is in the account.** 📁 The same rule
            [`StatedAbsence`](../../../../components/feedback/stated-absence.tsx)
            follows: say what is still true. */}
        Nothing in your organization has changed, and no one has been signed in.
      </p>
    </AuthShell>
  );
}
