/**
 * **The bulk bar's *Add tag*** — [TASK-466](../../../docs/BACKLOG.md), against
 * 📁 `Fortune Signora Companies.dc.html`.
 *
 * ## 🔴 The confirm names the count and the act, in the customer's words
 *
 * 📁 [TASK-466](../../../docs/BACKLOG.md)'s Definition of Done: ***"the confirm
 * states the COUNT and the ACTION in the customer's words"***
 * ([ADR-0034](../../../docs/architecture/adr/0034-ubiquitous-language.md)).
 *
 * ⛔ **So it says *companies*, never *accounts*** — a salesperson says the
 * first about the businesses they sell to, and `account` is the platform's
 * word for the entity.
 *
 * ## ⚠️ It proposes; it does not apply
 *
 * 📁 [ADR-0405](../../../docs/architecture/adr/0405-an-action-is-approved-before-it-is-effective.md):
 * *an action is approved before it is effective.* ⛔ **Nothing is tagged when
 * this resolves**, and the copy says so rather than implying the work is
 * done — **a screen that showed the chips immediately would have told the
 * customer something untrue.**
 */
import { useState } from 'react';

import { Button } from '@/components/ui/button';
import { Dialog } from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import type { AccountTag } from '@/lib/api/types';

export interface AddTagControlProps {
  /** **How many companies the batch would cover.** */
  readonly count: number;
  readonly tags: readonly AccountTag[];
  /** ⛔ Absent while the vocabulary has not arrived — see below. */
  readonly onPropose: ((tagId: string) => void) | undefined;
  readonly onCreate: (name: string) => void;
  readonly pending: boolean;
}

export function AddTagControl({
  count,
  tags,
  onPropose,
  onCreate,
  pending,
}: AddTagControlProps) {
  const [open, setOpen] = useState(false);
  const [name, setName] = useState('');

  // ⛔ **No control while the vocabulary is unread.** ⚡ Opening a picker with
  // an empty list would look like *"this workspace has no labels"* to somebody
  // whose labels simply had not arrived — 📁 [P-A](../../../docs/DOMAIN_DISCOVERY_REGISTER.md)'s
  // shape: **an unresolved read must never render as an empty result.**
  if (onPropose === undefined) return null;

  return (
    <>
      <Button variant="ghost" onClick={() => setOpen(true)}>
        Add tag
      </Button>

      <Dialog
        open={open}
        onClose={() => setOpen(false)}
        title={`Add a tag to ${count} ${count === 1 ? 'company' : 'companies'}`}
      >
        {/* 📁 **The count and the act, in the customer's words** — and the
            second sentence is the one that keeps the promise honest. */}
        <p className="text-sm text-content-muted">
          Nothing changes until somebody approves it. You can take it back for a
          day afterwards.
        </p>

        {tags.length > 0 ? (
          <ul className="mt-3 flex flex-wrap gap-2">
            {tags.map((tag) => (
              <li key={tag.id}>
                <Button
                  variant="secondary"
                  disabled={pending}
                  onClick={() => {
                    onPropose(tag.id);
                    setOpen(false);
                  }}
                >
                  {tag.name}
                </Button>
              </li>
            ))}
          </ul>
        ) : (
          /* ⛔ **A designed empty state, not a blank panel.** This workspace
             has genuinely named no labels, which is different from not having
             read them — the control does not render at all in that case. */
          <p className="mt-3 text-sm text-content-muted">
            This organization has no tags yet. Name one below.
          </p>
        )}

        <form
          className="mt-4 flex gap-2"
          onSubmit={(event) => {
            event.preventDefault();
            const wanted = name.trim();
            if (wanted === '') return;
            onCreate(wanted);
            setName('');
          }}
        >
          {/* ♿ **`label` is required by the component and that is the point**
              — 📁 *"an unlabelled input is unusable with a screen reader and
              the omission is invisible in review."* */}
          <Input
            label="New tag name"
            value={name}
            maxLength={40}
            onChange={(event) => setName(event.target.value)}
            placeholder="At risk"
          />
          {/* ⚡ **Creating a name that exists SELECTS it** — the server answers
              200 with the existing tag — so this button never has to be an
              *"already exists"* error a customer has to understand. */}
          <Button type="submit" disabled={pending || name.trim() === ''}>
            Create
          </Button>
        </form>
      </Dialog>
    </>
  );
}
