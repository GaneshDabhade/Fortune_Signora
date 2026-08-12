'use client';

import { Badge, Card, CardBody, CardHeader, CardTitle } from '@/components/ui';

import { posture, type PostureCell, type PostureTone } from './rules';

/**
 * **§01 · Security posture** — [TASK-1414](../../../../../docs/BACKLOG.md).
 *
 * 📁 ***"Posture is computed from your account only. Workspace-wide controls
 * live in Settings and are shown here as context, never as something you can
 * change."***
 *
 * ## 🔴 Three of five cells say they cannot answer, and that is the panel
 *
 * ⚡ **The alternative was to render two cells and look complete.** ⛔ **A
 * posture strip that silently omits *open alerts* reports a posture the product
 * cannot see as one it has checked** — and the reader this page is designed
 * for is *"someone who thinks they have been compromised"*, reading it
 * *"in under a minute, while frightened"*.
 *
 * 📁 **[P-A](../../../../../docs/DOMAIN_DISCOVERY_REGISTER.md) is the rule and
 * this is its worst case**: *a failed read must never render as an empty
 * result.* **Here the empty result would read `Open alerts: none`.**
 */
const TONE: Readonly<Record<PostureTone, 'success' | 'warning' | 'danger'>> = {
  positive: 'success',
  attention: 'warning',
  risk: 'danger',
};

export interface PosturePanelProps {
  /** How many second factors are enrolled. `null` when the read failed. */
  readonly factors: number | null;
  /** How many sessions this account holds. `null` when the read failed. */
  readonly sessions: number | null;
}

export function PosturePanel({ factors, sessions }: PosturePanelProps) {
  const cells = posture({ factors, sessions });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Security posture</CardTitle>
        <p className="mt-1 text-sm text-content-muted">
          Computed from your account only. Anything your organization controls lives in
          Settings, and is not something you can change here.
        </p>
      </CardHeader>
      <CardBody>
        <dl
          className="grid grid-cols-1 gap-x-6 gap-y-5 phone:grid-cols-2 smalllaptop:grid-cols-3"
          data-testid="posture-strip"
        >
          {cells.map((cell) => (
            <PostureCellView key={cell.label} cell={cell} />
          ))}
        </dl>
      </CardBody>
    </Card>
  );
}

function PostureCellView({ cell }: { cell: PostureCell }) {
  return (
    <div data-testid="posture-cell" data-label={cell.label}>
      <dt className="text-xs font-medium uppercase tracking-wide text-content-muted">
        {cell.label}
      </dt>
      <dd className="mt-1">
        {cell.reading.known ? (
          <>
            <Badge tone={TONE[cell.reading.tone]}>{cell.reading.value}</Badge>
            <p className="mt-1.5 text-sm text-content-muted">{cell.reading.meta}</p>
          </>
        ) : (
          /**
           * ⛔ **`Not known` and never `None`, `0` or an em dash.** ⚡ **A dash
           * is read as *nothing to report*, which is the false reassurance this
           * whole panel exists to refuse.**
           */
          <>
            <Badge tone="neutral">Not known</Badge>
            <p className="mt-1.5 text-sm text-content-muted">{cell.reading.because}</p>
          </>
        )}
      </dd>
    </div>
  );
}
