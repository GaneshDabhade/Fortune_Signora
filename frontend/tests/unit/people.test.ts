/**
 * How the product turns an identifier into a person.
 *
 * **D23 said Signora could name nobody**, and it was right when it was
 * written: the Python tier verifies tokens without ever learning who anybody
 * is (ADR-0026). TM-01 changed the fact underneath it by giving a membership
 * the address it was created with — so the honest absence is now a fallback
 * rather than the only answer.
 *
 * These assert the two properties that keep it honest: **no identifier ever
 * escapes as a name**, and an unnamed membership is absent rather than
 * present-and-blank.
 */
import { describe, expect, it } from 'vitest';

import { colleaguesFrom, nameOf, peopleFrom } from '@/components/team/people';
import type { Membership } from '@/lib/api/types';

const ME = 'aaaaaaaa-1111-4111-8111-111111111111';
const RAVI = 'bbbbbbbb-2222-4222-8222-222222222222';
const NAMELESS = 'cccccccc-3333-4333-8333-333333333333';

function member(user_id: string, member_email: string | null): Membership {
  return {
    id: crypto.randomUUID(),
    workspace_id: 'dddddddd-4444-4444-8444-444444444444',
    user_id,
    role: 'member',
    created_at: '2026-06-01T09:00:00Z',
    member_email,
  };
}

const ROSTER = [member(ME, 'ana@acme.com'), member(RAVI, 'ravi@acme.com'), member(NAMELESS, null)];

describe('who the organization can name', () => {
  it('keys everybody with an address by their identifier', () => {
    const people = peopleFrom(ROSTER);

    expect(people.get(RAVI)).toBe('ravi@acme.com');
  });

  it('omits a membership added by identifier rather than holding a blank', () => {
    // A map holding `''` would push the decision into every reader, and one of
    // them would render it.
    const people = peopleFrom(ROSTER);

    expect(people.has(NAMELESS)).toBe(false);
  });

  it('answers nothing at all before the roster has loaded', () => {
    expect(peopleFrom(undefined).size).toBe(0);
  });
});

describe('who can be offered', () => {
  it('leaves the reader out, because you cannot hand an account to yourself', () => {
    expect(colleaguesFrom(ROSTER, ME).map((one) => one.id)).toEqual([RAVI]);
  });

  it('omits anybody who cannot be named', () => {
    // **Named or not offered.** *"Somebody here"* in a picker is a row nobody
    // can choose between.
    expect(colleaguesFrom(ROSTER, ME).map((one) => one.id)).not.toContain(NAMELESS);
  });

  it('offers everybody when nobody is signed in', () => {
    expect(colleaguesFrom(ROSTER, null)).toHaveLength(2);
  });
});

describe('what to call somebody', () => {
  const PEOPLE = peopleFrom(ROSTER);

  it('says *you* first, because a reader recognises themselves first', () => {
    expect(nameOf(ME, PEOPLE, ME)).toBe('you');
  });

  it('names a colleague the roster holds', () => {
    expect(nameOf(RAVI, PEOPLE, ME)).toBe('ravi@acme.com');
  });

  it('never returns an identifier for somebody it cannot name', () => {
    // **The property, not the phrasing.** A raw identifier on screen is the
    // same absence dressed as information — including for somebody who has
    // since left, whose name the roster no longer holds.
    expect(nameOf(NAMELESS, PEOPLE, ME)).toBe('somebody here');
    expect(nameOf(NAMELESS, PEOPLE, ME)).not.toContain(NAMELESS);
  });

  it('says *nobody* rather than inventing a person for an unowned account', () => {
    expect(nameOf(null, PEOPLE, ME)).toBe('nobody');
  });
});
