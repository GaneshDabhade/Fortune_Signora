'use client';

import { useRouter } from 'next/navigation';
import { useState } from 'react';

import { Button, ChoiceCards, Inferred } from '@/components/ui';
import { cn } from '@/lib/design/cn';
import { describePerson } from '@/lib/api/onboarding';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

import { OnboardingShell } from '../onboarding-shell';
import { OnboardingRail } from './rail';
import { OnboardingSkeleton } from './company-form';
import { COUNTED_STEPS, COUNTED_TOTAL, ROLES, positionOf } from './steps';
import { SkipSetup } from './skip-setup';
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
 * me*, and the honest answer is that they are one. 📁 The design writes it
 * out: ***"Enter 1 or more — count yourself"***.
 *
 * ### ⛔ One sentence the design draws is deliberately NOT rendered
 *
 * 📁 The mock's action row ends with *"Validation runs on blur, never per
 * keystroke"*, right-aligned in `--ink-3`. ⚡ **That is an annotation about
 * the screen, not copy on it** — 📁 the same sentence appears in the
 * document's own *Validation* specification table, ⛔ **screen 04's identical
 * action row carries no such line**, and 📁 [ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)
 * asks whether a salesperson would use the words unprompted. **Nobody
 * describes their own job in terms of blur events.** ✅ **The behaviour is
 * implemented; the note about the behaviour is not drawn.**
 */
export function YouForm() {
  const router = useRouter();
  const { activeWorkspace } = useWorkspaceContext();
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
    if (parsed === 0) return 'Enter 1 or more — count yourself';
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
    if (chosenRole !== null) {
      // ⚡ **A role left as the product found it is *confirmed*, not re-entered**
      // — the same rule screen 04 applies to its four facts. ⛔ Nothing infers
      // a role today, so this is `entered` on every real run; the branch is
      // here because the moment something does, silently restamping somebody
      // else's guess as the person's own answer would be the lie.
      const untouched = role === null && run?.role?.provenance === 'inferred';
      body.role = { value: chosenRole, provenance: untouched ? 'confirmed' : 'entered' };
    }
    const size = shownTeamSize.toString().trim();
    if (size !== '')
      body.team_size = { value: Number(size), provenance: 'entered' } as never;

    await save((id) => describePerson(id, body));
    await advance('goals');
    router.push('/onboarding/goals');
  };

  /** 📁 *"What do you do at Northwind?"* — ⚡ **the customer's own Organization
   * name** ([ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)),
   * ⛔ **never the word *workspace***. Falls back to the unpersonalised
   * question rather than rendering a name-shaped hole. */
  const workspaceName = activeWorkspace?.name ?? null;

  return (
    <OnboardingShell
      rail={
        <OnboardingRail
          steps={COUNTED_STEPS}
          currentId="you"
          completedIds={[...(run?.completed_steps ?? []), 'workspace']}
          progress={{ step: positionOf('you'), of: COUNTED_TOTAL }}
          footer={
            <SkipSetup
              completedIds={run?.completed_steps ?? []}
              industry={run?.industry?.value ?? null}
            />
          }
        />
      }
      title={
        workspaceName === null
          ? 'What do you do here?'
          : `What do you do at ${workspaceName}?`
      }
      description="Your role decides your home page and which alerts reach you."
      actions={
        <>
          <Button
            onClick={submit}
            // 📁 **Disabled while the field is known to be wrong** — the design
            // draws Continue at 42% beside the error. ⛔ Not disabled *before*
            // blur: nothing is known to be wrong yet, and a primary action that
            // starts dead reads as a screen that has not loaded.
            disabled={isSaving || teamSizeError !== null}
          >
            {isSaving ? 'Saving…' : 'Continue'}
          </Button>
          <button
            type="button"
            onClick={async () => {
              // ⛔ **Skipping saves nothing and still advances**, exactly as on
              // screen 04. A skip that persisted a half-typed team size would
              // record an answer nobody gave.
              await advance('goals');
              router.push('/onboarding/goals');
            }}
            className="text-sm font-semibold text-content-subtle hover:text-content "
          >
            Skip for now
          </button>
        </>
      }
    >
      <div>
        {/* ♿ The heading is the question, so the group's legend repeats it to
            assistive technology rather than drawing a second one. 📁 The design
            puts no label above these cards. */}
        <ChoiceCards
          legend="Your role"
          legendHidden
          name="role"
          choices={ROLES}
          value={chosenRole}
          onChange={setRole}
        />
        {run?.role?.provenance === 'inferred' && role === null ? (
          // 📁 *"Role guessed from job title when the CRM is connected."*
          // ⛔ **Nothing produces that today** — Connect is the step *after*
          // this one — so this renders on no current run. ✅ It exists because
          // §9 requires every inferred value to be marked wherever it appears,
          // and a marking added later is a marking somebody forgets.
          <p className="mt-2.5 flex items-center gap-2 text-2xs text-content-muted">
            <Inferred />
            <span>Change it if that is not right.</span>
          </p>
        ) : null}

        {/* 📁 *"font-size:12.5px; font-weight:600; margin:22px 0 7px"*. */}
        <label
          htmlFor="team-size"
          className="mb-[7px] mt-[22px] block text-label font-semibold text-content"
        >
          How many people are on your revenue team?
        </label>
        <input
          id="team-size"
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
          aria-invalid={teamSizeError !== null}
          aria-describedby={teamSizeError === null ? undefined : 'team-size-error'}
          className={cn(
            // 🔴 **`outline-none` removed** — 📁 §17 `2.4.7`, *"never
            // suppressed"*. **Measured: it defeated the outline AND the 3px
            // ring `globals.css` draws.** ⚠️ **The `ring-danger-subtle` below is
            // a VALIDATION state and is unaffected.**
            'h-control-md w-full rounded-md border bg-surface px-[13px] text-sm text-content transition-shadow',
            teamSizeError === null
              ? 'border-border '
              : // 📁 *"border:1px solid var(--risk); box-shadow:0 0 0 3px var(--risk-tint)"*.
                'border-danger ring-[3px] ring-danger-subtle',
          )}
        />
        {teamSizeError === null ? null : (
          <p
            id="team-size-error"
            role="alert"
            className="mt-[7px] flex items-center gap-1.5 text-xs font-semibold text-danger"
          >
            {/* 📁 The design's own 12px glyph. ♿ **`aria-hidden`, because the
                sentence beside it already says everything the icon does** — and
                the colour is never the only carrier. */}
            <svg
              aria-hidden
              width="12"
              height="12"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              className="flex-none"
            >
              <circle cx="8" cy="8" r="6.2" />
              <path d="M8 5v3.5M8 11h.01" />
            </svg>
            {teamSizeError}
          </p>
        )}

        {error !== null ? (
          <p role="alert" className="mt-4 text-sm text-danger">
            {error}
          </p>
        ) : null}
      </div>
    </OnboardingShell>
  );
}
