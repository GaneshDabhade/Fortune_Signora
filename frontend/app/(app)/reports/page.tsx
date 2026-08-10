import { ReportsScreen } from './reports-screen';

/**
 * **`/reports`** — [TASK-1417](../../../../docs/BACKLOG.md).
 *
 * ⚡ **A route file that renders one component**, the pattern
 * [`/signals`](../signals/page.tsx) already uses: **the screen is a client
 * component and the route is not**, so nothing about the frame has to become
 * client-side to reach it.
 */
export const dynamic = 'force-dynamic';

export default function ReportsPage() {
  return <ReportsScreen />;
}
