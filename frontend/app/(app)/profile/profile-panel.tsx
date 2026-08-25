'use client';

import { useEffect, useRef, useState } from 'react';

import { Button, FieldOriginTag, Input } from '@/components/ui';
import { changePreferences, getPreferences, type Preferences } from '@/lib/api/preferences';
import { displayNameProblem, normalizeDisplayName } from '@/lib/profile/display-name';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';

/**
 * **Screen `01 · Personal profile`** — [TASK-470](../../../../docs/BACKLOG.md),
 * Workflow 9, against `docs/design-snapshot/screens/Fortune Signora User
 * Profile.dc.html` ([D-138](../../../../docs/DECISION_REGISTER.md)).
 *
 * ### 🔴 Three of the design's seven fields are absent, deliberately
 *
 * The design draws **Full name · Display name · Pronouns · Work email · Job
 * title · Department · Mobile number**. **Three do not ship**, and the reason
 * is the screen's own headline number — `0`, *"edits accepted that a sync
 * would undo"*:
 *
 * | | |
 * |---|---|
 * | ⛔ **Job title · Department** | **Nothing in the product knows them.** They are drawn *From directory* and **no directory integration exists** — [C-248](../../../../docs/LANE_COORDINATION.md). A locked field with no sync behind it is a rule the product does not have, painted as one it does ([D-156](../../../../docs/DECISION_REGISTER.md) ④) |
 * | ⛔ **Mobile number** | Drawn with *"Verified 14 Mar 2026"*. **No number is stored and nothing verifies one**, and a field that displayed an unverified number under a verified badge is the same defect wearing a friendlier face |
 *
 * ⚠️ **`Full name` ships read-only and is NOT tagged *From directory***. Better
 * Auth holds it, so it is the account's — the design attributes the lock to a
 * directory, and attributing it to a sync that does not exist would be the
 * false half of a true statement.
 */
