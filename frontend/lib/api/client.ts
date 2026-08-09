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

/** Fetches an access token from our own server-side route. The private
 * signing key stays on the server; the browser only ever sees the token. */
async function fetchAccessToken(workspaceId?: string): Promise<string> {
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
