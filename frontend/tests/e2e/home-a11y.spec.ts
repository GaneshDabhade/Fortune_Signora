import { expect, test } from './fixtures/signora';

/**
 * **Home's accessibility table** — 📁 `Fortune Signora Home.dc.html` §11, and the
 * keyboard table in §10.
 *
 * ## ⛔ Why these are browser assertions
 *
 * ⚡ **Every one is about the rendered document**: how many landmarks exist, what
 * order the headings come in, where focus lands, what Tab reaches next. 📁 A
 * component test renders one card in isolation and **cannot see the page these
 * criteria are about** — `1.3.1` is a statement about the whole `<main>`.
 */

async function openHome(page: import('@playwright/test').Page) {
  await page.goto('/');
  await page.waitForURL(/\/w\/[0-9a-f-]{36}\/home$/, { timeout: 30_000 });
  await expect(page.locator('[data-card]').first()).toBeVisible({ timeout: 30_000 });
  // The reads settle before structure is measured; a skeleton is not the card.
  await page.waitForLoadState('networkidle');
}

/**
 * 🔴 **The same page, composed the other way** — 📁 the activation composition,
 * which **no structural check had ever covered.**
 *
 * ⚠️ **Every assertion below this line used to run against whichever composition
 * the seeded persona resolved to**, and that is `seller` on the Playground. ⛔
 * **Activation renders entirely different components** — three step cards, a
 * progress line, a footer — and `1.3.1` and `2.5.8` are claims about *"Home"*,
 * not about one composition's cards.
 *
 * ⚡ **Nothing connected is the real entry condition**, so it is stubbed at the
 * production read boundary rather than by reaching past it: 📁 the design
 * resolves activation from *"a working capability"*, and an empty systems list
 * is exactly what a workspace that has connected nothing returns.
 */
async function openActivationHome(page: import('@playwright/test').Page) {
  await page.route('**/api/proxy/**/integrations', (route) =>
    route.fulfill({ status: 200, contentType: 'application/json', body: '[]' }),
  );
  await openHome(page);
  await expect(
    page.getByTestId('home'),
    'the integrations stub did not produce the activation composition',
  ).toHaveAttribute('data-composition', 'activation');
}

/**
 * 🔴 **A Home that HAS recents — B-1033, and the reason the suite was 14/14
 * green while `card.recents` failed `2.5.8`.**
 *
 * ⚠️ **The Playground's `recently_viewed` is empty**, so the card renders one
 * line of prose and **no rows**. ⛔ **`2.5.8` then measured whatever happened to
 * be on the page** — it is not a vacuous guard, it asserts `measured.length > 0`
 * and did find controls — **it is a coverage gap: the offending targets only
 * exist when there is data.** ⚡ **Same shape as the rail-band finding one file
 * over**: an assertion that cannot distinguish *the rule holds* from *the case
 * never arose*.
 *
 * ## ⛔ Stubbed at the read boundary, with the workspace's own accounts
 *
 * ⚡ **Not written into the database**, which would leave every other spec
 * measuring a different Home depending on what ran first — the flake
 * `search-journey.spec.ts` already paid for once. **Not fabricated ids
 * either**: 📁 the card resolves names from the identity surface, so invented
 * ids would render five *"Unnamed account"* fallbacks and the geometry would be
 * measured against a state the product only reaches when something is wrong.
 *
 * ✅ **Five real accounts, read from the list**, returned by the one endpoint
 * the card reads — which is exactly what the server returns for somebody who
 * opened five records.
 */
