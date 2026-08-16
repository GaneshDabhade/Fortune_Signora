'use client';

import { Avatar } from '@/components/ui';

/**
 * **The design's avatar area** — 📁 `Fortune Signora User Profile.dc.html`,
 * section `01 · Personal profile, avatar & contact information`.
 *
 * ## ✅ What is faithful
 *
 * 📁 ***"72px, `border-radius:999px`, on `var(--brand)`, 24px initials"***,
 * beside a *Avatar* label, the design's own supporting sentence, and a
 * `--sunken` panel explaining cropping. ⚡ **Every string here is the design's.**
 *
 * ## 🔴 What is bounded, and why it is not two dead buttons
 *
 * ⛔ **The design draws *Upload photo* and *Choose colour*. Signora has neither
 * capability** — ✅ **measured**: there is no image endpoint, no object-storage
 * port reachable from the frontend, and nothing on `PreferencesResponse` or
 * Better Auth's user that carries an avatar or a colour.
 *
 * ⚠️ **So the controls are NOT rendered as disabled buttons.** 📁 This
 * repository has paid for that twice and recorded it both times —
 * [`navigation.tsx`](../../../components/shell/navigation.tsx): *"an entry that
 * leads nowhere advertises absence"*, and
 * [`ai-panel.tsx`](ai-panel.tsx): *"a disabled control would invite the
 * question of who may enable it."*
 *
 * ✅ **The structure is faithful and the absence is stated where the buttons
 * would be**, so a reader learns what the avatar currently is rather than
 * meeting a control that does nothing.
 *
 * ⛔ **No `<input type="file">` was substituted**, which would be the generic
 * placeholder the correction explicitly forbids.
 *
 * **The missing capability, exactly:** image upload with square-crop, plus
 * storage and a URL on the person's record. **Nothing here fabricates one.**
 */
export function AvatarArea({ name, email }: { name: string | null; email: string }) {
  return (
    <div className="flex flex-wrap items-start gap-5 border-b border-border pb-6">
      <div className="flex flex-wrap items-center gap-4">
        {/* ⚡ **The shared `Avatar`, at the design's size and on the brand
            colour.** ⛔ **The component is not modified** — 📁 [§20c](../../../../CLAUDE.md):
            its `className` is the sanctioned extension point, and bending the
            default for one screen would make it slightly wrong everywhere else.
            ⚡ **Initials come from the NAME when there is one**, because the
            design draws *"AD"* for *Aurélie Duval* and an address cannot
            produce that. */}
        <Avatar
          name={name ?? email}
          decorative
          className="h-18 w-18 bg-accent text-xl text-accent-contrast"
        />
        <div className="min-w-0">
          <p className="text-sm font-semibold text-content">Avatar</p>
          {/* 📁 The design's own sentence. ⚠️ **The size and format guidance is
              kept even though upload is unavailable**: it is what the avatar
              WILL accept, and removing it would lose the design's statement of
              the rule. */}
          <p className="mt-1 max-w-[34ch] text-xs leading-5 text-content-muted">
            Initials on your brand colour until you upload one. PNG or JPG, square, at
            least 256px, under 2 MB.
          </p>
          {/* 🔴 **Where the design's two buttons are.** ⛔ **Stated rather than
              rendered dead** — see the file docstring. */}
          <p className="mt-2.5 text-xs leading-5 text-content-subtle">
            Uploading a photo and choosing a colour are not available yet. Your initials
            are shown everywhere your avatar appears.
          </p>
        </div>
      </div>

      {/* 📁 The design's `--sunken` cropping panel, kept because it states the
          behaviour an upload will have — ⚡ and it is the design's own copy. */}
      <div className="min-w-[230px] flex-1 rounded-md bg-surface-sunken px-4 py-3.5">
        <p className="text-xs font-semibold text-content-muted">Cropping</p>
        <p className="mt-1.5 text-xs leading-5 text-content-muted">
          Uploads open a square crop with pinch, drag and a zoom slider. The circle mask is
          shown during cropping, never applied to the stored file.
        </p>
      </div>
    </div>
  );
}
