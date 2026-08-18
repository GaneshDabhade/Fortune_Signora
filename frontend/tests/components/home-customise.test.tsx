/**
 * **Home's *Customise* control and drawer** — 📁 `Fortune Signora Home.dc.html`
 * §10's keyboard table:
 *
 * > *"**Customise** — opens the card-order panel as a drawer. **Escape closes and
 * > returns focus to the trigger.**"* `⌘⇧H`
 * >
 * > **`U-05`, interim** — *"**reorder and remove only.**"*
 */
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const save = vi.hoisted(() => vi.fn());

import { CustomiseButton, useCustomise } from '@/components/home/customise';
import { CustomiseDrawer } from '@/components/home/customise-drawer';
import type { CardContract, HomeCardLayout } from '@/lib/home/cards';

const card = (id: string, title: string): CardContract =>
  ({ id, title, module: 'test', requires: null }) as CardContract;

const CARDS = [
  card('daily-briefing', 'Daily briefing'),
  card('needs-you-today', 'Needs you today'),
  card('recents', 'Pick up where you left off'),
];

beforeEach(() => {
  save.mockReset();
});

/**
 * ⚡ **Both halves, wired the way Home wires them.** 📁 `Drawer` *"renders in the
 * flow its parent gives it"*, so the placing level owns the state — testing the
 * button alone would test a control with nothing behind it.
 */
function Harness({ layout }: { layout?: HomeCardLayout }) {
  const controls = useCustomise(true);
  return (
    <>
      <CustomiseButton controls={controls} className="trigger" />
      <CustomiseDrawer
        open={controls.open}
        onClose={controls.close}
        composition="seller"
        cards={CARDS}
        layout={layout}
        saving={false}
        onSave={(next) => {
          save({ composition: 'seller', layout: next });
          controls.close();
        }}
      />
    </>
  );
}

function renderControl() {
  return render(<Harness />);
}

describe('📁 "opens the card-order panel as a drawer"', () => {
  it('is closed until somebody asks for it', () => {
    renderControl();

    expect(screen.queryByRole('complementary')).not.toBeInTheDocument();
  });

  it('opens from the control', async () => {
    const user = userEvent.setup();
    renderControl();

    await user.click(screen.getByRole('button', { name: /Customise/ }));

    expect(await screen.findByRole('complementary')).toBeVisible();
  });

  /**
   * 🔴 **`⌘⇧H`**, and 📁 the design writes the Mac glyph. ⚡ **`Ctrl⇧H` is the
   * same gesture on every other platform** — a Mac-only binding would be a
   * capability half the customers do not have.
   */
  it('🔴 opens from ⌘⇧H', async () => {
    const user = userEvent.setup();
    renderControl();

    await user.keyboard('{Meta>}{Shift>}h{/Shift}{/Meta}');

    expect(await screen.findByRole('complementary')).toBeVisible();
  });

  it('and from Ctrl⇧H', async () => {
    const user = userEvent.setup();
    renderControl();

    await user.keyboard('{Control>}{Shift>}h{/Shift}{/Control}');

    expect(await screen.findByRole('complementary')).toBeVisible();
  });

  /**
   * ⛔ **Never while somebody is typing.** ⚡ A shortcut that fires inside a field
   * is what makes people distrust every shortcut — the same guard the `V`
   * composition shortcut carries.
   */
  it('⛔ and never while somebody is typing', async () => {
    const user = userEvent.setup();
    render(
      <>
        <input aria-label="Search" />
        <Harness />
      </>,
    );

    await user.click(screen.getByLabelText('Search'));
    await user.keyboard('{Meta>}{Shift>}h{/Shift}{/Meta}');

    expect(screen.queryByRole('complementary')).not.toBeInTheDocument();
  });
});

describe('📁 "Escape closes and returns focus to the trigger"', () => {
  it('🔴 returns focus to the control that opened it', async () => {
    const user = userEvent.setup();
    renderControl();
    const trigger = screen.getByRole('button', { name: /Customise/ });

    await user.click(trigger);
    await screen.findByRole('complementary');
    await user.keyboard('{Escape}');

    await waitFor(() => expect(screen.queryByRole('complementary')).not.toBeInTheDocument());
    // ⛔ **Focus lost to `<body>` drops a keyboard user at the top of the page.**
    expect(trigger).toHaveFocus();
  });
});

describe('📁 "reorder and remove only" — U-05', () => {
  it('🔴 saves the order the person left', async () => {
    const user = userEvent.setup();
    renderControl();

    await user.click(screen.getByRole('button', { name: /Customise/ }));
    await screen.findByRole('complementary');
    await user.click(screen.getByRole('button', { name: 'Move Pick up where you left off up' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    expect(save).toHaveBeenCalledTimes(1);
    expect(save.mock.calls[0]?.[0]).toMatchObject({
      composition: 'seller',
      layout: {
        order: ['daily-briefing', 'recents', 'needs-you-today'],
        hidden: [],
      },
    });
  });

  it('🔴 saves a removal', async () => {
    const user = userEvent.setup();
    renderControl();

    await user.click(screen.getByRole('button', { name: /Customise/ }));
    await screen.findByRole('complementary');
    await user.click(screen.getByRole('button', { name: 'Remove Needs you today' }));
    await user.click(screen.getByRole('button', { name: 'Save' }));

    expect(save.mock.calls[0]?.[0]).toMatchObject({
      layout: { hidden: ['needs-you-today'] },
    });
  });

  /**
   * ⛔ **A removed card stays in the panel**, greyed with a restore control —
   * 📁 `P-11`'s instinct one state over: *"hidden capability is the most common
   * cause of 'the product does not do X' when it does."* ⚡ The drawer is the one
   * place a person can find it again.
   */
  it('🔴 keeps a removed card in the panel so it can be restored', async () => {
    const user = userEvent.setup();
    renderControl();

    await user.click(screen.getByRole('button', { name: /Customise/ }));
    await screen.findByRole('complementary');
    await user.click(screen.getByRole('button', { name: 'Remove Needs you today' }));

    expect(screen.getByRole('button', { name: 'Restore Needs you today' })).toBeVisible();
  });

  /**
   * ⛔ **Nothing is saved until *Save*.** ⚡ A live-applying panel would reorder
   * the page behind the drawer while somebody was still deciding, which is the
   * reshuffle-under-the-cursor 📁 `P-05` names.
   */
  it('⛔ and Cancel writes nothing', async () => {
    const user = userEvent.setup();
    renderControl();

    await user.click(screen.getByRole('button', { name: /Customise/ }));
    await screen.findByRole('complementary');
    await user.click(screen.getByRole('button', { name: 'Remove Needs you today' }));
    await user.click(screen.getByRole('button', { name: 'Cancel' }));

    expect(save).not.toHaveBeenCalled();
  });

  /**
   * ⚡ **Re-seeded on every open**, so a cancelled edit is genuinely discarded
   * rather than waiting in state for the next time the drawer is opened.
   */
  it('⛔ and a cancelled edit does not survive the next open', async () => {
    const user = userEvent.setup();
    renderControl();

    await user.click(screen.getByRole('button', { name: /Customise/ }));
    await screen.findByRole('complementary');
    await user.click(screen.getByRole('button', { name: 'Remove Needs you today' }));
    await user.click(screen.getByRole('button', { name: 'Cancel' }));
    await user.click(screen.getByRole('button', { name: /Customise/ }));
    await screen.findByRole('complementary');

    expect(screen.getByRole('button', { name: 'Remove Needs you today' })).toBeVisible();
  });
});