async function openHomeWithRecents(page: import('@playwright/test').Page) {
  await page.goto('/accounts');
  const rows = page.locator('main a[href^="/accounts/"]');
  await expect(rows.first()).toBeVisible({ timeout: 20_000 });

  /**
   * ⚠️ **Named accounts only, and that is not fastidiousness.** ⛔ The Playground
   * holds accounts **no source has named** — 📁 the card renders those as
   * *"Unnamed account"*, which is a legitimate state and **not the one Home
   * normally shows.** ⚡ The filter is `search-journey.spec.ts`'s, for the same
   * reason it has one.
   */
  const listed = await rows.evaluateAll((els) =>
    els.map((el) => ({
      id: (el.getAttribute('href') ?? '').split('/').pop() ?? '',
      name: ((el.textContent ?? '').trim().split('\n')[0] ?? '').trim(),
    })),
  );
  const opened = listed
    .filter((row) => /^[0-9a-f]{8}-[0-9a-f-]{27}$/.test(row.id))
    .filter((row) => /^[A-Za-z][A-Za-z' ]{4,}$/.test(row.name))
    .slice(0, 5)
    .map((row) => row.id);
  // 📁 *"Last five records touched"* — ⛔ **fewer would measure a shorter list
  // than the design's**, and the separation defect is between adjacent rows.
  expect(opened.length, 'this workspace has fewer than five named accounts to have opened').toBe(5);

  // ⚡ **An hour apart**, so the right-hand column reads `Today` rather than
  // five identical strings — the row's width varies with it.
  const now = Date.now();
  await page.route('**/api/proxy/**/recently-viewed', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/json',
      body: JSON.stringify(
        opened.map((id, index) => ({
          entity_id: id,
          kind: 'account',
          viewed_at: new Date(now - index * 3_600_000).toISOString(),
        })),
      ),
    }),
  );

  await openHome(page);
  // ⛔ **The guard that stops this gap reopening.** ⚠️ Without it, a change that
  // silently emptied the card would turn every assertion below back into a
  // question nobody asked.
  const card = page.getByTestId('home-recents');
  await expect(
    card.locator('a[href^="/accounts/"]'),
    'the recents card rendered no rows, so nothing below this measured one',
  ).toHaveCount(5);
  /**
   * ⚠️ **The names arrive after the rows do**, and this waits for them. 📁 The
   * card resolves names from the identity surface in a second read, so for a
   * frame every row reads *"Unnamed account"* — ⛔ **measuring there would
   * measure a card mid-load**, which is the same class of error as measuring
   * one with no rows at all.
   */
  await expect(
    card.getByText('Unnamed account'),
    'the recents card is still resolving names, so it was measured mid-load',
  ).toHaveCount(0);
}

/**
 * 📁 **`1.3.1`'s structural claims, as one measurement** — *"each card is a
 * `<section>` with its own h2"* — so the two compositions assert the same thing
 * rather than drifting into two nearly-identical copies (§2).
 */
async function expectCardStructure(page: import('@playwright/test').Page) {
  const cards = page.locator('[data-card]');
  const count = await cards.count();
  expect(count, 'no cards rendered').toBeGreaterThan(0);

  for (let index = 0; index < count; index += 1) {
    const card = cards.nth(index);
    const id = await card.getAttribute('data-card');
    // ⛔ **The card's own element IS the section.**
    expect(await card.evaluate((el) => el.tagName), `${id} is not a section`).toBe('SECTION');
    // 🔴 **And it contains no second one.** ⚠️ Several cards rendered their own
    // `<section>` inside Home's, which made two nested landmarks per card and
    // left the outer one carrying the name.
    expect(await card.locator('section').count(), `${id} nests a second section`).toBe(0);
    // 🔴 **`h2`, not `h3`.** ⛔ Under the page's `h1`, a card heading at `h3`
    // skips a level — `1.3.1`'s own defect, and what several cards did.
    //
    // ⚠️ **A card showing its error or forbidden panel has no h2 of its own** —
    // 📁 `SystemState` renders a region title as a `<p>` deliberately, *"the
    // ARIA dialog role carries an expectation this panel does not meet"* being
    // the same instinct. **Those cards are named by the section instead.**
    const headings = await card
      .locator('h1, h2, h3, h4, h5, h6')
      .evaluateAll((els) => els.map((el) => el.tagName));
    for (const tag of headings) {
      expect(tag, `${id} has a ${tag} where the design says h2`).toBe('H2');
    }
  }
}

test.describe('📁 1.3.1 — one main, one h1, and a section per card', () => {
  /**
   * 📁 *"Home is one `<main>` with an **h1 naming the workspace**. Each card is a
   * `<section>` with its own **h2** in DOM order matching visual order at every
   * breakpoint."*
   */
  test('@a11y every card is one section, with one h2, under one h1', async ({ page }) => {
    await openHome(page);

    await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
    // ⚡ **Shared with the activation composition below**, which asserts the
    // same three things about entirely different components — 📁 `1.3.1` is a
    // claim about *"Home"*, not about one composition's cards, and two copies
    // of the loop would be two things to keep in step (§2).
    await expectCardStructure(page);
  });

  /**
   * ⛔ **DOM order is visual order.** 📁 *"…in DOM order matching visual order at
   * every breakpoint"* — ⚡ which is why the grid PLACES cards rather than
   * reordering them, and why the column pins are `col-start` rather than `order`.
   */
  test('@a11y DOM order matches visual order at the reference viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openHome(page);

    const boxes = await page.locator('[data-card]').evaluateAll((els) =>
      els.map((el) => {
        const rect = el.getBoundingClientRect();
        return { id: el.getAttribute('data-card'), top: Math.round(rect.top), left: Math.round(rect.left) };
      }),
    );

    // ⚡ **Reading order is rows then columns**, which is what a two-column grid
    // presents to somebody reading down the page.
    const visual = [...boxes].sort((a, b) => a.top - b.top || a.left - b.left);
    expect(boxes.map((b) => b.id)).toEqual(visual.map((b) => b.id));
  });
});

