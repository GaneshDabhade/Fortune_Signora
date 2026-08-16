'use client';

/**
 * **The utility panel** — [TASK-1433](../../../docs/BACKLOG.md), against 📁
 * `Fortune Signora App Shell.dc.html` §13.
 *
 * ## 🔴 The row's risk, and the shape that takes it seriously
 *
 * > ⚠️ ***"Building the chrome because it is the easy half. The chrome is not
 * > the deliverable."***
 *
 * ⛔ **So this component holds no content and cannot invent any.** ⚡ **The
 * shell owns the DOCK; modules supply what is in it** — 📁 the row is explicit
 * that this is *"three modules' worth, none of which is the shell's"*, and
 * 📁 the shell's constitution says *"the frame owns no product decision."*
 *
 * ✅ **A module publishes into a tab with `useUtilityPanel`.** ⛔ **A tab
 * nobody publishes into renders the design's own empty state** — **never
 * invented copy** ([§20c](../../../CLAUDE.md)).
 *
 * ## ⛔ Why the panel is not the only home for what it holds
 *
 * 📁 **Below 1024 the design gives the panel no width at all.** ⚠️ **If a
 * module put its only copy of something here, a phone would lose it
 * entirely** — **and the design never says the CONTENT disappears, only the
 * panel.**
 *
 * ✅ **So `useUtilityPanel` reports whether the panel is carrying the content**,
 * and a module renders it inline when it is not. ⛔ **One component, one data
 * source, two placements decided by the band** — **never two copies, and never
 * both at once.**
 */

import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState } from 'react';
import type { ReactNode } from 'react';

import { cn } from '@/lib/design/cn';
import {
  PANEL_TABS,
  PANEL_WIDTH,
  panelKey,
  panelLabel,
  panelStateFor,
  type PanelState,
  type PanelTab,
} from '@/lib/shell/utility-panel';
import { bandFor } from '@/lib/shell/rail';
import { UTILITY_PANEL_TARGET } from './skip-links';

interface PanelContract {
  readonly state: PanelState;
  readonly width: number | null;
  readonly activeTab: PanelTab;
  readonly setActiveTab: (tab: PanelTab) => void;
  readonly toggle: () => void;
  readonly publish: (tab: PanelTab, content: ReactNode) => void;
  readonly withdraw: (tab: PanelTab) => void;
}

const PanelContext = createContext<PanelContract | null>(null);

/**
 * ⛔ **Published content is a SEPARATE context from the contract**, and that is
 * not tidiness. ⚡ **A module publishes on every data change**, so folding the
 * two together would give every consumer of `useUtilityPanel` a new contract
 * object each time — **and the publish effect would re-run on its own output**,
 * which is an infinite loop rather than a slow render.
 */
const PublishedContext = createContext<Partial<Record<PanelTab, ReactNode>>>({});

/**
 * ⚡ **What a module asks the panel.**
 *
 * 🔴 **`carrying` is the field that matters and the reason this is a hook
 * rather than a `<PanelSlot>` component.** **A module has to know whether the
 * panel took its content**, so it can render it inline when the panel is
 * absent — **a slot component could only tell it *"published"*, which is true
 * on a phone and useless.**
 *
 * ⛔ **Returns `carrying: false` outside a panel provider rather than
 * throwing.** ⚡ **A module rendered in a test, a story or a route with no
 * shell should show its content inline**, which is exactly what `false` makes
 * it do — **and a throw would make the panel a hard dependency of every screen
 * that might one day dock something.**
 */
export function useUtilityPanel(tab: PanelTab, content: ReactNode): { carrying: boolean } {
  const panel = useContext(PanelContext);
  const carrying = panel !== null && panel.state !== 'absent';

  const publish = panel?.publish;
  const withdraw = panel?.withdraw;

  useEffect(() => {
    if (!carrying || publish === undefined || withdraw === undefined) return;
    publish(tab, content);
    return () => withdraw(tab);
  }, [carrying, publish, withdraw, tab, content]);

  return { carrying };
}

/**
 * ⚡ **Whether a utility panel exists on this screen right now.**
 *
 * ⛔ **Exists so the SKIP LINK and the panel cannot disagree.** 📁
 * [`skip-links.tsx`](skip-links.tsx) states the rule it has to obey: *"a skip
 * link to a missing landmark sends a keyboard user nowhere and is worse than
 * the omission."* ⚠️ **The panel is absent below 1024**, so an unconditional
 * third link would be exactly that, on every phone.
 */
export function useUtilityPanelPresent(): boolean {
  const panel = useContext(PanelContext);
  return panel !== null && panel.state !== 'absent';
}

