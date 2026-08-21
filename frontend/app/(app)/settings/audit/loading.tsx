import { SkeletonText } from '@/components/ui';

/**
 * **The loading state for the audit log** — [TASK-1447](../../../../../docs/BACKLOG.md)'s
 * rule, applied to a route [TASK-1412](../../../../../docs/BACKLOG.md) adds.
 *
 * ⚡ **Every route directory owes one**, and a new route arriving without it is
 * how 0 of 26 happened in the first place. ⛔ **A skeleton is not an empty
 * state**: the error path belongs to the read.
 */
export default function Loading() {
  return <SkeletonText lines={6} label="the audit log" />;
}
