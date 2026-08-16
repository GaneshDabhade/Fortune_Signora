'use client';

import { useEffect, useState } from 'react';

import { FieldOriginTag, SegmentedControl } from '@/components/ui';
import { changePreferences, getPreferences, type Preferences } from '@/lib/api/preferences';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **Screen `04 · AI preferences`** — [TASK-470](../../../../docs/BACKLOG.md),
 * milestone 2.
 *
 * ### 🔴 Consent is never inferred, and it is the defaults that say so
 *
 * **Every setting a person has not touched sits at the conservative end.**
 * ⚠️ **Two default to on, and that is not a contradiction**: neither is a
 * permission over the customer's data. Insights rank what Signora has already
 * read, and drafting is safe because of a property of the product rather than
 * of a flag — *"drafts open in your composer. **Nothing is ever sent on your
 * behalf.**"*
 *
 * ### ⚡ The two statements at the bottom are not settings, and must not look like them
 *
 * The design draws them as rows with the others, and **they are facts rather
 * than choices** — so they render as statements with no control at all. ⛔ **A
 * disabled toggle would invite somebody to ask who can enable it**, and for
 * one of the two the honest answer is *nobody, ever*.
 *
 * ⚠️ **The training statement is the strongest claim on this screen and it is
 * the repository's, not this lane's.**
 * [10-security.md](../../../../docs/architecture/10-security.md) makes
 * no-training/no-retention vendor terms **a condition of use**, re-verified at
 * each contract renewal ([14-ai-architecture.md](../../../../docs/architecture/14-ai-architecture.md)).
 * ⛔ **It is contractual rather than something code enforces**, and that is
 * worth knowing before anybody strengthens the wording.
 */

const ANSWER_STYLES = [
  { value: 'direct', label: 'Direct' },
  { value: 'detailed', label: 'Detailed' },
] as const;

const FLOORS = [
  { value: '3', label: '3' },
  { value: '4', label: '4' },
  { value: '5', label: '5' },
] as const;

/** The design's three data-use statements, and every one is checkable. */
const DATA_USE = [
  {
    fact: 'Read to answer your questions',
    detail:
      'Accounts, deals, calls and emails you already have access to. Nothing beyond your permissions.',
    holds: true,
  },
  {
    fact: 'Retained as generated content',
    detail: 'Answers and their citations stay with the record until you delete them.',
    holds: true,
  },
  {
    fact: 'Used to train a shared model',
    // ⚠️ **The design's sentence reads *"not for your workspace"* and this
    // says *organization*** — [ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)
    // applied at the edge it names, and `vocabulary.test.tsx` is what caught
    // it. **The second instance of [C-246](../../../../docs/LANE_COORDINATION.md)**,
    // which already asks for the general ruling rather than a per-screen one.
    detail: 'Never. Not for your organization, and not for anyone else’s.',
    holds: false,
  },
  {
    // 🔴 **The design offers this as a TOGGLE — *"Write risk flags to the
    // CRM"* — and Signora cannot honour one.** ⚡ **Measured rather than
    // assumed**: the provider port's verbs are `store_records`,
    // `save_watermark` and `get`, all inbound. **There is no write path to a
    // connected system anywhere in the contract.**
    //
    // ⛔ **So it is stated as a fact rather than rendered as a control.** 📁
    // The precedent is this file's own line three above and
    // [`navigation.tsx`](../../../components/shell/navigation.tsx)'s: *"an
    // entry that leads nowhere advertises absence"* — **and a disabled toggle
    // would invite the question of who may enable it**, which is the sentence
    // twelve lines up.
    fact: 'Written back to your connected systems',
    detail:
      'Never. Signora reads from your CRM and calendar; it does not write to them. Risk flags stay in Signora.',
    holds: false,
  },
] as const;

