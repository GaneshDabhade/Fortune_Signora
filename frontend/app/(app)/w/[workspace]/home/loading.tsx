import { SkeletonText } from '@/components/ui';

/**
 * **Home's route-segment loading state** —
 * [TASK-1405](../../../../../../docs/BACKLOG.md).
 *
 * ⚡ **Owed because the route now READS.** ⛔ **It did not before**: it
 * re-exported `/`, whose own `loading.tsx` served it. 📁 §13 — *"route changes
 * keep the shell and skeleton the content"* — and
 * [`route-states.test.tsx`](../../../../../tests/components/route-states.test.tsx)
 * is what noticed the moment the route gained queries of its own.
 *
 * ⛔ **A skeleton is NOT an empty state and never stands in for one.** ⚡ **Home
 * has a designed empty state — *"Signora has nothing to put on your home yet"*
 * — and it is a statement about the REGISTRY.** **This is a statement about a
 * request**, and the two must never be confused: 📁
 * [P-A](../../../../../../docs/DOMAIN_DISCOVERY_REGISTER.md), *a failed read
 * must never render as an empty result*, and **a skeleton that never resolves
 * is the same lie held open.**
 */
export default function Loading() {
  return <SkeletonText lines={5} />;
}
