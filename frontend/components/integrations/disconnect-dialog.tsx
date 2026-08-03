'use client';

import { Button, Dialog } from '@/components/ui';
import { systemName } from '@/components/integrations/connection-center';
import type { DisconnectResult } from '@/lib/query/hooks/integrations';

/**
 * Confirming, and then explaining, a disconnection.
 *
 * **A confirmation earns its interruption by saying something the customer did
 * not already know.** *"Are you sure?"* does not; *"Signora stops reading
 * immediately, what it already learned stays, and you can reconnect"* does. A
 * dialog that only asks twice is a speed bump, and people learn to click
 * through speed bumps.
 *
 * ### The three questions somebody actually has before pressing this
 *
 * *What stops · what happens to what you already have · can I undo it.* All
 * three are answered before the destructive button, not after it.
 *
 * ### The honest partial success
 *
 * Signora can always stop reading. It cannot always tell the other system —
 * there is no revocation adapter yet, and a vendor can be unreachable anyway.
 * Reporting that plainly is the difference between a customer who knows to
 * tidy up on HubSpot's side and one who believes they are finished.
 */

interface DisconnectDialogProps {
  open: boolean;
  systemSlug: string;
  label: string;
  isPending: boolean;
  result: DisconnectResult | null;
  isError: boolean;
  onConfirm: () => void;
  onClose: () => void;
}

export function DisconnectDialog({
  open,
  systemSlug,
  label,
  isPending,
  result,
  isError,
  onConfirm,
  onClose,
}: DisconnectDialogProps) {
  const name = systemName(systemSlug);

  if (result) {
    return (
      <Dialog open={open} onClose={onClose} title={`${name} disconnected`}>
        <div className="flex flex-col gap-3">
          <p className="text-sm text-content">
            Signora has stopped reading from {label}.
          </p>
          {result.revoked_at_provider ? (
            <p className="text-sm text-content-muted">
              {name} has been told, and Signora&rsquo;s access there has been removed.
            </p>
          ) : (
            // Said plainly rather than omitted. A customer who believes they
            // are finished when Signora's access still exists at the vendor is
            // worse off than one given a second step.
            <p className="text-sm text-content">
              Signora could not tell {name}. Nothing here can read from it any more, but you
              may also want to remove Signora from your {name} settings.
            </p>
          )}
          <p className="text-sm text-content-muted">
            You can connect {name} again whenever you want.
          </p>
          <div>
            <Button onClick={onClose}>Done</Button>
          </div>
        </div>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} title={`Disconnect ${name}?`}>
      <div className="flex flex-col gap-3">
        <p className="text-sm text-content">
          Signora will stop reading from {label} immediately.
        </p>
        <ul className="flex flex-col gap-1">
          <li className="text-sm text-content-muted">
            What Signora already learned from it stays — your accounts keep their history.
          </li>
          <li className="text-sm text-content-muted">
            Nothing in {name} is changed or deleted.
          </li>
          <li className="text-sm text-content-muted">
            You can connect it again later.
          </li>
        </ul>

        {isError ? (
          <p className="text-sm text-content">
            That did not work. Nothing was changed — try again in a moment.
          </p>
        ) : null}

        <div className="flex items-center gap-2">
          <Button variant="danger" onClick={onConfirm} disabled={isPending}>
            {isPending ? 'Disconnecting…' : `Disconnect ${name}`}
          </Button>
          <Button variant="ghost" onClick={onClose} disabled={isPending}>
            Keep it connected
          </Button>
        </div>
      </div>
    </Dialog>
  );
}
