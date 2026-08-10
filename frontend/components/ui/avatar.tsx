import { cn } from '@/lib/design/cn';

/**
 * **Avatar** — [TASK-1448](../../../docs/BACKLOG.md), against 📁 the App Shell
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Help & account · 32 + 32 · the avatar is the only circle in the
 * > shell."***
 *
 * ## 🔴 The circle is a rule, not a style
 *
 * ⚡ **`lib/shell/top-bar.ts` records why**: *"the avatar's uniqueness is what
 * makes it findable without reading — a second circle anywhere in the frame
 * costs that."* ⛔ **So `rounded-full` here is load-bearing**, and the
 * workspace switcher's 22px tile and the record header's 46px tile are both
 * deliberately `rounded-md`/`rounded-lg` rather than circles.
 *
 * ## ⛔ Initials, never an image
 *
 * **The platform publishes no avatar image for a person or an account.**
 * ⚡ **A placeholder photograph would be a fact the product does not have**,
 * and a broken `<img>` is worse than two letters. ✅ **When an image source
 * exists, it arrives as a prop on this component and every caller inherits
 * it** — which is the reason this is a component rather than a class string.
 *
 * ## ⚠️ Its first caller already existed, inline
 *
 * 📁 **[TASK-1440](../../../docs/BACKLOG.md) built this circle by hand inside
 * `account-menu.tsx`**, because `components/ui` had no avatar. ✅ **That inline
 * copy is replaced here** — ⛔ **a component landing with no caller is what
 * [TASK-1451](../../../docs/BACKLOG.md) exists to prevent**, and this row's own
 * `Delivers` says so.
 */

export type AvatarSize = 'sm' | 'md';

export interface AvatarProps {
  /**
   * ♿ **What the avatar stands for**, used to derive the initials AND as the
   * accessible name. ⛔ **Not optional** — an avatar labelled *"avatar"* tells
   * a screen-reader user nothing they can act on.
   */
  name: string;
  size?: AvatarSize;
  /** ⚡ `true` when the avatar sits beside its own name already rendered. */
  decorative?: boolean;
  className?: string;
}

/** 📁 App Shell: the account avatar is **32px**. `sm` is the 22px row tile. */
const SIZES: Record<AvatarSize, string> = {
  sm: 'h-[22px] w-[22px] text-2xs',
  md: 'h-8 w-8 text-xs',
};

/**
 * ⚡ **Two letters from the ends, not the first two.** *"Vantage Logistics"*
 * reads as `VL`, and `Va` would make every account beginning with the same
 * word look identical in a list — which is the one job initials have.
 */
export function initialsFor(name: string): string {
  const words = name.trim().split(/\s+/).filter(Boolean);
  const first = words[0];
  if (first === undefined) return '??';
  const last = words[words.length - 1] ?? first;
  if (words.length === 1) return first.slice(0, 2).toUpperCase();
  return `${first.slice(0, 1)}${last.slice(0, 1)}`.toUpperCase();
}

export function Avatar({ name, size = 'md', decorative = false, className }: AvatarProps) {
  return (
    <span
      // ♿ **Hidden when the name is already on screen beside it.** Announcing
      // "MR" and then "M. Reinhardt" makes a screen reader read the same person
      // twice, which is noise rather than information.
      aria-hidden={decorative || undefined}
      aria-label={decorative ? undefined : name}
      role={decorative ? undefined : 'img'}
      className={cn(
        // 🔴 **The only circle in the shell.** See the note above.
        'inline-flex shrink-0 items-center justify-center rounded-full',
        'bg-surface-sunken font-semibold text-content-muted',
        SIZES[size],
        className,
      )}
    >
      {initialsFor(name)}
    </span>
  );
}
