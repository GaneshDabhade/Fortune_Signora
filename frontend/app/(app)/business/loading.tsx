import { SkeletonText } from '@/components/ui';

/**
 * **The loading state for your business** — [TASK-1447](../../../../docs/BACKLOG.md).
 *
 * ⚡ **`loading.tsx` existed on 0 of 26 route directories**, which is the first
 * half of what that row measured. **Next renders this while the route segment
 * resolves**, so a navigation shows the shape of what is coming rather than a
 * blank frame.
 *
 * ⛔ **A skeleton is NOT an empty state and never stands in for one.** 📁
 * [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): *a failed read must never
 * render as an empty result* — and a skeleton that never resolves is the same
 * lie held open. **The error path belongs to the read**, not here.
 *
 * ⚡ **`SkeletonText` is reused rather than a new vocabulary invented** — 📁 the
 * row is explicit that it is about REACH, not components.
 */
export default function Loading() {
  return <SkeletonText lines={5} />;
}
