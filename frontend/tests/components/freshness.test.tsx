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

import { Freshness } from '@/components/intelligence/freshness';

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
