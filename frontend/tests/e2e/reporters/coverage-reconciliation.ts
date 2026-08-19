/**
 * 🔴 **[B-1027](../../../../docs/BUGS.md) — a run that stops counting the tests
 * it did not run, while every number it prints stays individually true.**
 *
 * ```
 * --list      Total: 393 tests in 53 files
 * the run     363 passed · 17 failed · 5 skipped   =  385
 *                                                     ────
 *                                     8 tests never ran, and nothing said so
 * ```
 *
 * ⚡ **`test.describe.configure({ mode: 'serial' })` abandons the rest of its
 * block when a test fails, and counts the abandoned tests as NEITHER failed
 * NOR skipped.** ⛔ **So nothing distinguished *"eight tests failed to run"*
 * from *"eight tests were not there"*, and the exit code was already non-zero
 * for other reasons.
 *
 * ⛔ **And it hides most where it hurts most**: a serial block abandons its
 * tail precisely on the runs where something is wrong.
 *
 * ## ✅ What this does, and what it deliberately does not
 *
 * **It compares what Playwright ENUMERATED against what reported an outcome,
 * and fails the run when they differ, naming every test that never ran.**
 *
 * ⛔ **It does not change what `mode: 'serial'` means.** 📁 That is a decision
 * about the spec that declares it, not a repair, and [B-1027](../../../../docs/BUGS.md)
 * says so. **This makes the cap visible; it does not remove it** — 📁 the
 * repository's own rule: *"if a workflow bounds coverage, log what was
 * dropped — silent truncation reads as 'covered everything' when it didn't."*
 */
import type { FullResult, Reporter, Suite, TestCase } from '@playwright/test/reporter';

export class CoverageReconciliation implements Reporter {
  private root: Suite | undefined;
  /** ⚡ **By id, because a retry reports the same `TestCase` more than once.** */
  private readonly reported = new Set<string>();

  onBegin(_config: unknown, suite: Suite): void {
    this.root = suite;
  }

  onTestEnd(test: TestCase): void {
    this.reported.add(test.id);
  }

  // ⚠️ **`async` because `Reporter.onEnd` returns `void | Promise<…>`** — a
  // synchronous object is not one of its return types, and `tsc` says so.
  async onEnd(result: FullResult): Promise<{ status?: FullResult['status'] } | undefined> {
    const enumerated = this.root?.allTests() ?? [];
    const unrun = enumerated.filter((test) => !this.reported.has(test.id));
    if (unrun.length === 0) {
      return undefined;
    }

    process.stdout.write(
      `\n  ${unrun.length} of ${enumerated.length} enumerated tests never ran and were counted as ` +
        `neither failed nor skipped (B-1027):\n` +
        unrun.map((test) => `    ${test.titlePath().filter(Boolean).join(' › ')}\n`).join('') +
        '\n',
    );

    // ⚠️ **An interrupted run is already saying it did not finish** — a
    // `--max-failures` stop or a Ctrl-C. ⛔ **Reported, never re-failed**: the
    // tests that did not run there are the ones the operator asked to skip.
    return result.status === 'interrupted' ? undefined : { status: 'failed' };
  }
}

export default CoverageReconciliation;
