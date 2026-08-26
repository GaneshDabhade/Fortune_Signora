/**
 * 🔴 **📁 `Security Gates` `contract`: *"No gate response contains a fact
 * classified `DISC_NEVER`. **A build-time lint checks gate copy against the
 * class table.**"*** ⛔ **No such lint existed** — `DISC_NEVER` appears nowhere
 * in the repository.
 *
 * 📁 **The class table's own definition of Class A:**
 *
 * > ***"Withheld by the backend as a deliberate property. The interface must
 * > not reveal it even indirectly, through wording, timing, response size or
 * > the presence of an action."***
 *
 * ⚡ **The copy is clean today and that is exactly why this is worth writing.**
 * 📁 `forgot-password-form.tsx` carries a comment reasoning that *"no account
 * with that address"* would be **an enumeration oracle** — **one person
 * reasoned about it once, and nothing has held it since.**
 *
 * ## ⚠️ What this does NOT cover, stated so the green is readable
 *
 * ⛔ **One of the four Class A facts.** *Whether a workspace slug exists*,
 * *which authentication factor failed* and *whether an invitation was
 * reassigned* are **not** checked here — the first two have no single phrasing
 * a regex can hold, and the third has no surface yet.
 *
 * ⛔ **Wording only.** 📁 The class names *"timing, response size or the
 * presence of an action"* too, and **a source scan cannot see any of those.**
 *
 * ⚡ **Registration status is the one worth pinning**: it has a live precedent,
 * a single well-known phrasing family, and it is the oracle password-reset
 * flows leak most often.
 */
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join, relative } from 'node:path';

import { describe, expect, it } from 'vitest';

const AUTH = join(process.cwd(), 'app', '(auth)');

function sources(dir: string): { name: string; source: string }[] {
  return readdirSync(dir).flatMap((entry) => {
    const path = join(dir, entry);
    if (statSync(path).isDirectory()) return sources(path);
    if (!entry.endsWith('.tsx') && !entry.endsWith('.ts')) return [];
    return [{ name: relative(process.cwd(), path), source: readFileSync(path, 'utf8') }];
  });
}

/**
 * ⛔ **Comments are stripped FIRST, and that is not a convenience.** ⚡ The one
 * file that discusses this oracle is the one that refuses it — **a scan that
 * read comments would flag the reasoning and miss nothing else.**
 */
function prose(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, ' ').replace(/(^|[^:])\/\/.*$/gm, '$1 ');
}

/**
 * Phrasings that ASSERT whether an address is known.
 *
 * 🔴 **The first draft matched *"**If** an account exists for that address, a
 * reset link is on its way"* — which is the CORRECT anti-oracle wording**, the
 * standard conditional that discloses nothing either way. ⛔ **A population too
 * wide, and it failed loudly on the one file that gets this right.**
 *
 * ⚡ **The oracle is an ASSERTION, never a CONDITIONAL.** *"No account with
 * that address"* answers the question; *"if an account exists"* refuses to.
 */
const ORACLE =
  /(no|not an?|unknown|invalid)\s+(account|user|email|address)\b|(account|email|address)\s+(is\s+)?(not\s+)?(registered|recognised|recognized|on file|exists)|never\s+registered/i;

/** ⚡ **A match governed by `if` or `whether` is the refusal, not the leak.** */
const CONDITIONAL = /\b(if|whether|unless)\b/i;

function discloses(line: string): boolean {
  const match = ORACLE.exec(line);
  if (match === null) return false;
  // Look back over the clause the match sits in, not the whole line: a
  // sentence may legitimately contain an `if` about something else entirely.
  const clause = line.slice(0, match.index).split(/[.;]/).pop() ?? '';
  return !CONDITIONAL.test(clause);
}

describe('🔴 Class A · whether an email is registered is never disclosed', () => {
  it('states neither that an address is registered nor that it is not', () => {
    const offenders = sources(AUTH)
      .flatMap(({ name, source }) =>
        prose(source)
          .split('\n')
          .filter(discloses)
          .map((line) => `${name}: ${line.trim()}`),
      );

    expect(
      offenders,
      `authentication copy discloses registration status:\n${offenders.join('\n')}`,
    ).toEqual([]);
  });

  it('⛔ and the scan reaches real files, so a green means something', () => {
    /**
     * ⚡ **The positive control.** ⛔ Without it a wrong path, an empty
     * directory or a broken walk reports zero offenders and reads as a pass —
     * 📁 [B-1073](../../../docs/BUGS.md)'s class, and the reason
     * [B-1063](../../../docs/BUGS.md) exists: a gate that silently passes when
     * its population is absent.
     */
    const scanned = sources(AUTH);
    expect(scanned.length).toBeGreaterThan(10);
    expect(scanned.some(({ name }) => name.includes('forgot-password'))).toBe(true);
  });
});
