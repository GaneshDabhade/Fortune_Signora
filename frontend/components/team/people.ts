import type { Membership } from '@/lib/api/types';

/**
 * How the product turns an identifier into a person.
 *
 * ### Why this exists at all
 *
 * Better Auth owns user profiles in the Next.js tier and the Python tier
 * verifies tokens without ever learning who anybody is (ADR-0026), so every
 * person on a brief arrives as a UUID. **D23** made *"somebody here"* the
 * honest form of that absence.
 *
 * **TM-01 changed the fact underneath it.** A membership now carries the
 * address it was created with, and the roster is already in the cache on every
 * screen that needs one — so a name is resolvable today where it was not
 * yesterday, and *"held by someone else"* has become an absence the product is
 * choosing rather than one it is stuck with.
 *
 * ### Why it is one module and not an expression repeated three times
 *
 * Three surfaces ask the same question of the same roster: the hand-over
 * picker, the workflow line, and the decision history. **Two would have been a
 * coincidence** — the rule that refused a shared history framework
 * ([46-team-management.md](../../../docs/architecture/46-team-management.md)
 * §11) — and three is the pattern it named as the trigger.
 *
 * The real argument is not repetition, though. It is that the three must agree:
 * a picker offering *ana@acme.com* whose history then says *"somebody here"*
 * describes two different people to a reader who knows there is only one.
 */

/** Somebody who can be named, and therefore offered. */
export interface Person {
  id: string;
  name: string;
}

/**
 * Everybody in the organization who can be named, keyed by identifier.
 *
 * **Unnamed memberships are absent rather than present-and-blank.** A caller
 * asking for a name it cannot have should get nothing back and say the honest
 * thing itself — a map holding `''` would push that decision into every
 * reader, and one of them would render it.
 */
export function peopleFrom(members: readonly Membership[] | undefined): ReadonlyMap<string, string> {
  const people = new Map<string, string>();
  for (const member of members ?? []) {
    if (member.member_email) people.set(member.user_id, member.member_email);
  }
  return people;
}

/**
 * Everybody *else*, as a list something can offer.
 *
 * **Named or not offered.** A membership added by identifier has no address,
 * and *"Somebody here"* in a picker is a row nobody can choose between — the
 * same rule the account sequence applies to an unresolved account name.
 */
export function colleaguesFrom(
  members: readonly Membership[] | undefined,
  viewerId: string | null,
): Person[] {
  return (members ?? [])
    .filter((one) => one.user_id !== viewerId)
    .flatMap((one) => (one.member_email ? [{ id: one.user_id, name: one.member_email }] : []));
}

/**
 * What to call somebody, in the terms the reader can act on.
 *
 * The order is deliberate: **you first**, because a reader recognises
 * themselves before they read anything else; then a name; then D23's honest
 * absence. A raw identifier is never a fourth option — it is the same absence
 * dressed as information.
 */
export function nameOf(
  id: string | null,
  people: ReadonlyMap<string, string>,
  viewerId: string | null,
): string {
  if (id === null) return 'nobody';
  if (id === viewerId) return 'you';
  return people.get(id) ?? 'somebody here';
}
