/**
 * **Workflow 8 · Initial Onboarding** — [TASK-469](../../../docs/BACKLOG.md)
 * milestone 1, against `docs/design-snapshot/screens/Fortune Signora
 * Onboarding.dc.html`.
 *
 * ⚡ **The four assertions the row asks for by name** — validation on blur and
 * not per keystroke · an inferred value renders its marking · goal selection
 * stops at three · (the slug debounce is TASK-468's screen) — **plus the ones
 * the design states as accessibility criteria by number**, because *"choice
 * grids are radiogroup or group with checkboxes, not clickable divs"* is a
 * requirement rather than an implementation note.
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import { ChoiceCards, Inferred, MultiChoiceCards, StepRail } from '@/components/ui';

import {
  SIZE_BANDS,
  GOALS,
  INDUSTRIES,
  RAIL_STEPS,
  ROLES,
} from '@/app/(onboarding)/onboarding/steps';

describe('the rail — WCAG 1.3.1 and 2.4.3, which the design names by number', () => {
  it('is an ordered list, so the steps have an order a screen reader can read', () => {
    render(<StepRail steps={RAIL_STEPS} currentId="company" completedIds={['welcome']} />);

    const list = screen.getByRole('list');
    expect(within(list).getAllByRole('listitem')).toHaveLength(RAIL_STEPS.length);
  });

  it('marks exactly one step aria-current="step"', () => {
    const { container } = render(
      <StepRail steps={RAIL_STEPS} currentId="you" completedIds={['welcome', 'workspace']} />,
    );

    const current = container.querySelectorAll('[aria-current="step"]');
    expect(current).toHaveLength(1);
    expect(current[0]).toHaveTextContent('You');
  });

  it('🔴 says "completed" in words, never in colour alone', () => {
    /**
     * *"Never colour alone — the control mark carries it."* ⛔ **A green dot
     * is not a state anybody can read**, and `aria-current` covers only the
     * active step — a finished one has no ARIA equivalent, so it gets words.
     */
    render(<StepRail steps={RAIL_STEPS} currentId="company" completedIds={['welcome']} />);

    const welcome = screen.getByText('Welcome').closest('div');
    expect(welcome).toHaveTextContent(/completed/i);
  });

  it('⛔ offers no way to navigate, because selecting never advances', () => {
    // *"The user commits with the primary action."* A clickable rail would be
    // a second route through the flow, and the two would disagree about what
    // advancing saves.
    render(<StepRail steps={RAIL_STEPS} currentId="welcome" completedIds={[]} />);

    expect(screen.queryAllByRole('button')).toHaveLength(0);
    expect(screen.queryAllByRole('link')).toHaveLength(0);
  });

  it('does not mark the current step completed even when it is in the list', () => {
    // Going back is not destructive, so a step stays completed — but the one
    // being *shown* reads as current rather than as done, or the rail would
    // claim somebody finished the screen they are looking at.
    const { container } = render(
      <StepRail steps={RAIL_STEPS} currentId="company" completedIds={['welcome', 'company']} />,
    );

    const company = container.querySelector('[aria-current="step"]');
    expect(company).not.toHaveTextContent(/completed/i);
  });
});

describe('a single-choice grid is real radios — 1.3.1, and 2.1.1 follows free', () => {
  it('renders a radiogroup with one radio per choice', () => {
    render(
      <ChoiceCards
        legend="Your role"
        name="role"
        choices={ROLES}
        value={null}
        onChange={vi.fn()}
      />,
    );

    expect(screen.getAllByRole('radio')).toHaveLength(ROLES.length);
  });

  it('⛔ reports the choice and never advances', async () => {
    /** *"Selecting a choice never advances automatically"* (3.2.2). */
    const onChange = vi.fn();
    render(
      <ChoiceCards
        legend="Industry"
        name="industry"
        choices={INDUSTRIES}
        value={null}
        onChange={onChange}
      />,
    );

    await userEvent.click(screen.getByRole('radio', { name: /software/i }));

    expect(onChange).toHaveBeenCalledWith('Software');
  });

  it('is reachable and operable with no pointer at all', async () => {
    // 2.1.1: *"Nothing needs a pointer."* Native radios give roving arrow-key
    // movement inside the group; a div with role="radio" would need it
    // written, and B-312 is that defect one component over.
    const onChange = vi.fn();
    render(
      <ChoiceCards
        legend="Industry"
        name="industry"
        choices={INDUSTRIES}
        value={INDUSTRIES[0]!.value}
        onChange={onChange}
      />,
    );

    await userEvent.tab();
    await userEvent.keyboard('{ArrowDown}');

    expect(onChange).toHaveBeenCalledWith(INDUSTRIES[1]!.value);
  });
});

