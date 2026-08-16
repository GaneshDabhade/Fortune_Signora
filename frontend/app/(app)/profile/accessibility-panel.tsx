'use client';

import { useEffect, useState } from 'react';

import { FieldOriginTag, SegmentedControl } from '@/components/ui';
import { changePreferences, getPreferences, type Preferences } from '@/lib/api/preferences';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **Screen `04 · Accessibility`** — the finalized User Profile design.
 *
 * ## 🔴 *Reduce motion* is an OVERRIDE, and that is the whole design of this panel
 *
 * 📁 **The design shows it *"On — from system"*.** ⚡ **The system half already
 * works and needed no field**: `globals.css` carries
 * `@media (prefers-reduced-motion: reduce)` and the shell uses `motion-reduce:`
 * throughout, so a device that asks for reduced motion already gets it.
 *
 * ⛔ **So this toggle does not mean *motion is fine when off*.** It means
 * ***on regardless of what the device says***, and leaving it off returns the
 * question to the media query. ⚠️ **Storing what the browser already reports
 * would be the hidden input [§2](../../../../CLAUDE.md) forbids** — and a
 * default of `true` would have forced reduced motion on everybody who has
 * never opened this screen.
 *
 * ## ⛔ What this panel does not do
 *
 * **Apply any of it.** ⚡ **It records the choice; the document reads it** —
 * 📁 the same division `AppearancePanel` states for the theme: *"a panel that
 * painted the page would be the second place a theme is decided."*
 *
 * ## ⚠️ Six controls, and every one is the design's
 *
 * ⛔ **No speculative field.** The design names *Reduce motion*, *Increase
 * contrast*, *Text size*, *Always show focus ring*, *Underline links* and
 * *Screen reader verbosity*, and this panel has exactly those.
 */

/** 📁 The design's segmented control: *100% · 112% · 125%*. */
const TEXT_SIZES = [
  { value: '100', label: '100%' },
  { value: '112', label: '112%' },
  { value: '125', label: '125%' },
] as const;

/** 📁 The design's segmented control: *Concise · Detailed*. */
const VERBOSITIES = [
  { value: 'concise', label: 'Concise' },
  { value: 'detailed', label: 'Detailed' },
] as const;

