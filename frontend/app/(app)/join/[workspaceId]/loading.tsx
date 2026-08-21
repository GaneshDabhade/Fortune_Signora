import { SkeletonText } from '@/components/ui';

/**
 * **The loading state for accepting an invitation** —
 * [TASK-1447](../../../../../docs/BACKLOG.md).
 *
 * ⚠️ **This route was missed by the manual sweep and caught by the guard**,
 * which is the argument for the guard: 📁 the sweep listed the routes a person
 * thought of, and `route-states.test.tsx` lists the routes that actually read.
 *
 * ⛔ **A skeleton is NOT an empty state.** 📁
 * [P-A](../../../../../docs/DOMAIN_DISCOVERY_REGISTER.md): *a failed read must
 * never render as an empty result* — and this screen matters more than most,
 * because **somebody arriving on an invitation link has no other route in.**
 */
export default function Loading() {
  return <SkeletonText lines={4} label="this invitation" />;
}
