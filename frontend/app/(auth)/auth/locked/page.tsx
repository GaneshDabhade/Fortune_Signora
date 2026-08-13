/** 📁 Entry rule's `ACCOUNT_LOCKED` — [TASK-1423](../../../../../docs/BACKLOG.md). */
import { GateScreen } from '../../gate/gate-screen';

export default function Page() {
  return <GateScreen reason="ACCOUNT_LOCKED" />;
}
