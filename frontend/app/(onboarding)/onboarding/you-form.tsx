'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button, ChoiceCards, Input } from '@/components/ui';
import { describePerson } from '@/lib/api/onboarding';

import { OnboardingShell } from '../onboarding-shell';
import { OnboardingSkeleton } from './company-form';
import { RAIL_STEPS, ROLES } from './steps';
import { useOnboarding } from './use-onboarding';

/** *"Integer ≥ 1, ≤ 10,000. Validated on blur, not per keystroke. Zero
 * explains that they count."* */
const MIN_TEAM_SIZE = 1;
const MAX_TEAM_SIZE = 10_000;

/**
 * **Screen `05 You`** — [TASK-469](../../../../docs/BACKLOG.md).
 *
 * > *"Role and team size. **Role sets the home page and the alert routing.**"*
 *
 * ### 🔴 Validation fires on blur, and that is a rule rather than a taste
 *
 * *"Team size: Integer ≥ 1, ≤ 10,000. **Validated on blur, not per
 * keystroke.**"* ⛔ **Per keystroke, somebody typing `24` is told `2` is wrong
 * before they have finished the number.** The row names this behaviour
 * explicitly, and `onboarding.test.tsx` asserts it, because it is the kind of
 * thing a later refactor "tidies" into `onChange`.
 *
 * ### ⚠️ Zero is answered, not corrected
 *
 * *"Zero explains that they count."* **The message says why rather than
 * restating the range** — a person typing `0` is usually saying *it is just
 * me*, and the honest answer is that they are one.
 */
export function YouForm() {
  const router = useRouter();
  const { run, error, isLoading, isSaving, save, advance } = useOnboarding();
  const [role, setRole] = useState<string | null>(null);
  const [teamSize, setTeamSize] = useState<string>('');
  const [teamSizeError, setTeamSizeError] = useState<string | null>(null);
  const [touched, setTouched] = useState(false);

  if (isLoading) return <OnboardingSkeleton />;

  const chosenRole = role ?? run?.role?.value ?? null;
  const shownTeamSize = touched ? teamSize : (run?.team_size?.value ?? '');

  /** ⛔ **Called from `onBlur`, never from `onChange`.** */
  const validateTeamSize = (raw: string): string | null => {
    if (raw.trim() === '') return null;
    const parsed = Number(raw);
    if (!Number.isInteger(parsed)) return 'Enter a whole number.';
    if (parsed === 0) return 'Even a team of one counts — enter 1.';
    if (parsed < MIN_TEAM_SIZE || parsed > MAX_TEAM_SIZE) {
      return `Enter a number between ${MIN_TEAM_SIZE} and ${MAX_TEAM_SIZE.toLocaleString()}.`;
    }
    return null;
  };

  const submit = async () => {
    const message = validateTeamSize(shownTeamSize.toString());
    setTeamSizeError(message);
    if (message !== null) return;

    const body: Parameters<typeof describePerson>[1] = {};
    if (chosenRole !== null) body.role = { value: chosenRole, provenance: 'entered' };
    const size = shownTeamSize.toString().trim();
    if (size !== '') body.team_size = { value: Number(size), provenance: 'entered' } as never;

    await save((id) => describePerson(id, body));
    await advance('goals');
    router.push('/onboarding/goals');
  };

  return (
    <OnboardingShell
      steps={RAIL_STEPS}
      currentId="you"
      completedIds={run?.completed_steps ?? []}
      title="What do you do here?"
      description="Your role decides what your home page opens on and where alerts go. You can change it later in Settings."
      actions={
        <>
          <Button onClick={submit} loading={isSaving}>
            Continue
          </Button>
          <button
            type="button"
            onClick={async () => {
              await advance('goals');
              router.push('/onboarding/goals');
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
          legend="Your role"
          name="role"
          choices={ROLES}
          value={chosenRole}
          onChange={setRole}
        />

        <Input
          label="How many people are on your team?"
          inputMode="numeric"
          value={shownTeamSize.toString()}
          onChange={(event) => {
            setTouched(true);
            setTeamSize(event.target.value);
            // ⛔ **The error is cleared as they type and never raised there.**
            // Clearing is a kindness; raising would be the per-keystroke
            // validation the design refuses.
            setTeamSizeError(null);
          }}
          onBlur={(event) => setTeamSizeError(validateTeamSize(event.target.value))}
          {...(teamSizeError !== null ? { error: teamSizeError } : {})}
        />

        {error !== null ? (
          <p role="alert" className="text-sm text-danger">
            {error}
          </p>
        ) : null}
      </div>
    </OnboardingShell>
  );
}
