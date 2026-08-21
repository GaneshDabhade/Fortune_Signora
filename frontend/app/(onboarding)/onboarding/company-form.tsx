'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useState } from 'react';

import { Button, Inferred } from '@/components/ui';
import { cn } from '@/lib/design/cn';
import { confirmCompany, type Answer } from '@/lib/api/onboarding';

import { OnboardingShell } from '../onboarding-shell';
import { OnboardingRail } from './rail';
import {
  SIZE_BANDS,
  INDUSTRIES,
  COUNTED_STEPS,
  COUNTED_TOTAL,
  positionOf,
} from './steps';
import { SkipSetup } from './skip-setup';
import { useOnboarding } from './use-onboarding';

/**
 * **Screen `04 Company`** — [TASK-469](../../../../docs/BACKLOG.md).
 *
 * > *"Confirm industry, size, region and timezone. **Four confirmations, no
 * > typing.** Inferred: all four, from the domain record and the browser."*
 *
 * ### ⚡ Confirming is what the primary action does
 *
 * **A value shown as `Inferred` and left alone is *confirmed* when the person
 * advances** — that is what the design means by *"four confirmations"*. ⛔ **It
 * is not left inferred**, because the difference between *the product guessed*
 * and *a human agreed* is the whole reason provenance is stored.
 *
 * ### ⛔ Nothing here blocks
 *
 * *"Never blocks — 'Other' is always available"*, and the step is skippable
 * entirely. **A required field on a skippable step would be a rule the flow
 * does not have.**
 */
export function CompanyForm() {
  const router = useRouter();
  const { run, error, isLoading, isSaving, save, advance } = useOnboarding();
  const [dirty, setDirty] = useState<Record<string, Answer>>({});

  /**
   * ⚡ **The one value on this screen the product can honestly infer today.**
   *
   * 📁 The design marks it *From your browser*, and the browser is 📁
   * [§2](../../../../CLAUDE.md)'s least powerful author that can get it right:
   * `Intl` reports the zone, nothing derives it, and nothing can be wrong about
   * it in a way a person cannot see.
   *
   * ⛔ **Industry, size and headquarters are NOT inferred**, because no
   * enrichment producer exists in this repository — 📁 `StartOnboardingUseCase`
   * opens every run with all four answers `None`. ✅ **That is a state the
   * design specifies rather than a gap it left**: *"Enrichment unavailable:
   * fields stay empty and editable, the Inferred badge is absent, and the step
   * is never blocked by it."*
   */
  useEffect(() => {
    if (run === null || run.timezone !== null) return;
    const zone = Intl.DateTimeFormat().resolvedOptions().timeZone;
    if (!zone) return;
    void save((id) =>
      confirmCompany(id, { timezone: { value: zone, provenance: 'inferred' } }),
    );
  }, [run, save]);

  if (isLoading) {
    return <OnboardingSkeleton />;
  }

  if (error !== null && run === null) {
    return (
      <OnboardingShell
        rail={
          <OnboardingRail
            steps={COUNTED_STEPS}
            currentId="company"
            completedIds={[...[], 'workspace']}
            progress={{ step: positionOf('company'), of: COUNTED_TOTAL }}
          />
        }
        title="About your company"
      >
        <p role="alert" className="text-sm text-danger">
          {error}
        </p>
      </OnboardingShell>
    );
  }

  const current = (
    field: 'industry' | 'company_size' | 'region' | 'timezone',
  ): Answer | null => dirty[field] ?? run?.[field] ?? null;

  /** A correction. **The provenance becomes `entered`** — they typed it, so
   * it is theirs, and the badge goes. */
  const correct = (field: string, value: string) => {
    setDirty((previous) => ({ ...previous, [field]: { value, provenance: 'entered' } }));
  };

  const submit = async () => {
    // **Everything shown is sent, and anything untouched is sent as
    // `confirmed`.** That is the confirmation the design describes: the person
    // read four pre-filled facts and agreed with them.
    const body: Record<string, Answer> = {};
    for (const field of ['industry', 'company_size', 'region', 'timezone'] as const) {
      const answer = current(field);
      if (answer === null) continue;
      body[field] =
        answer.provenance === 'inferred'
          ? { value: answer.value, provenance: 'confirmed' }
          : answer;
    }

    await save((id) => confirmCompany(id, body));
    await advance('you');
    router.push('/onboarding/you');
  };

  const industry = current('industry');
  const size = current('company_size');
  const region = current('region');
  const timezone = current('timezone');

  const inferredAnything = [industry, size, region, timezone].some(
    (answer) => answer?.provenance === 'inferred',
  );

  return (
    <OnboardingShell
      rail={
        <OnboardingRail
          steps={COUNTED_STEPS}
          currentId="company"
          completedIds={[...(run?.completed_steps ?? []), 'workspace']}
          progress={{ step: positionOf('company'), of: COUNTED_TOTAL }}
          footer={
            <>
              {/* 📁 The design's rail note: *"Pre-filled from northwind.com ·
                  Public company record. Nothing is sent to your CRM."*
                  ⛔ **It renders only where something WAS pre-filled** — a
                  standing claim that the screen was filled in from a public
                  record would be false on every run where nothing was. */}
              {inferredAnything ? (
                <div className="mt-[22px] rounded-md border border-ai-line bg-ai-subtle p-3">
                  <p className="text-2xs font-semibold text-ai">Pre-filled for you</p>
                  <p className="mt-1 text-2xs leading-6 text-content-muted">
                    Nothing is sent to your CRM.
                  </p>
                </div>
              ) : null}
              <SkipSetup
                completedIds={run?.completed_steps ?? []}
                industry={run?.industry?.value ?? null}
              />
            </>
          }
        />
      }
      title="About your company"
      description="We filled in what we could. Correct anything that is wrong — it changes which benchmarks Signora compares you against."
      actions={
        <>
          <Button onClick={submit} disabled={isSaving}>
            {isSaving ? 'Saving…' : 'Looks right, continue'}
          </Button>
          <button
            type="button"
            onClick={async () => {
              // ⛔ **Skipping saves nothing and still advances.** A skip that
              // quietly confirmed four guesses would record agreement nobody
              // gave.
              await advance('you');
              router.push('/onboarding/you');
            }}
            className="text-sm font-semibold text-content-subtle hover:text-content "
          >
            Skip for now
          </button>
        </>
      }
    >
      <div className="flex flex-col gap-4">
        <Labelled label="Industry" answer={industry}>
          {/* 📁 *"Single choice, pre-selected. Never blocks — 'Other' is always
              available."* ⚡ Chips at the design's 32px, not cards. */}
          <div role="radiogroup" aria-label="Industry" className="flex flex-wrap gap-2">
            {INDUSTRIES.map((choice) => {
              const chosen = industry?.value === choice.value;
              return (
                <button
                  key={choice.value}
                  type="button"
                  role="radio"
                  aria-checked={chosen}
                  onClick={() => correct('industry', choice.value)}
                  className={cn(
                    'inline-flex h-8 items-center rounded-md border px-[13px] text-label transition-colors',
                    chosen
                      ? 'border-accent bg-accent-subtle font-semibold text-accent'
                      : 'border-border bg-surface text-content-muted hover:text-content',
                  )}
                >
                  {choice.label}
                </button>
              );
            })}
          </div>
        </Labelled>

        {/* 📁 *"grid-template-columns:1fr 1fr; gap:16px"*. */}
        <div className="grid gap-4 smalllaptop:grid-cols-2">
          <Labelled label="Company size" answer={size}>
            <Picker
              label="Company size"
              value={size?.value ?? ''}
              onChange={(value) => correct('company_size', value)}
              options={SIZE_BANDS}
            />
          </Labelled>
          <Labelled label="Headquarters" answer={region}>
            {/* ⛔ **A field rather than a picker, and the reason is honesty.**
                📁 The design draws a select; **this repository has no country
                vocabulary**, and a list invented here would be domain data
                nobody owns. ✅ *"Fields stay empty and editable"* is the
                design's own answer to exactly this. */}
            <input
              aria-label="Headquarters"
              value={region?.value ?? ''}
              onChange={(event) => correct('region', event.target.value)}
              className={CONTROL}
            />
          </Labelled>
        </div>

        <Labelled label="Timezone" answer={timezone}>
          <input
            aria-label="Timezone"
            value={timezone?.value ?? ''}
            onChange={(event) => correct('timezone', event.target.value)}
            className={CONTROL}
          />
          <p className="mt-[7px] text-2xs text-content-subtle">
            Sets when digests arrive and what &ldquo;today&rdquo; means in every report.
          </p>
        </Labelled>

        {error !== null ? (
          <p role="alert" className="text-sm text-danger">
            {error}
          </p>
        ) : null}
      </div>
    </OnboardingShell>
  );
}

