import { SkeletonText } from '@/components/ui';

/**
 * **The loading state for the Security Center** —
 * [TASK-1414](../../../../../docs/BACKLOG.md).
 *
 * ⛔ **Required, because the route reads** — the session and the account list,
 * both on the server ([TASK-1447](../../../../../docs/BACKLOG.md)'s rule, and
 * the gate that enforces it).
 *
 * ⚡ **A skeleton is not an empty state and never stands in for one.** 📁
 * [P-A](../../../../../docs/DOMAIN_DISCOVERY_REGISTER.md) — **and on this page
 * the empty result would read as *nothing is wrong*.**
 */
export default function Loading() {
  return <SkeletonText lines={6} label="your security settings" />;
}
