/**
 * 📁 Entry rule 10 — `NO_WORKSPACE` — [TASK-1423](../../../../docs/BACKLOG.md).
 *
 * ⚠️ **Outside both shells, and deliberately.** ⛔ The app shell needs an
 * organization to render a rail for and **this is the screen for somebody who
 * has none**; the auth shell is a 400px card for signing in, **and this person
 * is already signed in.**
 */
import { GateScreen } from '../../(auth)/gate/gate-screen';

export default function Page() {
  return (
    <main className="mx-auto flex min-h-screen max-w-xl flex-col justify-center px-6">
      <GateScreen reason="NO_WORKSPACE" />
    </main>
  );
}