export function AiPanel() {
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
    setPrefs((current) => (current === null ? current : { ...current, ...changes }));
    setStatus('saving');
    try {
      setPrefs(await changePreferences(workspaceId, changes));
      setStatus('saved');
    } catch {
      setStatus('error');
    }
  };

  return (
    <section className="flex flex-col gap-6" aria-labelledby="ai-heading">
      <header className="flex flex-col gap-1">
        <h2 id="ai-heading" className="text-lg font-semibold text-content">
          AI preferences
        </h2>
        <p className="text-sm leading-6 text-content-muted">
          How much Signora volunteers, and how it answers.
        </p>
      </header>

      {loading ? (
        <p role="status" className="text-sm text-content-muted">
          Loading your preferences…
        </p>
      ) : null}

      <div className="flex flex-col gap-5">
        <Toggle
          label="Insights on my home page"
          description="Unprompted findings, ranked. Off means Signora only answers what you ask."
          checked={prefs?.ai_insights ?? true}
          onChange={(value) => change({ ai_insights: value })}
        />
        <Toggle
          label="Draft emails for me"
          description="Drafts open in your composer. Nothing is ever sent on your behalf."
          checked={prefs?.ai_drafts ?? true}
          onChange={(value) => change({ ai_drafts: value })}
        />
        <Toggle
          label="Always show citations"
          description="Expands evidence under every claim instead of keeping it one click away."
          checked={prefs?.always_show_citations ?? false}
          onChange={(value) => change({ always_show_citations: value })}
        />

        <div className="flex flex-col gap-1.5">
          <SegmentedControl
            legend="Answer style"
            name="answer_style"
            segments={ANSWER_STYLES}
            value={prefs?.answer_style ?? 'direct'}
            onChange={(value) => change({ answer_style: value as Preferences['answer_style'] })}
          />
          <p className="text-xs leading-5 text-content-muted">
            Direct gives the conclusion first. Detailed shows the reasoning inline before the
            answer.
          </p>
          <FieldOriginTag origin="yours" className="self-start" />
        </div>

        <div className="flex flex-col gap-1.5">
          <SegmentedControl
            legend="Confidence floor"
            name="confidence_floor"
            segments={FLOORS}
            value={String(prefs?.confidence_floor ?? 3)}
            onChange={(value) => change({ confidence_floor: Number(value) })}
          />
          {/* ⚠️ **The design adds "yours can be stricter than the workspace
              floor of 3, never looser".** No workspace AI floor exists, so the
              comparison is not stated — C-249. Saying it would describe a rule
              nothing enforces. */}
          <p className="text-xs leading-5 text-content-muted">
            Hide anything Signora is less sure of than this.
          </p>
          <FieldOriginTag origin="yours" className="self-start" />
        </div>
      </div>

      <div className="flex flex-col gap-3 rounded-md border border-border-soft bg-surface-sunken p-4">
        <h3 className="text-sm font-semibold text-content">What happens to your data</h3>
        <dl className="flex flex-col gap-3">
          {DATA_USE.map((entry) => (
            <div key={entry.fact} className="flex items-start gap-2.5">
              {/* ⛔ **A mark, not a toggle.** These are facts, and a disabled
                  control would invite the question of who may enable it. */}
              <span
                aria-hidden
                className={
                  entry.holds
                    ? 'mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-success text-xs text-surface'
                    : 'mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-full bg-danger text-xs text-surface'
                }
              >
                {entry.holds ? '✓' : '✕'}
              </span>
              <div className="flex flex-col gap-0.5">
                <dt className="text-sm font-medium text-content">
                  {entry.fact}
                  <span className="sr-only">{entry.holds ? ': yes' : ': never'}</span>
                </dt>
                <dd className="text-xs leading-5 text-content-muted">{entry.detail}</dd>
              </div>
            </div>
          ))}
        </dl>
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

/**
 * A labelled switch.
 *
 * ⛔ **A checkbox rather than a styled `div`**, for the reason the choice grids
 * are radios: the role, the state and the keyboard all arrive with the native
 * control, and none of them has to be remembered.
 */
function Toggle({
  label,
  description,
  checked,
  onChange,
}: {
  label: string;
  description: string;
  checked: boolean;
  onChange: (value: boolean) => void;
}) {
  return (
    <div className="flex flex-col gap-1.5">
      <label className="flex items-start gap-3">
        <input
          type="checkbox"
          checked={checked}
          onChange={(event) => onChange(event.target.checked)}
          className="mt-0.5 h-4 w-4 shrink-0 accent-accent"
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
