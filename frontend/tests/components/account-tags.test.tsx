/**
 * **The Companies table's Tags column** — [TASK-466](../../../docs/BACKLOG.md).
 *
 * 🔴 **The assertion that matters is the absent one**: an account the customer
 * has not labelled renders **nothing** — not an em dash, not *"None"*.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AccountTags, TAG_TONES, tagsFor } from '@/components/accounts/account-tags';
import type { AccountTag } from '@/lib/api/types';

const RISK: AccountTag = { id: 't1', name: 'At risk', tone: 'risk' };
const STRATEGIC: AccountTag = { id: 't2', name: 'Strategic', tone: 'neutral' };
const EXPANSION: AccountTag = { id: 't3', name: 'Expansion', tone: 'pos' };

describe('🔴 an unlabelled account renders nothing at all', () => {
  it('⛔ not an em dash, and not the word None', () => {
    /**
     * 📁 [`table.ts`](../../lib/accounts/table.ts)'s own law: *"a column of
     * `—` is worse than an absent column — it says Signora looked and found
     * nothing."* ⚡ **Here the truth is that the CUSTOMER has not labelled
     * this account**, which is a fact about them rather than about Signora,
     * and a placeholder would make it look like a gap the product should fill.
     */
    const { container } = render(<AccountTags tags={[]} />);

    expect(container).toBeEmptyDOMElement();
  });

  it('✅ and a labelled one renders its chips', () => {
    render(<AccountTags tags={[RISK, STRATEGIC]} />);

    expect(screen.getByText('At risk')).toBeVisible();
    expect(screen.getByText('Strategic')).toBeVisible();
  });
});

describe('🔴 a customer label can never wear Signora’s own tone', () => {
  /**
   * ⛔ **Enforced in both tiers.** The server's `TagTone` has four members and
   * `ai` is not one; this map is total over exactly those four. 📁 `Badge`
   * reserves `ai` for *"a machine produced this"*, and **a human opinion
   * wearing it is the one confusion the evidence model exists to prevent.**
   */
  it('⛔ no tone maps to `ai`', () => {
    expect(Object.values(TAG_TONES)).not.toContain('ai');
  });

  it('✅ and the four the design draws each map to a token the library already has', () => {
    expect(TAG_TONES).toEqual({
      risk: 'danger',
      warn: 'warning',
      pos: 'success',
      neutral: 'neutral',
    });
  });
});

describe('⚡ resolving a row’s tags against the vocabulary', () => {
  const vocabulary = [RISK, STRATEGIC, EXPANSION];

  it('returns the tags this account wears', () => {
    const held = tagsFor('a1', { a1: ['t3', 't1'] }, vocabulary);

    expect(held.map((t) => t.name)).toEqual(['At risk', 'Expansion']);
  });

  it('🔴 order is the vocabulary’s, not the assignment’s', () => {
    /**
     * ⚡ **Insertion order is a hidden input.** The server returns the
     * vocabulary in name order; **a row rendering its chips in whatever order
     * the assignment happened to arrive would reorder between two visits** —
     * the kind of defect nobody files and everybody notices.
     */
    const one = tagsFor('a1', { a1: ['t3', 't1'] }, vocabulary);
    const other = tagsFor('a1', { a1: ['t1', 't3'] }, vocabulary);

    expect(one.map((t) => t.id)).toEqual(other.map((t) => t.id));
  });

  it('⛔ an account absent from the answer has no tags, and does not throw', () => {
    // ⚡ **Absent rather than present-and-empty is the server's contract**, and
    // the request named exactly which accounts were asked about.
    expect(tagsFor('nobody', { a1: ['t1'] }, vocabulary)).toEqual([]);
  });

  it('⛔ an id with no tag in the vocabulary is dropped, never rendered broken', () => {
    /**
     * ⚠️ **Two separate reads.** A tag created between them is a transient the
     * customer must never see as a broken chip — **and the next vocabulary
     * fetch resolves it.**
     */
    const held = tagsFor('a1', { a1: ['t1', 'gone'] }, vocabulary);

    expect(held.map((t) => t.id)).toEqual(['t1']);
  });

  it('⛔ neither read having landed yet is empty rather than a crash', () => {
    // 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md) is about a FAILED
    // read rendering as empty; this is the loading case, where empty is the
    // honest answer and the column simply has nothing yet.
    expect(tagsFor('a1', undefined, vocabulary)).toEqual([]);
    expect(tagsFor('a1', { a1: ['t1'] }, undefined)).toEqual([]);
  });
});
