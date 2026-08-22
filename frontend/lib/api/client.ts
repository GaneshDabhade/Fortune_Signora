import { recordConnection } from '@/lib/system-states/last-connected';
/**
 * Typed client for the Signora API.
 *
 * Attaches the Bearer token, refreshes once on 401, and surfaces the API's
 * standard error envelope (19-api-conventions.md) as a typed error rather
 * than letting callers parse it themselves.
 */


export interface ApiErrorBody {
  code: string;
  message: string;
  details?: { field: string; message: string }[];
  correlation_id: string;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code: string;
  readonly correlationId: string;
  readonly details?: { field: string; message: string }[];

  constructor(status: number, body: ApiErrorBody) {
    super(body.message);
    this.name = 'ApiError';
    this.status = status;
    this.code = body.code;
    this.correlationId = body.correlation_id;
    this.details = body.details;
  }
}

/**
 * 🔴 **[B-1035](../../../docs/BUGS.md) — one mint per data read, and each mint
 * is an RS256 signature on the Next tier.** 📁 **Measured on `/accounts`: 15
 * mints for 16 reads against a ceiling of 12 and a design target of 1** — *"the
 * token is valid for minutes and nothing caches it."*
 *
 * ⚡ **Concurrent callers now share ONE mint.** A page opens by firing its
 * queries together, so the reads that were minting a token each are the same
 * reads that can share one — **this is deduplication of work already in
 * flight, not a cache.**
 *
 * ⛔ **NOTHING IS STORED, and that is deliberate.** ⚠️ **The entry is removed
 * the moment the mint settles**, so no token outlives the requests that asked
 * for it. **A real cache wants the token's own `exp`, and 📁
 * [CLAUDE.md §13](../../../CLAUDE.md) puts JWT parsing in
 * `signora_platform/auth/`** — ⛔ **so reading `exp` in the browser is a
 * decision to raise, not one to take here.** ✅ **Deduplication needs no expiry
 * and makes no assumption about lifetime.**
 *
 * ⛔ **Browser only.** 🔴 **A module-level map on the Next server would be
 * shared by every request in the process** — one customer's token handed to
 * another. **`typeof window` is the guard, and it is a security boundary rather
 * than an optimisation.**
 */
const inFlightMints = new Map<string, Promise<string>>();

/** Fetches an access token from our own server-side route. The private
 * signing key stays on the server; the browser only ever sees the token. */
async function fetchAccessToken(workspaceId?: string): Promise<string> {
  // ⛔ **On the server every caller is a different customer.** No sharing.
  if (typeof window === 'undefined') return mintAccessToken(workspaceId);

  const key = workspaceId ?? '';
  // ⚡ **A retry cannot receive the mint that just 401'd, and it needs no flag
  // to prevent it.** 🔴 **I added one — `fresh`, deleting the entry before the
  // lookup — and then fire-tested it: removing it changed nothing.** ⛔ **The
  // `.finally` below deletes each entry the moment its mint SETTLES, so an
  // entry never outlives the token it produced**; by the time a 401 comes back
  // there is nothing left to reuse. ⚠️ **A guard whose removal does not change
  // the property it claims to protect is what
  // [§2](../../../CLAUDE.md) calls Decorative Logic**, and the comment beside
  // it was already asserting a failure it did not prevent.
  const pending = inFlightMints.get(key);
  if (pending !== undefined) {
    try {
      return await pending;
    } catch {
      /**
       * 🔴 **[B-1067](../../../docs/BUGS.md) — sharing a SUCCESS is the point;
       * sharing a REJECTION removed the retries this deduplication never meant
       * to remove.**
       *
       * ⛔ **A mint's verdict is formed when its request ARRIVES at
       * `/api/token`**, and the server answers from the session cookie it can
       * see at that moment. ⚠️ **A caller that joins later inherited a verdict
       * formed before it existed** — including a caller that fires *after* the
       * cookie has become readable and would have succeeded on its own.
       *
       * ⚡ **And nothing downstream recovers it**: 📁 `apiRequest` throws at
       * `await fetchAccessToken(...)` **before** its `fetch`, so **the single
       * 401 retry below never runs for a failed MINT** — it only ever covered a
       * 401 *response*.
       *
       * **Measured, identical timings, the sharing as the only variable:**
       *
       * ```
       * shared    mints=1   0:rej  2:rej  4:rej  6:rej  40:rej        45:rej
       * control   mints=6   0:rej  2:rej  4:rej  6:rej  40:FULFILLED  45:FULFILLED
       * ```
       *
       * 🔴 **One mint, six failures. Six mints, four failures and two
       * successes.** ⛔ **The deduplication turned N independent chances into
       * one shared outcome**, and on the seconds after a sign-in — when the
       * cookie is not yet readable — that is the difference between a partial,
       * self-healing failure and a total one.
       *
       * ✅ **So this caller mints its own rather than inheriting.** ⛔ **Not
       * through `fetchAccessToken`**: re-entering would let a crowd of
       * simultaneously-failing joiners share a *second* verdict, which is the
       * same defect one round later. **Each gets its own chance, which is
       * exactly what it had before B-1035.**
       */
      return mintAccessToken(workspaceId);
    }
  }

  const mint = mintAccessToken(workspaceId).finally(() => {
    inFlightMints.delete(key);
  });
  inFlightMints.set(key, mint);
  return mint;
}

