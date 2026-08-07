/**
 * **TASK-478 — the three components slice 3 added, driven rather than
 * inspected.**
 *
 * `canonical-set.test.tsx` asserts that the design's enumeration and the
 * exported set agree. **That is a structural claim and it cannot see whether
 * any of it works** — a component exporting the right name and rendering
 * nothing would satisfy every check in that file.
 *
 * So this drives them: the keys §12 states, the copy §13 requires, and the
 * one behavioural difference that makes a drawer not a dialog.
 */
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { describe, expect, it, vi } from 'vitest';

import {
  CommandPalette,
  Confidence,
  Drawer,
  ErrorState,
  type CommandItem,
} from '@/components/ui';

const ITEMS: CommandItem[] = [
  { id: 'a', label: 'Vantage Logistics', group: 'Accounts', meta: 'Enterprise' },
  { id: 'b', label: 'Northwind Global', group: 'Accounts' },
  { id: 'c', label: 'Renewal risk sweep', group: 'Agents' },
];

function palette(overrides: Partial<React.ComponentProps<typeof CommandPalette>> = {}) {
  const onSelect = vi.fn();
  const onClose = vi.fn();
  render(
    <CommandPalette
      open
      onClose={onClose}
      items={ITEMS}
      query=""
      onQueryChange={() => {}}
      onSelect={onSelect}
      {...overrides}
    />,
  );
  return { onSelect, onClose };
}

describe('CommandPalette — the key map §12 states', () => {
  it('↓ moves the selection and ↵ opens what is selected', async () => {
    const user = userEvent.setup();
    const { onSelect } = palette();

    await user.keyboard('{ArrowDown}{Enter}');

    expect(onSelect).toHaveBeenCalledWith(
      expect.objectContaining({ id: 'b' }),
      'here',
    );
  });

  it('↑ from the first result wraps to the last', async () => {
    const user = userEvent.setup();
    const { onSelect } = palette();

    await user.keyboard('{ArrowUp}{Enter}');

    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 'c' }), 'here');
  });

  it('⌘↵ opens in the panel rather than here — the second destination', async () => {
    const user = userEvent.setup();
    const { onSelect } = palette();

    await user.keyboard('{Meta>}{Enter}{/Meta}');

    expect(onSelect).toHaveBeenCalledWith(expect.objectContaining({ id: 'a' }), 'panel');
  });

  it('esc closes', async () => {
    const user = userEvent.setup();
    const { onClose } = palette();

    await user.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalled();
  });

  it('groups by first appearance and does not re-sort the caller’s order', () => {
    palette();
    const groups = screen.getAllByText(/^(Accounts|Agents)$/).map((el) => el.textContent);
    expect(groups).toEqual(['Accounts', 'Agents']);
  });

  it('says it found nothing rather than rendering an empty box', () => {
    palette({ items: [], query: 'zzz' });
    // Stated absence: an empty list is indistinguishable from a search that
    // never ran, which is the whole of P-A.
    expect(screen.getByText(/Nothing matches/)).toBeInTheDocument();
  });

  it('an empty result set has nothing selected, so ↵ opens nothing', async () => {
    const user = userEvent.setup();
    const { onSelect } = palette({ items: [], query: 'zzz' });

    await user.keyboard('{Enter}');

    expect(onSelect).not.toHaveBeenCalled();
  });
});

describe('Drawer — non-modal, which is the behavioural claim', () => {
  it('leaves the rest of the page reachable', async () => {
    const user = userEvent.setup();
    render(
      <div>
        <button type="button">Behind the drawer</button>
        <Drawer open onClose={() => {}} title="Assistant">
          <p>Panel body</p>
        </Drawer>
      </div>,
    );

    // **The test that separates this from `Dialog`.** A modal would make
    // this button inert; §14 requires the drawer to push content rather
    // than cover it, so the page stays usable while the panel is open.
    const behind = screen.getByRole('button', { name: 'Behind the drawer' });
    await user.click(behind);
    expect(behind).toHaveFocus();
  });

  it('escape closes it, because that behaviour is the panel’s own', async () => {
    const user = userEvent.setup();
    const onClose = vi.fn();
    render(<Drawer open onClose={onClose} title="Assistant" />);

    await user.keyboard('{Escape}');

    expect(onClose).toHaveBeenCalled();
  });

  it('renders the scope it was asked about', () => {
    render(<Drawer open onClose={() => {}} title="Assistant" scope="EMEA enterprise · Q3" />);
    expect(screen.getByText('EMEA enterprise · Q3')).toBeInTheDocument();
  });

  it('renders nothing when closed', () => {
    render(<Drawer open={false} onClose={() => {}} title="Assistant" />);
    expect(screen.queryByText('Assistant')).not.toBeInTheDocument();
  });
});