describe('goals stop at three, and the fourth says why', () => {
  it('⛔ disables the unchosen ones at the limit rather than ignoring a click', async () => {
    const onChange = vi.fn();
    render(
      <MultiChoiceCards
        legend="Your goals"
        name="goals"
        choices={GOALS}
        value={[GOALS[0]!.value, GOALS[1]!.value, GOALS[2]!.value]}
        onChange={onChange}
        max={3}
        countLabel={(count, max) => `${count} of ${max} chosen.`}
      />,
    );

    expect(screen.getByRole('checkbox', { name: /coach the team/i })).toBeDisabled();
  });

  it('⚠️ never disables an already-chosen one, so deselecting always works', async () => {
    /**
     * ⛔ **A limit that trapped somebody at their first three guesses would be
     * worse than no limit.** The design's own wording is *"unpick one"*.
     */
    const onChange = vi.fn();
    render(
      <MultiChoiceCards
        legend="Your goals"
        name="goals"
        choices={GOALS}
        value={[GOALS[0]!.value, GOALS[1]!.value, GOALS[2]!.value]}
        onChange={onChange}
        max={3}
        countLabel={(count, max) => `${count} of ${max} chosen.`}
      />,
    );

    await userEvent.click(screen.getByRole('checkbox', { name: /forecast accurately/i }));

    expect(onChange).toHaveBeenCalledWith([GOALS[1]!.value, GOALS[2]!.value]);
  });

  it('states the count as a status, not an alert — 4.1.3', () => {
    // *"Progress changes and autosave confirmations are status messages, not
    // alerts — they do not interrupt."* The count changes on every click.
    render(
      <MultiChoiceCards
        legend="Your goals"
        name="goals"
        choices={GOALS}
        value={[GOALS[0]!.value]}
        onChange={vi.fn()}
        max={3}
        countLabel={(count, max) => `${count} of ${max} chosen.`}
      />,
    );

    expect(screen.getByRole('status')).toHaveTextContent('1 of 3 chosen.');
  });

  it('⚡ keeps selection order, because the goals order the home page', async () => {
    const onChange = vi.fn();
    render(
      <MultiChoiceCards
        legend="Your goals"
        name="goals"
        choices={GOALS}
        value={[GOALS[2]!.value]}
        onChange={onChange}
        max={3}
        countLabel={(count, max) => `${count} of ${max} chosen.`}
      />,
    );

    await userEvent.click(screen.getByRole('checkbox', { name: /forecast accurately/i }));

    // Appended, not sorted — a sort would silently reorder the home page.
    expect(onChange).toHaveBeenCalledWith([GOALS[2]!.value, GOALS[0]!.value]);
  });
});

describe('the Inferred marking', () => {
  it('says the word rather than showing an icon', () => {
    // Somebody meeting this on their first screen has no legend to look it
    // up in.
    render(<Inferred />);

    expect(screen.getByText('Inferred')).toBeInTheDocument();
  });

  it('⚠️ is not a warning, and the tone is the assertion', () => {
    /**
     * ⛔ **Eleven of fifteen values arrive inferred on the happy path.**
     * Marking the ordinary case as a problem would make the whole screen read
     * as a list of things gone wrong — so no `alert`, and no danger tone.
     */
    const { container } = render(<Inferred />);

    expect(screen.queryByRole('alert')).toBeNull();
    expect(container.innerHTML).not.toMatch(/danger|warning/);
  });
});

describe("the design's enumerations, and the contract with the server", () => {
  it('offers "Other" on industry, because the step must never block', () => {
    // *"Single choice, pre-selected. Never blocks — 'Other' is always
    // available."*
    expect(INDUSTRIES.map((i) => i.value)).toContain('Other');
  });

  it('🔴 sizes are bands, never a free number', () => {
    /**
     * *"Free numbers are not accepted; bands are what benchmarks are computed
     * against."* ⛔ **The values must match the domain's `CompanySizeBand`
     * exactly** — a label the server cannot parse is a `422` on a step the
     * design says never blocks.
     */
    expect(SIZE_BANDS.map((s) => s.value)).toEqual([
      '1-10',
      '11-50',
      '51-200',
      '201-1000',
      '1001-5000',
      '5000+',
    ]);
  });

  it('names all six steps the design draws, in its order', () => {
    expect(RAIL_STEPS.map((s) => s.id)).toEqual([
      'welcome',
      'workspace',
      'company',
      'you',
      'goals',
      'connect',
    ]);
  });

  it('⛔ offers exactly six goals, because a seventh would map to nothing', () => {
    // The server's `Goal` enum is closed; a choice here it does not have is a
    // 422 rather than a preference.
    expect(GOALS).toHaveLength(6);
  });
});