export function UtilityPanelProvider({
  userId,
  module,
  children,
}: {
  userId: string | null;
  /** 📁 *"Remembers its open state per module."* */
  module: string;
  children: ReactNode;
}) {
  const [openPreference, setOpenPreference] = useState(false);
  const [width, setWidth] = useState(1440);
  const [activeTab, setActiveTab] = useState<PanelTab>('Insights');
  const [published, setPublished] = useState<Partial<Record<PanelTab, ReactNode>>>({});

  /**
   * ⛔ **Measured in an effect, never during render.** ⚡ **The server has no
   * viewport**, so reading one during render would make the markup React
   * expects disagree with the markup the server produced — the same reason
   * [`use-rail-collapse.ts`](../../lib/shell/use-rail-collapse.ts) applies its
   * stored preference in an effect.
   */
  useEffect(() => {
    const measure = () => setWidth(window.innerWidth);
    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, []);

  /**
   * 🔴 **`settled` is what stops the stored preference overwriting a person's
   * toggle**, and it is a real defect rather than a precaution.
   *
   * ⚠️ **Found in a browser, not in a test.** ⛔ **`⌘.` pressed in the first
   * moments after a route change did nothing**: the hydration effect was still
   * queued, and when it ran it wrote the stored `false` over the `true` the
   * keypress had just set. ⚡ **The panel opened and closed again within a
   * frame**, which reads as a shortcut that does not work.
   *
   * ✅ **Hydration happens once per module and never after a deliberate
   * action** — the toggle claims the key, so a late read has nothing to say.
   */
  const settled = useRef<string | null>(null);

  useEffect(() => {
    if (userId === null || userId === '') return;
    const key = panelKey(userId, module);
    if (settled.current === key) return;
    settled.current = key;
    try {
      setOpenPreference(window.localStorage.getItem(key) === 'true');
    } catch {
      // ⚡ **A cosmetic preference must never cost the panel** — the same
      // reasoning the rail's collapse memory records.
    }
  }, [userId, module]);

  const toggle = useCallback(() => {
    // ⛔ **Claim the key before changing anything**, so a hydration effect that
    // has not run yet cannot undo this.
    if (userId !== null && userId !== '') settled.current = panelKey(userId, module);
    setOpenPreference((was) => {
      const next = !was;
      if (userId !== null && userId !== '') {
        try {
          window.localStorage.setItem(panelKey(userId, module), String(next));
        } catch {
          // The toggle still works for this session; only the memory is lost.
        }
      }
      return next;
    });
  }, [userId, module]);

  /**
   * 📁 **`⌘.` — *"Toggle utility panel"***, from the design's own
   * `shortcutGroups`.
   *
   * ⛔ **Ignored while a text field has focus**, because `.` is a character
   * somebody types — ⚠️ **and the modifier does not make that safe on its own**:
   * a shortcut that fires mid-sentence is a shortcut people disable.
   */
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== '.' || !(event.metaKey || event.ctrlKey)) return;
      const target = event.target as HTMLElement | null;
      const tag = target?.tagName;
      if (tag === 'INPUT' || tag === 'TEXTAREA' || target?.isContentEditable === true) return;
      event.preventDefault();
      toggle();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [toggle]);

  const publish = useCallback((tab: PanelTab, content: ReactNode) => {
    setPublished((was) => ({ ...was, [tab]: content }));
  }, []);

  const withdraw = useCallback((tab: PanelTab) => {
    setPublished((was) => {
      const next = { ...was };
      delete next[tab];
      return next;
    });
  }, []);

  const state = panelStateFor(width, openPreference);
  /**
   * ⛔ **The width comes from the design's table, not from a Tailwind class** —
   * ⚡ **the precedent is `RAIL_WIDTH`**, which `app-shell.tsx` applies the same
   * way. 📁 **`w-panel-wide` does not exist and adding one would be a change to
   * the design system** ([§20c](../../../CLAUDE.md)) **to serve one caller.**
   */
  const panelWidth = state === 'open' ? PANEL_WIDTH[bandFor(width)] : PANEL_WIDTH.smallLaptop;

  const contract = useMemo<PanelContract>(
    () => ({ state, width: panelWidth, activeTab, setActiveTab, toggle, publish, withdraw }),
    [state, panelWidth, activeTab, toggle, publish, withdraw],
  );

  return (
    <PanelContext.Provider value={contract}>
      <PublishedContext.Provider value={published}>{children}</PublishedContext.Provider>
    </PanelContext.Provider>
  );
}

