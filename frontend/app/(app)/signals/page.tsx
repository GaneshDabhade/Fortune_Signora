import { SignalQueue } from './signal-queue';

/**
 * **`/signals`** — the Signal Center, [TASK-439](../../../../docs/BACKLOG.md).
 *
 * ⚡ **Reached from the attention list**, not from a navigation entry:
 * [D38](../../../../docs/architecture/39-product-review-findings.md) removed
 * these screens from the rail by name and says *"adding one back is a claim
 * that needs defending"*. ⛔ **And the rail belongs to
 * [TASK-1408](../../../../docs/BACKLOG.md)**, which owns the frame — a feature
 * row reaching into it would be taking another row's scope.
 */
export const dynamic = 'force-dynamic';

export default function SignalsPage() {
  return <SignalQueue />;
}
