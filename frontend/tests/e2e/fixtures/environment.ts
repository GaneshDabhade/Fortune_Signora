/**
 * Which environment this suite is allowed to drive, and why it refuses.
 *
 * ## The hazard this removes
 *
 * `playwright.config.ts` defaulted `SIGNORA_APP_URL` to `http://localhost:3000`
 * — **the Human Review stack, which belongs to the product owner and to no
 * lane** (`docs/RUNNING.md` § Running a lane). Running `npm run test:e2e` with
 * no environment variable therefore drove the product owner's review
 * environment.
 *
 * That was survivable while the suite only *read*. It stopped being survivable
 * the moment it started **writing**: this suite adds products, watches
 * companies, and records **permanent, attributed decisions** against accounts.
 * A reviewer opening the demo would have found decisions they never made,
 * signed with a persona's name.
 *
 * **This is the cycle-25 class of incident** — one operation quietly mutating
 * an environment another operation owned — and [`RELEASE_ENGINEERING.md`](../../../docs/RELEASE_ENGINEERING.md)
 * §7 is explicit about the lesson: the answer is *prevention*, not detection.
 * `release-preflight.py` reports a held review port and asks the operator to
 * look; this refuses to start.
 *
 * ## Why a hard refusal rather than a warning
 *
 * A warning is read once and then filtered out. A refusal cannot be. It is the
 * same reasoning `demo-users.ts` applies to a published password — *"a startup
 * failure, not a runtime check, because the failure mode of getting it wrong is
 * silent."*
 *
 * ## What it deliberately does not do
 *
 * It does not allocate a port, choose a database, or start anything. **The
 * allocation already exists** and `RUNNING.md` is authoritative for it; a
 * second scheme here would be the parallel environment model the repository has
 * twice declined to build (RE-05, deprioritised 2026-08-03).
 */

import { existsSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

/** Ports that belong to Human Review on `main`, and to no lane. */
const REVIEW_PORTS = new Set(['3000', '8000']);

/** The deliberate escape hatch, for the one legitimate case: the product owner
 * demonstrating the product on their own stack, on purpose. Never set it in a
 * script. */
const OVERRIDE = 'SIGNORA_E2E_ALLOW_REVIEW_PORTS';

export function resolveAppUrl(): string {
  const configured = process.env.SIGNORA_APP_URL;

  if (!configured) {
    throw new Error(
      [
        '',
        '  SIGNORA_APP_URL is not set, and this suite has no safe default.',
        '',
        '  It used to default to http://localhost:3000 — the Human Review stack,',
        '  which belongs to the product owner and to no lane. This suite writes:',
        '  it adds products, watches companies, and records permanent decisions',
        '  against accounts. A reviewer would have found decisions nobody made.',
        '',
        '  Set it to your own row in docs/RUNNING.md § Running a lane:',
        '',
        '    SIGNORA_APP_URL=http://localhost:3400 npm run test:e2e     # Lane B',
        '',
      ].join('\n'),
    );
  }

  const port = new URL(configured).port;
  if (REVIEW_PORTS.has(port) && process.env[OVERRIDE] !== '1') {
    throw new Error(
      [
        '',
        `  REFUSING to drive ${configured}.`,
        '',
        '  Ports 3000 and 8000 are Human Review on `main` (docs/RUNNING.md).',
        '  This suite writes to whatever it is pointed at, so a run here would',
        '  put products, watched companies and permanent decisions into the',
        '  environment the product owner reviews the product in.',
        '',
        '  Use your lane\'s ports. If you genuinely mean to demonstrate the',
        `  product on the review stack, set ${OVERRIDE}=1 and know why.`,
        '',
      ].join('\n'),
    );
  }

  return configured;
}

/**
 * **The browser's system libraries, when they were installed without root.**
 *
 * `npx playwright install-deps` needs sudo, which a lane does not have, so on
 * this workstation the shared objects Chromium links against live unpacked
 * under `~/.cache/ms-playwright-deps/lib` rather than in the system paths.
 *
 * ### Why this belongs in the repository rather than in a shell
 *
 * It was working, and nothing here made it work: **`LD_LIBRARY_PATH` happened
 * to be exported in one terminal.** The same suite that passed 119/119 in that
 * terminal could not launch a browser at all in another, and the failure is
 * `browserType.launch` on every test — which reads like a broken suite and is
 * a missing environment variable.
 *
 * **That is a hidden input, and hidden inputs are architecture defects**
 * (`CLAUDE.md` §2): the same declared inputs produced different results
 * depending on something outside the declared contract. The fix is not to
 * document the variable — it is to stop needing anybody to know it.
 *
 * Adds the directory when it exists and changes nothing when it does not, so a
 * machine with the libraries properly installed is unaffected. **It remains a
 * property of one workstation rather than of the repository** ([B-011](../../../../docs/BUGS.md)'s
 * distinction: a workstation gap is never a repository defect) — what the
 * repository owns is not *depending on somebody's shell*.
 */
export function browserEnvironment(): NodeJS.ProcessEnv | undefined {
  const root =
    process.env.PLAYWRIGHT_BROWSERS_PATH ?? join(homedir(), '.cache', 'ms-playwright');
  const lib = `${root}-deps/lib`;
  if (!existsSync(lib)) return undefined;
  return {
    ...process.env,
    LD_LIBRARY_PATH: [lib, process.env.LD_LIBRARY_PATH].filter(Boolean).join(':'),
  };
}

/**
 * **Which mode a run is watched in** — [TASK-476](../../../../docs/BACKLOG.md).
 *
 * ## The defect this closes is a sentence, not a bug
 *
 * `CLAUDE.md` §19 says ***"Headed is the default mode for local development and
 * review"*** and the config read `headless: process.env.HEADED !== '1'` —
 * **headless by default, headed on opt-in.** The file said one thing and the
 * repository did the other, which is §2's damaging direction: **a rule a lane
 * reads and believes.** §19 flags it against itself and names this row.
 *
 * ## Why the default is inverted rather than the sentence deleted
 *
 * [D-134](../../../../docs/DECISION_REGISTER.md) makes a headed run a **handover
 * gate**, and its purpose is not verification — *"the assertions already did
 * that"* — it is **continuous product review**. Transitions, empty states,
 * error states and loading states are what a lane is meant to *see*.
 * **A gate whose default is the opposite of the rule is a gate every lane has
 * to remember to opt into**, and a gate kept by memory is not a gate.
 *
 * ## The two flags, and why `HEADED` wins when both are set
 *
 * | | |
 * |---|---|
 * | `HEADED=1` | **Watch it, at a human pace.** Adds `slowMo` |
 * | `HEADLESS=1` · `HEADED=0` | **Do not open a window.** The opt-out for an unattended run |
 * | *neither* | **Headed, at full speed** — the new default |
 *
 * ⚠️ **`HEADED=1` beats `HEADLESS=1`, deliberately.** `HEADLESS` describes an
 * *environment* and is the kind of thing a shell exports and forgets;
 * **`HEADED=1` is an intent, and it is on the command that carries it** —
 * `make product-demo`. **A demonstration that silently ran headless would lose
 * the only thing it exists for**, and nobody would notice until the day it was
 * put in front of somebody.
 *
 * ## `slowMo` follows the intent, not the default
 *
 * ⛔ **The row says `slowMo` *"already rides on the same flag and should follow
 * it"*, and following it literally would put 250ms on every action of every
 * local run** — turning a six-minute suite into a gate nobody can afford,
 * which is the failure `make endurance` is deliberately kept out of `make e2e`
 * to avoid. **So it follows the *explicit* `HEADED=1`**: *visible while it runs*
 * and *watchable at a human pace* are two different products, and only the
 * second is worth four times the wall clock.
 *
 * ## What it deliberately does not do
 *
 * ⛔ **It does not look at `DISPLAY`, `CI`, or `SIGNORA_ENVIRONMENT`.** The row
 * is explicit: **certification runs on the same machine as development**
 * (§20c-2 — *the correct quantity of CI is zero*), so a deployment or
 * environment variable cannot separate them, and **the distinction is which
 * command was run, not where.** ⚠️ **A `DISPLAY` probe would also be a hidden
 * input** — the same command producing different behaviour from something
 * outside the declared contract, which is the defect `browserEnvironment()`
 * above exists to remove rather than one to add beside it.
 *
 * ⚠️ **Measured before it was written, because the row feared the opposite:**
 * `make certify` runs `backend/tests/certification`, which shells out to `tsc`
 * and **never invokes Playwright.** **No certification path reads this
 * function today**, so inverting the default cannot slow a gate. The opt-out
 * exists for the unattended run that will want it, not for one that exists.
 */
export interface RunMode {
  headed: boolean;
  /** `undefined` rather than `0` — Playwright treats the key's absence as off. */
  slowMo: number | undefined;
  /** Which rule decided, so a test can pin the precedence rather than the result. */
  reason: string;
}

/** The demonstration's pace, unchanged from when it rode directly on `HEADED`. */
export const DEMONSTRATION_SLOW_MO = 250;

/**
 * ⚠️ **Not `NodeJS.ProcessEnv`, and `tsc` is what said so.** This repository
 * augments that type to REQUIRE `NODE_ENV`, so every test case would have had
 * to carry a variable this function never reads. ⚡ **The narrower type is also
 * the truer one**: the whole contract is *two names, looked up in a string map*.
 */
export type RunModeEnvironment = Readonly<Record<string, string | undefined>>;

export function resolveRunMode(env: RunModeEnvironment = process.env): RunMode {
  if (env.HEADED === '1') {
    return { headed: true, slowMo: DEMONSTRATION_SLOW_MO, reason: 'HEADED=1 — watch it' };
  }
  if (env.HEADLESS === '1' || env.HEADED === '0') {
    return { headed: false, slowMo: undefined, reason: 'opted out of a window' };
  }
  return { headed: true, slowMo: undefined, reason: 'the default: headed, full speed' };
}
