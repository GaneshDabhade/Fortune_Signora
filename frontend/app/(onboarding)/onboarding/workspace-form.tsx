'use client';

import { useRouter } from 'next/navigation';
import { useEffect, useRef, useState } from 'react';

import { cn } from '@/lib/design/cn';
import { checkSlug, type SlugAvailability } from '@/lib/api/workspaces';
import { useCreateWorkspace } from '@/lib/query/hooks';
import { useSession } from '@/lib/auth/client';
import { useWorkspaceContext } from '@/lib/state/workspace-provider';
import { MAX_SLUG, MIN_SLUG, suggestSlug } from '@/lib/workspace/slug';

import { OnboardingShell } from '../onboarding-shell';
import { OnboardingRail } from './rail';
import { COUNTED_STEPS, COUNTED_TOTAL, positionOf } from './steps';
import { Button } from '@/components/ui';

/** 📁 *"Checked as you type, **300ms after you stop**."* */
const SETTLE_MS = 300;

/**
 * **Screen `03 Workspace creation` — the only required step.**
 *
 * > *"Workspace name and URL, both pre-filled from the email domain."*
 * > *"**Required · 20s**"*
 *
 * ### 🔴 It is the only step that creates something
 *
 * ⚡ **Every screen after this one refines a product the person already
 * owns** — 📁 which is the design's own explanation for why the rest is
 * skippable and why the completion screen can show real data. ⛔ **So this one
 * cannot be skipped, and there is no *Skip for now* here.**
 *
 * ### ⚡ *Organization*, not *workspace*, everywhere a person reads it
 *
 * 📁 The design writes *"Name your workspace"* and *"Workspace URL"*, and
 * [ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)
 * keeps that word off a customer's screen — ⛔ **`vocabulary.test.tsx` enforces
 * it.** ✅ Settings already says *"Create organization"*, so this is the
 * product's established translation rather than a choice made here.
 *
 * ### ⛔ The availability check is a courtesy, not the guarantee
 *
 * ⚡ **A unique index is what actually holds.** 📁 The design knows it —
 * *"That URL was taken while you were typing"* is one of its four named error
 * cases — so a `409` from `Create` is rendered as that sentence rather than as
 * a failure, **and nothing typed is lost.**
 *
 * ### ⚠️ Nothing here is inferred, because the domain record does not exist
 *
 * 📁 The design pre-fills both fields *"from the email domain"* and marks the
 * name *"Filled from northwind.com — edit if it's wrong"*. ⚡ **The email IS
 * available** — it is the signed-in person's — **so the suggestion is real and
 * the note names the actual domain.** ⛔ **What is NOT claimed is a public
 * company record**: the design's *"Northwind Global"* is a company name from
 * an enrichment provider, and no such producer exists here. **The suggestion
 * says where it came from and it came from the address, so that is what it
 * says.**
 */
