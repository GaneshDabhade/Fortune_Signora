'use client';

import { useEffect, useState } from 'react';

import { FieldOriginTag, SegmentedControl } from '@/components/ui';
import { changePreferences, getPreferences, type Preferences } from '@/lib/api/preferences';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **Screen `03 · Appearance`** — [TASK-470](../../../../docs/BACKLOG.md),
 * milestone 2.
 *
 * ### 🔴 The row's constraint, verbatim, and it decides the storage
 *
 * > ***"applies to this account on every device you sign in from, not to this
 * > browser"*** — **so it is server-persisted preference, never
 * > `localStorage`.**
 *
 * ⛔ **There is no `localStorage` in this file and there must not be.** A theme
 * cached in the browser is a theme that is right on the laptop it was chosen
 * on and wrong on every other one, which is the precise promise this sentence
 * makes and breaks.
 *
 * ⚠️ **`System` is stored as `system`, never resolved.** *"Follows your
 * device, switching at sunset"* is a **deferral**, and answering it with
 * `light` or `dark` would replace the person's choice with one reading of it —
 * taken at the moment they happened to be looking.
 *
 * ### ⛔ What this panel does not do
 *
 * **Apply the theme.** It records the choice; the document reads it. **Nothing
 * here writes a class onto `<html>`** — the design system owns rendering, and
 * a panel that painted the page would be the second place a theme is decided.
 */

/** The design's three, with its own supporting lines. */
const THEMES = [
  { value: 'light', label: 'Light', description: 'Warm paper. The default.' },
  { value: 'dark', label: 'Dark', description: 'For low light and long sessions.' },
  {
    value: 'system',
    label: 'System',
    description: 'Follows your device, switching at sunset.',
  },
] as const;

const DENSITIES = [
  { value: 'comfortable', label: 'Comfortable' },
  { value: 'compact', label: 'Compact' },
] as const;

export function AppearancePanel() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [loading, setLoading] = useState(true);
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');

  useEffect(() => {
    if (workspaceId === null) return;
    let live = true;
    getPreferences(workspaceId)
      .then((loaded) => {
        if (live) setPrefs(loaded);
      })
      // ⛔ A failed read is an error, never an empty form — P-A.
      .catch(() => {
        if (live) setStatus('error');
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [workspaceId]);

  const change = async (changes: Partial<Preferences>) => {
    if (workspaceId === null) return;
    // ⚡ **Optimistic, because a theme that lags a click feels broken.** The
    // server's answer replaces it below, so a refusal corrects the screen
    // rather than leaving it lying.
    setPrefs((current) => (current === null ? current : { ...current, ...changes }));
    setStatus('saving');
    try {
      setPrefs(await changePreferences(workspaceId, changes));
      setStatus('saved');
    } catch {
      setStatus('error');
      if (workspaceId !== null) {
        // Re-read rather than guess what the server kept: the screen must
        // show what is stored, not what was attempted.
        getPreferences(workspaceId)
          .then(setPrefs)
          .catch(() => undefined);
      }
    }
  };

  return (
    <section className="flex flex-col gap-6" aria-labelledby="appearance-heading">
      <header className="flex flex-col gap-1">
        <h2 id="appearance-heading" className="text-lg font-semibold text-content">
          Appearance
        </h2>
        <p className="text-sm leading-6 text-content-muted">
          Applies to this account on every device you sign in from — not just this browser.
        </p>
      </header>

      {loading ? (
        <p role="status" className="text-sm text-content-muted">
          Loading your preferences…
        </p>
      ) : null}

      {/* 🔴 **The controls appear when they can work, and not before.**

          ⛔ **They were rendered while the read was still in flight**, and the
          optimistic update bails when there is no current value to spread over
          — so a click moved nothing and the screen said nothing. ⚡ **The
          headed journey reported it as *"clicking did not change its
          state"***, which is [B-255](../../../../docs/BUGS.md)'s shape: a
          control that silently does nothing is worse than one that is absent.

          ✅ **The loading line above is the stated wait.** ⛔ **Not `disabled`
          on `SegmentedControl`** — that prop does not exist, and adding one to
          a shared component to suit one page is what [§20c](../../../../CLAUDE.md)
          forbids. */}
      {prefs === null ? null : (
      <div className="flex flex-col gap-6">
        <div className="flex flex-col gap-1.5">
          <SegmentedControl
            legend="Theme"
            name="theme"
            segments={THEMES}
            value={prefs?.theme ?? 'system'}
            onChange={(value) => change({ theme: value as Preferences['theme'] })}
          />
          <FieldOriginTag origin="yours" className="self-start" />
        </div>

        <div className="flex flex-col gap-1.5">
          <SegmentedControl
            legend="Density"
            name="density"
            segments={DENSITIES}
            value={prefs?.density ?? 'comfortable'}
            onChange={(value) => change({ density: value as Preferences['density'] })}
          />
          <FieldOriginTag origin="yours" className="self-start" />
        </div>
      </div>
      )}

      {/* A status, not an alert — 4.1.3. Changing a theme should not interrupt. */}
      <p role="status" className="text-sm text-content-muted">
        {status === 'saved' ? 'Saved' : ''}
      </p>
      {status === 'error' ? (
        <p role="alert" className="text-sm text-danger">
          That did not save. Check your connection and try again.
        </p>
      ) : null}
    </section>
  );
}
