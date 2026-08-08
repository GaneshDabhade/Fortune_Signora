'use client';

import { useEffect, useState } from 'react';

import { Button, FieldOriginTag, Select } from '@/components/ui';
import { changePreferences, getPreferences, type Preferences } from '@/lib/api/preferences';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **Screen `02 · Language & region`** — [TASK-470](../../../../docs/BACKLOG.md).
 *
 * ### 🔴 The timezone prompt OFFERS and does not switch
 *
 * The design draws it as three things, not one: ***"Your timezone changed ·
 * Switch to Singapore · Keep Copenhagen."*** ⛔ **Both answers are buttons**,
 * and the row names this behaviour explicitly because it is the one place a
 * helpful product becomes a presumptuous one.
 *
 * ⚡ **Why switching silently would be wrong even though it is usually right:**
 * a person in Copenhagen who opens Signora from a hotel in Singapore has not
 * moved — their digests should still arrive at 07:00 CEST. **The browser knows
 * where the laptop is, not where the person works**, and only they can tell
 * the difference.
 *
 * ✅ ***Keep* is a real answer and is recorded.** Dismissing without choosing
 * would bring the prompt back on the next page load, which is the *second ask*
 * the product refuses one workflow over.
 *
 * ### ⛔ Week starts on is not here
 *
 * The design draws it as **Organization policy** — *"Locked so weekly rollups
 * mean the same thing for everyone."* **No workspace-level locale policy
 * exists**, so a field showing a locked Monday would assert a rule nothing
 * enforces ([D-156](../../../../docs/DECISION_REGISTER.md) ④). Absent, with
 * the reason, rather than drawn.
 */

/** A short list, and it is not a claim to have localised the product. */
const LANGUAGES = [
  { value: 'en-GB', label: 'English (UK)' },
  { value: 'en-US', label: 'English (US)' },
] as const;

const TIME_FORMATS = [
  { value: '24h', label: '24-hour' },
  { value: '12h', label: '12-hour' },
] as const;

export function LocalePanel() {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved' | 'error'>('idle');
  const [promptDismissed, setPromptDismissed] = useState(false);

  // What the browser reports. **A reading, never a decision** — it is only
  // ever used to ask a question.
  const [browserZone, setBrowserZone] = useState<string | null>(null);
  useEffect(() => {
    setBrowserZone(Intl.DateTimeFormat().resolvedOptions().timeZone ?? null);
  }, []);

  useEffect(() => {
    if (workspaceId === null) return;
    let live = true;
    getPreferences(workspaceId)
      .then((loaded) => {
        if (live) setPrefs(loaded);
      })
      .catch(() => {
        if (live) setStatus('error');
      });
    return () => {
      live = false;
    };
  }, [workspaceId]);

  const change = async (changes: Partial<Preferences>) => {
    if (workspaceId === null) return;
    setStatus('saving');
    try {
      setPrefs(await changePreferences(workspaceId, changes));
      setStatus('saved');
    } catch {
      setStatus('error');
    }
  };

  // ⚡ **The offer appears only when the two genuinely differ**, and never
  // while the person has no stored zone at all — with nothing to compare
  // against, "your timezone changed" would be a claim about a change that
  // never happened.
  const offerZone =
    prefs !== null &&
    browserZone !== null &&
    prefs.timezone !== null &&
    prefs.timezone !== browserZone &&
    !promptDismissed;

  return (
    <section className="flex flex-col gap-6" aria-labelledby="locale-heading">
      <header className="flex flex-col gap-1">
        <h2 id="locale-heading" className="text-lg font-semibold text-content">
          Language &amp; region
        </h2>
        <p className="text-sm leading-6 text-content-muted">
          Sets when digests arrive and what “today” means.
        </p>
      </header>

      {offerZone && prefs !== null ? (
        <div
          role="status"
          className="flex flex-wrap items-center gap-3 rounded-md border border-border-soft bg-surface-sunken p-3 text-sm"
        >
          <span className="text-content-muted">
            Your browser reports <span className="font-medium text-content">{browserZone}</span>,
            and your timezone is set to{' '}
            <span className="font-medium text-content">{prefs.timezone}</span>.
          </span>
          {/* ⛔ **Two answers, both buttons.** The design gives *Keep* equal
              standing, because a traveller's correct answer is *Keep*. */}
          <Button size="sm" onClick={() => change({ timezone: browserZone })}>
            Switch to {browserZone}
          </Button>
          <Button size="sm" variant="secondary" onClick={() => setPromptDismissed(true)}>
            Keep {prefs.timezone}
          </Button>
        </div>
      ) : null}

      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Select
            label="Language"
            value={prefs?.language ?? 'en-GB'}
            options={LANGUAGES}
            onChange={(event) => change({ language: event.target.value })}
          />
          <FieldOriginTag origin="yours" className="self-start" />
        </div>

        <div className="flex flex-col gap-1.5">
          <Select
            label="Time format"
            value={prefs?.time_format ?? '24h'}
            options={TIME_FORMATS}
            onChange={(event) =>
              change({ time_format: event.target.value as Preferences['time_format'] })
            }
          />
          <FieldOriginTag origin="yours" className="self-start" />
        </div>

        <div className="flex flex-col gap-1.5">
          <p className="text-sm font-medium text-content">Timezone</p>
          <p className="text-sm text-content-muted">
            {prefs?.timezone ?? 'Not set — Signora is using your browser’s zone for now.'}
          </p>
          {browserZone !== null && prefs?.timezone === null ? (
            <Button
              size="sm"
              variant="secondary"
              className="self-start"
              onClick={() => change({ timezone: browserZone })}
            >
              Use {browserZone}
            </Button>
          ) : null}
          <FieldOriginTag origin="yours" className="self-start" />
        </div>
      </div>

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