export function WorkspaceForm() {
  const router = useRouter();
  const session = useSession();
  const { setActiveWorkspace } = useWorkspaceContext();
  const create = useCreateWorkspace();

  const domain = emailDomain(session.data?.user?.email ?? null);
  const suggestedName = domain === null ? '' : titleFromDomain(domain);

  const [name, setName] = useState<string | null>(null);
  const [slug, setSlug] = useState<string | null>(null);
  const [availability, setAvailability] = useState<SlugAvailability | null>(null);
  const [checking, setChecking] = useState(false);
  /**
   * 🔴 **A check that FAILED is not a check still running.**
   *
   * ⛔ **Without this the two are the same state** — `availability === null`
   * with `checking` false — **and `Verdict` painted *Checking…* forever.** ⚡ It
   * is [B-277](../../../../docs/BUGS.md)'s exact shape one screen over: **a
   * read that finished, rendered as one still in flight**, on the field
   * carrying the only permanent decision in onboarding.
   *
   * 📁 **The design rules this without needing a new state.** Its treatment of
   * a producer that cannot answer is stated for the enrichment badge —
   * *"Enrichment unavailable: fields stay empty and editable, **the Inferred
   * badge is absent**, and the step is never blocked by it."* ✅ **So the
   * verdict is ABSENT**, and `Create` stays enabled because the server is what
   * actually decides.
   */
  const [checkFailed, setCheckFailed] = useState(false);
  const [failure, setFailure] = useState<string | null>(null);

  const shownName = name ?? suggestedName;
  const shownSlug = slug ?? suggestSlug(shownName);

  /**
   * 📁 *"Checked as you type, 300ms after you stop."*
   *
   * ⛔ **Debounced, and every stale answer is discarded.** ⚡ A reply for a
   * slug the person has since edited would paint *Available* beside different
   * text — **the classic race, and the one a customer reads as a lie.**
   */
  const settled = useRef<ReturnType<typeof setTimeout> | null>(null);
  useEffect(() => {
    const candidate = shownSlug;
    setAvailability(null);
    setCheckFailed(false);
    if (candidate.length < MIN_SLUG) {
      setChecking(false);
      return;
    }
    setChecking(true);
    if (settled.current !== null) clearTimeout(settled.current);

    let live = true;
    settled.current = setTimeout(() => {
      void checkSlug(candidate)
        .then((answer) => {
          /**
           * ⛔ **Only if this effect is still the current one.**
           *
           * 🔴 **This also compared `answer.slug === candidate` and that was a
           * DEFECT.** ⚡ The server answers with the *normalized* slug, so
           * anything needing normalization — `North Wind!`, ` Northwind ` —
           * came back with a different string and **its verdict was silently
           * thrown away.** ⛔ **The field showed *Checking…* forever**, which is
           * the shape [B-277](../../../../docs/BUGS.md) has one screen over: a
           * read that finished, rendered as one still running.
           *
           * ✅ **`live` already carries staleness** — the cleanup below flips it
           * on every edit — so the extra comparison bought nothing and cost the
           * one case it was meant to protect.
           */
          if (live) setAvailability(answer);
        })
        .catch(() => {
          // ⚠️ **A failed check is NOT *unavailable*.** [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md)
          // — the read failed, and rendering that as an answer would block
          // somebody out of a name that is theirs. **Create stays enabled and
          // the server decides.**
          //
          // ⚠️ **Nor is it *still checking*.** ⛔ **Without `checkFailed` these
          // two states are the same pair** — `checking` false, `availability`
          // null — **and the field said *Checking…* forever.** ✅ The marker
          // goes ABSENT instead, which is 📁 the design's own treatment of a
          // producer that cannot answer.
          if (live) {
            setAvailability(null);
            setCheckFailed(true);
          }
        })
        .finally(() => {
          if (live) setChecking(false);
        });
    }, SETTLE_MS);

    return () => {
      live = false;
      if (settled.current !== null) clearTimeout(settled.current);
    };
  }, [shownSlug]);

  const submit = async () => {
    setFailure(null);
    try {
      const workspace = await create.mutateAsync({
        name: shownName.trim(),
        slug: shownSlug,
      });
      // ⚡ **The context must know before the next screen reads it** — every
      // step after this one is workspace-scoped, and 📁 [B-277](../../../../docs/BUGS.md)
      // is exactly what an onboarding screen does with no active organization.
      setActiveWorkspace(workspace.id);
      router.push('/onboarding/company');
    } catch (error) {
      setFailure(messageFor(error));
    }
  };

  const tooShort = shownSlug.length < MIN_SLUG;
  const blocked = availability !== null && !availability.available;
  const canCreate =
    shownName.trim().length > 0 && !tooShort && !blocked && !create.isPending;

  // 📁 **The design's *creating* state is a named-step list, not a spinner** —
  // screen `08`. It replaces the form while the workspace is being made.
  if (create.isPending) return <CreatingWorkspace name={shownName.trim()} />;

  return (
    <OnboardingShell
      rail={
        <OnboardingRail
          steps={COUNTED_STEPS}
          currentId="workspace"
          completedIds={[]}
          progress={{ step: positionOf('workspace'), of: COUNTED_TOTAL }}
        />
      }
      title="Name your organization"
      description="This is what your team will see. You can change it later."
      actions={
        <>
          <Button onClick={submit} disabled={!canCreate}>
            Create organization
          </Button>
          {/* 📁 *"You'll be the owner. Data region is EU, set by your
              account."* ⚠️ **The data region half is NOT rendered** — nothing
              in this product records or chooses a region, and stating one
              would be a claim about where a customer's data lives. **That is
              the one sentence on this screen it would be worst to guess.** */}
          <p className="max-w-[30ch] text-xs leading-[1.45] text-content-subtle">
            You&rsquo;ll be the owner.
          </p>
        </>
      }
    >
      <div>
        <label
          htmlFor="workspace-name"
          className="mb-1.5 mt-1 block text-label font-semibold text-content"
        >
          Organization name
        </label>
        <input
          id="workspace-name"
          value={shownName}
          onChange={(event) => {
            setName(event.target.value);
            // ⚡ **The address follows the name until somebody touches it.**
            // ⛔ After that it is theirs and the name stops steering it —
            // silently rewriting an address a person had just typed is the
            // control-that-fights-you shape.
            if (slug === null) setAvailability(null);
          }}
          // 📁 *"height:42px; font-size:14px"* — taller than a step control,
          // because this field is the screen.
          // 🔴 **`outline-none` removed** — 📁 §17 `2.4.7`, *"never
          // suppressed"*. ⛔ **Measured in a browser: it suppressed both the
          // outline and the ring.** ⚠️ **The slug control below keeps its own
          // `outline-none` and is correct — its wrapper carries `focus-proxy`.**
          className="h-[42px] w-full rounded-md border border-border bg-surface px-[13px] text-sm text-content transition-shadow "
        />
        {domain === null ? null : (
          // 📁 *"Filled from northwind.com — edit if it's wrong"*, in `--ai-ink`
          // with the spark. ⚡ **The domain is real** — it is the address the
          // person signed in with.
          <p className="mt-[7px] flex items-center gap-[7px] text-2xs text-ai">
            <svg
              aria-hidden
              width="12"
              height="12"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.8"
              strokeLinecap="round"
              className="flex-none"
            >
              <path d="M8 2v2.5M8 11.5V14M2 8h2.5M11.5 8H14" />
            </svg>
            Filled from {domain} — edit if it&rsquo;s wrong
          </p>
        )}

        <label
          htmlFor="workspace-slug"
          className="mb-1.5 mt-5 block text-label font-semibold text-content"
        >
          Organization URL
        </label>
        {/* 📁 The design's joined control: a `--sunken` monospace prefix, the
            editable slug, and the verdict on the right. */}
        <div
          className={cn(
            'flex h-[42px] items-center overflow-hidden rounded-md border bg-surface transition-shadow',
            // ♿ **`focus-proxy` because of `overflow-hidden`** — 📁
            // [B-1058](../../../../docs/BUGS.md). ⛔ **The input inside is
            // perfectly visible, but its indicator is CLIPPED by the joined
            // control's own clipping**, so the ring has to be drawn on the
            // element doing the clipping. ⚡ **Same declaration, moved outward.**
            'focus-proxy',
            // ⚠️ **`blocked` is a VALIDATION state, not a focus one** — it is
            // unconditional and stays.
            blocked ? 'border-danger ring-[3px] ring-danger-subtle' : 'border-border',
          )}
        >
          <span className="flex h-full flex-none items-center border-r border-border-soft bg-surface-sunken px-3 font-mono text-sm text-content-subtle">
            signora.app/
          </span>
          <input
            id="workspace-slug"
            value={shownSlug}
            maxLength={MAX_SLUG}
            onChange={(event) => setSlug(event.target.value)}
            aria-invalid={blocked}
            aria-describedby="slug-state"
            className="min-w-0 flex-1 bg-transparent px-3 font-mono text-sm text-content outline-none"
          />
          <span id="slug-state" role="status" className="flex-none pr-3">
            <Verdict
              checking={checking}
              checkFailed={checkFailed}
              tooShort={tooShort}
              availability={availability}
            />
          </span>
        </div>
        {/* ⚠️ **The REASON goes here, not inside the control.** 📁 The design's
            in-field marker is a short 12px verdict — *"Available"* — and a
            sentence in that slot squeezes the address until it is unreadable.
          **Found in a screenshot**: `North Wind!` rendered as `North Wind`
            with the message sitting on top of the rest. */}
        {blocked && availability?.reason ? (
          <p className="mt-[7px] text-2xs font-semibold text-danger">
            {availability.reason}
          </p>
        ) : (
          <p className="mt-[7px] text-2xs text-content-subtle">
            Checked as you type. Permanent once created.
          </p>
        )}

        {failure === null ? null : (
          // 📁 Screen `08`'s error card — *"nothing typed is lost"*.
          <div
            role="alert"
            className="mt-[14px] flex items-start gap-[11px] rounded-lg border border-danger-line bg-danger-subtle px-[15px] py-[13px]"
          >
            <svg
              aria-hidden
              width="15"
              height="15"
              viewBox="0 0 16 16"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.7"
              strokeLinecap="round"
              className="mt-0.5 flex-none text-danger"
            >
              <circle cx="8" cy="8" r="6.2" />
              <path d="M8 5v3.5M8 11h.01" />
            </svg>
            <p className="text-label leading-[1.55] text-content">{failure}</p>
          </div>
        )}
      </div>
    </OnboardingShell>
  );
}

