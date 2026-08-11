/**
 * **The keyboard map, and which of it a customer can actually press** —
 * [TASK-1445](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora App Shell.dc.html` §15 *Keyboard shortcuts*.
 *
 * ## 🔴 The rule this file exists to make unbreakable
 *
 * 📁 **[`command-palette.tsx`](../../components/ui/command-palette.tsx) already
 * states it**, for its own four keys: ⛔ ***"the footer hint and the handler
 * read from one table, so a hint promising a key nothing binds is not
 * expressible. A legend that can drift from the behaviour it documents is
 * worse than no legend — it is read as a contract."***
 *
 * ⚠️ **A shortcut reference is that hazard at the scale of the whole product,
 * and it points BOTH WAYS.**
 *
 * ⛔ **Listing a dead key.** **The design publishes eighteen shortcuts and five
 * were bound.** **A reference that simply rendered the design's list would tell
 * every customer that thirteen things work, and each is disproved by pressing
 * it** — 🔴 **worse than no reference, because a person who presses a published
 * shortcut and gets nothing concludes the PRODUCT is broken.**
 *
 * ⛔ **Omitting a live one, which this file did on its first version** —
 * 📁 [B-239](../../../docs/BUGS.md). **`1`–`9` selects a workspace by position
 * and the design does not publish it**, so a map built from the design alone
 * was silent about a key a customer can press. ⚠️ **The same defect, and the
 * harder one to notice**: nothing fails, nobody complains, the feature simply
 * goes unused.
 *
 * ✅ **So the state is carried per shortcut, and
 * [`shortcut-registry.test.ts`](../../tests/unit/shortcut-registry.test.ts)
 * cross-references it against the source both ways** — a `live` entry whose
 * file binds nothing fails, and a file that binds a global key without
 * appearing here fails too. ⚡ **The second direction is the one that keeps
 * this file true**: it is the direction a registry rots in.
 *
 * ⚠️ **And that guard has a KNOWN LIMIT, stated rather than left to be
 * discovered**: 📁 **it verifies FILES, not CHORDS.** ⛔ **A file registered for
 * one shortcut may bind a second silently** — **which is exactly how `1`–`9`
 * was missed**, since `workspace-switcher.tsx` was already registered for
 * `⌘⇧W`. **Closing it needs a parser rather than a scan**, and that is
 * [B-239](../../../docs/BUGS.md)'s open half.
 *
 * ## ⛔ Three designs publish a shortcut table and they disagree
 *
 * 📁 **App Shell §15, Help Center and User Profile each declare
 * `shortcutGroups`, and three chords have two meanings between them** —
 * ⚠️ **[C-285](../../../docs/LANE_COORDINATION.md)**, raised rather than
 * settled here. **This file follows App Shell**, because the shortcut reference
 * is a shell surface and App Shell is the one design whose subject is the
 * shell. ⛔ **That is a reading, not a ruling** — the ruling is the product
 * owner's.
 */

/** ⚡ Whether pressing it does anything today. */
export type ShortcutState =
  /** ✅ Bound, globally, and it does what the design says. */
  | 'live'
  /**
   * ⚠️ **Bound somewhere narrower than the design's claim.** ⛔ **Distinct from
   * `unbound`**: the key works, and telling a customer it does not would be as
   * wrong as telling them it works everywhere.
   */
  | 'partial'
  /** ⛔ **Nothing binds it.** Pressing it does nothing at all. */
  | 'unbound';

export interface Shortcut {
  readonly id: string;
  /**
   * 🔴 **Whether the DESIGN publishes it**, which is a different question from
   * whether the product binds it.
   *
   * ⛔ **Added because this registry shipped omitting a live shortcut** —
   * [B-239](../../../docs/BUGS.md). 📁 `workspace-switcher.tsx` binds `1`–`9`
   * to select a workspace by position; **the design's `shortcutGroups` does not
   * list it**, so a map built only from the design was silent about a key a
   * customer can press today.
   *
   * ⚠️ **A live shortcut omitted misleads exactly as much as a dead one
   * listed** — ⛔ **the same [§2](../../../CLAUDE.md) defect, pointed the other
   * way.** ✅ **So the map carries both, and this field keeps the design's
   * eighteen countable.**
   */
  readonly published: boolean;
  /** 📁 The design's own words for the command, or the product's where it has none. */
  readonly what: string;
  /** 📁 The design's own notation — ⛔ Apple glyphs, translated by {@link keysFor}. */
  readonly keys: string;
  readonly state: ShortcutState;
  /**
   * ⚡ Repo-relative path of the file that binds it. ⛔ **Required for `live`
   * and `partial`** — it is what the registry test reads.
   */
  readonly boundIn?: string;
  /**
   * 📁 **What a customer is told about the narrowness.** ⛔ **Required for
   * `partial`**, and written in the customer's language rather than naming a
   * component.
   */
  readonly limit?: string;
}

