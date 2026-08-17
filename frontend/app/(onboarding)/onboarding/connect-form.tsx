'use client';

import { useState } from 'react';

import { CAPABILITY_VALUE, systemName } from '@/components/integrations/connection-center';
import { cn } from '@/lib/design/cn';
import { finishOnboarding } from '@/lib/api/onboarding';
import type { IntegrationSystem, PersonPreferences } from '@/lib/api/types';
import { useIntegrations } from '@/lib/query/hooks/integrations';
import { useChangePreferences, usePreferences } from '@/lib/query/hooks/preferences';

import { OnboardingShell } from '../onboarding-shell';
import { OnboardingSkeleton } from './company-form';
import { useOnboardingExit } from './exit';
import { useOnboarding } from './use-onboarding';

/**
 * **Screen `07 Connect & AI personalisation`** — [TASK-469](../../../../docs/BACKLOG.md).
 *
 * > *"CRM connection and AI settings: read-only by default, drafts need
 * > approval. **Inferred: nothing. Consent is never inferred.**"*
 *
 * ### 🔴 There is no rail, and the design draws none
 *
 * 📁 Every other step sits in the `240px 1fr` frame. **This one is a single
 * `36px 40px` plane** — the flow's questions are over, and the rail's job was
 * to say how many were left.
 *
 * ### ⛔ Consent is never inferred, and never pre-granted
 *
 * ⚡ **Every toggle here shows what the server currently holds** and nothing is
 * defaulted on by this screen. 📁 The design says it in the section title —
 * *"consent is explicit, never inferred"* — and it is the one line on the
 * screen that would be a lie if a control were even slightly optimistic.
 *
 * ### ⚠️ Two of the design's four toggles cannot be honest toggles, and they say so
 *
 * ⛔ **This is not the design being trimmed.** 📁 [§9](../../../../CLAUDE.md)'s
 * rule is *"do not silently remove the UI, do not replace it with a fake
 * control, do not fabricate data"* — **so both rows are drawn, with their
 * copy, and what is true of them is stated in place of a control.**
 *
 * | Design's row | What exists | What is drawn |
 * |---|---|---|
 * | *Surface insights I did not ask for* | `ai_insights` | ✅ a toggle |
 * | *Draft emails and summaries* | `ai_drafts` | ✅ a toggle |
 * | *Write risk flags back to the CRM* | ⛔ **nothing writes to a provider** | *Not available yet* |
 * | *Hide insights below 3 of 5 confidence* | `confidence_floor`, **min 3** | *Always on* |
 *
 * **The third:** 📁 every provider scope in `lib/integrations/providers.ts` is
 * read-only, and that file records why — *"a write scope here would make the
 * connect screen's central sentence false."* ⚡ **The sentence is on this very
 * screen**: *"Signora is read-only until you say otherwise."* ⛔ **Storing a
 * `true` would record permission for something nothing can do**, which is
 * worse than absent: it is consent collected under a false premise.
 *
 * **The fourth:** 📁 `MIN_CONFIDENCE_FLOOR = 3`, so the floor is **always** at
 * least 3 of 5. ⛔ **A toggle whose off state is unrepresentable is a control
 * that silently does nothing** — [B-255](../../../../docs/BUGS.md) — and its
 * *on* position is not a choice anybody made. ✅ **Saying *always on* is the
 * same fact without the false affordance.**
 */
