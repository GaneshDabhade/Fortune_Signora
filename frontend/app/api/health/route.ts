/**
 * Authentication readiness endpoint.
 *
 * Returns 503 when the subsystem cannot authenticate anyone, so an
 * orchestrator withholds traffic rather than routing users into a broken
 * sign-in. "degraded" still returns 200: the process is serving correctly
 * and restarting it would not help.
 */

import { NextResponse } from 'next/server';

import { checkAuthHealth } from '@/lib/auth/health';

export async function GET(): Promise<NextResponse> {
  const report = await checkAuthHealth();
  return NextResponse.json(report, {
    status: report.status === 'unavailable' ? 503 : 200,
  });
}
