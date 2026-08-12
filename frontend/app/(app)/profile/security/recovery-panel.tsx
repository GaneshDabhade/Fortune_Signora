import { Badge, Card, CardBody, CardHeader, CardTitle } from '@/components/ui';

import { NEVER_DOES, NO_SELF_SERVICE_RESET, RECOVERY_ROUTES } from './rules';

/**
 * **§04 · Account recovery**, and **§02's *What Signora never does*** —
 * [TASK-1414](../../../../../docs/BACKLOG.md).
 *
 * ## 🔴 This is the section the row is really about
 *
 * ⚠️ **The row says so in terms**: *"the design has an explicit section stating
 * the product's own limits, and it must be built as content the product commits
 * to, not as filler."*
 *
 * ⚡ **So the four sentences are the design's, verbatim**, and they live in
 * [`rules.ts`](rules.ts) as data — 📁 a commitment a support agent can be held
 * to, and rewording a commitment is how it stops being one.
 *
 * ## ⛔ A route that does not exist says so
 *
 * 📁 The design draws four recovery routes as though all four work. ⚠️ **Two
 * are real Better Auth calls; admin-assisted recovery is not built at all** —
 * no request, no approvals, no hold.
 *
 * ⚡ **The design's own argument decides this**: *"saying this plainly is better
 * than a recovery flow that ends in a dead end after four steps."* **It was
 * written about the identity provider and it applies to this product's own gaps
 * unchanged.**
 *
 * ⛔ **Server component — nothing here is interactive**, so nothing here ships
 * a client bundle.
 */
export function RecoveryPanel() {
  return (
    <div className="flex flex-col gap-6">
      <Card>
        <CardHeader>
          <CardTitle>If you lose everything</CardTitle>
          <p className="mt-1 text-sm text-content-muted">
            Recovery is, by definition, the path that works without your factors. Signora
            treats it as an attack surface rather than a convenience, so each route states
            what it proves and how long it takes.
          </p>
        </CardHeader>
        <CardBody className="flex flex-col gap-4">
          <ol className="flex flex-col gap-3" data-testid="recovery-routes">
            {RECOVERY_ROUTES.map((route) => (
              <li
                key={route.rank}
                className="rounded-md border border-border p-4"
                data-testid="recovery-route"
                data-built={route.built}
              >
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-sm font-medium text-content">
                    {route.rank}. {route.title}
                  </span>
                  <Badge tone={route.built ? 'info' : 'warning'}>{route.tag}</Badge>
                  {route.built ? (
                    <span className="text-xs text-content-muted">{route.time}</span>
                  ) : null}
                </div>
                <p className="mt-1.5 text-sm leading-6 text-content-muted">{route.body}</p>
                <p className="mt-1 text-sm leading-6 text-content-muted">{route.proves}</p>
                {route.absent === undefined ? null : (
                  <p className="mt-2 text-sm leading-6 text-content">{route.absent}</p>
                )}
              </li>
            ))}
          </ol>

          <p className="text-sm leading-6 text-content">{NO_SELF_SERVICE_RESET}</p>
        </CardBody>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>What Signora never does</CardTitle>
        </CardHeader>
        <CardBody>
          <ul className="flex flex-col gap-2" data-testid="never-does">
            {NEVER_DOES.map((commitment) => (
              <li key={commitment} className="flex gap-2 text-sm leading-6 text-content">
                <span aria-hidden="true" className="text-danger">
                  ✕
                </span>
                <span>{commitment}</span>
              </li>
            ))}
          </ul>
          <p className="mt-3 text-sm leading-6 text-content-muted">
            If something claiming to be Signora does any of these, it is not Signora.
          </p>
        </CardBody>
      </Card>
    </div>
  );
}