export function AccessibilityPanel() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [loading, setLoading] = useState(true);
  /**
   * 🔴 **`unavailable` is a member rather than a silent return** —
   * 📁 [B-255](../../../../docs/BUGS.md), which this lane fixed in
   * `ProfilePanel` and which `AppearancePanel` still carries.
   *
   * ⛔ **The first version of this file returned early when there was no
   * organization**, so somebody clicked a toggle, watched it not move, and got
   * neither a change nor a reason. ⚡ **The headed journey caught it** — the
   * click reported *"did not change its state"* and the screen said nothing.
   *
   * ✅ **A preference is a person's own, so the panel is right to render**; the
   * honest thing is to say the write cannot be made rather than to remove the
   * way to make it.
   */
  const [status, setStatus] = useState<
    'idle' | 'saving' | 'saved' | 'error' | 'unavailable'
  >('idle');

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
    if (workspaceId === null) {
      setStatus('unavailable');
      return;
    }
    // ⚡ **Optimistic**, and the server's answer replaces it below — so a
    // refusal corrects the screen rather than leaving it lying.
    setPrefs((current) => (current === null ? current : { ...current, ...changes }));
    setStatus('saving');
    try {
      setPrefs(await changePreferences(workspaceId, changes));
      setStatus('saved');
    } catch {
      setStatus('error');
      // Re-read rather than guess what the server kept.
      getPreferences(workspaceId)
        .then(setPrefs)
        .catch(() => undefined);
    }
  };

  return (
    <section className="flex flex-col gap-6" aria-labelledby="accessibility-heading">
      <header className="flex flex-col gap-1">
        <h2 id="accessibility-heading" className="text-lg font-semibold text-content">
          Accessibility
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

      <div className="flex flex-col gap-6">
        <Toggle
          label="Reduce motion"
          /* 🔴 **The description says what OFF means**, because it is not what
             a reader assumes. ⛔ Off does not mean *animate everything*; it
             means *follow the device*, and a toggle that let somebody believe
             otherwise would read as broken on a machine already set to
             reduce. */
          description="Removes every transform and drops transitions to short opacity fades. Your device’s own setting is already respected — turn this on to reduce motion everywhere, whatever the device says."
          checked={prefs?.reduce_motion ?? false}
          disabled={prefs === null}
          onChange={(value) => change({ reduce_motion: value })}
        />

        <Toggle
          label="Increase contrast"
          description="Raises borders, darkens secondary text, and removes tinted backgrounds behind text."
          checked={prefs?.increase_contrast ?? false}
          disabled={prefs === null}
          onChange={(value) => change({ increase_contrast: value })}
        />

        <Toggle
          label="Always show focus ring"
          /* ⚡ **The ring is always there for a keyboard**, and this asks for
             it after a pointer too — ⛔ so the description says which case it
             changes rather than implying focus is otherwise invisible. */
          description="Keeps the focus outline visible after a mouse click, not only when moving by keyboard."
          checked={prefs?.always_show_focus_ring ?? false}
          disabled={prefs === null}
          onChange={(value) => change({ always_show_focus_ring: value })}
        />

        <Toggle
          label="Underline links"
          description="Underlines links in body text rather than relying on colour alone."
          checked={prefs?.underline_links ?? true}
          disabled={prefs === null}
          onChange={(value) => change({ underline_links: value })}
        />

        <div className="flex flex-col gap-1.5">
          <SegmentedControl
            legend="Text size"
            name="text_size"
            segments={TEXT_SIZES}
            value={prefs?.text_size ?? '100'}
            onChange={(value) => change({ text_size: value as Preferences['text_size'] })}
          />
          {/* 📁 The design's own line. ⚡ **The floor is stated because it is a
              promise**: nothing shrinks below 12.5px at any setting. */}
          <p className="text-xs leading-5 text-content-muted">
            Scales interface text. Data tables keep tabular alignment at every size.
          </p>
          <FieldOriginTag origin="yours" className="self-start" />
        </div>

        <div className="flex flex-col gap-1.5">
          <SegmentedControl
            legend="Screen reader verbosity"
            name="screen_reader_verbosity"
            segments={VERBOSITIES}
            value={prefs?.screen_reader_verbosity ?? 'detailed'}
            onChange={(value) =>
              change({
                screen_reader_verbosity: value as Preferences['screen_reader_verbosity'],
              })
            }
          />
          <p className="text-xs leading-5 text-content-muted">
            Detailed announces the evidence and confidence behind a figure. Concise announces
            the figure.
          </p>
          <FieldOriginTag origin="yours" className="self-start" />
        </div>
      </div>

      {/* A status, not an alert — 4.1.3. Changing a preference must not interrupt. */}
      <p role="status" className="text-sm text-content-muted">
        {status === 'saved' ? 'Saved' : ''}
      </p>
      {status === 'error' ? (
        <p role="alert" className="text-sm text-danger">
          That did not save. Check your connection and try again.
        </p>
      ) : null}
      {status === 'unavailable' ? (
        <p role="alert" className="text-sm text-danger">
          These settings belong to an organization, and you are not in one yet.
        </p>
      ) : null}
    </section>
  );
}

/**
 * ⚡ **A real checkbox**, not a `role="switch"` div.
 *
 * ⛔ **The native control carries its own label association, focus, keyboard
 * and announcement** — and this is the one panel where reimplementing any of
 * that would be self-defeating.
 */
function Toggle({
  label,
  description,
  checked,
  disabled,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  /**
   * 🔴 **Disabled only while the read is in flight**, and it is the honest
   * answer rather than a convenience.
   *
   * ⛔ **The first version left the controls live before `prefs` resolved**, so
   * a click did nothing at all: the optimistic update bails when there is no
   * current value to spread over. ⚡ **The headed journey reported *"clicking
   * the checkbox did not change its state"*** — **an interactive control that
   * does nothing, which is [B-255](../../../../docs/BUGS.md)'s shape and this
   * lane's own rule**: *a control that silently does nothing is worse than one
   * that is absent.*
   *
   * ✅ **The loading line above says why**, so this is a stated wait rather
   * than a dead control.
   */
  disabled: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={checked}
          disabled={disabled}
          onChange={(event) => onChange(event.target.checked)}
          className="mt-0.5 h-4 w-4 shrink-0 rounded border-border text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent disabled:cursor-not-allowed disabled:opacity-60"
        />
        <span className="flex flex-col gap-0.5">
          <span className="text-sm font-medium text-content">{label}</span>
          <span className="text-xs leading-5 text-content-muted">{description}</span>
        </span>
      </label>
      <FieldOriginTag origin="yours" className="self-start" />
    </div>
  );
}
