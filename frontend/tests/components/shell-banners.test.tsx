/**
 * **The shell's banner region** — [TASK-1408](../../../docs/BACKLOG.md).
 *
 * ⚡ **Rule 10's ordering is a safety property, so it is tested as one.** The
 * environment banner carries the sentence that tells somebody they are
 * impersonating another person; a commercial banner above it pushes that
 * sentence down, and on a short viewport off it entirely.
 */
import { render, screen, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it } from 'vitest';

import { ShellBanners, type ShellBanner } from '@/components/ui/shell-banners';

const SANDBOX: ShellBanner = {
  kind: 'environment',
  title: 'Sandbox.',
  body: 'A copy of production. Changes do not sync.',
};
const IMPERSONATION: ShellBanner = {
  kind: 'environment',
  risky: true,
  title: 'Viewing as J. Okafor.',
  body: 'Support session · every action is logged.',
};
const TRIAL: ShellBanner = {
  kind: 'commercial',
  title: '21 days left in your Enterprise trial.',
  body: 'Seats 34 of 50.',
};

function rendered() {
  return within(screen.getByTestId('shell-banners')).queryAllByRole('status');
}

describe('📁 rule 10 — at most two, environment before commercial', () => {
  it('🔴 puts environment first even when the caller passes commercial first', () => {
    /**
     * ⚠️ **This case caught a real defect while it was being written.** The
     * first version paired each admitted rule back to its source *by index* —
     * ⛔ **which is wrong the moment sorting moves one**, and this is the
     * input that moves one. **The rule and its banner now travel together and
     * cannot come apart.**
     */
    render(<ShellBanners banners={[TRIAL, IMPERSONATION]} />);
    const rows = rendered();
    expect(rows[0]).toHaveAttribute('data-kind', 'environment');
    expect(rows[0]).toHaveTextContent('Viewing as J. Okafor.');
    expect(rows[1]).toHaveAttribute('data-kind', 'commercial');
    expect(rows[1]).toHaveTextContent('21 days left');
  });

  it('⛔ never renders a third', () => {
    render(<ShellBanners banners={[SANDBOX, TRIAL, { ...TRIAL, title: 'Another.' }]} />);
    expect(rendered()).toHaveLength(2);
    expect(screen.queryByText('Another.')).not.toBeInTheDocument();
  });
});

describe('🔴 the sentence that must not be dismissable', () => {
  it('⛔ a risky environment banner has NO dismiss control — absent, not disabled', () => {
    /**
     * ⚡ **A disabled control still reads as *"this is optional"*.** The state
     * it announces is one somebody must not forget they are in.
     */
    render(<ShellBanners banners={[IMPERSONATION]} />);
    expect(screen.queryByRole('button', { name: /Dismiss/ })).not.toBeInTheDocument();
    expect(rendered()[0]).toHaveAttribute('data-dismissible', 'false');
  });

  it('a non-risky environment banner can be dismissed, and stays dismissed', async () => {
    render(<ShellBanners banners={[SANDBOX]} />);
    await userEvent.click(screen.getByRole('button', { name: /Dismiss: Sandbox/ }));
    expect(screen.queryByText('Sandbox.')).not.toBeInTheDocument();
  });
});

describe('🔴 commercial banners are suppressed in sandbox, not queued', () => {
  it('📁 "suppressed entirely inside sandbox"', () => {
    /**
     * ⛔ **A trial countdown over a copy of production is an upsell against
     * data that is not real** — and 📁 the System States rules name *"no
     * upsell to someone without the authority to buy"* as the same family.
     */
    render(<ShellBanners banners={[SANDBOX, TRIAL]} inSandbox />);
    expect(screen.getByText('Sandbox.')).toBeInTheDocument();
    expect(screen.queryByText(/Enterprise trial/)).not.toBeInTheDocument();
    expect(rendered()).toHaveLength(1);
  });
});

describe('⛔ the region owns no navigation', () => {
  it('renders the action the caller supplies and invents none', () => {
    /**
     * 📁 **[D-193](../../../docs/DECISION_REGISTER.md)**: modules register
     * capabilities rather than issuing redirects, and
     * [D-194](../../../docs/DECISION_REGISTER.md) already found five modules
     * routing. ⛔ **A sixth in the shell would be the hardest to remove.**
     */
    render(
      <ShellBanners
        banners={[{ ...SANDBOX, action: <a href="/production">Switch to production</a> }]}
      />,
    );
    expect(screen.getByRole('link', { name: 'Switch to production' })).toHaveAttribute(
      'href',
      '/production',
    );

    // ⛔ With no action supplied, the region adds none of its own.
    const { container } = render(<ShellBanners banners={[IMPERSONATION]} />);
    expect(within(container).queryAllByRole('link')).toHaveLength(0);
  });
});