export function ProfilePanel({ name, email }: { name: string | null; email: string }) {
  const { activeWorkspace } = useWorkspaceContext();
  const workspaceId = activeWorkspace?.id ?? null;
  // Only the setter is held: the inputs are the editable copy, and the
  // server's answer is folded back into them on load and after each save.
  // Keeping a second rendered copy would be two representations of one fact.
  const [prefs, setPrefs] = useState<Preferences | null>(null);
  const [displayName, setDisplayName] = useState('');
  const [pronouns, setPronouns] = useState('');
  /**
   * ⚡ **`unavailable` is a fourth member rather than a flag beside `error`**
   * — 📁 [B-255](../../../../docs/BUGS.md). **The two refusals need different
   * sentences**: one is *try again*, the other is *there is nothing to save
   * against*, ⛔ **and telling somebody to check their connection when their
   * connection is fine is a false instruction** ([§2](../../../../CLAUDE.md)).
   */
  const [status, setStatus] = useState<
    'idle' | 'saving' | 'saved' | 'error' | 'unavailable'
  >('idle');
  const [loading, setLoading] = useState(true);
  /**
   * 📁 ***"Validated on blur."*** — §07's `validation` table.
   *
   * ⛔ **Not per keystroke, and the difference is not cosmetic.** ⚡ Every
   * name passes through *one character* on its way to two, so a validator
   * that ran on input would call somebody wrong for typing — and the design
   * rules it out by name in the same paragraph.
   */
  const [nameBlurred, setNameBlurred] = useState(false);
  /** Set by Save, never cleared: a form that has been submitted once is a
   *  form whose problems have been asked for. */
  const [attempted, setAttempted] = useState(false);
  const nameField = useRef<HTMLInputElement>(null);

  useEffect(() => {
    if (workspaceId === null) return;
    let live = true;
    getPreferences(workspaceId)
      .then((loaded) => {
        if (!live) return;
        setPrefs(loaded);
        // ⛔ **Never over the top of a person's typing.** The server's copy
        // seeds an untouched form and loses to a touched one, because the
        // newer fact is the one in front of them.
        /**
         * 🔴 **[B-215](../../../../docs/BUGS.md) — a slow read was erasing what
         * somebody had already typed.**
         *
         * ⛔ **The seed loses to anything the person has entered.** If this
         * effect resolves after the first keystroke, assigning the server's
         * copy overwrites it — and `Save` then sends the empty field as
         * `null`, the row stores nothing, and the screen says *"Saved"*.
         * **That was the whole defect**, and it was here rather than in the
         * transport: the endpoint and the proxy each handle a `PATCH` body
         * correctly, proved by sending one through each.
         *
         * ⚡ **Guarded through the setter, not through a flag.** A `hasEdited`
         * boolean read inside this callback would be the value captured when
         * the effect ran — always `false` — so it would have been a fix that
         * never fired. **The updater sees the state at resolution time**,
         * which is the only moment that can answer the question.
         */
        setDisplayName((current) => (current === '' ? (loaded.display_name ?? '') : current));
        setPronouns((current) => (current === '' ? (loaded.pronouns ?? '') : current));
      })
      // ⛔ **A failed read renders as an error, never as an empty form** — P-A,
      // and the shape C-226 found six times on one screen. Blank fields here
      // would invite somebody to retype what they had already saved.
      .catch(() => {
        if (live) setStatus('error');
      })
      .finally(() => {
        if (live) setLoading(false);
      });
    return () => {
      live = false;
    };
  }, [workspaceId]);

  /**
   * 🔴 **Shown once it has been left, or once Save has been pressed.**
   *
   * ⚡ **The second half matters**: somebody can press Save without ever
   * leaving the field they are in — 📁 and *"pressing it moves focus to the
   * first problem"* is only possible if pressing it also reveals the problem.
   */
  const nameProblem = displayNameProblem(displayName);
  const showNameProblem = nameProblem !== null && (nameBlurred || attempted);

  /**
   * 📁 ***"Explicit, with a count of changed fields."*** — §07, `Save`.
   *
   * ⚡ **Measured against what the server last returned**, not against a
   * separate copy of the form: the baseline is `prefs`, so a value that has
   * been typed and typed back is correctly *not* a change.
   *
   * ⛔ **Compared after normalisation** — trailing whitespace is stripped
   * before the value is sent, so counting the raw string would report a change
   * that the `PATCH` does not make.
   */
  const changed = (() => {
    if (prefs === null) return 0;
    const name = normalizeDisplayName(displayName);
    const said = pronouns.trim();
    let count = 0;
    if (name !== (prefs.display_name ?? '')) count += 1;
    if (said !== (prefs.pronouns ?? '')) count += 1;
    return count;
  })();

  const save = async () => {
    /**
     * 📁 ***"The Save button stays enabled — pressing it moves focus to the
     * first problem instead of doing nothing."***
     *
     * 🔴 **Both halves are the design's, and the second is why the button is
     * not disabled.** ⛔ A disabled Save on an invalid form is the control
     * that silently does nothing this file already refuses one guard clause
     * below — it withholds the reason at exactly the moment it is needed.
     *
     * ⚠️ **And it was reaching the server.** 📁 `schemas.py:714` carries
     * `min_length=2`, so a one-character name was a `422` — rendered by the
     * `catch` below as ***"Check your connection and try again."*** **The
     * connection was fine and the instruction was false**
     * ([§2](../../../../CLAUDE.md)).
     */
    setAttempted(true);
    if (displayNameProblem(displayName) !== null) {
      nameField.current?.focus();
      return;
    }
    /**
     * 🔴 **[B-255](../../../../docs/BUGS.md): this returned and said nothing.**
     *
     * ⛔ **The status stayed `idle`**, so somebody with no workspace pressed
     * `Save`, watched the button not even spin, and got neither a confirmation
     * nor a refusal. ⚡ **That is the [§2](../../../../CLAUDE.md) rule this
     * lane has applied three times this week — *a control that silently does
     * nothing is worse than one that is absent*** — **and it was sitting in a
     * guard clause.**
     *
     * ✅ **It is an error rather than a hidden button**: preferences are a
     * person's own, so the panel is right to render, and the honest thing is
     * to say the write cannot be made rather than to remove the way to make
     * it.
     */
    if (workspaceId === null) {
      setStatus('unavailable');
      return;
    }
    setStatus('saving');
    try {
      // ⚡ **Only the two fields this panel owns are sent.** The server
      // distinguishes absent from null, so spreading the whole object would
      // clear the theme and timezone other panels set.
      const saved = await changePreferences(workspaceId, {
        // ⚡ **The same normalisation the validator ran** — otherwise the
        // string that was checked and the string that is sent differ.
        display_name: normalizeDisplayName(displayName) || null,
        pronouns: pronouns.trim() === '' ? null : pronouns.trim(),
      });
      setPrefs(saved);
      // Adopt the server's copy rather than trusting the local one — a
      // trimmed or truncated value must show as what was actually stored.
      setDisplayName(saved.display_name ?? '');
      setPronouns(saved.pronouns ?? '');
      setStatus('saved');
    } catch {
      setStatus('error');
    }
  };

  return (
    <section className="flex flex-col gap-6" aria-labelledby="profile-heading">
      <header className="flex flex-col gap-1">
        <h2 id="profile-heading" className="text-lg font-semibold text-content">
          Profile
        </h2>
        <p className="text-sm leading-6 text-content-muted">
          How you appear to everyone else in your organization.
        </p>
      </header>

      <dl className="flex flex-col gap-5">
        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <dt className="text-sm font-medium text-content">Full name</dt>
            {/* Locked because it is the account's, and said in those words —
                the design attributes this to a directory and there is none. */}
            <FieldOriginTag origin="account" />
          </div>
          <dd className="text-sm text-content-muted">{name ?? 'Not set'}</dd>
        </div>

        <div className="flex flex-col gap-1.5">
          <div className="flex items-center gap-2">
            <dt className="text-sm font-medium text-content">Work email</dt>
            <FieldOriginTag origin="account" />
          </div>
          <dd className="font-mono text-sm text-content-muted">{email}</dd>
          <p className="text-xs text-content-subtle">
            Changing this creates a new identity — it cannot be edited here.
          </p>
        </div>
      </dl>

      {/* §19's loading state, said in words rather than implied by a control
          that does not respond. */}
      {loading ? (
        <p role="status" className="text-sm text-content-muted">
          Loading your preferences…
        </p>
      ) : null}

      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <Input
            ref={nameField}
            label="Display name"
            value={displayName}
            onChange={(event) => setDisplayName(event.target.value)}
            onBlur={() => setNameBlurred(true)}
            hint="Used in mentions and comments. 2–32 characters."
            error={showNameProblem ? nameProblem : undefined}
            // ⛔ **`maxLength` is gone, and it was wrong twice.** ⚡ It refuses
            // a keystroke by making it vanish — **a silent refusal, where the
            // design asks for a stated one** — and it counts UTF-16 units, so
            // it capped an emoji name at sixteen glyphs while
            // 📁 `schemas.py:714` counts code points and would have taken
            // thirty-two. **The ceiling is now said rather than enforced by
            // absence**, and it is counted the way the server counts it.
          />
          <FieldOriginTag origin="yours" className="self-start" />
        </div>

        <div className="flex flex-col gap-1.5">
          <Input
            label="Pronouns"
            value={pronouns}
            onChange={(event) => setPronouns(event.target.value)}
            // ⛔ **Optional, and never inferred from a name.** Guessing is
            // worse than an empty field.
            hint="Optional. Appears beside your name in mentions."
            maxLength={32}
          />
          <FieldOriginTag origin="yours" className="self-start" />
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/*
          ⛔ **Not disabled on `prefs === null`, and the first version was.**
          Saving a display name is a `PATCH` of two fields — **it does not need
          the values the read would have returned**, so gating it on a
          successful read couples a write to a read it has no dependency on.
          ⚠️ **The journey caught it**: the control sat disabled with nothing on
          screen saying why, which is a loading state wearing a disabled
          control's clothes. **The loading state is now stated** below.
        */}
        <Button onClick={save} loading={status === 'saving'}>
          {/* 📁 ***"Explicit, with a count of changed fields."*** ⛔ **The
              count is omitted rather than rendered as zero**: *"Save 0
              changes"* is a label that argues with the button it is on. */}
          {changed === 0
            ? 'Save changes'
            : `Save ${changed} ${changed === 1 ? 'change' : 'changes'}`}
        </Button>
        {/* ⚡ **A status, not an alert** — 4.1.3. A save confirmation must not
            interrupt somebody who has moved on to the next field. */}
        <p role="status" className="text-sm text-content-muted">
          {status === 'saved' ? 'Saved' : ''}
        </p>
        {status === 'error' ? (
          <p role="alert" className="text-sm text-danger">
            That did not save. Check your connection and try again.
          </p>
        ) : null}
        {/* ⛔ **A different refusal needs a different sentence** — 📁
            [B-255](../../../../docs/BUGS.md). **Nothing failed and nothing is
            worth retrying**: there is no organization for the preference to
            belong to, and saying *check your connection* would send somebody
            to look at a thing that is working. */}
        {status === 'unavailable' ? (
          <p role="alert" className="text-sm text-danger">
            These settings belong to an organization, and you are not in one yet.
          </p>
        ) : null}
      </div>
    </section>
  );
}