export function ConnectForm() {
  const { exit } = useOnboardingExit();
  const { run, workspaceId, error, isLoading, isSaving, save } = useOnboarding();
  const integrations = useIntegrations(workspaceId);
  const preferences = usePreferences(workspaceId);
  const changePreference = useChangePreferences(workspaceId);
  const [connecting, setConnecting] = useState<string | null>(null);

  if (isLoading) return <OnboardingSkeleton />;

  const finish = async () => {
    await save((id) => finishOnboarding(id));
    exit();
  };

  return (
    <OnboardingShell
      // ⛔ **No rail.** 📁 The design draws this screen as one plane.
      rail={null}
      title="Connect your data"
      // ⚠️ **The design writes *"land in a workspace with sample data"*** and
      // 📁 [ADR-0034](../../../../docs/architecture/adr/0034-ubiquitous-language.md)
      // keeps that word off a customer's screen — ⛔ **`vocabulary.test.tsx`
      // refused it, correctly.** ✅ **Dropping the noun rather than translating
      // it**: *Organization* would be accurate and clumsy, and the sentence
      // does not need a noun at all.
      description="Signora is read-only until you say otherwise. You can connect now, or skip and start with sample data until you're ready."
      actions={
        <>
          <button
            type="button"
            onClick={finish}
            disabled={isSaving}
            className="inline-flex h-control-md items-center rounded-md bg-accent px-[18px] text-[13.5px] font-semibold text-accent-contrast shadow-sm transition-colors hover:bg-accent-hover disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            {isSaving ? 'Finishing…' : 'Connect and finish'}
          </button>
          <button
            type="button"
            onClick={finish}
            className="text-[13px] font-semibold text-content-subtle hover:text-content focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            {/* 📁 The design's words. ⚠️ **And they are true**: the Playground
                is what a skipped workspace lands in. ⛔ A *"Skip"* that
                promised sample data and delivered an empty product would be
                the shape [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md)
                warns about, one screen earlier. */}
            Skip — use sample data
          </button>
        </>
      }
    >
      <Connectors
        systems={integrations.data ?? []}
        failed={integrations.isError}
        loading={integrations.isLoading}
        connecting={connecting}
        onConnect={(slug) => {
          setConnecting(slug);
          // ⚡ **The existing acquisition route, unchanged.** ⛔ A second
          // connect flow for onboarding would be a second thing to keep
          // correct, and this one already carries the state parameter, the
          // callback and every failure outcome.
          window.location.href = `/api/integrations/${slug}/start?return=/onboarding/connect`;
        }}
      />

      <Behaviour
        preferences={preferences.data ?? null}
        onChange={(changes) => changePreference.mutate(changes)}
        saving={changePreference.isPending}
      />

      {error !== null ? (
        <p role="alert" className="mt-4 text-sm text-danger">
          {error}
        </p>
      ) : null}
      {run === null ? null : <span className="sr-only">Setup is saved as you go.</span>}
    </OnboardingShell>
  );
}

/**
 * 📁 **The design's 2×2 of connectors.**
 *
 * ### 🔴 The four it names are not the four that exist
 *
 * 📁 The mock draws **Salesforce · HubSpot · Google Calendar · Gmail**.
 * ⛔ **`lib/integrations/providers.ts` configures two** — HubSpot and Google
 * Calendar — **and Gmail is configured nowhere at all.** ⚡ **So the grid is
 * built from what the server says Signora understands**, and each tile's button
 * comes from that system's own `connectable`.
 *
 * ⛔ **Not a hardcoded four with two dead buttons.** 📁 [B-255](../../../../docs/BUGS.md):
 * *a control that silently does nothing is worse than one that is absent*, and
 * `connect-panel.tsx` already answers this exact question the same way —
 * *"No dead button. The catalog says this cannot be connected yet, and offering
 * a control that does nothing is worse than saying so."*
 *
 * ⚠️ **A failed read is not an empty grid** — [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md),
 * which [C-226](../../../../docs/LANE_COORDINATION.md) found six times on one
 * screen. **Nothing to connect and *we could not ask* are different sentences.**
 */
function Connectors({
  systems,
  failed,
  loading,
  connecting,
  onConnect,
}: {
  systems: readonly IntegrationSystem[];
  failed: boolean;
  loading: boolean;
  connecting: string | null;
  onConnect: (slug: string) => void;
}) {
  if (loading) {
    return (
      <p role="status" className="text-sm text-content-muted">
        Loading what you can connect…
      </p>
    );
  }

  if (failed) {
    return (
      <p role="alert" className="text-sm text-danger">
        We could not read which systems you can connect. You can skip this and connect from
        Settings later — nothing is lost.
      </p>
    );
  }

  if (systems.length === 0) {
    return (
      <p className="text-sm text-content-muted">
        There is nothing to connect yet. Signora will work on the sample data you already have
        until there is.
      </p>
    );
  }

  return (
    // 📁 *"grid-template-columns:1fr 1fr; gap:12px"*.
    //
    // ⚠️ **What can be connected leads.** 📁 The design draws four tiles and
    // this renders however many the server understands — ⛔ **it is not a
    // hardcoded four** — so the ones a person can act on must not sit below the
    // ones they cannot. ✅ **Stable within each group**, so the grid does not
    // reshuffle as a connection lands.
    <div className="grid gap-3 smalllaptop:grid-cols-2">
      {[...systems]
        .sort((a, b) => Number(b.connectable) - Number(a.connectable))
        .map((system) => (
        <Connector
          key={system.integration}
          system={system}
          busy={connecting === system.integration}
          onConnect={() => onConnect(system.integration)}
        />
      ))}
    </div>
  );
}

