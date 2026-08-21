'use client';

import Link from 'next/link';

import {
  AccountOwner,
  UnassignedOwner,
  type AccountOwnerProps,
} from '@/components/accounts/account-owner';
import {
  AccountSegments,
  type AccountSegmentsProps,
} from '@/components/accounts/account-segments';
import { NothingSaid, StageBadge } from '@/components/accounts/account-commercial';
import { AccountTags } from '@/components/accounts/account-tags';
import { formatDay } from '@/components/intelligence/dates';
import { Drawer } from '@/components/ui';
import { formatMoney } from '@/lib/accounts/table';
import type { ListedAccount } from '@/lib/api/types';

/**
 * **The design's context drawer** — 📁 `Fortune Signora Companies.dc.html`,
 * *"Context drawer · row preview"*.
 *
 * ## ⚡ Composed from the shared `Drawer`, never rebuilt
 *
 * 📁 [§20c](../../../../CLAUDE.md): *"compose pages from `components/ui`, never
 * restyle a shared component for one page's benefit."* **The overlay, the
 * backdrop, the focus trap, the escape key and the 420px of Design System v2
 * §12 are all `Drawer`'s** — ⛔ **this file contributes the Companies content
 * and nothing else.**
 *
 * ## 📁 The design's six facts, and why four of them render
 *
 * | Design's fact | Here |
 * |---|---|
 * | **Open ACV** | ✅ [ADR-0409](../../../../docs/architecture/adr/0409-commercial-account-facts.md) |
 * | **Renewal** | ✅ ADR-0409 |
 * | **Owner** | ✅ ADR-0411, joined by the screen |
 * | **Signora score** | ⛔ **No source anywhere.** The one design column with none |
 * | **Last touch** | ⛔ **Not the same fact as *last observed*.** ⚠️ Last touch is an engagement; last observed is when a source last reported. **Relabelling one as the other would be the quietest lie on the panel** |
 * | **Open opportunities** | ⛔ Not read by this screen |
 *
 * ⚡ **The three absent facts are OMITTED rather than dashed**, which is
 * 📁 [`table.ts`](../../../lib/accounts/table.ts)'s law: *"a column of `—` is
 * worse than an absent column when nothing was ever asked."* ✅ **Open ACV,
 * Renewal and Stage DO dash**, because the read path exists and no source has
 * answered — **the distinction the whole commercial slice turns on.**
 *
 * ## ⛔ What is deliberately not drawn
 *
 * **The tab row.** 📁 The design shows four tabs. ⚠️ **Three of the four have no
 * content this screen can fill**, and a tab that opens an empty panel is
 * [B-255](../../../../docs/BUGS.md)'s shape — *a control that silently does
 * nothing is worse than one that is absent.*
 *
 * **The *Recommended next step* block.** 📁 The design tints it `--ai-tint` and
 * offers *Draft intro* and *Evidence*. ⚡ **The read exists** —
 * `GET /workspaces/{id}/accounts/{id}/decision-package`, and it is per-account,
 * which is exactly what this panel is — ⛔ **but no frontend hook consumes it
 * yet.** **Stated here rather than drawn as two buttons that do nothing.**
 */
