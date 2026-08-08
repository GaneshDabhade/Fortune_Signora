import { notFound } from 'next/navigation';

import { loadAuthConfig } from '@/lib/auth/config';

import { AuthShell } from '../auth-shell';
import { SignUpForm } from './sign-up-form';

/**
 * **Read at boot, never baked in.** This page's content depends on which
 * sign-in methods are configured, and Next.js would otherwise prerender it —
 * so an image built without OAuth credentials would keep showing no provider
 * buttons after being deployed *with* them, because the HTML was decided at
 * build time.
 *
 * That is the Infrastructure Contract's environment-based-configuration rule
 * (CLAUDE.md §20b).
 */
export const dynamic = 'force-dynamic';

/**
 * **Screen `06 · Create account`** — *"Create your account · Step 1 of 2 ·
 * takes about a minute"*, [TASK-485](../../../../docs/BACKLOG.md).
 *
 * **404 when password sign-in is off**, rather than a page explaining that
 * registration is unavailable. A route that exists to say it does not work is
 * a dead end somebody can bookmark; with OAuth alone, an account is created by
 * signing in and there is nothing here to do.
 *
 * ⚠️ **The design gives this screen no *"Already have an account?"* line and
 * neither does this page.** The legacy screen had one; [D-162](../../../../docs/DECISION_REGISTER.md)
 * says to pretend it never existed. **It is not a dead end** — the product
 * mark above the card is a link to `/welcome`, which is where both entrances
 * live, and Workflow 1's journey already asserts that.
 */
export default function SignUpPage() {
  if (!loadAuthConfig().passwordEnabled) notFound();

  return (
    <AuthShell title="Create your account" description="Step 1 of 2 · takes about a minute">
      <SignUpForm />

      {/*
        ⚠️ **The design links *Terms* and *Privacy Notice*; these are not
        links, and the difference is deliberate.** The design's own markup
        points both at `#legal` — a placeholder — and **no legal route, page or
        configured URL exists anywhere in this repository**, checked rather
        than assumed. **Two dead links is the exact defect Workflow 1 shipped
        at `Use single sign-on`** and had to repair in milestone 4.

        ⛔ **Writing the documents is not this lane's** — they are legal text,
        not product surface, and inventing them would be worse than omitting
        them ([§21](../../../../CLAUDE.md)). **The sentence stays** because the
        agreement it describes is real and the design requires it to be stated
        before the button is pressed; **the destinations are raised.**
      */}
      <p className="mt-3.5 text-center text-xs leading-relaxed text-content-subtle">
        By continuing you agree to the Terms and Privacy Notice.
      </p>
    </AuthShell>
  );
}
