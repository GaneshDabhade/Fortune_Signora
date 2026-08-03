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
