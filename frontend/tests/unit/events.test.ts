/**
 * Authentication event tests.
 *
 * These are security tests. An auth event carrying a token or an email
 * address puts credentials and PII into a log aggregator, where retention
 * means they stay there.
 */

import { describe, expect, it } from 'vitest';

import { AUTH_EVENTS, emitAuthEvent, sanitize } from '@/lib/auth/events';

function capture(fn: (sink: (line: string) => void) => void): Record<string, unknown> {
  let captured = '';
  fn((line) => {
    captured = line;
  });
  return JSON.parse(captured) as Record<string, unknown>;
}

describe('sanitize', () => {
  it('strips an email address', () => {
    // A user id is an opaque UUID and is safe; an email is PII.
    const result = sanitize({ userId: 'u1', email: 'rep@customer.test' } as never);

    expect(result).toHaveProperty('userId', 'u1');
    expect(result).not.toHaveProperty('email');
  });

  it('strips token- and secret-shaped keys', () => {
    const result = sanitize({
      accessToken: 'abc',
      password: 'p',
      apiKey: 'k',
      authorization: 'Bearer x',
    } as never);

    expect(Object.keys(result)).toHaveLength(0);
  });

  it('permits tokenId, which is an identifier rather than a credential', () => {
    // jti is what makes a token traceable to a revocation decision later.
    const result = sanitize({ tokenId: 'tok_123' });

    expect(result).toHaveProperty('tokenId', 'tok_123');
  });

  it('redacts a JWT appearing inside an allowed field', () => {
    const jwt = 'eyJhbGciOiJSUzI1NiJ9.eyJzdWIiOiJhIn0.sig';

    const result = sanitize({ reason: `rejected ${jwt}` });

    expect(result.reason).not.toContain(jwt);
    expect(result.reason).toContain('[REDACTED]');
  });

  it('drops undefined values rather than emitting nulls', () => {
    expect(sanitize({ userId: undefined, workspaceId: 'w1' })).toEqual({
      workspaceId: 'w1',
    });
  });
});

describe('emitAuthEvent', () => {
  it('emits structured JSON matching the backend log shape', () => {
    const payload = capture((sink) =>
      emitAuthEvent(
        AUTH_EVENTS.LOGIN_SUCCESS,
        { userId: 'u1', provider: 'google' },
        sink,
      ),
    );

    expect(payload.auth_event).toBe('AUTH_LOGIN_SUCCESS');
    expect(payload.level).toBe('INFO');
    expect(payload.outcome).toBe('success');
    expect(payload.tier).toBe('frontend');
    expect(payload.userId).toBe('u1');
    expect(payload.timestamp).toBeTruthy();
  });

  it('derives failure outcome from the event, not from an argument', () => {
    // Passing outcome in would let a failure be recorded as a success by a
    // mistaken call, making the audit trail actively misleading.
    const payload = capture((sink) =>
      emitAuthEvent(AUTH_EVENTS.LOGIN_FAILURE, { reason: 'oauth_denied' }, sink),
    );

    expect(payload.outcome).toBe('failure');
    expect(payload.level).toBe('WARNING');
  });

  it('marks a rejected token as a failure', () => {
    const payload = capture((sink) =>
      emitAuthEvent(AUTH_EVENTS.TOKEN_REJECTED, { reason: 'expired' }, sink),
    );

    expect(payload.outcome).toBe('failure');
  });

  it('never emits a token even when one is passed', () => {
    const jwt = 'eyJhbGciOiJIUzI1NiJ9.eyJhIjoxfQ.sig';

    const payload = capture((sink) =>
      emitAuthEvent(
        AUTH_EVENTS.TOKEN_ISSUED,
        { userId: 'u1', accessToken: jwt, email: 'a@b.test' } as never,
        sink,
      ),
    );

    expect(JSON.stringify(payload)).not.toContain(jwt);
    expect(JSON.stringify(payload)).not.toContain('a@b.test');
  });

  it('covers every documented auth event name', () => {
    const required = [
      'AUTH_LOGIN_SUCCESS',
      'AUTH_LOGIN_FAILURE',
      'AUTH_TOKEN_REFRESH',
      'AUTH_TOKEN_REJECTED',
      'AUTH_LOGOUT',
      'AUTH_OAUTH_CALLBACK',
      'AUTH_WORKSPACE_SWITCH',
    ];

    expect(Object.values(AUTH_EVENTS)).toEqual(expect.arrayContaining(required));
  });
});