export interface ShortcutGroup {
  readonly label: string;
  readonly items: readonly Shortcut[];
}

/**
 * 📁 **App Shell §15's three groups, in its order, with its labels.**
 *
 * ⛔ **Nothing is omitted for being unbound.** ⚡ **The same reasoning
 * [`rail.ts`](rail.ts) records for a destination a person may not enter** —
 * *"a hidden destination teaches a person the feature does not exist, so they
 * ask for the wrong thing or ask nobody"* — **and the same reasoning
 * [§20c](../../../CLAUDE.md) applies to a screen with no module behind it.**
 * ✅ **Published and marked beats absent**, as long as the mark is honest.
 *
 * 📁 **Measured 2026-08-11** against every `addEventListener('keydown'` in
 * `app/`, `components/` and `lib/`.
 */
export const SHORTCUT_GROUPS: readonly ShortcutGroup[] = [
  {
    label: 'Surfaces',
    items: [
      {
        id: 'palette',
        published: true,
        what: 'Command palette',
        keys: '⌘K',
        state: 'live',
        boundIn: 'components/shell/shell-palette.tsx',
      },
      {
        id: 'ask',
        published: true,
        what: 'Ask Signora',
        keys: '⌘⇧A',
        state: 'live',
        boundIn: 'components/shell/copilot.tsx',
      },
      {
        id: 'notifications',
        published: true,
        what: 'Notifications',
        keys: '⌘⇧N',
        // ⛔ **No notification surface exists to open.** ⚡ Not a missing
        // binding — a missing destination, so binding the key would be the
        // shortcut equivalent of a screen with nothing behind it.
        state: 'unbound',
      },
      {
        id: 'switch-workspace',
        published: true,
        what: 'Switch workspace',
        keys: '⌘⇧W',
        state: 'live',
        boundIn: 'components/shell/workspace-switcher.tsx',
      },
      {
        id: 'utility-panel',
        published: true,
        what: 'Toggle utility panel',
        keys: '⌘.',
        state: 'live',
        boundIn: 'components/shell/utility-panel.tsx',
      },
      {
        /**
         * 🔴 **The design does not publish this one and the product binds it**
         * — [B-239](../../../docs/BUGS.md), and it is the reason
         * {@link Shortcut.published} exists.
         *
         * 📁 `workspace-switcher.tsx`: *"1–9 selects by position."* ⛔ **A
         * customer can press it today**, and the first version of this map was
         * silent about it because the map was built from the design's list
         * alone. ⚠️ **A reference that omits a live key is the same defect as
         * one that lists a dead key**, and it is the harder one to notice.
         */
        id: 'switch-by-position',
        published: false,
        what: 'Switch to workspace 1–9',
        keys: '1 – 9',
        state: 'partial',
        boundIn: 'components/shell/workspace-switcher.tsx',
        limit: 'Works while the organization switcher is open, and not while you are typing in it.',
      },
      {
        id: 'reference',
        published: true,
        what: 'Shortcut reference',
        keys: '?',
        // ✅ **This row's own deliverable**, and the design says why it is not
        // optional: 📁 *"? opens the reference from anywhere."*
        state: 'live',
        boundIn: 'components/shell/shortcuts-reference.tsx',
      },
    ],
  },
  {
    label: 'Navigate',
    items: [
      // ⛔ **The whole `G` family is unbound, for TWO reasons — and only one
      // of them is a keyboard problem.**
      //
      // ⚡ **① The mechanism.** 📁 The design calls them *"Vim-style
      // sequences"* — **a two-key sequence needs a pending-prefix state
      // machine that nothing in this product has**, and building it for a
      // single destination would leave three published chords still dead.
      //
      // 🔴 **② Two of the four name a destination that does not exist.**
      // 📁 `components/shell/navigation.tsx` publishes Home · Attention ·
      // Your business · Signals · Reports · Settings · Docs & support —
      // ⛔ **there is no `/forecast` route and no `/pipeline` route at all.**
      // ⚠️ **So `G F` and `G P` are not a missing binding, they are a missing
      // screen**, and binding them would be a shortcut to a `404`.
      { id: 'go-home', published: true, what: 'Home', keys: 'G H', state: 'unbound' },
      { id: 'go-forecast', published: true, what: 'Forecast', keys: 'G F', state: 'unbound' },
      { id: 'go-pipeline', published: true, what: 'Pipeline', keys: 'G P', state: 'unbound' },
      { id: 'go-accounts', published: true, what: 'Accounts', keys: 'G A', state: 'unbound' },
      {
        id: 'history',
        published: true,
        what: 'Back / forward',
        keys: '⌘[ / ⌘]',
        // ⚠️ **The browser already does this**, which is exactly why it must
        // not be listed as live: ⛔ **Signora binds nothing, so a customer
        // whose browser does not carry the chord gets nothing.**
        state: 'unbound',
      },
      {
        id: 'collapse-rail',
        published: true,
        what: 'Collapse rail',
        keys: '[',
        state: 'live',
        boundIn: 'lib/shell/use-rail-collapse.ts',
      },
    ],
  },
  {
    label: 'Work',
    items: [
      {
        id: 'search-in-view',
        published: true,
        what: 'Search in view',
        keys: '/',
        // ⛔ **No view publishes an in-view filter to focus.**
        state: 'unbound',
      },
      {
        id: 'move-selection',
        published: true,
        what: 'Move selection',
        keys: 'J / K',
        state: 'partial',
        boundIn: 'components/intelligence/sequence.tsx',
        limit: 'Works on an account, to step through the accounts in your sequence.',
      },
      {
        id: 'open-record',
        published: true,
        what: 'Open record',
        keys: '↵',
        state: 'partial',
        boundIn: 'components/ui/command-palette.tsx',
        limit: 'Works in the command palette, on the highlighted result.',
      },
      {
        id: 'open-in-panel',
        published: true,
        what: 'Open in panel',
        keys: '⌘↵',
        state: 'partial',
        boundIn: 'components/ui/command-palette.tsx',
        limit: 'Works in the command palette, on the highlighted result.',
      },
      {
        id: 'select-extend',
        published: true,
        what: 'Select / extend',
        keys: 'X / ⇧X',
        // ⛔ **Nothing in Signora has a multi-row selection to extend.**
        state: 'unbound',
      },
      {
        id: 'edit-cell',
        published: true,
        what: 'Edit cell',
        keys: 'E',
        // ⛔ **No editable cell exists**, and 📁 [C-285](../../../docs/LANE_COORDINATION.md)
        // is open on what this key even means: **App Shell binds `E` to it and
        // two other designs bind `⏎`.**
        state: 'unbound',
      },
    ],
  },
] as const;