export function ContextDrawer({
  row,
  open,
  onClose,
  assignment,
  members,
  segments,
  vocabulary,
  tags,
}: {
  row: ListedAccount | null;
  open: boolean;
  onClose: () => void;
  /** ⛔ **The assignment and the roster, not a resolved name.** ⚡ **`AccountOwner`
   * already turns one into the other** — ADR-0411 stores a reference precisely
   * so a name is never duplicated, and resolving it a second time here would
   * be the second representation [§2](../../../../CLAUDE.md) forbids. */
  assignment: AccountOwnerProps['assignment'];
  members: AccountOwnerProps['members'];
  segments: AccountSegmentsProps['membership'];
  /** ⚡ **The vocabulary the membership's ids resolve against** — passed in
   * because the page already read it and a second fetch would be a second
   * answer. */
  vocabulary: AccountSegmentsProps['segments'];
  tags: Parameters<typeof AccountTags>[0]['tags'];
}) {
  return (
    <Drawer
      open={open && row !== null}
      onClose={onClose}
      title={row?.account.name ?? 'This account'}
      // 📁 **The design's eyebrow** — *"Context drawer · row preview"*. ⚡ It
      // says what the panel IS, which is what stops it reading as the record.
      scope="Row preview"
      footer={
        row === null ? null : (
          <div className="flex flex-wrap items-center gap-3">
            {/* 📁 The design's `Navigate` line, verbatim in intent: the drawer
                follows the row rather than replacing it. */}
            <span className="text-2xs text-content-subtle">
              A preview. The record has everything.
            </span>
            <Link
              href={`/accounts/${row.account.account_id}`}
              className="ml-auto text-xs font-semibold text-accent hover:underline "
            >
              Open record
            </Link>
          </div>
        )
      }
    >
      {row === null ? null : (
        <div className="flex flex-col gap-4">
          {/* 📁 **The design's fact list** — *"`k` left in `--ink-3`, `v` right
              at 600 weight with tabular numerals"*. */}
          <dl className="flex flex-col">
            <Fact label="Open ACV" numeric>
              {row.commercial.open_acv === null ? (
                <NothingSaid />
              ) : (
                formatMoney(row.commercial.open_acv)
              )}
            </Fact>
            <Fact label="Renewal" numeric>
              {row.commercial.renewal_date === null ? (
                <NothingSaid />
              ) : (
                formatDay(row.commercial.renewal_date)
              )}
            </Fact>
            <Fact label="Stage">
              {row.commercial.stage === null ? (
                <NothingSaid />
              ) : (
                <StageBadge stage={row.commercial.stage} />
              )}
            </Fact>
            <Fact label="Owner">
              {assignment === undefined ? (
                <UnassignedOwner />
              ) : (
                <AccountOwner assignment={assignment} members={members} />
              )}
            </Fact>
            <Fact label="Sources" numeric>
              {row.account.source_count.toLocaleString()}
            </Fact>
            <Fact label="Last observed" numeric>
              {/* ⚠️ **Not *last touch*.** 📁 The contract's own words: *"not when
                  Signora last looked"* — this is when a source last REPORTED,
                  and the design's *last touch* is an engagement nothing here
                  records. **Labelled as what it is.** */}
              {row.account.last_observed_at === null
                ? 'Never'
                : formatDay(row.account.last_observed_at)}
            </Fact>
          </dl>

          {/* ⛔ **A heading over nothing is worse than no heading.**
              ⚠️ **The first version rendered both labels unconditionally**, and
              the screenshot showed `SEGMENTS` and `TAGS` with empty space under
              them — ⚡ **which reads as a panel that failed to load**, not as an
              account with no groupings.

              ✅ **`AccountSegments` renders nothing for an unread answer** —
              deliberately, so forty rows cannot say *No segment* during a load
              — **so the section follows it rather than announcing it.** */}
          {segments === undefined ? null : (
            <Section label="Segments">
              <AccountSegments membership={segments} segments={vocabulary} />
            </Section>
          )}

          {tags.length === 0 ? null : (
            <Section label="Tags">
              <AccountTags tags={tags} />
            </Section>
          )}
        </div>
      )}
    </Drawer>
  );
}

/** ⚡ A titled block, rendered only where it has something to title. */
function Section({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex flex-col gap-2 border-t border-border-soft pt-4">
      <p className="text-2xs font-semibold uppercase tracking-wide text-content-subtle">
        {label}
      </p>
      {children}
    </div>
  );
}

/** 📁 One row of the design's fact list. */
function Fact({
  label,
  numeric = false,
  children,
}: {
  label: string;
  numeric?: boolean;
  children: React.ReactNode;
}) {
  return (
    <div className="flex items-baseline justify-between gap-3 py-1.5 text-sm">
      <dt className="text-content-subtle">{label}</dt>
      <dd
        className={
          numeric
            ? 'font-semibold tabular-nums text-content'
            : 'font-semibold text-content'
        }
      >
        {children}
      </dd>
    </div>
  );
}