async function mintAccessToken(workspaceId?: string): Promise<string> {
  const url = workspaceId ? `/api/token?workspace_id=${workspaceId}` : '/api/token';
  const response = await fetch(url, { method: 'POST' });

  if (!response.ok) {
    throw new ApiError(response.status, {
      code: 'unauthenticated',
      message: 'Could not obtain an access token.',
      correlation_id: '',
    });
  }

  const body = (await response.json()) as { access_token: string };
  return body.access_token;
}

export interface RequestOptions {
  method?: string;
  body?: unknown;
  workspaceId?: string;
  /** Internal: prevents infinite retry if a refreshed token also 401s. */
  _retried?: boolean;
}

export async function apiRequest<T>(
  path: string,
  options: RequestOptions = {},
): Promise<T> {
  const { method = 'GET', body, workspaceId } = options;
  // **Read directly, not through `loadAuthConfig()`.** Where the API lives is
  // not an authentication concern, and loading the whole auth config to obtain
  // one URL made every server-rendered page depend on the auth database and the
  // signing secret — values it never uses. That coupling was invisible while
  // those had fallbacks, and became a build failure the moment they stopped
  // ([B-104](../../../docs/BUGS.md)).
  const baseUrl =
    typeof window === 'undefined'
      ? (process.env.SIGNORA_API_URL ?? 'http://localhost:8000')
      : '/api/proxy';

  const token = await fetchAccessToken(workspaceId);
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: {
      Authorization: `Bearer ${token}`,
      ...(body ? { 'Content-Type': 'application/json' } : {}),
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });

  // 🔴 **The write [TASK-1436](../../../docs/BACKLOG.md) exists for**, and it
  // is here rather than on a timer: **any response at all proves the service
  // was reachable**, so a heartbeat would be traffic whose only purpose is
  // making a label true. ⛔ **Before the status checks, deliberately** — a
  // `401` or a `500` still crossed the network, and *"last connected"* is
  // about the CONNECTION, not about the answer.
  if (typeof window !== 'undefined') recordConnection();

  if (response.status === 401 && !options._retried) {
    // A single retry with a fresh token. Retrying more would mask a real
    // configuration problem as intermittent slowness.
    return apiRequest<T>(path, { ...options, _retried: true });
  }

  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as {
      error: ApiErrorBody;
    } | null;
    throw new ApiError(
      response.status,
      payload?.error ?? {
        code: 'unknown_error',
        message: response.statusText,
        correlation_id: '',
      },
    );
  }

  if (response.status === 204) return undefined as T;
  return (await response.json()) as T;
}