/**
 * 📁 The design's right-hand marker: a green check and *Available*.
 *
 * ⛔ **Five states, and two of them say nothing.** ⚠️ **Silence while a check
 * is in flight is not *unavailable***, and a red mark that appears for 300ms
 * on every keystroke would teach somebody to ignore it.
 *
 * 🔴 **And a check that FAILED renders no marker at all** — ⛔ **not
 * *Checking…*, which is what it used to do forever.**
 */
function Verdict({
  checking,
  checkFailed,
  tooShort,
  availability,
}: {
  checking: boolean;
  checkFailed: boolean;
  tooShort: boolean;
  availability: SlugAvailability | null;
}) {
  if (tooShort) {
    return (
      <span className="text-xs text-content-subtle">{MIN_SLUG} characters or more</span>
    );
  }
  // ⛔ **Before the in-flight branch** — a failed check has `checking` false
  // and `availability` null, which is otherwise indistinguishable from a
  // check that has not answered yet.
  if (checkFailed) return null;
  if (checking || availability === null) {
    return <span className="text-xs text-content-subtle">Checking…</span>;
  }
  if (!availability.available) {
    // ⛔ **Short, because it sits INSIDE the control.** 📁 The full reason is
    // rendered beneath it, where there is room for a sentence.
    return <span className="text-xs font-semibold text-danger">Unavailable</span>;
  }
  return (
    <span className="flex items-center gap-1.5 text-xs font-semibold text-success">
      <svg
        aria-hidden
        width="13"
        height="13"
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path d="m3.5 8.5 3 3 6-6.5" />
      </svg>
      Available
    </span>
  );
}