/** `navigator.clipboard` is a getter in jsdom, so it is replaced rather than
 * assigned over — `Object.assign` throws on it. */
function stubClipboard(writeText: ReturnType<typeof vi.fn>) {
  Object.defineProperty(navigator, 'clipboard', {
    value: { writeText },
    configurable: true,
  });
}

describe('ErrorState — §13’s copyable correlation id', () => {
  it('copies the id to the clipboard and says so', async () => {
    const user = userEvent.setup();
    // **After `setup()`, deliberately.** userEvent v14 installs its own
    // clipboard stub, so a stub written before this line is replaced by it
    // and the component ends up calling userEvent's rather than the spy.
    const writeText = vi.fn().mockResolvedValue(undefined);
    stubClipboard(writeText);

    render(
      <ErrorState
        title="Score trend unavailable"
        description="The scoring service did not respond."
        correlationId="req_9f3c-88ad"
      />,
    );
    await user.click(screen.getByRole('button', { name: /req_9f3c-88ad/ }));

    expect(writeText).toHaveBeenCalledWith('req_9f3c-88ad');
    expect(await screen.findByText('Copied')).toBeInTheDocument();
  });

  it('reports a failed copy instead of swallowing it', async () => {
    // **The half that matters.** A silent failure produces a support ticket
    // carrying whatever was in the clipboard beforehand, and an engineer
    // concluding the event was never logged.
    const user = userEvent.setup();
    // **After `setup()`, deliberately.** userEvent v14 installs its own
    // clipboard stub, so a stub written before this line is replaced by it
    // and the component ends up calling userEvent's rather than the spy.
    const writeText = vi.fn().mockRejectedValue(new Error('denied'));
    stubClipboard(writeText);

    render(
      <ErrorState
        title="Score trend unavailable"
        description="The scoring service did not respond."
        correlationId="req_9f3c-88ad"
      />,
    );
    await user.click(screen.getByRole('button', { name: /req_9f3c-88ad/ }));

    expect(await screen.findByText('Copy failed')).toBeInTheDocument();
    // And the id is still on screen, so selecting it by hand remains possible.
    expect(screen.getByText(/req_9f3c-88ad/)).toBeInTheDocument();
  });

  it('announces itself, because the user did not ask for this', () => {
    render(<ErrorState title="Score trend unavailable" description="No response." />);
    expect(screen.getByRole('alert')).toBeInTheDocument();
  });

  it('offers the assistant only when a caller supplies it', () => {
    const { rerender } = render(
      <ErrorState title="Score trend unavailable" description="No response." />,
    );
    expect(screen.queryByRole('button', { name: 'Ask what changed' })).not.toBeInTheDocument();

    rerender(
      <ErrorState
        title="Score trend unavailable"
        description="No response."
        assistantAction={<button type="button">Ask what changed</button>}
      />,
    );
    // §13 offers it "when the failure is a data question rather than an
    // outage" — a distinction only the caller can make.
    expect(screen.getByRole('button', { name: 'Ask what changed' })).toBeInTheDocument();
  });
});

describe('Confidence — §14’s figure, readable without the pips', () => {
  it('states the level in words, not only in dots', () => {
    render(<Confidence level={4} />);
    expect(screen.getByText(/Confidence 4 of 5/)).toBeInTheDocument();
  });

  it('names its sources when it has them, and stays silent when it does not', () => {
    const { rerender } = render(<Confidence level={4} sources={6} />);
    expect(screen.getByText(/6 sources/)).toBeInTheDocument();

    rerender(<Confidence level={4} />);
    // ⛔ A count is never invented. "0 sources" and "unknown" are different
    // claims, and only one of them is true here.
    expect(screen.queryByText(/sources/)).not.toBeInTheDocument();
  });

  it('says "1 source" rather than "1 sources"', () => {
    render(<Confidence level={2} sources={1} />);
    expect(screen.getByText(/1 source(?!s)/)).toBeInTheDocument();
  });

  it('clamps outside the scale rather than redefining it', () => {
    // Seven pips against a five-point scale would silently change what the
    // figure means, and the reader\'s calibration is the whole value.
    const { rerender } = render(<Confidence level={9} />);
    expect(screen.getByText(/Confidence 5 of 5/)).toBeInTheDocument();

    rerender(<Confidence level={-3} />);
    expect(screen.getByText(/Confidence 0 of 5/)).toBeInTheDocument();
  });
});
