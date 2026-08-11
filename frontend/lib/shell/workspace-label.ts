/**
 * **§19 · when a workspace-scoped surface says which workspace it is** —
 * [TASK-1463](../../../docs/BACKLOG.md), against
 * `docs/design-snapshot/screens/Fortune Signora App Shell.dc.html`
 * ([D-138](../../../docs/DECISION_REGISTER.md)).
 *
 * > 📁 ***"Every workspace-scoped surface — search, notifications, filters, the
 * > assistant — is labelled with the workspace it belongs to whenever more than
 * > one is available to the user."***
 * >
 * > 📁 **§19 ② *Labelled surfaces*: *"When a user has more than one workspace,
 * > search, notifications and the assistant all carry the workspace name in
 * > their header. Ambiguity here is what causes the wrong customer to be
 * > discussed."***
 *
 * ## 🔴 The condition is half the rule, and it is the half that is easy to drop
 *
 * ⛔ **A single-workspace user must NOT see the label.** ⚡ **They have no
 * ambiguity to resolve**, and a chip naming the only workspace they have is
 * noise on every surface it appears on — 📁 which is why the design wrote
 * *"whenever more than one is available"* rather than *"always"*.
 *
 * ⚠️ **`workspaces` is already published by
 * [`useWorkspaceContext`](../state/workspace-provider.tsx)**, so the condition
 * is a fact rather than an estimate. ⛔ **Never approximate it** — *"they
 * probably have one"* is a guess about the person reading the screen.
 *
 * ## ⚡ One rule, two callers
 *
 * 📁 [§2](../../../CLAUDE.md), *behaviour exists exactly once*. **The palette
 * and the assistant ask the same question and must not answer it separately**
 * — two copies drift, and the drift is invisible: one surface labelled and the
 * other not reads as a rendering bug rather than as a rule that disagrees with
 * itself.
 */
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * The active workspace's name **when naming it resolves an ambiguity**, and
 * `undefined` otherwise.
 *
 * ⛔ **`undefined` rather than an empty string**, so a caller renders nothing
 * rather than an empty header line — 📁 the shape
 * [`Drawer`](../../components/ui/drawer.tsx) already expects for `scope`.
 */
export function useWorkspaceLabel(): string | undefined {
  const { workspaces, activeWorkspace } = useWorkspaceContext();

  if (workspaces.length <= 1) return undefined;
  return activeWorkspace?.name ?? undefined;
}