/**
 * 📁 **Screen `08` — *"Creating the workspace"*, and it is named steps rather
 * than a spinner.**
 *
 * > *"Named steps, not a spinner. Typically 1.4s; past 6s the copy changes to
 * > say it's taking longer and offers to continue in the background."*
 *
 * ### ⛔ Three of the design's four steps are drawn and the fourth is not
 *
 * 📁 The mock lists *Workspace created · Data region set to EU · Applying your
 * preferences · Preparing your home page*. ⚡ **`Data region set to EU` is
 * omitted for the same reason the footnote below the Create button is** —
 * **nothing in this product sets or records a data region**, and a tick beside
 * that sentence would be a claim about where somebody's data physically lives.
 *
 * ### ⚠️ The ticks are elapsed time, not progress, and they never overtake the truth
 *
 * ⛔ **There is one request.** The server does not report stages, so these
 * cannot be real per-stage progress — **and pretending otherwise would be
 * decorative.** ✅ **What they honestly are: the named things that happen, in
 * order, revealed as the wait goes on**, with **none of them marked done
 * until the request actually returns.** The final step stays active until the
 * screen navigates away.
 */
export function CreatingWorkspace({ name }: { name: string }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const tick = setInterval(() => setElapsed((e) => e + 1), 1000);
    return () => clearInterval(tick);
  }, []);

  const steps = [
    { label: name === '' ? 'Creating your organization' : `Creating ${name}`, at: 0 },
    { label: 'Applying your preferences', at: 1 },
    { label: 'Preparing your home page', at: 2 },
  ];

  return (
    <OnboardingShell
      rail={
        <OnboardingRail
          steps={COUNTED_STEPS}
          currentId="workspace"
          completedIds={[]}
          progress={{ step: positionOf('workspace'), of: COUNTED_TOTAL }}
        />
      }
      title="Setting things up"
      description="This usually takes a moment."
    >
      <div role="status" className="flex flex-col gap-3">
        {steps.map((step) => {
          const reached = elapsed >= step.at;
          return (
            <div
              key={step.label}
              className={cn(
                'flex items-center gap-[11px] text-sm transition-colors',
                reached ? 'text-content-muted' : 'text-content-subtle',
              )}
            >
              <span
                aria-hidden
                className={cn(
                  // 📁 *"18px; border:1.5px solid"* — the same dot the rail uses.
                  'grid h-[18px] w-[18px] flex-none place-items-center rounded-full border-[1.5px]',
                  reached ? 'border-accent' : 'border-border',
                )}
              >
                {reached ? <span className="h-1.5 w-1.5 rounded-full bg-accent" /> : null}
              </span>
              {step.label}
            </div>
          );
        })}
      </div>

      {/* 📁 *"Past 6s the copy changes to say it's taking longer."* ⛔ **And it
          does NOT offer to continue in the background**, which the design also
          says: there is nothing to continue *to* until the organization
          exists, and every screen after this one needs it. **Offering it would
          be a control that could not do what it said.** */}
      {elapsed >= 6 ? (
        <p className="mt-5 text-2xs leading-[1.5] text-content-subtle">
          This is taking longer than usual. Nothing is lost — stay on this page and it
          will finish.
        </p>
      ) : null}
    </OnboardingShell>
  );
}

