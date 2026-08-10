/**
 * **Who is actually being invited** — [TASK-471](../../../docs/BACKLOG.md),
 * 📁 `Fortune Signora Team Management.dc.html` §02.
 *
 * 🔴 **The row's Component coverage, in the design's own words**:
 * ***"an existing member is skipped, not rejected."***
 */
import { describe, expect, it } from 'vitest';

import {
  classifyAddresses,
  explainVerdict,
  sendable,
  splitAddresses,
} from '@/lib/team/invitations';

const MEMBERS = ['j.okafor@northwind.com'];
const INVITED = ['a.silva@partner-logistics.com'];

describe('🔴 an existing member is skipped, not rejected', () => {
  it('⛔ the rest of the batch still sends', () => {
    /**
     * ⚡ **This is the whole rule.** **Somebody pasting twenty addresses from a
     * spreadsheet must not have the batch refused because one colleague is
     * already here** — ⛔ **or they will send nineteen invitations one at a
     * time instead**, which is worse for them and worse for the audit trail.
     */
    const classified = classifyAddresses(
      'new@northwind.com, j.okafor@northwind.com, second@northwind.com',
      MEMBERS,
      INVITED,
    );

    expect(classified.map((c) => c.verdict)).toEqual([
      'invite',
      'already-a-member',
      'invite',
    ]);
    expect(sendable(classified)).toEqual(['new@northwind.com', 'second@northwind.com']);
  });

  it("📁 and it says so in the design's register — what will HAPPEN, not what is wrong", () => {
    const [entry] = classifyAddresses('j.okafor@northwind.com', MEMBERS, INVITED);

    // 📁 *"j.okafor@northwind.com is already a member. It will be skipped."*
    expect(explainVerdict(entry as never)).toBe(
      'j.okafor@northwind.com is already a member. It will be skipped.',
    );
  });

  it('⚡ an outstanding invitation is a DIFFERENT answer from a member', () => {
    // ⛔ **The useful action differs**: resend, not invite again. Collapsing
    // the two would send somebody to the wrong control.
    const [entry] = classifyAddresses('a.silva@partner-logistics.com', MEMBERS, INVITED);

    expect(entry?.verdict).toBe('already-invited');
    expect(explainVerdict(entry as never)).toMatch(/resend/);
  });
});

describe('📁 "type or paste addresses, separated by commas"', () => {
  it('⚡ and by the separators a spreadsheet and Outlook actually produce', () => {
    /**
     * ⛔ **A form that only honours the separator its label mentions punishes
     * the commonest way anybody will use it** — a column pastes as newlines,
     * Outlook pastes as semicolons.
     */
    expect(splitAddresses('a@x.com, b@x.com\nc@x.com;d@x.com')).toEqual([
      'a@x.com',
      'b@x.com',
      'c@x.com',
      'd@x.com',
    ]);
  });

  it('⛔ the same address twice is invited once, and says so', () => {
    const classified = classifyAddresses('a@x.com, a@x.com', [], []);

    expect(classified.map((c) => c.verdict)).toEqual(['invite', 'duplicate']);
    expect(sendable(classified)).toEqual(['a@x.com']);
  });

  it('⚡ case does not make two people out of one', () => {
    const classified = classifyAddresses('J.Okafor@Northwind.com', MEMBERS, INVITED);
    expect(classified[0]?.verdict).toBe('already-a-member');
  });

  it('⛔ something that is not an address is refused before it is sent', () => {
    // ⚡ **So somebody is not told about it one round trip at a time.**
    const classified = classifyAddresses('Jane Okafor, jane@x.com', [], []);

    expect(classified[0]?.verdict).toBe('not-an-address');
    expect(sendable(classified)).toEqual(['jane@x.com']);
  });

  it('⚠️ but the check is permissive, because the server is the authority', () => {
    /**
     * ⛔ **A strict local pattern rejects addresses that are valid** — new
     * TLDs, tagged mailboxes — ✅ **and this only catches the paste that
     * obviously went wrong.**
     */
    for (const address of ['a+tag@x.io', 'first.last@sub.domain.travel']) {
      expect(classifyAddresses(address, [], [])[0]?.verdict, address).toBe('invite');
    }
  });
});

describe('⛔ nothing is invented where the platform is silent', () => {
  it('🔴 an external address is NOT labelled Guest', () => {
    /**
     * 📁 **The design's other branch**: *"is outside your verified domains and
     * will be invited as a **Guest**."* ⛔ **Neither half exists** — there are
     * no verified domains, and the product has `owner` and `member`; the
     * design's five roles are [C-1416](../../../docs/LANE_COORDINATION.md)'s
     * open decision.
     *
     * ⚡ **Inventing a `Guest` chip would be a permission the server does not
     * enforce**, which is [§20c](../../../CLAUDE.md)'s *a client check is a
     * courtesy, never enforcement* — inverted into a lie.
     */
    const [entry] = classifyAddresses('a.silva@partner-logistics.com', [], []);

    expect(entry?.verdict).toBe('invite');
    expect(JSON.stringify(entry)).not.toMatch(/guest/i);
  });

  it('⚡ an ordinary address gets no line at all', () => {
    // ⛔ A line under every one of twenty turns the list into a wall.
    const [entry] = classifyAddresses('new@northwind.com', MEMBERS, INVITED);
    expect(explainVerdict(entry as never)).toBeNull();
  });
});
