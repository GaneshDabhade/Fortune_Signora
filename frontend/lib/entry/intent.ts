/**
 * **What the person was trying to reach** —
 * [TASK-1402](../../../docs/BACKLOG.md), [workflow 29](../../../docs/coordination/workflows.toml).
 *
 * 📁 **The spec**: ***"Authentication hands over an identity AND AN INTENT — the
 * route the person was trying to reach."*** ⚡ **Four of the twenty-four reason
 * codes are intent codes**, so intent is a first-class input rather than a
 * query parameter somebody remembered to forward.
 *
 * ## ⛔ The shape is settled and is not re-decided here
 *
 * 📁 **`Intent` already exists in [`session.ts`](./session.ts)** as
 * `{ path, workspaceId, access }`, and its own comment names this file's
 * boundary: ***"⛔ Never computed here… the engine has no way to produce them —
 * which is the point."*** ✅ **This is the producer of those four values and
 * nothing else.**
 *
 * ## 🔴 Two security properties, and they ARE the row
 *
 * ### ① A captured route must never become an open redirect
 *
 * ⚠️ **This is the classic vulnerability in exactly this feature.** A login
 * that faithfully returns you to where you were going is also a login that
 * will send you to `https://evil.example` if it is told to — **and the
 * attacker's link is indistinguishable from the honest one**, because both are
 * *"the page you asked for."*
 *
 * ⛔ **So {@link captureIntent} accepts a same-origin PATH and nothing else**,
 * and 🔴 **{@link decodeIntent} re-applies the same test on the way back**:
 * **what survives a round trip through a URL is attacker-controlled by
 * definition**, and a sanitiser that runs only on capture protects nothing.
 *
 * ### ② `not_member` is reached WITHOUT asking whether the workspace exists
 *
 * 📁 **[§7](../../../CLAUDE.md): *a caller who is not a member of the workspace
 * they name gets `404`, never `403`. This is a security property — it prevents
 * workspace enumeration.*** ⚡ **Applied here BEFORE the question is asked
 * rather than after it**: {@link classifyIntent} tests membership against the
 * caller's own list, locally, and **only consults the server when the workspace
 * is one of theirs.**
 *
 * ⛔ **The ordering is the control.** A classifier that asked the server first
 * and mapped its `404` to `not_member` would be correct in its output and
 * wrong in its behaviour — **it would have probed for a workspace the caller
 * has no business knowing about, and timing alone answers the question the
 * status code refused to.** ✅ **`intent.test.ts` asserts the server is never
 * reached in that case**, which is the only way to prove an absence of a call.
 */

import type { Intent, IntentAccess, Membership } from './session';

/**
 * ⚡ **What the server may answer for a path the caller CAN be asked about.**
 *
 * ⛔ **`not_member` is deliberately absent.** It is not the server's to say
 * here — it is decided locally from the caller's own memberships, before this
 * is ever called, which is property ② above.
 */
export type PathAccess = Extract<IntentAccess, 'granted' | 'forbidden' | 'missing'>;

/**
 * **Capture the attempted route, or refuse it.**
 *
 * ⛔ **Returns `null` for anything that is not a same-origin path**, and the
 * refusal is silent by design: a person who followed a hostile link should land
 * on their home rather than on an error explaining what was wrong with it.
 *
 * ⚠️ **The rejections are not a blocklist of known-bad strings.** ✅ **The rule
 * is positive** — *it must begin with exactly one `/`, and contain no scheme
 * and no control characters* — because a blocklist of tricks is a list somebody
 * eventually finds a gap in, and this is the wrong place to be one trick behind.
 */
