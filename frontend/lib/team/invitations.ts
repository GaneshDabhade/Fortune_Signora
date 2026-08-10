/**
 * **Who is actually being invited** — [TASK-471](../../../docs/BACKLOG.md),
 * 📁 `Fortune Signora Team Management.dc.html` **§02**.
 *
 * ## 📁 The design's sentence, and it is a behaviour rather than a message
 *
 * > ***"j.okafor@northwind.com is already a member. It will be skipped."***
 *
 * ⚡ **Skipped, not rejected.** ⛔ **The difference is the whole rule**: somebody
 * pasting twenty addresses from a spreadsheet should not have the whole invite
 * refused because one colleague is already here. **A form that rejects the
 * batch makes them find the duplicate by hand, and they will send nineteen
 * invitations one at a time instead.**
 *
 * ## ⛔ Classified before anything is sent
 *
 * ⚡ **The design shows the verdict under the input, before the send button** —
 * so the person **knows what will happen** rather than reading about it
 * afterwards in a toast. ✅ **That makes this a pure function over what is
 * already loaded**: the member list and the pending invitations are both on
 * the screen already, so no request is needed to decide.
 *
 * ## ⚠️ What this deliberately does NOT classify
 *
 * 📁 **The design's other branch**: *"a.silva@partner-logistics.com is outside
 * your verified domains and will be invited as a **Guest**."*
 *
 * ⛔ **Neither half of that exists.** **There are no verified domains in this
 * product, and there is no `Guest` role** — 📁 the platform has `owner` and
 * `member`, and the design's five roles are
 * [C-1416](../../../docs/LANE_COORDINATION.md)'s open decision.
 * ⚠️ **So an external address is classified as ordinary and invited as
 * whatever role was chosen** — ⛔ **inventing a `Guest` chip would be a
 * permission the server does not enforce**, which is
 * [§20c](../../../CLAUDE.md)'s *a client check is a courtesy, never
 * enforcement*, inverted into a lie.
 */

/** What will happen to one pasted address when Send is pressed. */
export type InviteVerdict =
  | 'invite'
  /** 📁 *"is already a member. It will be skipped."* */
  | 'already-a-member'
  /** ⚡ **Not the same as a member**: an invitation exists and has not been
   * accepted, so the useful action is *resend*, not *invite again*. */
  | 'already-invited'
  /** ⛔ **Not an address.** Refused rather than sent, because the server would
   * refuse it and the person would learn one failure at a time. */
  | 'not-an-address'
  /** ⚡ **The same address twice in one paste** — a spreadsheet column almost
   * always has one. */
  | 'duplicate';

export interface ClassifiedAddress {
  readonly address: string;
  readonly verdict: InviteVerdict;
}

/**
 * ⚠️ **Deliberately permissive, and that is a decision rather than laziness.**
 *
 * ⛔ **A strict local pattern rejects addresses that are valid** — new TLDs,
 * tagged mailboxes, quoted locals — **and the server is the authority anyway.**
 * ✅ **This catches the paste that obviously went wrong** (a name, a phone
 * number, a stray column) **so somebody is not told about it one round trip at
 * a time.**
 */
const LOOKS_LIKE_AN_ADDRESS = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * 📁 *"Type or paste addresses, separated by commas."*
 *
 * ⚡ **Newlines and semicolons split too, because a spreadsheet column pastes
 * as newlines and Outlook pastes as semicolons** — ⛔ **and a form that only
 * honours the separator its label mentions punishes the commonest way anybody
 * will actually use it.**
 */
export function splitAddresses(input: string): string[] {
  return input
    .split(/[,;\n\r\t]+/)
    .map((part) => part.trim())
    .filter((part) => part !== '');
}

/**
 * **Every pasted address, with what will happen to it.**
 *
 * ⚡ **Order is preserved** so the list under the input matches what somebody
 * typed — ⛔ **a re-sorted verdict list makes them hunt for the address they
 * are worried about.**
 *
 * @param members addresses already in the workspace
 * @param invited addresses with an invitation outstanding
 */
export function classifyAddresses(
  input: string,
  members: readonly string[],
  invited: readonly string[],
): ClassifiedAddress[] {
  const isMember = new Set(members.map((m) => m.toLowerCase()));
  const isInvited = new Set(invited.map((i) => i.toLowerCase()));
  const seen = new Set<string>();

  return splitAddresses(input).map((address) => {
    const key = address.toLowerCase();

    // ⚡ **Checked before anything else.** An address that is not an address
    // cannot meaningfully be a member or a duplicate, and saying *"already a
    // member"* about `j.okafor` with no domain would be nonsense.
    if (!LOOKS_LIKE_AN_ADDRESS.test(address)) return { address, verdict: 'not-an-address' };

    if (seen.has(key)) return { address, verdict: 'duplicate' };
    seen.add(key);

    if (isMember.has(key)) return { address, verdict: 'already-a-member' };
    if (isInvited.has(key)) return { address, verdict: 'already-invited' };
    return { address, verdict: 'invite' };
  });
}

/** ⚡ **What Send will actually do** — the design's *"Send 3 invitations"*. */
export function sendable(classified: readonly ClassifiedAddress[]): string[] {
  return classified.filter((c) => c.verdict === 'invite').map((c) => c.address);
}

/**
 * **The sentence shown beside an address**, in the design's own register.
 *
 * ⛔ **Every verdict says what will HAPPEN, not what is wrong.** 📁 The design's
 * line is *"It will be skipped"* rather than *"duplicate member"* — ⚡ **a
 * person pasting a list wants to know the outcome, and a diagnosis is only
 * useful if they have to do something about it.**
 */
export function explainVerdict(entry: ClassifiedAddress): string | null {
  switch (entry.verdict) {
    case 'invite':
      // ⛔ **Nothing is said about the ordinary case.** A line under every
      // address turns a paste of twenty into a wall nobody reads.
      return null;
    case 'already-a-member':
      return `${entry.address} is already a member. It will be skipped.`;
    case 'already-invited':
      return `${entry.address} has already been invited. It will be skipped — resend the invitation instead.`;
    case 'duplicate':
      return `${entry.address} appears twice. It will be invited once.`;
    case 'not-an-address':
      return `${entry.address} does not look like an email address. It will not be sent.`;
  }
}
