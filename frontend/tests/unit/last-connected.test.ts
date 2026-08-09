/**
 * **When Signora last reached its own service** —
 * [TASK-1436](../../../docs/BACKLOG.md).
 *
 * 🔴 **The row names its own failure mode before it happens**: *"a relative
 * time that says **last connected 0 minutes ago** forever because nothing
 * writes it. The write is the row, not the render."* ⚡ **So the case that
 * earns this file is `the API client writes it`** — the render is the easy
 * half and the one that would pass against a value nothing produces.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';

import {
  describeLastConnected,
  lastConnected,
  probeConnection,
  recordConnection,
} from '@/lib/system-states/last-connected';

const NOW = 1_760_000_000_000;

/** `tests/unit/**` runs in node, so the storage this reads has to be supplied. */
function stubStorage(): Storage {
  const map = new Map<string, string>();
  const store = {
    getItem: (k: string) => map.get(k) ?? null,
    setItem: (k: string, v: string) => void map.set(k, v),
    removeItem: (k: string) => void map.delete(k),
    clear: () => map.clear(),
    key: (i: number) => [...map.keys()][i] ?? null,
    get length() {
      return map.size;
    },
  } as Storage;
  vi.stubGlobal('window', { localStorage: store });
  return store;
}

beforeEach(() => {
  stubStorage();
});
afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe('🔴 the write, which is the row', () => {
  it('records a moment and reads it back', () => {
    recordConnection(NOW);
    expect(lastConnected()).toBe(NOW);
  });

  it('⛔ a browser that has never connected reports null, not "just now"', () => {
    // 📁 The design asks this screen to be "honest about having nothing".
    // `null` is a real answer and the caller renders it as one.
    expect(lastConnected()).toBeNull();
  });

  it('⚠️ a corrupted value is no answer rather than NaN in a sentence', () => {
    window.localStorage.setItem('signora.last-connected', 'yesterday');
    expect(lastConnected()).toBeNull();
    window.localStorage.setItem('signora.last-connected', '-1');
    expect(lastConnected()).toBeNull();
  });

  it('⛔ a storage that throws costs the phrase, never the screen', () => {
    // The comparison is use-rail-collapse (swallows, cosmetic) against
    // copyable-id (reports, relied upon). Nobody relies on this being written.
    vi.stubGlobal('window', {
      localStorage: {
        getItem: () => {
          throw new Error('private mode');
        },
        setItem: () => {
          throw new Error('private mode');
        },
      },
    });
    expect(() => recordConnection(NOW)).not.toThrow();
    expect(lastConnected()).toBeNull();
  });
});

describe('📁 "last connected 3 minutes ago" — the design’s own phrasing', () => {
  it.each([
    [0, 'Last connected less than a minute ago'],
    [30_000, 'Last connected less than a minute ago'],
    [60_000, 'Last connected 1 minute ago'],
    [180_000, 'Last connected 3 minutes ago'],
    [3_600_000, 'Last connected 1 hour ago'],
    [7_200_000, 'Last connected 2 hours ago'],
    [86_400_000, 'Last connected 1 day ago'],
    [172_800_000, 'Last connected 2 days ago'],
  ])('%ims ago reads "%s"', (elapsed, expected) => {
    expect(describeLastConnected(NOW - elapsed, NOW)).toBe(expected);
  });

  it('⛔ never singular-plural wrong, which is the tell of a generated string', () => {
    expect(describeLastConnected(NOW - 60_000, NOW)).toContain('1 minute ago');
    expect(describeLastConnected(NOW - 120_000, NOW)).toContain('2 minutes ago');
  });

  it('⚡ a clock that went backwards clamps rather than saying "in 3 minutes"', () => {
    // A device clock correcting itself must not turn the sentence into a
    // future tense on a screen about the past.
    expect(describeLastConnected(NOW + 600_000, NOW)).toBe(
      'Last connected less than a minute ago',
    );
  });

  it('nothing recorded renders nothing', () => {
    expect(describeLastConnected(null, NOW)).toBeNull();
  });
});

describe('🔴 retry PROBES and never reloads', () => {
  it('⚡ it asks Signora’s own service, uncached', async () => {
    const fetchMock = vi.fn().mockResolvedValue({ ok: true });
    vi.stubGlobal('fetch', fetchMock);
    stubStorage();

    await expect(probeConnection()).resolves.toBe(true);

    const [url, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(url).toBe('/api/health');
    // ⛔ A cached 200 would report a connection that does not exist, which is
    // the exact failure this screen is about.
    expect(init.cache).toBe('no-store');
  });

  it('⛔ a network failure is an ANSWER, not a thrown error', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockRejectedValue(new TypeError('Failed to fetch')),
    );
    // The caller asked "is it back?" and "no" is a legitimate reply. A throw
    // here would take down the screen whose whole job is surviving this.
    await expect(probeConnection()).resolves.toBe(false);
  });

  it('✅ a successful probe records the connection, so the label self-heals', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: true }));
    const store = stubStorage();
    await probeConnection();
    expect(store.getItem('signora.last-connected')).not.toBeNull();
  });

  it('⛔ a failed probe records NOTHING — a failure is not a connection', async () => {
    vi.stubGlobal('fetch', vi.fn().mockResolvedValue({ ok: false, status: 503 }));
    const store = stubStorage();
    await probeConnection();
    expect(store.getItem('signora.last-connected')).toBeNull();
  });
});

describe('🔴 the API client is what writes it, and this is the test that was missing', () => {
  it('⚡ a successful request records the connection', async () => {
    /**
     * ⛔ **Added because a fire-test found nothing protecting it.** Removing
     * `recordConnection()` from `apiRequest` left the whole suite green —
     * 2101 passing — while *"last connected"* froze at whatever it happened to
     * say and never moved again. **That is the row's own named risk**: *"a
     * relative time that says last connected 0 minutes ago forever because
     * nothing writes it. The write is the row, not the render."*
     *
     * ⚡ **[B-162](../../../docs/BUGS.md)'s lesson, applied one step earlier**:
     * proving the new code works is half of it, and the half that catches this
     * is asking what would still pass if the change were undone.
     */
    const store = stubStorage();
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        // the token route, then the API call
        .mockResolvedValueOnce({ ok: true, json: async () => ({ access_token: 't' }) })
        .mockResolvedValueOnce({ ok: true, status: 200, json: async () => ({ ok: true }) }),
    );
    const { apiRequest } = await import('@/lib/api/client');
    await apiRequest('/anything');

    expect(store.getItem('signora.last-connected')).not.toBeNull();
  });

  it('⛔ and a 500 records it too — the CONNECTION succeeded, the request did not', async () => {
    // The sentence is about reaching the service. A 500 crossed the network,
    // so treating it as "still offline" would tell somebody they had no
    // connection while the server was answering them.
    const store = stubStorage();
    vi.stubGlobal(
      'fetch',
      vi
        .fn()
        .mockResolvedValueOnce({ ok: true, json: async () => ({ access_token: 't' }) })
        .mockResolvedValueOnce({ ok: false, status: 500, statusText: 'boom', json: async () => null }),
    );
    const { apiRequest } = await import('@/lib/api/client');
    await expect(apiRequest('/anything')).rejects.toThrow();

    expect(store.getItem('signora.last-connected')).not.toBeNull();
  });
});