export function captureIntent(candidate: string | null | undefined): string | null {
  if (typeof candidate !== 'string' || candidate === '') return null;

  // ⛔ **`//evil.example` and `/\evil.example` are protocol-relative URLs**, and
  // a browser follows them off-origin. **They begin with `/`, which is why
  // "starts with a slash" is not the test people think it is.**
  if (!candidate.startsWith('/')) return null;
  if (candidate.startsWith('//') || candidate.startsWith('/\\')) return null;

  // ⛔ **A scheme anywhere means this was a URL, not a path.** `javascript:`,
  // `data:` and `https:` are all refused by the same rule rather than by three.
  if (/^[a-z][a-z0-9+.-]*:/i.test(candidate)) return null;

  // ⛔ **Control characters, including the newline and tab a browser strips**
  // before parsing — which is how `/\njavascript:…` becomes a scheme again
  // after this function has already looked at it.
  // eslint-disable-next-line no-control-regex
  if (/[\u0000-\u001f\u007f]/.test(candidate)) return null;

  return candidate;
}

/**
 * ⚡ **How it survives the round trip.**
 *
 * ⛔ **A query parameter, not a cookie.** A cookie set before authentication is
 * a cookie that outlives the attempt: somebody who abandons a login and comes
 * back an hour later would be sent somewhere they no longer remember asking
 * for. **The parameter dies with the URL, which is the lifetime intent should
 * have.**
 */
export const INTENT_PARAM = 'next' as const;

export function encodeIntent(path: string): string {
  return encodeURIComponent(path);
}

/**
 * 🔴 **Re-sanitised on the way back, and this is not belt-and-braces.**
 *
 * ⚡ **Whatever arrives here came through a URL somebody else could write.**
 * ⛔ **A sanitiser that runs only at capture protects the one path an attacker
 * never uses** — they do not call `captureIntent`, they hand the browser a
 * crafted `?next=`.
 */
export function decodeIntent(raw: string | null | undefined): string | null {
  if (typeof raw !== 'string' || raw === '') return null;
  let decoded: string;
  try {
    decoded = decodeURIComponent(raw);
  } catch {
    // ⛔ **A malformed escape is a refusal, never a partial decode.** Passing
    // the raw string on would hand the next reader a value this one could not
    // even parse.
    return null;
  }
  return captureIntent(decoded);
}

/**
 * **The workspace a path names, when it names one.**
 *
 * 📁 The design's route is `/w/:workspace/…`, which
 * [`rules.ts`](./rules.ts)'s `workspaceHome` already writes. ⚡ **Read here
 * rather than parsed by each caller**, so the two cannot drift.
 */
export function workspaceFromPath(path: string): string | null {
  const segments = path.split('?')[0]?.split('/') ?? [];
  // ['', 'w', ':workspace', …]
  if (segments[1] !== 'w') return null;
  const workspace = segments[2];
  return workspace === undefined || workspace === '' ? null : workspace;
}

/**
 * **Classify a captured route into one of the four intent codes.**
 *
 * @param permits **The server's answer**, for a path the caller may be asked
 * about. ⛔ **Not called at all when the path names a workspace the caller is
 * not in** — property ② above, and the reason this is a callback rather than a
 * value: **a value would already have been fetched.**
 *
 * ⚠️ **A path naming no workspace still asks the server.** `/settings` is not
 * workspace-scoped, so membership decides nothing about it and the
 * authorization answer is the only one there is.
 */
export function classifyIntent(
  path: string,
  memberships: readonly Membership[],
  permits: (path: string) => PathAccess,
): Intent {
  const workspaceId = workspaceFromPath(path);

  if (workspaceId !== null && !memberships.some((m) => m.workspaceId === workspaceId)) {
    /**
     * 🔴 **Decided locally, and the server is never asked.**
     *
     * 📁 [§7](../../../CLAUDE.md): *"A caller who is not a member of the
     * workspace they name gets `404`, never `403`. This is a security property
     * — it prevents workspace enumeration."*
     *
     * ⛔ **Returning `not_member` after a server round trip would leak the same
     * fact through timing** that the status code was chosen to withhold, and
     * ⚠️ **it would leak it to the one caller who has no business knowing.**
     * ✅ **Not asking is the only version of this that holds.**
     */
    return { path, workspaceId, access: 'not_member' };
  }

  return { path, workspaceId, access: permits(path) };
}