/** 📁 *"padding:15px 16px; border-radius:12px"*, a 30px initial tile, the name,
 *  what it gives, and the action on the right. */
function Connector({
  system,
  busy,
  onConnect,
}: {
  system: IntegrationSystem;
  busy: boolean;
  onConnect: () => void;
}) {
  const name = systemName(system.integration);

  return (
    <div
      className={cn(
        'flex items-center gap-3 rounded-lg border px-4 py-[15px]',
        system.working ? 'border-accent/40 bg-accent-subtle' : 'border-border-soft bg-surface',
      )}
    >
      {/* 📁 The design's 30px `--sunken` square with the system's initials.
          ♿ `aria-hidden` — the name is right beside it. */}
      <span
        aria-hidden
        className="grid h-[30px] w-[30px] flex-none place-items-center rounded-md bg-surface-sunken text-2xs font-bold text-content-muted"
      >
        {initials(name)}
      </span>
      <div className="min-w-0">
        <p className="truncate text-[13px] font-semibold text-content">{name}</p>
        {/* 📁 The design's second line is *"Read-only · 3 objects"*. ⚡ **This
            says what the connection GIVES instead**, which is the rule
            `connection-center.tsx` already establishes and the reason
            `CAPABILITY_VALUE` is exported: *"Salesforce · Connected tells an
            administrator nothing they can act on."* ⛔ **And an object count
            would be a number nothing here measures.** */}
        <p className="mt-0.5 text-[11.5px] leading-[1.4] text-content-subtle">
          {system.capabilities.length === 0
            ? 'Read-only'
            : `Read-only · ${CAPABILITY_VALUE[system.capabilities[0]!].toLowerCase()}`}
        </p>
      </div>
      <div className="ml-auto flex-none">
        {system.working ? (
          // ✅ Already connected — **the tile reports rather than offers.**
          <span className="text-xs font-semibold text-accent">Connected</span>
        ) : system.connectable ? (
          <button
            type="button"
            onClick={onConnect}
            disabled={busy}
            className="inline-flex h-[30px] items-center rounded-md border border-border bg-surface px-3 text-xs font-semibold text-content transition-colors hover:border-accent hover:text-accent disabled:opacity-40 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
          >
            {busy ? 'Opening…' : 'Connect'}
          </button>
        ) : (
          // ⛔ **No dead button**, and the reason is said rather than implied.
          <span className="text-xs font-semibold text-content-subtle">Not available yet</span>
        )}
      </div>
    </div>
  );
}

/** Two letters, so *Google Calendar* reads `GC` exactly as the design draws it. */
function initials(name: string): string {
  const words = name.split(/\s+/).filter(Boolean);
  return (words.length === 1 ? name.slice(0, 2) : words.slice(0, 2).map((w) => w[0]).join(''))
    .toUpperCase();
}

/**
 * 📁 **"How Signora should behave"** — the design's second half, below a
 * hairline.
 *
 * ⚠️ **Read the file docstring for why two of the four rows carry a stated
 * truth instead of a switch.** Both are drawn.
 */