/** The address the person signed in with, which is a fact rather than a guess. */
function emailDomain(email: string | null): string | null {
  const at = email?.lastIndexOf('@') ?? -1;
  if (email === null || at < 0) return null;
  const domain = email.slice(at + 1).toLowerCase();
  // ⛔ **A free mailbox is not an organization.** Suggesting *Gmail* as
  // somebody's company name would be worse than suggesting nothing.
  return FREE_MAIL.has(domain) ? null : domain;
}

const FREE_MAIL = new Set([
  'gmail.com',
  'googlemail.com',
  'outlook.com',
  'hotmail.com',
  'live.com',
  'yahoo.com',
  'icloud.com',
  'me.com',
  'proton.me',
  'protonmail.com',
  'aol.com',
]);

/** *northwind.com* → *Northwind*. ⚡ **The registrable label only** — a
 * suffix in the name is nobody's company. */
function titleFromDomain(domain: string): string {
  const label = domain.split('.')[0] ?? '';
  return label.charAt(0).toUpperCase() + label.slice(1);
}

/**
 * 📁 Screen `08`'s error copy, chosen by what actually failed.
 *
 * ⛔ **The taken-URL case gets the design's own sentence**, because it is the
 * one a person can act on immediately — ⚡ ***"Your other answers are saved"***
 * is true here: nothing is cleared and the form is exactly as they left it.
 */
function messageFor(error: unknown): string {
  const status = (error as { status?: number } | null)?.status;
  if (status === 409) {
    return 'That URL was taken while you were typing. Your other answers are saved — pick another and continue.';
  }
  if (status === 422) {
    return 'That URL cannot be used. Try lowercase letters, numbers and hyphens.';
  }
  return 'We could not create your organization. Nothing you typed is lost — try again.';
}
