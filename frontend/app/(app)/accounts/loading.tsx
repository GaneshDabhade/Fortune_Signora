import { SkeletonText } from '@/components/ui';

/**
 * **The loading state for Companies** — [TASK-440](../../../../docs/BACKLOG.md).
 *
 * ⚡ **Next renders this while the route segment resolves**, so a navigation
 * shows the shape of what is coming rather than a blank frame.
 *
 * ⛔ **A skeleton is NOT an empty state and never stands in for one.** 📁
 * [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): *a failed read must
 * never render as an empty result* — ⚠️ **and on this screen the two are
 * indistinguishable to a seller**, which is why the page checks `isError`
 * before it checks for rows. **The error path belongs to the read**, not here.
 *
 * ✅ **`SkeletonText` is reused rather than a new vocabulary invented**, on
 * [TASK-1447](../../../../docs/BACKLOG.md)'s own rule.
 */
export default function Loading() {
  return <SkeletonText lines={6} label="your companies" />;
}