function Behaviour({
  preferences,
  onChange,
  saving,
}: {
  preferences: PersonPreferences | null;
  onChange: (changes: Partial<PersonPreferences>) => void;
  saving: boolean;
}) {
  return (
    // 📁 *"margin-top:24px; padding-top:22px; border-top:1px solid --line-soft"*.
    <section className="mt-6 border-t border-border-soft pt-[22px]">
      <div className="flex items-center gap-[9px]">
        <span aria-hidden className="grid h-[22px] w-[22px] flex-none place-items-center rounded-sm bg-ai">
          <svg
            width="12"
            height="12"
            viewBox="0 0 16 16"
            fill="none"
            stroke="currentColor"
            strokeWidth="1.7"
            strokeLinecap="round"
            className="text-accent-contrast"
          >
            <path d="M8 2v2.5M8 11.5V14M2 8h2.5M11.5 8H14M4 4l1.8 1.8M10.2 10.2 12 12" />
          </svg>
        </span>
        {/* 📁 *"font-size:15px; font-weight:600; letter-spacing:-0.016em"*. */}
        <h2 className="text-md font-semibold tracking-[-0.016em] text-content">
          How Signora should behave
        </h2>
      </div>

      <div className="mt-4 flex flex-col">
        <Row
          title="Surface insights I did not ask for"
          detail="Ranked findings on your home page. Off means Signora only answers questions."
        >
          {preferences === null ? (
            <Unknown />
          ) : (
            <Switch
              label="Surface insights I did not ask for"
              on={preferences.ai_insights}
              disabled={saving}
              onToggle={(on) => onChange({ ai_insights: on })}
            />
          )}
        </Row>

        <Row
          title="Draft emails and summaries"
          detail="Drafts only. Nothing sends without your approval, ever."
        >
          {preferences === null ? (
            <Unknown />
          ) : (
            <Switch
              label="Draft emails and summaries"
              on={preferences.ai_drafts}
              disabled={saving}
              onToggle={(on) => onChange({ ai_drafts: on })}
            />
          )}
        </Row>

        <Row
          title="Write risk flags back to the CRM"
          detail="Signora only reads from the systems you connect. Nothing writes back yet, so there is nothing to permit."
        >
          {/* ⛔ **A stated absence, not a switch off.** An unchecked toggle
              would say *you could turn this on* — 📁 and no provider scope in
              this product can carry it. */}
          <Fixed>Not available yet</Fixed>
        </Row>

        <Row
          title="Hide insights below 3 of 5 confidence"
          detail="Fewer, stronger findings. You can raise the bar per view later in Settings."
        >
          {/* 📁 `MIN_CONFIDENCE_FLOOR = 3` — ⛔ **the floor cannot go below it**,
              so this is a fact rather than a preference. */}
          <Fixed>Always on</Fixed>
        </Row>
      </div>
    </section>
  );
}

/** 📁 *"padding:13px 0; border-bottom:1px solid --line-soft; gap:14px"*. */
function Row({
  title,
  detail,
  children,
}: {
  title: string;
  detail: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-[14px] border-b border-border-soft py-[13px]">
      <div className="min-w-0 flex-1">
        <p className="text-[13px] font-semibold text-content">{title}</p>
        <p className="mt-[3px] text-xs leading-[1.5] text-content-muted">{detail}</p>
      </div>
      <div className="flex-none pt-0.5">{children}</div>
    </div>
  );
}

/**
 * 📁 **The design's 38×22 track with an 18px knob.**
 *
 * ♿ **`role="switch"` on a real button**, so it is reachable, operable by
 * Space and Enter, and announced with its state — ⛔ **which a styled `div`
 * would not be**, and the design names 2.1.1 by number.
 */
function Switch({
  label,
  on,
  disabled,
  onToggle,
}: {
  label: string;
  on: boolean;
  disabled: boolean;
  onToggle: (on: boolean) => void;
}) {
  return (
    <button
      type="button"
      role="switch"
      aria-checked={on}
      aria-label={label}
      disabled={disabled}
      onClick={() => onToggle(!on)}
      className={cn(
        'flex h-[22px] w-[38px] items-center rounded-full p-0.5 transition-colors',
        'disabled:opacity-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent',
        on ? 'justify-end bg-accent' : 'justify-start bg-surface-sunken shadow-[inset_0_0_0_1px_rgb(var(--color-border))]',
      )}
    >
      <span aria-hidden className="h-[18px] w-[18px] rounded-full bg-surface shadow-sm" />
    </button>
  );
}

/** ⛔ **Not a toggle in an off position.** A fixed fact about the product. */
function Fixed({ children }: { children: React.ReactNode }) {
  return (
    <span className="inline-flex items-center rounded-xs bg-surface-sunken px-2 py-0.5 text-2xs font-semibold text-content-subtle">
      {children}
    </span>
  );
}

/** ⚠️ **The preferences read failed or has not landed.** ⛔ **A switch drawn
 *  off would claim the person had declined** — [P-A](../../../../docs/DOMAIN_DISCOVERY_REGISTER.md):
 *  a failed read must never render as an answer. */
function Unknown() {
  return (
    <span role="status" className="text-2xs font-semibold text-content-subtle">
      Loading…
    </span>
  );
}