test.describe('📁 §10 — the keyboard table', () => {
  /**
   * 📁 *"**Enter Home** — focus lands on the h1, not the search field."*
   */
  test('@a11y focus lands on the h1, never the search field', async ({ page }) => {
    await openHome(page);

    const focused = await page.evaluate(() => ({
      tag: document.activeElement?.tagName,
      role: document.activeElement?.getAttribute('role'),
    }));

    expect(focused.tag, 'focus did not land on the page heading').toBe('H1');
  });

  /**
   * 📁 *"**Move between cards** — each card is a tab group. Tab enters, Tab exits
   * at the last control; **arrows do not move between cards**."*
   *
   * ⚡ **Satisfied by construction and asserted anyway.** ⛔ Nothing on Home binds
   * an arrow key, so the browser's own behaviour is the design's — **and this
   * fails the day something starts binding one**, which is the only way that
   * regression would ever be noticed.
   */
  test('@a11y arrows do not move focus between cards', async ({ page }) => {
    await openHome(page);

    // Tab into the first card's own controls.
    const card = page.locator('[data-card]').first();
    const control = card.locator('a, button').first();
    // ⚡ **Not every composition's first card has a control**, and a test that
    // silently found none would assert nothing. 📁 The arrow rule is about cards
    // that HAVE controls.
    await expect(control, 'no focusable control in the first card').toBeVisible({
      timeout: 20_000,
    });
    await control.focus();
    const before = await page.evaluate(() => document.activeElement?.outerHTML?.slice(0, 80));

    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('ArrowRight');

    const after = await page.evaluate(() => document.activeElement?.outerHTML?.slice(0, 80));
    expect(after, 'an arrow key moved focus').toBe(before);
  });

  /**
   * 📁 *"**Open the focused item** — activates the row's primary action, **not a
   * detail overlay**."*
   *
   * ⚡ The row's action is a link, so Enter navigates. ⛔ **What this rules out is
   * a dialog**: an overlay here would mean a keyboard reader could not reach the
   * account at all without a second decision.
   */
  test('@a11y @journey Enter on a row action opens the account, not an overlay', async ({
    page,
  }) => {
    await openHome(page);

    // 🔴 **The seller composition's card**, stated rather than assumed — 📁 the
    // design gives `card.attention` to `SE` alone, so this row exists on one
    // composition and a spec that did not say so measured an unknown.
    await expect(page.getByTestId('home')).toHaveAttribute('data-composition', 'seller');
    const action = page
      .locator('[data-card="needs-you-today"] a[href^="/accounts/"]')
      .first();
    await expect(action).toBeVisible({ timeout: 20_000 });
    const href = await action.getAttribute('href');
    await action.focus();
    await page.keyboard.press('Enter');

    await page.waitForURL(new RegExp(href!.replace(/\//g, '\\/')), { timeout: 20_000 });
    expect(await page.getByRole('dialog').count()).toBe(0);
  });
});

/**
 * ⚡ **Every actionable element Home renders, measured** — not one card's.
 *
 * 📁 *"Every action is at least 24 × 24px with 8px separation; on mobile every
 * primary action is 44px tall."* ⛔ **A control is an action wherever it sits** —
 * inside a card, inside a strip, or in the page's own header — so this queries
 * `main` rather than `[data-card]`, and it is deliberately **composition-agnostic**:
 * `2.5.8` is a statement about the rendered page, not about one composition's
 * cut list.
 */
async function actions(page: import('@playwright/test').Page) {
  return page
    .locator('main a:visible, main button:visible, main [role="button"]:visible')
    .evaluateAll((els) =>
      els.map((el) => {
        const rect = el.getBoundingClientRect();
        return {
          name: (el.textContent ?? '').trim().slice(0, 32) || el.getAttribute('aria-label') || el.tagName,
          card: el.closest('[data-card]')?.getAttribute('data-card') ?? 'the page',
          // 📁 *"opening the owning module's flow"* — the design's own definition
          // of a card's one primary action, and what separates it from a dismiss.
          navigates: el.tagName === 'A' && !!el.getAttribute('href'),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          x: Math.round(rect.left),
          y: Math.round(rect.top),
        };
      }),
    );
}

test.describe('📁 2.5.8 — target size, everywhere Home renders one', () => {
  test('@a11y every action clears 24 × 24 at the reference viewport', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    // 🔴 **B-1033** — ⛔ **this measured a Home whose recents card had no rows**,
    // so the five targets the criterion is hardest on were never on the page.
    await openHomeWithRecents(page);

    const measured = await actions(page);
    // ⚠️ **A query that found nothing would assert nothing** — and this one is
    // broad enough that an empty result means the page did not render.
    expect(measured.length).toBeGreaterThan(0);

    for (const action of measured) {
      expect(
        Math.min(action.width, action.height),
        `${action.card} — "${action.name}" is ${action.width}×${action.height}`,
      ).toBeGreaterThanOrEqual(24);
    }
  });

  /**
   * ⚡ **The second clause, and it is a separate requirement.** 📁 *"…with 8px
   * separation"* — ⛔ two controls that each clear 24px but sit flush against one
   * another are still one mis-tap, which is the failure `2.5.8` is about.
   */
  test('@a11y no two actions sit closer than 8px', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    // 🔴 **B-1033, and this is the clause that was actually broken** — 📁 Entry
    // §05 draws the recents rows at `gap:0` with a rule between them, so five
    // 37px links sat **flush**. ⚡ **The rows are on the page now**, which is
    // what makes this assertion a measurement rather than a question.
    await openHomeWithRecents(page);

    const measured = await actions(page);
    for (let a = 0; a < measured.length; a += 1) {
      for (let b = a + 1; b < measured.length; b += 1) {
        const one = measured[a]!;
        const two = measured[b]!;
        // ⚡ **Rectangle distance, not centre distance** — two tall rows in one
        // column are far apart by centre and adjacent by edge.
        const dx = Math.max(0, one.x - (two.x + two.width), two.x - (one.x + one.width));
        const dy = Math.max(0, one.y - (two.y + two.height), two.y - (one.y + one.height));
        expect(
          Math.hypot(dx, dy),
          `"${one.name}" and "${two.name}" are adjacent`,
        ).toBeGreaterThanOrEqual(8);
      }
    }
  });

  /**
   * 📁 *"…on mobile every **primary** action is 44px tall."* ⚡ **`AC-H12` states
   * the same figure independently**, and `home-viewports.spec.ts` asserts it for
   * the attention card's rows. ⛔ **This is the page-wide half.**
   *
   * ## ⚠️ Why this queries links and the test above queries everything
   *
   * 🔴 **The design's two clauses have different subjects, and reading them as one
   * fails a control the design does not govern.** 📁 The first is *"**every**
   * action is at least 24 × 24px"*; the second is *"every **primary** action is
   * 44px tall"* — and the design defines the difference itself: *"**Exactly one
   * primary per card, opening the owning module's flow**"*, against a `Secondary`
   * that is *"at most one"* and a strip dismiss bound to `Esc`.
   *
   * ⚡ **Opening the owning module's flow is a navigation**, so the anchors are
   * the primary actions and the buttons are Home's own chrome — dismiss, skip,
   * customise, switch composition. ⛔ **Asserting 44px across both classes failed
   * the degraded strip's `Dismiss` at exactly 24px**, which is a control the
   * design sizes by the *first* clause and the test above still measures.
   */
  test('@a11y 390 gives every primary action a 44px touch target', async ({ page }) => {
    await page.setViewportSize({ width: 390, height: 844 });
    await openHomeWithRecents(page);

    const primary = (await actions(page))
      .filter((action) => action.navigates)
      // 🔴 **`card.recents` is held by the test below instead, and the reason is
      // [B-289](../../../docs/BUGS.md) rather than convenience.** 📁 The design
      // says *"**exactly one** primary per card"* — **the recents card renders
      // five identical rows**, so whether a row is *the* primary or a list item
      // governed by the first clause is a product question this lane must not
      // answer by choosing which assertion to write. ⛔ **Excluding it silently
      // would be the gap this whole file just closed**, so it is excluded
      // loudly and measured separately.
      .filter((action) => action.card !== 'recents');
    expect(primary.length, 'no primary action found on the phone layout').toBeGreaterThan(0);

    for (const action of primary) {
      expect(
        action.height,
        `${action.card} — "${action.name}" is ${action.height}px tall on a phone`,
      ).toBeGreaterThanOrEqual(44);
    }
  });

  /**
   * 🔴 **B-289 — the recents row at 390, under the strictest reading of the
   * second clause.**
   *
   * ⚠️ **`test.fail()`, not a skip and not a lowered figure.** ⚡ **It runs, it
   * measures, and it turns red the moment the row reaches 44px** — the same
   * device [B-286](../../../docs/BUGS.md) is held by, and the property a skip
   * does not have.
   *
   * ⛔ **This lane will not make it pass**, because both ways to are product
   * decisions: 📁 the registry declares `card.recents` at **160px** showing
   * **five** records, and five rows at 44px need **220px before padding and an
   * eyebrow**. **Growing the row cuts a record the design names; keeping the
   * footprint keeps the row under the figure the design states.**
   */
  test('@a11y 390 — a recents row is 37px against the 44px second clause', async ({ page }) => {
    test.fail();
    await page.setViewportSize({ width: 390, height: 844 });
    await openHomeWithRecents(page);

    // ⚠️ **Not `toBe(5)`** — `actions()` queries `:visible`, and the card clips
    // at 160px, which is the very contradiction this test is here to hold.
    const rows = (await actions(page)).filter((action) => action.card === 'recents');
    expect(rows.length, 'the recents card rendered no rows on the phone layout').toBeGreaterThan(0);

    for (const row of rows) {
      expect(row.height, `a recents row is ${row.height}px tall on a phone`).toBeGreaterThanOrEqual(44);
    }
  });
});

test.describe('📁 4.1.3 — entry announces once', () => {
  /**
   * 📁 *"Entry announces once: workspace, composition, attention count.
   * **Individual card arrivals announce nothing** — a screen-reader user hears
   * one sentence, not six."*
   *
   * ⛔ **One polite live region on the page, and it is the scope line.** ⚡ A card
   * that announced its own arrival would make entry six sentences, which is the
   * defect this criterion names.
   */
  test('@a11y one live region, and it is the scope line', async ({ page }) => {
    await openHome(page);

    const live = page.locator('main [aria-live]');
    expect(await live.count()).toBe(1);
    // ⚡ **Polite, never assertive** — arriving somewhere is not an interruption.
    await expect(live.first()).toHaveAttribute('aria-live', 'polite');
  });
});

test.describe('📁 the activation composition — the same criteria, the other half of Home', () => {
  /**
   * ⛔ **These are not new criteria.** They are `1.3.1`, `2.4.3`, `4.1.3` and
   * `2.5.8` — every one already asserted above — **measured against the
   * composition that had never been measured.**
   *
   * ⚡ **The gap was invisible because the suite passed.** 📁 A seeded persona
   * resolves to `seller`, so *"every card is a section"* was a true statement
   * about four cards and an unasked question about three others.
   */
  test('@a11y every activation card is a section with its own h2', async ({ page }) => {
    await openActivationHome(page);

    await expectCardStructure(page);
  });

  test('@a11y one h1, one live region, and focus on the heading', async ({ page }) => {
    await openActivationHome(page);

    await expect(page.getByRole('heading', { level: 1 })).toHaveCount(1);
    const live = page.locator('main [aria-live]');
    expect(await live.count()).toBe(1);
    await expect(live.first()).toHaveAttribute('aria-live', 'polite');
    // 📁 *"Focus lands on the h1, not the search field."*
    expect(await page.evaluate(() => document.activeElement?.tagName)).toBe('H1');
  });

  /**
   * 📁 **`2.5.8` on the composition with the most controls per card** — three
   * steps, each with a primary, a secondary and in one case a skip.
   */
  test('@a11y every activation action clears 24 × 24', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await openActivationHome(page);

    const measured = await actions(page);
    expect(measured.length).toBeGreaterThan(0);

    for (const action of measured) {
      expect(
        Math.min(action.width, action.height),
        `${action.card} — "${action.name}" is ${action.width}×${action.height}`,
      ).toBeGreaterThanOrEqual(24);
    }
  });
});
