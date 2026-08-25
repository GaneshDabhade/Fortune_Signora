/**
 * 🔴 **[B-1061](../../../docs/BUGS.md) — the palette was not a combobox to
 * assistive technology, and its groups were decorative.**
 *
 * 📁 `Fortune Signora Global Search.dc.html`, `a11y` §4.1.2, verbatim:
 *
 * > ***"The input is a combobox with `aria-expanded`, `aria-activedescendant`
 * > and an owned listbox; results are options, groups are labelled groups."***
 *
 * ⚠️ **Every assertion here queries by ROLE, never by class or attribute
 * string** — 📁 the row's own acceptance criterion, and the reason it asks for
 * it: **`aria-controls` and `aria-activedescendant` were already present and
 * correct**, which is exactly what made the palette read as finished from the
 * source while failing in the tree. ⛔ **A test that had asserted those two
 * would have been green throughout.**
 *
 * 📁 **Same family as [B-1055](../../../docs/BUGS.md)** — *an ARIA pattern
 * implemented to the attribute that is visible in source, and not to the
 * relationship that makes it work.*
 */
import { render, screen, within } from '@testing-library/react';
import { describe, expect, it, vi } from 'vitest';

import { CommandPalette, type CommandItem } from '@/components/ui';

const noop = vi.fn();

const RESULTS: CommandItem[] = [
  { id: 'a', group: 'Records', label: 'Porterfield Health Systems' },
  { id: 'b', group: 'Records', label: 'Porter Freight' },
  { id: 'c', group: 'Navigate', label: 'Accounts' },
];

function palette(over: Partial<Parameters<typeof CommandPalette>[0]> = {}) {
  return render(
    <CommandPalette
      open
      onClose={noop}
      items={RESULTS}
      query="porter"
      onQueryChange={noop}
      onSelect={noop}
      {...over}
    />,
  );
}

describe('§4.1.2 · the input is a combobox', () => {
  it('🔴 has the widget role that makes the other attributes mean anything', () => {
    palette();

    // ⛔ **The whole defect in one query.** `aria-activedescendant` is only
    // meaningful on an element with a widget role — on a plain `<input>`
    // there is nothing for assistive technology to apply it to, so the
    // highlighted result was never announced.
    expect(screen.getByRole('combobox')).toBeInTheDocument();
  });

  it('announces the highlighted result, which is what the role buys', () => {
    palette();

    const input = screen.getByRole('combobox');
    const active = input.getAttribute('aria-activedescendant');
    expect(active).not.toBeNull();

    // ⚡ **The relationship, not the attribute.** A non-null id proves
    // nothing if it points at no element — which is how this class of defect
    // survives a test that reads the attribute and stops there.
    const options = screen.getAllByRole('option');
    expect(options.some((option) => option.id === active)).toBe(true);
  });

  it('owns the list it controls', () => {
    palette();

    const controls = screen.getByRole('combobox').getAttribute('aria-controls');
    expect(screen.getByRole('listbox').id).toBe(controls);
  });
});

describe('§4.1.2 · aria-expanded reflects the LIST, not the dialog', () => {
  it('is expanded while there are options', () => {
    palette();
    expect(screen.getByRole('combobox')).toHaveAttribute('aria-expanded', 'true');
  });

  it('🔴 is NOT expanded on an open palette with nothing to show', () => {
    /**
     * ⛔ **Hardcoding `true` would have passed the test above and been
     * wrong.** ⚡ **The palette opens with no results until something is
     * typed** — announcing an expanded list there tells somebody there are
     * options to arrow through when there are none.
     */
    palette({ items: [], query: '' });
    expect(screen.getByRole('combobox')).toHaveAttribute('aria-expanded', 'false');
  });
});

describe('§4.1.2 · groups are labelled groups', () => {
  it('🔴 renders a group per section, where there were none at all', () => {
    palette();

    // ⛔ `document.querySelectorAll('[role=group]').length` was **0**: a
    // sighted reader saw results in labelled sections and a screen-reader
    // user heard a flat list.
    expect(screen.getAllByRole('group')).toHaveLength(2);
  });

  it('names each group from the label already on screen', () => {
    palette();

    // ⚡ Queried BY NAME — which only resolves if `aria-labelledby` points at
    // an element that exists and carries the text.
    expect(screen.getByRole('group', { name: 'Records' })).toBeInTheDocument();
    expect(screen.getByRole('group', { name: 'Navigate' })).toBeInTheDocument();
  });

  it('🔴 puts the options INSIDE their group, not merely beside it', () => {
    /**
     * ⚠️ **The containment is the point.** ⛔ A `listbox` may own only
     * `option` and `group` children, so a label sitting loose between options
     * was invalid inside the role it was in — and grouping that does not
     * contain its members conveys nothing.
     */
    palette();

    const records = screen.getByRole('group', { name: 'Records' });
    expect(within(records).getAllByRole('option')).toHaveLength(2);
    expect(within(records).getByText('Porter Freight')).toBeInTheDocument();
  });
});
