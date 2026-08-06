/**
 * How current Signora's knowledge of an account is — A4.
 *
 * **The product's promise is *here is what changed*, and until this line it
 * never said when it last learned anything.** A seller could not tell *"nothing
 * is happening at this account"* from *"nothing has reached us since March"*,
 * and those demand opposite actions.
 *
 * These assert two things a customer would notice, and one they would not
 * notice until it had cost them: that absence is stated rather than left blank,
 * and that **the sentence never claims Signora checked.** Nothing in the
 * repository records when a provider last *looked* at a given account —
 * `provider_sync` carries no subject and `provider_watermark.position` only
 * advances when records arrive — so a line reading *"last checked"* would be
 * the product claiming a capability it does not have, on the surface where
 * trust is being built.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { Freshness, LastChecked } from '@/components/intelligence/freshness';

describe('how current the evidence is', () => {
  it('says how long ago the newest evidence was seen', () => {
    const twoWeeksAgo = new Date(Date.now() - 15 * 86_400_000).toISOString();

    render(<Freshness observedAt={twoWeeksAgo} />);

    expect(screen.getByText(/Latest evidence · 2 weeks ago/)).toBeInTheDocument();
  });

  it('says so in words when nothing has ever been collected', () => {
    // **Not a blank.** A missing line reads as a page that forgot to render
    // something; this reads as an answer — and it is the answer that should
    // stop a seller trusting the score above it.
    render(<Freshness observedAt={null} />);

    expect(screen.getByText('No evidence collected yet')).toBeInTheDocument();
  });

  it('never tells a customer that Signora checked', () => {
    /** **The assertion that protects the honesty**, not the wording.
     *
     * The fact behind this line is *when a provider observed the newest thing
     * we hold*. Signora cannot currently say when it last looked at an
     * account, and the two differ exactly where it matters: a provider that
     * ran and found nothing leaves no trace. Somebody tightening this copy to
     * the more natural *"Last checked 2 weeks ago"* would make the product
     * state something no table in the repository supports, and no other test
     * in the suite would notice.
     */
    const { container } = render(
      <Freshness observedAt={new Date(Date.now() - 3 * 86_400_000).toISOString()} />,
    );

    expect(container.textContent).not.toMatch(/check|updated|synced|refreshed/i);
  });
});

describe('whether Signora looked at all — A7', () => {
  const THREE_DAYS_AGO = new Date(Date.now() - 3 * 86_400_000).toISOString();

  /**
   * **The refusal above is scoped by this, never lifted by it.**
   *
   * `51 §A7`'s risk line says *"only ship the word checked once it is true"*
   * and that `freshness.test.tsx` *"is updated by this slice, never worked
   * around"*. This is that update, and the shape of it matters: the
   * `Freshness` test three blocks up still asserts that the brief's line never
   * says *checked*, and it still passes, because on the brief it still would
   * not be true. What changed is that a different fact now exists — a
   * completed read of a named company, written whether or not anything came
   * back — and a different component renders it where it *is* true.
   *
   * **The two are separate exports for exactly that reason.** A prop on
   * `Freshness` would have made the honest sentence and the dishonest one one
   * component away from each other, with a boolean deciding which.
   */
  it('says how long ago somebody last looked', () => {
    render(<LastChecked lastAttempt={THREE_DAYS_AGO} storedAnything />);

    expect(screen.getByText('Checked 3 days ago')).toBeInTheDocument();
  });

  it('says when a look found nothing', () => {
    // **The state that was unrenderable before A7**, and the reason the slice
    // exists: the watermark's position only moves when records arrive, so a
    // completed read that stored nothing left no trace to render.
    render(<LastChecked lastAttempt={THREE_DAYS_AGO} storedAnything={false} />);

    expect(screen.getByText('Checked 3 days ago · nothing found')).toBeInTheDocument();
  });

  it('says so in words when nobody has looked', () => {
    render(<LastChecked lastAttempt={null} storedAnything={false} />);

    expect(screen.getByText('Not checked yet')).toBeInTheDocument();
  });

  it('never says nobody looked at something it holds evidence for', () => {
    /** **The fourth state, and the one a shortcut would get wrong.** A row
     * written before `attempted_at` existed carries evidence and no time.
     * Treating a null attempt as *never checked* would tell a customer
     * something false about their own account — so absence of the *time* is
     * stated, and absence of the *look* is not claimed. */
    const { container } = render(<LastChecked lastAttempt={null} storedAnything />);

    expect(container.textContent).not.toMatch(/not checked yet/i);
    expect(container.textContent).toMatch(/did not record when/i);
  });

  it('never claims to know what a check found', () => {
    /** **The promise beyond this one.** `attempted_at` records that a read
     * completed; nothing records what it returned, and *"nothing found"* is
     * about stored evidence rather than about a provider's verdict. A line
     * saying *no change* or *nothing new at this account* would assert a
     * judgement no table in the repository supports. */
    const { container } = render(
      <LastChecked lastAttempt={THREE_DAYS_AGO} storedAnything={false} />,
    );

    for (const overclaim of [/no change/i, /nothing new/i, /up to date/i, /unchanged/i]) {
      expect(container.textContent).not.toMatch(overclaim);
    }
  });
});