/** ⚡ Every shortcut, flat, in the design's order. */
export function allShortcuts(): readonly Shortcut[] {
  return SHORTCUT_GROUPS.flatMap((group) => group.items);
}

/**
 * 📁 **The subset the App Shell design publishes.**
 *
 * ⚡ **Kept countable on purpose**: the design's list is a fixed artifact and
 * a change to it is a design change, ⛔ **while the product's own bindings grow
 * without one.** **Conflating the two loses the ability to say which is which.**
 */
export function publishedByTheDesign(): readonly Shortcut[] {
  return allShortcuts().filter((shortcut) => shortcut.published);
}

/** ✅ What a customer can press right now and have something happen. */
export function pressable(shortcut: Shortcut): boolean {
  return shortcut.state !== 'unbound';
}

/**
 * 📁 **The one sentence the reference states about itself.**
 *
 * ⛔ **Counted, never written by hand.** ⚠️ **A hand-written count is a fact
 * that goes stale the moment somebody binds a key** — and a reference whose
 * own summary is wrong is the [§2](../../../CLAUDE.md) defect: the product
 * asserting something untrue of itself.
 *
 * ⛔ **It does not say *"yet"* and it does not say *"coming soon"***. 📁 The
 * rail already paid for that once — *"at M12.3, three of six said `coming
 * soon` on the screen a customer sees first"* — **and a promise nobody
 * scheduled is the thing [§20c](../../../CLAUDE.md) forbids.**
 */
export function coverage(): string {
  const all = allShortcuts();
  const working = all.filter(pressable).length;
  const dead = all.length - working;
  if (dead === 0) return `All ${all.length} of these shortcuts work.`;
  return (
    `${working} of these ${all.length} shortcuts work today. ` +
    `The other ${dead} are part of Signora's published design and nothing binds them, ` +
    `so pressing one does nothing.`
  );
}

/**
 * 🔴 **The design writes `⌘` and the code binds `⌘` OR `Ctrl`.**
 *
 * ⚠️ **Every modifier binding in this product reads
 * `event.metaKey || event.ctrlKey`** — 📁 `copilot.tsx` states the reason:
 * *"so one product does not bind ⌘ on a Mac and something else on Windows."*
 * ⛔ **The label never followed.** **A reference showing `⌘K` to somebody on
 * Windows is naming a key their keyboard does not have**, and they conclude
 * the shortcut is not for them.
 *
 * ⚡ **`⇧` and `↵` are left alone** — they are the shift and return keys
 * everywhere, and spelling them out would be noise rather than translation.
 */
export function keysFor(keys: string, apple: boolean): string {
  return apple ? keys : keys.replaceAll('⌘', 'Ctrl ');
}

/**
 * ⚡ **Whether this machine's keyboard has a `⌘` key.**
 *
 * ⛔ **Never called during a server render.** 📁 The reference mounts on a
 * keypress, so there is no server pass to disagree with — ⚠️ **and calling
 * this in one would hydrate `⌘` into `Ctrl` and warn.**
 */
export function isApplePlatform(): boolean {
  if (typeof navigator === 'undefined') return true;
  return /Mac|iPhone|iPad|iPod/i.test(navigator.userAgent);
}