/** 📁 The design's control: *"height:40px; padding:0 13px; border-radius:8px;
 * border:1px solid var(--line); font-size:13.5px."* */
const CONTROL =
  'h-control-md w-full rounded-md border border-border bg-surface px-[13px] text-sm text-content outline-none transition-shadow ';

/**
 * 📁 **The design's label row** — the field name at 12.5px/600 with its
 * provenance badge beside it, 7px above the control.
 *
 * ⛔ **The badge is beside the LABEL, never under the control.** That is where
 * the design puts it, and it is where it belongs: it qualifies what the field
 * is, not what was typed into it.
 */
function Labelled({
  label,
  answer,
  children,
}: {
  label: string;
  answer: Answer | null;
  children: React.ReactNode;
}) {
  return (
    <div>
      <div className="mb-[7px] flex items-center gap-2">
        <span className="text-label font-semibold text-content">{label}</span>
        {answer?.provenance === 'inferred' ? (
          <Inferred from={label === 'Timezone' ? 'browser' : 'inference'} />
        ) : null}
      </div>
      {children}
    </div>
  );
}

/** A native select, styled to the design's control. ♿ **Native rather than a
 * bespoke menu** — it carries its own keyboard, focus and announcement. */
function Picker({
  label,
  value,
  onChange,
  options,
}: {
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: readonly { value: string; label: string }[];
}) {
  return (
    <select
      aria-label={label}
      value={value}
      onChange={(event) => onChange(event.target.value)}
      className={cn(CONTROL, 'cursor-pointer')}
    >
      <option value="">Not set</option>
      {options.map((option) => (
        <option key={option.value} value={option.value}>
          {option.label}
        </option>
      ))}
    </select>
  );
}

/** *"Loading"* is one of the five states §19 requires, and the one most often
 * skipped. */
export function OnboardingSkeleton() {
  return (
    <div className="min-h-screen bg-canvas px-5 py-16">
      <p role="status" className="mx-auto max-w-[57.5rem] text-sm text-content-muted">
        Loading your setup…
      </p>
    </div>
  );
}
