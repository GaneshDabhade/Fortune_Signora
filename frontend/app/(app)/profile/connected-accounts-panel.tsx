import Link from 'next/link';

/**
 * **Screen `05 · Connected accounts & sessions`** — 📁 `Fortune Signora User
 * Profile.dc.html`.
 *
 * ## 🔴 This section said it was not built, on a page that links to half of it
 *
 * ⛔ **The notice read *"The accounts you have connected, their scope, and
 * **every session signed in as you**."*** ⚡ **The card at the bottom of
 * `/profile` reads *"your password, your second factors, and **every session
 * signed in as you** — including the ones you can end."*** — **the same clause,
 * on the same screen, once as an absence and once as a shipped capability.**
 *
 * ✅ **Sessions are real**: 📁 `profile/security/sessions-panel.tsx` lists them
 * from `authClient.listSessions()`, revokes one, revokes a selection, and signs
 * out everywhere. **The design's §05 sentence *"Sign out everywhere"* is
 * built** — it is one route away, not missing.
 *
 * ## ⛔ What is genuinely absent, and it is the other half
 *
 * 📁 The design is explicit that these are *"your **personal** connections,
 * **separate from the workspace's Salesforce**"*. ⚡ **Measured rather than
 * assumed** — every route in `integrations/interface/router.py` is
 * `/workspaces/{workspace_id}/connections`, and `user_id` appears **only** as
 * `actor_id`, the person who made the change. **There is no such thing as a
 * connection a person owns**, so there is nothing to list and nothing to
 * disconnect.
 *
 * ⛔ **That is stated rather than drawn as an empty table.** ⚡ An empty
 * *"Connected accounts"* table invites somebody to look for the Connect button,
 * and there is not one — 📁 the same refusal [D23](../../../../docs/DECISION_REGISTER.md)
 * makes about a raw identifier: **an absence dressed as information is still an
 * absence, and now it is misleading too.**
 */
export function ConnectedAccountsPanel() {
  return (
    <section className="flex flex-col gap-6" aria-labelledby="accounts-heading">
      <header className="flex flex-col gap-1">
        <h2 id="accounts-heading" className="text-lg font-semibold text-content">
          Connected accounts
        </h2>
        {/* 📁 **The design's own sentence, minus its second clause.** ⛔ *"Each
            one names exactly what it reads"* is a promise about rows that do
            not exist, and it would be the screen describing a capability by
            its future behaviour. */}
        <p className="text-sm leading-6 text-content-muted">
          Your own connections, separate from the ones your organization has set up.
        </p>
      </header>

      <div className="rounded-md border border-border-soft bg-surface-sunken p-5">
        <p className="text-sm leading-6 text-content-muted">
          You have no personal connections, and Signora cannot hold one yet — every
          connection it stores belongs to an organization rather than to a person.
        </p>
        <p className="mt-2 text-xs leading-5 text-content-subtle">
          Your organization’s connections are in Settings, and changing one there
          changes it for everybody.
        </p>
        {/* ⚡ **A route to the thing that DOES exist**, because the reason this
            section is thin is that the capability sits at a different scope —
            and somebody who came here looking for Salesforce should be told
            where it is rather than that it is missing. */}
        <Link
          href="/settings/connections"
          className="mt-3 inline-block rounded text-sm text-content underline decoration-border underline-offset-4 transition-colors hover:decoration-accent"
        >
          Organization connections
        </Link>
      </div>

      <div className="flex flex-col gap-1">
        <h3 className="text-base font-semibold text-content">Active sessions</h3>
        {/* 📁 **The design's sentence, kept whole** — ⚡ including the clause
            about the identity provider, which is the honest half: *"we say so
            rather than implying we control it."* */}
        <p className="text-sm leading-6 text-content-muted">
          Every session signed in as you, and the ones you can end. Signing out
          everywhere ends every session except this one — your identity provider may
          still hold its own.
        </p>
        <Link
          href="/profile/security"
          className="mt-2 inline-block rounded text-sm text-content underline decoration-border underline-offset-4 transition-colors hover:decoration-accent"
        >
          Your sessions
        </Link>
      </div>
    </section>
  );
}
