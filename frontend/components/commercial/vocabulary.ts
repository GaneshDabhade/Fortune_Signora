/**
 * The words the commercial profile is read in.
 *
 * **Promoted from the editors by CX-05, not written for it.** `PART_LABELS`,
 * `PART_HINTS` and `size()` were page-local to the authoring screen for as long
 * as authoring was the only place these declarations were read. The read
 * surface at `/business` is the second, and **the two must agree**: a committee
 * whose part reads *Economic buyer* while being declared and *economic_buyer*
 * while being read describes two different taxonomies to somebody who knows
 * there is only one.
 *
 * **Behaviour exists exactly once** (`CLAUDE.md` §2). Copying five labels into
 * a second file is the version of that rule people talk themselves out of,
 * because five strings look like nothing — right up to the sixth part being
 * added in one file.
 *
 * **Not `components/ui`.** These are Commercial Profile's vocabulary rather
 * than a design-system primitive, and §20c is explicit that the library gains
 * a component the library benefits from, not one caller's constants.
 */

import type { CommitteePart, ProductIcp } from '@/lib/api/types';

/**
 * What each part means, in the words a seller would use.
 *
 * **A label, not a translation.** The five parts are already ordinary sales
 * language; this only capitalises them for a screen.
 */
export const PART_LABELS: Record<CommitteePart, string> = {
  economic_buyer: 'Economic buyer',
  champion: 'Champion',
  evaluator: 'Evaluator',
  user: 'User',
  gatekeeper: 'Gatekeeper',
};

export const PART_HINTS: Record<CommitteePart, string> = {
  economic_buyer: 'Owns the budget. The signature at the end.',
  champion: 'Argues for it when you are not in the room.',
  evaluator: 'Judges whether it actually works.',
  user: 'Lives with it afterwards.',
  gatekeeper: 'Must sign off — security, legal, procurement.',
};

/**
 * A company size, in the form the customer stated it.
 *
 * **Either bound may be missing, and both absences are real answers** —
 * *anything over 500* and *under 50* are things a customer says. An empty
 * string means size was not stated at all, which the caller renders as absence
 * rather than as a range of nothing.
 */
export function size(employees: ProductIcp['employees']): string {
  if (employees === null) return '';
  const { minimum, maximum } = employees;
  if (minimum !== null && maximum !== null)
    return `${minimum.toLocaleString()}–${maximum.toLocaleString()} people`;
  if (minimum !== null) return `${minimum.toLocaleString()}+ people`;
  if (maximum !== null) return `up to ${maximum.toLocaleString()} people`;
  return '';
}
