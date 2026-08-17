'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button, ChoiceCards, Inferred, Input } from '@/components/ui';
import { confirmCompany, type Answer } from '@/lib/api/onboarding';

import { OnboardingShell } from '../onboarding-shell';
import { OnboardingRail } from './rail';
import { SIZE_BANDS, INDUSTRIES, COUNTED_STEPS, COUNTED_TOTAL, positionOf } from './steps';
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
            completedIds={[...([]), 'workspace']}
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

  const current = (field: 'industry' | 'company_size' | 'region' | 'timezone'): Answer | null =>
    dirty[field] ?? run?.[field] ?? null;

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
  const timezone = current('timezone');

  return (
    <OnboardingShell
      rail={
        <OnboardingRail
          steps={COUNTED_STEPS}
          currentId="company"
          completedIds={[...(run?.completed_steps ?? []), 'workspace']}
          progress={{ step: positionOf('company'), of: COUNTED_TOTAL }}
            footer={
              <SkipSetup
                completedIds={run?.completed_steps ?? []}
                industry={run?.industry?.value ?? null}
              />
            }
        />
      }
      title="About your company"
      description="We filled these in from your email domain. Correct anything that is wrong — nothing here is required."
      actions={
        <>
          <Button onClick={submit} loading={isSaving}>
            Continue
          </Button>
          <button
            type="button"
            onClick={async () => {
              // ⛔ **Skipping saves nothing and still advances.** The step is
              // skippable, so a skip that quietly confirmed four guesses would
              // record agreement nobody gave.
              await advance('you');
              router.push('/onboarding/you');
            }}
            className="text-sm text-content-muted underline underline-offset-4 hover:text-content"
          >
            Skip this step
          </button>
        </>
      }
    >
      <div className="flex flex-col gap-6">
        <ChoiceCards
          legend="Industry"
          name="industry"
          choices={INDUSTRIES}
          value={industry?.value ?? null}
          onChange={(value) => correct('industry', value)}
        />
        {industry?.provenance === 'inferred' ? <Inferred /> : null}

        <ChoiceCards
          legend="Company size"
          name="company_size"
          choices={SIZE_BANDS}
          value={size?.value ?? null}
          onChange={(value) => correct('company_size', value)}
        />
        {size?.provenance === 'inferred' ? <Inferred /> : null}

        <div className="flex flex-col gap-1.5">
          <Input
            label="Timezone"
            // *"IANA zone from the browser, editable."* The browser is the
            // least powerful author that can get this right, so it does.
            value={timezone?.value ?? ''}
            onChange={(event) => correct('timezone', event.target.value)}
            hint="This sets when your digests arrive."
          />
          {timezone?.provenance === 'inferred' ? <Inferred /> : null}
        </div>

        {error !== null ? (
          <p role="alert" className="text-sm text-danger">
            {error}
          </p>
        ) : null}
      </div>
    </OnboardingShell>
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
