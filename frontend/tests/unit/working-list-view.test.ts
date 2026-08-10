/**
 * **A saved view the working list can and cannot open** —
 * [TASK-452](../../../docs/BACKLOG.md), on
 * [455 §4](../../../docs/architecture/455-context-definitions-r02-r03.md).
 *
 * 🔴 **The store never validates a declaration** — *"never parses, validates,
 * executes, ranks or optimises… never knows what a filter or a sort means"* —
 * ⚡ **so this module is the only thing that can refuse one, and these are the
 * refusals.**
 */
import { describe, expect, it } from 'vitest';

import {
  WORKING_LIST_DECLARATION_VERSION,
  apply,
  declare,
  describe as describeView,
  whyNotApplicable,
} from '@/lib/views/working-list';

const current = () =>
  declare(new URLSearchParams('owner=mine&raises=renewal&by=stage'));

describe('⚡ what the list saves is what the person is looking at', () => {
  it('📁 reads the URL, because that is where this screen keeps its three', () => {
    expect(current()).toEqual({
      kind: 'working-list',
      version: WORKING_LIST_DECLARATION_VERSION,
      owner: 'mine',
      raises: 'renewal',
      by: 'stage',
    });
  });

  it('⛔ an empty list is a legitimate declaration, not an absent one', () => {
    // ⚡ *"All accounts, not narrowed"* is a view somebody may genuinely want
    // to save and return to.
    expect(declare(new URLSearchParams())).toEqual({
      kind: 'working-list',
      version: WORKING_LIST_DECLARATION_VERSION,
      owner: 'all',
      raises: null,
      by: null,
    });
  });

  it('⚡ a round trip returns the same list', () => {
    const query = apply(current());
    expect(query).toBe('?owner=mine&raises=renewal&by=stage');
    expect(declare(new URLSearchParams(query as string))).toEqual(current());
  });

  it('⛔ a default is not written into the URL', () => {
    // ⚡ A URL carrying every default is one nobody can read at a glance, and
    // `scopeFrom` already answers `all` for a missing value.
    expect(apply(declare(new URLSearchParams()))).toBe('');
  });
});

describe('🔴 a declaration this screen cannot read is REFUSED, never approximated', () => {
  it("⛔ another screen's view is not opened on this one", () => {
    /**
     * ⚡ **The commonest real case, and it is not an error.** 📁 The store is
     * workspace-wide and 455 names four consumers, **so a Reports view and a
     * working-list view sit in the same list** — ⛔ **and opening one on the
     * other would silently show the wrong records.**
     */
    const reportsView = { kind: 'report', version: 1, columns: ['arr'] };

    expect(whyNotApplicable(reportsView)).toMatch(/different screen/);
    expect(apply(reportsView)).toBeNull();
  });

  it('⛔ a view from a newer Signora is refused rather than partly applied', () => {
    /**
     * 🔴 **Partly applying is the worst outcome**: the customer gets a list
     * that is neither what they saved nor what they asked for, **and nothing
     * says so.**
     */
    const future = { ...current(), version: WORKING_LIST_DECLARATION_VERSION + 1 };

    expect(whyNotApplicable(future)).toMatch(/newer version/);
    expect(apply(future)).toBeNull();
  });

  it('⛔ and anything that is not a declaration at all', () => {
    for (const junk of [null, 'a string', 42, []]) {
      expect(whyNotApplicable(junk), String(junk)).not.toBeNull();
      expect(apply(junk)).toBeNull();
    }
  });

  it('✅ but a declaration this screen DOES understand is applied', () => {
    // ⚡ **The discriminating case.** Four refusal tests all pass against a
    // function that refuses everything.
    expect(whyNotApplicable(current())).toBeNull();
    expect(apply(current())).toBe('?owner=mine&raises=renewal&by=stage');
  });

  it('⚡ an OLDER version stays readable, because adding a filter breaks nothing', () => {
    /**
     * ⛔ **The version is bumped only when an old declaration would be
     * MISREAD** — not when a filter is added. **A missing key means *not
     * narrowed*, which is what those views meant when they were written.**
     */
    const old = { kind: 'working-list', version: 1, owner: 'mine', raises: null, by: null };
    expect(whyNotApplicable(old)).toBeNull();
    expect(apply(old)).toBe('?owner=mine');
  });
});

describe('📁 a view nobody named still says what it is', () => {
  it('⛔ never "Untitled" — the default describes the filters', () => {
    // ⚡ Somebody scanning a list of views has to tell them apart.
    expect(describeView(current())).toBe('My accounts · raising renewal · by stage');
    expect(describeView(declare(new URLSearchParams()))).toBe('All accounts');
    expect(describeView(declare(new URLSearchParams('owner=unassigned')))).toBe(
      'Unassigned accounts',
    );
  });
});