/**
 * 🔴 **The dock, mounted by the SHELL rather than by the provider.**
 *
 * ⚠️ **The provider rendered this itself in the first draft, and it was
 * wrong in a way only a browser could show**: the provider wraps the whole
 * shell, so the panel landed *after* the frame's flex row instead of inside
 * it — ⛔ **it floated at the end of the page and the rail's `Settings` link
 * sat on top of its tabs**, which Playwright reported as *"intercepts pointer
 * events"*.
 *
 * ⚡ **The design's word is *"pushes content"***, and a panel that pushes has
 * to be a sibling of what it pushes. ✅ **So placement belongs to the layout,
 * and state belongs to the provider.**
 */
export function UtilityPanelDock() {
  const panel = useContext(PanelContext);
  const published = useContext(PublishedContext);
  if (panel === null) return null;

  return (
    <UtilityPanel
      state={panel.state}
      width={panel.width}
      activeTab={panel.activeTab}
      onTab={panel.setActiveTab}
      published={published}
    />
  );
}

/**
 * ⛔ **Exported for tests and for the shell; never mounted twice.** ⚡ The
 * provider renders it, so a second `<UtilityPanel>` would give the page two
 * `complementary` landmarks — the defect
 * [TASK-1444](../../../docs/BACKLOG.md) already found with `banner`.
 */
export function UtilityPanel({
  state,
  width,
  activeTab,
  onTab,
  published,
}: {
  state: PanelState;
  /** 📁 From `PANEL_WIDTH` — 360 on a desktop, 300 on the reference laptop. */
  width: number | null;
  activeTab: PanelTab;
  onTab: (tab: PanelTab) => void;
  published: Partial<Record<PanelTab, ReactNode>>;
}) {
  // ⛔ **Absent means ABSENT** — no element, no landmark. 📁 A zero-width
  // `aside` would still offer a screen-reader user a *complementary* region
  // containing nothing.
  if (state === 'absent') return null;

  const open = state === 'open';
  const content = published[activeTab];

  return (
    <aside
      // 📁 *"`aside[complementary]` — the utility panel, labelled with its
      // active tab."* ⛔ Not a constant: the label is what a screen-reader user
      // reads when choosing whether to enter the region.
      id={UTILITY_PANEL_TARGET}
      aria-label={panelLabel(activeTab)}
      data-state={state}
      style={{ width: width ?? PANEL_WIDTH.smallLaptop ?? undefined }}
      className={cn(
        // 📁 *"Non-modal, pushes content"* — ⚡ **in flow, never `fixed` and
        // never over the content.** A panel that covered the table would make
        // the customer close it to read what it describes.
        'hidden shrink-0 border-l border-border-soft bg-surface smalllaptop:flex',
        'flex-col transition-[width] duration-150',
      )}
    >
      <div
        role="tablist"
        aria-label="Utility panel sections"
        className={cn('flex gap-1 border-b border-border-soft p-1', !open && 'flex-col')}
      >
        {PANEL_TABS.map((tab) => (
          <button
            key={tab}
            type="button"
            role="tab"
            aria-selected={tab === activeTab}
            // ⚡ **The tab rail is 28px wide, so the label cannot show** —
            // ♿ but it must still be the accessible name, or the control is a
            // button called nothing.
            aria-label={tab}
            title={tab}
            onClick={() => onTab(tab)}
            className={cn(
              'rounded px-2 py-1 text-xs transition-colors',
              'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-accent',
              tab === activeTab
                ? 'bg-surface-sunken font-semibold text-content'
                : 'text-content-muted hover:text-content',
            )}
          >
            {open ? tab : tab.charAt(0)}
          </button>
        ))}
      </div>

      {open ? (
        <div role="tabpanel" aria-label={activeTab} className="min-h-0 flex-1 overflow-y-auto p-3">
          {content ?? <NothingDocked tab={activeTab} />}
        </div>
      ) : null}
    </aside>
  );
}

/**
 * ⛔ **The design's own empty state, not invented copy** — the row is explicit:
 * *"Insights and Notes are tab stubs only if the design's own empty state is
 * used; never invented copy."*
 *
 * ⚡ **It says what the tab is FOR rather than that it is empty**, because 📁
 * the panel is *"docked context, not a task surface"* — **a person who opened
 * it wants to know what would appear here, not that nothing has.**
 */
function NothingDocked({ tab }: { tab: PanelTab }) {
  return (
    <p className="text-sm text-content-muted">
      {tab === 'Activity'
        ? 'Nothing on this screen keeps a history yet.'
        : `This screen has no ${tab.toLowerCase()} to dock.`}
    </p>
  );
}
