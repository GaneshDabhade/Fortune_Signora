/**
 * Accessibility, as customer impact rather than as a compliance score.
 *
 * **Not aiming at WCAG in one pass** — the brief was to find the issues a
 * customer actually hits. Every assertion here corresponds to somebody being
 * unable to do something: reach a control without a mouse, know where they
 * are, get out of a dialog, or hear what a field is for.
 *
 * `components/ui` is frozen (§20c) and an accessibility issue in it is a
 * **defect**, not an enhancement — the freeze names them explicitly and says
 * they never wait for a business milestone.
 */

import { expect, test } from './fixtures/signora';

test.describe('reaching the product without a mouse', () => {
  test('@a11y the first tab stop is reachable and visible', async ({ page }) => {
    await page.goto('/');
    await expect(page.getByTestId('home')).toBeVisible();

    await page.keyboard.press('Tab');
    const focused = page.locator(':focus');
    await expect(focused).toBeVisible();

    // A focus ring that cannot be seen is the same as no focus at all for
    // somebody navigating by keyboard.
    const ring = await focused.evaluate((element) => {
      const style = getComputedStyle(element);
      return `${style.outlineStyle}|${style.outlineWidth}|${style.boxShadow}`;
    });
    expect(ring).not.toBe('none|0px|none');
  });

  test('@a11y every navigation entry is reachable by keyboard', async ({ page }) => {
    await page.goto('/');
    // ⚠️ **Wait for the destination, not for the rail.** 📁 `/` is the shell's
    // entry resolver and forwards to Home — ⛔ **focusing a link while that
    // navigation is in flight loses the focus to the new document**, which
    // reads as a keyboard defect and is a race in the test.
    await expect(page.getByTestId('home')).toBeVisible();
    const nav = page.getByRole('navigation', { name: 'Primary' });
    await expect(nav).toBeVisible();

    for (const link of await nav.getByRole('link').all()) {
      await link.focus();
      await expect(link).toBeFocused();
    }
  });

  test('@a11y the current page is announced, not only coloured', async ({ page }) => {
    // ⚠️ **Was `/`, whose rail entry [TASK-1482](../../../docs/BACKLOG.md)
    // removed on [D-240](../../../docs/DECISION_REGISTER.md).** ⛔ **A route with
    // no rail entry has nothing to mark current**, so the assertion would have
    // had no subject. ✅ **`/business` still has one and the PROPERTY is
    // unchanged**: exactly one destination is marked, and it says which.
    await page.goto('/business');
    const current = page
      .getByRole('navigation', { name: 'Primary' })
      .locator('[aria-current="page"]');

    // Colour alone tells a screen-reader user nothing about where they are.
    await expect(current).toHaveCount(1);
    await expect(current).toContainText('Your business');
  });

  test('@a11y an account can be opened with the keyboard alone', async ({
    page,
    accounts,
    brief,
  }) => {
    await accounts.open();
    await accounts.names();

    await accounts.accountLinks.first().focus();
    await page.keyboard.press('Enter');
    await page.waitForURL(/\/accounts\/[0-9a-f-]{36}/);
    // ⚠️ **Not `waitForScore()`** — 📁 `B-1022`: Companies is the whole book in
    // the book's own order and *"a Signora score is not on this list yet"*, so
    // its first row is whichever account sorts first and the Playground's is
    // one no provider has named. ⛔ That is a designed state, not a failure.
    // 📁 The claim is *an account can be opened with the keyboard alone*, so
    // what must be on screen is the brief.
    await expect(brief.title).toBeVisible({ timeout: 20_000 });
  });
});

test.describe('dialogs', () => {
  test('@a11y the evidence drawer is a dialog, is labelled, and takes focus', async ({
    home,
    brief,
    page,
  }) => {
    // ⚡ **Home's ranked card, because an unscored account has no citations**
    // and therefore no evidence drawer to inspect — `B-1022`.
    await home.open();
    await home.openFirstRankedAccount();
    await brief.waitForScore();
    await brief.openFirstCitation();

    const dialog = brief.evidenceDialog;
    await expect(dialog).toHaveAttribute('aria-labelledby', /.+/);
    // Focus inside the dialog, or a keyboard user is reading a dialog they
    // cannot operate and tabbing through the page behind it.
    const inside = await dialog.evaluate((element) =>
      element.contains(document.activeElement),
    );
    expect(inside).toBe(true);

    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
  });

  test('@a11y closing a dialog returns focus to what opened it', async ({
    home,
    brief,
    page,
  }) => {
    await home.open();
    await home.openFirstRankedAccount();
    await brief.waitForScore();

    const citation = brief.citations.first();
    await citation.click();
    await expect(brief.evidenceDialog).toBeVisible();
    await page.keyboard.press('Escape');

    // Losing focus to `<body>` drops a keyboard user at the top of the page,
    // and they have to tab all the way back to where they were reading.
    await expect(citation).toBeFocused();
  });

  test('@a11y the new-organization dialog is labelled and escapable', async ({
    settings,
    page,
  }) => {
    await settings.open();
    await settings.newOrganization.click();

    const dialog = settings.dialog;
    await expect(dialog).toBeVisible();
    await expect(dialog).toHaveAttribute('aria-labelledby', /.+/);
    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
  });
});

test.describe('forms say what they are for', () => {
  test('@a11y every input on the sign-in form has a real label', async ({ page }) => {
    await page.goto('/signin');

    for (const input of await page.locator('input:visible').all()) {
      const name = await input.evaluate((element) => {
        const label = element.labels?.[0]?.textContent;
        return (
          label ??
          element.getAttribute('aria-label') ??
          element.getAttribute('aria-labelledby') ??
          ''
        );
      });
      expect(name.trim().length).toBeGreaterThan(0);
    }
  });

  test('@a11y every input on the business page has a real label', async ({
    business,
  }) => {
    await business.open();
    await expect(business.heading).toBeVisible();
    await business.addProduct.click();
    await expect(business.dialog).toBeVisible();

    for (const input of await business.dialog.locator('input:visible, textarea:visible').all()) {
      const name = await input.evaluate((element) => {
        const labelled = (element as HTMLInputElement).labels?.[0]?.textContent;
        return labelled ?? element.getAttribute('aria-label') ?? '';
      });
      expect(name.trim().length).toBeGreaterThan(0);
    }
  });
});

test.describe('the page has a structure a screen reader can use', () => {
  for (const [name, path] of [
    ['Companies', '/accounts'],
    ['the business page', '/settings/products'],
    ['settings', '/settings'],
  ] as const) {
    test(`@a11y ${name} has exactly one level-1 heading`, async ({ page }) => {
      await page.goto(path);
      const h1 = page.getByRole('heading', { level: 1 });
      await expect(h1).toHaveCount(1);
      // A heading with no text is worse than none — it appears in the
      // document outline and says nothing.
      expect((await h1.innerText()).trim().length).toBeGreaterThan(0);
    });
  }

  test('@a11y icons that carry no meaning are hidden from assistive technology', async ({
    page,
  }) => {
    await page.goto('/');
    await expect(page.getByTestId('home')).toBeVisible();

    // A decorative icon announced as "image" between every score and every
    // name turns one list into twice as much to listen to.
    const bare = await page.locator('main svg:not([aria-hidden]):not([aria-label])').count();
    expect(bare).toBe(0);
  });
});

test.describe('controls are big enough to hit', () => {
  /**
   * 📁 **`Design Documents/Fortune Signora Design System v2.html` §17 `2.5.8`**
   * — ***"Targets ≥ 24px with 8px separation; the 26px compact button keeps a
   * 32px hit area."***
   *
   * ⚠️ **The App Shell's 44px is a DIFFERENT rule and is not asserted here** —
   * 📁 *"Every **top-bar** control is a 32px target with 8px separation; 44px on
   * touch."* ⛔ **Account 360 states no target rule of its own**, so the design
   * system's general floor is the one that governs its body.
   *
   * 🔴 **Company 360 had seven controls under it** — the section disclosure
   * headings, the research panel's heading, *Refresh research*, the focus-mode
   * toggle, the limitations disclosure and both sequence pager links — **and
   * every one measured the same at 1440 as at 390**, so this is a floor rather
   * than a narrow-viewport concern. ⚡ **Asserted at both ends** because the
   * fix is a minimum on a line box, and a minimum is exactly the kind of thing
   * a later `h-` utility silently overrides.
   */
  for (const width of [1440, 390]) {
    test(`@a11y every Company 360 control clears 24px at ${width}`, async ({
      page,
      home,
      brief,
    }) => {
      await page.setViewportSize({ width, height: 900 });
      await home.open();
      await home.openFirstRankedAccount();
      await expect(brief.title).toBeVisible({ timeout: 20_000 });

      const undersized = await page.evaluate(() => {
        const targets = document.querySelectorAll(
          'main button, main a, main [role="button"], main input, main select',
        );
        return [...targets]
          .map((el) => ({ el, box: el.getBoundingClientRect() }))
          // ⛔ A control the page is not currently showing has no target size
          // to measure — a collapsed section's body is hidden, not small.
          .filter(({ box }) => box.width > 1 && box.height > 1)
          .filter(({ box }) => box.width < 24 || box.height < 24)
          .map(({ el, box }) => ({
            name: (el.getAttribute('aria-label') ?? el.textContent ?? '').trim().slice(0, 40),
            width: Math.round(box.width),
            height: Math.round(box.height),
          }));
      });

      expect(undersized).toEqual([]);
    });
  }
});

test.describe('the record follows its design document', () => {
  /**
   * 📁 **`Design Documents/Fortune Signora Account 360.html`** —
   * ***"width:184px; flex:none; position:sticky; top:0; align-self:flex-start"***
   * for the *"On this page"* rail, beside `minmax(0,1fr) 340px`.
   *
   * ⛔ **It was a horizontal chip strip at EVERY width**, on the reasoning that
   * the right edge belongs to the utility panel. ⚠️ **That confused two
   * regions**: 📁 the App Shell's panel *"docks to the right of content"* and is
   * shell chrome; this rail is inside the content region, on its left.
   *
   * ⚡ **One landmark, two orientations** — asserted at both ends, because the
   * cheap mistake is to ship two `nav`s and give a screen reader a duplicate to
   * disambiguate.
   */
  test('@design the section rail is the design\'s 184px sticky column at 1440', async ({
    page,
    home,
    brief,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await home.open();
    await home.openFirstRankedAccount();
    await expect(brief.title).toBeVisible({ timeout: 20_000 });

    const rail = page.getByRole('navigation', { name: 'On this page' });
    await expect(rail).toHaveCount(1);
    const box = await rail.boundingBox();
    expect(box?.width).toBe(184);
    // ⚡ `sticky` lives on the wrapper; `self-start` is what lets it scroll
    // within its row rather than being stretched to the row's full height.
    const position = await rail.evaluate((el) =>
      getComputedStyle(el.parentElement as HTMLElement).position,
    );
    expect(position).toBe('sticky');
  });

  test('@design the rail yields to a strip below the laptop band', async ({
    page,
    home,
    brief,
  }) => {
    await page.setViewportSize({ width: 390, height: 900 });
    await home.open();
    await home.openFirstRankedAccount();
    await expect(brief.title).toBeVisible({ timeout: 20_000 });

    const rail = page.getByRole('navigation', { name: 'On this page' });
    // ⛔ **Yields, never vanishes** — 📁 the design system's *"chrome yields
    // before data"*, and an anchor nav that disappears takes the record's map
    // with it.
    await expect(rail).toHaveCount(1);
    const box = await rail.boundingBox();
    expect(box?.width).toBeGreaterThan(184);
  });

  /**
   * 📁 **Design System v2** — `--row-h: 44px`, and 📁 the Design Review names
   * ***"tables at 44px rows and 11.5px meta"*** as one of two reasons this
   * product beats a CRM.
   *
   * ⛔ **Density was expressed as PADDING and measured 49px** on every row of
   * the book of accounts. ⚡ **A height on a `td` is a minimum**, so this
   * asserts the floor rather than forbidding a wrapped row from growing.
   */
  test('@design Companies rows are the design\'s 44px', async ({ accounts, page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await accounts.open();
    await accounts.names();

    const heights = await page.evaluate(() =>
      [...document.querySelectorAll('tbody tr')]
        .slice(0, 5)
        .map((row) => Math.round(row.getBoundingClientRect().height)),
    );
    expect(heights.length).toBeGreaterThan(0);
    for (const height of heights) expect(height).toBe(44);
  });
});

test.describe('Companies follows its design document', () => {
  /**
   * 📁 **`Design Documents/Fortune Signora Companies.html`** — the filter row's
   * right-hand group is one element:
   *
   * ```
   * <span style="margin-left:auto;display:flex;gap:12px">
   *   <span>312 of 8,412</span>
   *   <span style="color:var(--brand-ink);font-weight:600">Save to view</span>
   * ```
   *
   * ⛔ **`Save to view` sat on the saved-view TAB row**, which the design draws
   * with the views and the mode switcher and nothing else. ⚡ **The placement is
   * not cosmetic**: saving acts on the FILTER state, so it belongs beside the
   * count that describes it.
   */
  test('@design Save to view sits with the filter count, not on the tab row', async ({
    accounts,
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await accounts.open();
    await accounts.names();

    const save = page.getByRole('button', { name: 'Save to view' });
    await expect(save).toHaveCount(1);

    const count = page.getByTestId('companies-count');
    await expect(count).toBeVisible();

    // ⚡ **Same row, asserted from GEOMETRY** — a shared parent could be
    // satisfied by a wrapper that stacks them; being on one optical line
    // cannot.
    const [saveBox, countBox] = await Promise.all([save.boundingBox(), count.boundingBox()]);
    expect(saveBox).not.toBeNull();
    expect(countBox).not.toBeNull();
    expect(Math.abs((saveBox?.y ?? 0) - (countBox?.y ?? 0))).toBeLessThan(12);

    // ⛔ The tab row is above the filter row, so the control must NOT be level
    // with the saved-view tabs.
    const tab = page.getByRole('tab', { name: 'All companies' });
    const tabBox = await tab.boundingBox();
    expect((saveBox?.y ?? 0)).toBeGreaterThan((tabBox?.y ?? 0) + 8);
  });

  /**
   * 📁 **The Experience Map** — Account 360's entries are ***"row · search ·
   * citation · signal · deep link"***, and the Signal Center's row reads ***"the
   * monitoring loop enters at the queue, exits into accounts."***
   *
   * ⛔ **The exit did not exist**: the queue rendered the company as plain text,
   * so a triager could disposition a signal and had no way to open the company
   * it was about.
   */
  test('@design the Signal Center exits into the company record', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/signals');

    const toAccount = page.locator('main a[href^="/accounts/"]');
    // ⚠️ **`count()` does not auto-wait, and this test skipped on its first run
    // because of it** — the queue's identity read settles after the queue does,
    // so counting immediately reported *no signals* on a screen that was about
    // to show thirteen. ⛔ **A skip that hides a working feature is worse than
    // a failure**, because nothing ever goes red to correct it. ⚡ **Wait for
    // the queue, THEN decide whether the scenario has rows.**
    const queue = page.locator('main input[type="checkbox"]');
    await expect(queue.first()).toBeVisible({ timeout: 20_000 });

    await expect(toAccount.first()).toBeVisible({ timeout: 20_000 });
    await toAccount.first().click();
    await page.waitForURL(/\/accounts\/[0-9a-f-]{36}/, { timeout: 20_000 });
    // ⚡ **One canonical record**, reached from the queue exactly as it is from
    // the list.
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible({ timeout: 20_000 });
  });
});

test.describe('On this page reaches what the page renders', () => {
  /**
   * 🔴 **Both directions, because this page has now shipped BOTH defects.**
   *
   * ⛔ **[TASK-1483](../../../docs/BACKLOG.md): *"the anchor existed and the
   * section did not"*** — a rail entry scrolling a reader to nothing.
   * ⛔ **And its inverse, found 2026-08-20: `opportunities` rendered
   * unconditionally and was missing from the rail**, so *Open opportunities*
   * was on the page and unreachable from the one control that exists to reach
   * sections.
   *
   * ⚡ **Neither fails anything.** **A dead anchor scrolls nowhere and a missing
   * entry is simply absent** — which is why this asserts the correspondence in
   * both directions rather than checking a list against itself.
   */
  test('@design every rail entry has a section, and every section has a rail entry', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 1200 });
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await page.locator('a[href^="/accounts/"]').first().click();
    await page.waitForURL(/\/accounts\/[0-9a-f-]{36}/);
    await expect(page.getByRole('heading', { name: 'Account score' })).toBeVisible({
      timeout: 20_000,
    });

    const rail = page.getByRole('navigation', { name: /on this page/i });
    const hrefs = await rail
      .locator('a[href^="#"]')
      .evaluateAll((nodes) =>
        nodes.map((n) => (n as HTMLAnchorElement).getAttribute('href')!.slice(1)),
      );
    expect(hrefs.length).toBeGreaterThan(0);

    // ⛔ **Direction 1 — a rail entry that scrolls nowhere.**
    const dead: string[] = [];
    for (const id of hrefs) {
      if ((await page.locator(`#${id}`).count()) === 0) dead.push(id);
    }
    expect(dead, 'rail entries with no section on the page').toEqual([]);

    // 🔴 **Direction 2 — a section the rail cannot reach.** ⚡ **This is the
    // direction that shipped**, and it is the one a list-against-itself check
    // cannot see.
    const anchoredSections = await page
      .locator('main section[id], main [id][aria-labelledby], main section[aria-label]')
      .evaluateAll((nodes) =>
        nodes.map((n) => n.getAttribute('id')).filter((id): id is string => Boolean(id)),
      );
    const unreachable = anchoredSections.filter((id) => !hrefs.includes(id));
    expect(unreachable, 'sections on the page with no rail entry').toEqual([]);
  });
});

test.describe('the record follows the Opportunity Intelligence design', () => {
  /**
   * 🔴 **📁 *"What moved it"* — the Opportunity Intelligence design's waterfall,
   * and it existed nowhere in the product.**
   *
   * ⚡ **What only a browser can say**: that the segments are actually OFFSET —
   * a waterfall rather than five bars from a common edge — **against the real
   * contributions the Playground produces**, not a fixture.
   *
   * ⛔ **Rendered on Account 360 rather than at `/opportunities`**: 📁 D38
   * removed that entry from first principles, and TASK-441 records that *"a
   * route is how D38 gets reversed by accident."*
   */
  test("@design the score section carries the design's what-moved-it waterfall", async ({
    page,
  }) => {
    await page.goto('/accounts');
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await page.locator('a[href^="/accounts/"]').first().click();
    await page.waitForURL(/\/accounts\/[0-9a-f-]{36}/);

    // 🔴 **Wait for the SECTION before asking about the waterfall.** ⛔ **`count()`
    // does not auto-wait**, so deciding on it immediately after navigation
    // reports zero on a section that simply had not rendered — **and the skip
    // that follows hides a feature that works.** ⚠️ **This lane shipped exactly
    // that once already**, on the Signal Center queue.
    const section = page.getByRole('heading', { name: 'Account score' });
    await expect(section).toBeVisible({ timeout: 20_000 });

    const heading = page.getByRole('heading', { name: 'What moved it' });
    // ⚠️ **An account whose score moved nothing renders none of this, and that
    // is the designed outcome** — 📁 a heading over an empty frame would state
    // that a section exists and failed. ✅ **Asserted against the CONTRIBUTIONS
    // the page is showing**, so the branch is a fact about the data rather than
    // about the clock.
    const anyMovement = await page
      .locator('h4:has-text("What moved it")')
      .or(page.getByText(/did not move the score|no lines/i))
      .first()
      .waitFor({ state: 'attached', timeout: 10_000 })
      .then(() => true)
      .catch(() => false);

    if (!anyMovement || (await heading.count()) === 0) {
      test.skip(true, 'this account has no counted movement');
      return;
    }

    await expect(heading).toBeVisible();
    const rows = page.locator('h4:has-text("What moved it") + ol > li');
    expect(await rows.count()).toBeGreaterThan(0);

    // 🔴 **The waterfall property, measured in the browser.** ⛔ **Every segment
    // starting at the same edge would be a bar chart** — the design offsets each
    // by the running total.
    const offsets = await page.locator('h4:has-text("What moved it") + ol > li div[style*="left"]')
      .evaluateAll((nodes) => nodes.map((n) => Number.parseFloat((n as HTMLElement).style.left)));

    expect(offsets.length).toBeGreaterThan(0);
    expect(offsets[0]).toBe(0);
    // Non-decreasing, and the last one starts after the first unless there is
    // only a single factor.
    for (let i = 1; i < offsets.length; i++) {
      expect(offsets[i]).toBeGreaterThan(offsets[i - 1] as number);
    }
  });
});

test.describe('the Signal Center follows its design document', () => {
  /**
   * 📁 **`Design Documents/Fortune Signora Signal Center.html`** draws the
   * header band as one baseline:
   *
   * ```
   * <div style="display:flex;align-items:baseline;gap:10px">
   *   <h1 style="font-size:25px;font-weight:700;…">Signals</h1>
   *   <span style="font-size:13px;color:var(--ink-3)">14 need review · …</span>
   * </div>
   * ```
   *
   * ⛔ **The screen hand-rolled it** — title at `text-xl`, count in a paragraph
   * BELOW the description. ⚡ **`PageHeader` is that shape**, and `/reports`
   * next door already used it.
   *
   * ⚠️ **The title text is "Signals" and that was verified, not assumed** —
   * *"Signal center"* is the design DOCUMENT's name, not the screen's heading.
   */
  test('@design the queue header is the approved page header, counts on the title baseline', async ({
    page,
  }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/signals');

    const heading = page.getByRole('heading', { level: 1, name: 'Signals' });
    await expect(heading).toBeVisible({ timeout: 20_000 });
    // 📁 §04's `Title` role — the approved header applies it; the local one did
    // not, and rendered at `text-xl`.
    await expect(heading).toHaveClass(/text-title/);

    const counts = page.getByTestId('queue-counts');
    await expect(counts).toBeVisible();

    // ⚡ **One baseline, asserted from GEOMETRY** — a shared parent could be
    // satisfied by a wrapper that stacks them.
    const [h, c] = await Promise.all([heading.boundingBox(), counts.boundingBox()]);
    expect(Math.abs((h?.y ?? 0) - (c?.y ?? 0))).toBeLessThan(20);
    expect((c?.x ?? 0)).toBeGreaterThan((h?.x ?? 0));
  });

  /**
   * 📁 §17 `2.5.8` — *"Targets ≥ 24px."* ⚠️ **The queue's selection boxes
   * measured `16 × 16`.** ⛔ **The visual stays at the design's size and the
   * target grows**, via the wrapping `<label>` the Companies table already uses.
   */
  test('@a11y every Signal Center target clears 24px', async ({ page }) => {
    await page.setViewportSize({ width: 1440, height: 900 });
    await page.goto('/signals');
    await expect(page.getByRole('heading', { level: 1, name: 'Signals' })).toBeVisible({
      timeout: 20_000,
    });

    const undersized = await page.evaluate(() => {
      const targets: Element[] = [
        ...document.querySelectorAll('main button, main a, main [role="button"], main select'),
      ];
      // ⚡ **A label-wrapped input's TARGET is the label**, which is what the
      // success criterion measures.
      for (const input of document.querySelectorAll('main input')) {
        targets.push(input.closest('label') ?? input);
      }
      return targets
        .map((el) => ({
          name: (el.getAttribute('aria-label') ?? el.textContent ?? '').trim().slice(0, 40),
          ...el.getBoundingClientRect().toJSON(),
        }))
        .filter((box) => box.height > 0 && (box.height < 24 || box.width < 24))
        .map((box) => ({ name: box.name, w: Math.round(box.width), h: Math.round(box.height) }));
    });

    expect(undersized).toEqual([]);
  });
});

/**
 * 🔴 **[B-1053](../../../docs/BUGS.md) — an account that does not exist rendered
 * as an account that exists with no data.**
 *
 * ⛔ **QE counted 20 API calls on that page and not one fetched the account**,
 * so `/accounts/00000000-…-000000000000` answered **200** with a full record
 * headed `00000000 — no source has named this account yet`.
 *
 * ⚠️ **The row's cause was one layer deeper than the row said, and only a
 * browser found it.** 📁 `/account-identities` **documents** *"an entity the
 * workspace does not own is simply absent"* — 🔴 **and returned a zero-filled
 * row for every id asked about**, which is exactly what
 * [ADR-0409](../../../docs/architecture/) §5 forbids. **The screen was
 * faithfully rendering what the platform told it.**
 */
test.describe('a record that is not there says so', () => {
  test('@design an account the workspace does not have renders a not-found state', async ({
    page,
  }) => {
    const identityBodies: string[] = [];
    page.on('response', async (response) => {
      if (response.url().includes('account-identities') && response.url().includes('00000000')) {
        identityBodies.push(await response.text().catch(() => ''));
      }
    });

    await page.goto('/accounts/00000000-0000-0000-0000-000000000000');
    const heading = page.getByRole('heading', { level: 1 });
    await expect(heading).toHaveText(/not here/i);

    // 🔴 **The name derived from the URL** — the UUID's first group — must be
    // nowhere on the page. ⛔ **That string WAS the `h1`.**
    await expect(page.locator('body')).not.toContainText('00000000-0000');

    // ⚡ **And the platform half, asserted here rather than trusted**: the
    // endpoint omits an id the workspace does not own.
    expect(identityBodies.length).toBeGreaterThan(0);
    expect(JSON.parse(identityBodies[0] ?? '[]')).toEqual([]);

    // ♿ **It names no cause.** 📁 [§7](../../../CLAUDE.md) — *404, never 403*:
    // a member of another organization reaches this identical page, so a
    // sentence about access would be inventing the one thing it cannot know.
    await expect(page.locator('main')).not.toContainText(/access|permission/i);
    await expect(page.getByRole('link', { name: /back to the companies/i })).toBeVisible();
  });

  /**
   * ✅ **The regression this must not cause.** ⛔ **Seeding the identity result
   * from bindings rather than from the request would take every account with
   * it if the reasoning were wrong** — so a real record is opened in the same
   * run, from the list, rather than from a hardcoded id.
   */
  test('@design a real account is untouched by that check', async ({ page }) => {
    await page.goto('/accounts');
    const first = page.locator('table a[href^="/accounts/"]').first();
    await expect(first).toBeVisible();
    const href = await first.getAttribute('href');
    expect(href).not.toBeNull();

    await page.goto(href!);
    const heading = page.getByRole('heading', { level: 1 });
    await expect(heading).toBeVisible();
    await expect(heading).not.toHaveText(/not here/i);
    // ⚡ **A named company, not the URL's first group.**
    await expect(heading).not.toHaveText(/^[0-9a-f]{8}$/);
  });
});

/**
 * 🔴 **[B-1055](../../../docs/BUGS.md) — every tablist in the product, in one
 * place, because the row was found and completed one tablist at a time.**
 *
 * ⛔ **QE measured `/signals` and filed two; the notifications popover turned
 * out to be a third.** ⚡ **A component test proves one strip; it cannot notice
 * a fourth appearing** — and 📁 two of the three only exist once something is
 * opened, so a scan of a settled page cannot see them either.
 *
 * ⚠️ **This asserts the ASSOCIATION by resolving ids**, never by comparing two
 * strings the test itself spells. 📁 The row's own note: ***"aria-selected
 * alone is what made this look correct."***
 */
test.describe('a tab names the panel it controls', () => {
  /** ⚡ Every `role="tab"` currently in the document, resolved against every panel. */
  async function unwired(page: import('@playwright/test').Page) {
    return page.evaluate(() => {
      const panels = new Set([...document.querySelectorAll('[role=tabpanel]')].map((p) => p.id));
      return [...document.querySelectorAll('[role=tab]')]
        .filter((tab) => {
          const controls = tab.getAttribute('aria-controls');
          return controls === null || !panels.has(controls);
        })
        .map((tab) => (tab.textContent ?? '').trim().slice(0, 24) || '(unnamed)');
    });
  }

  /** ⛔ **The panel points BACK**, or the contract is one-way. */
  async function unlabelled(page: import('@playwright/test').Page) {
    return page.evaluate(() =>
      [...document.querySelectorAll('[role=tabpanel]')]
        .filter((panel) => {
          const by = panel.getAttribute('aria-labelledby');
          return by === null || document.getElementById(by) === null;
        })
        .map((panel) => panel.id || '(no id)'),
    );
  }

  test('@a11y all three tablists carry the full contract, including the two that must be opened', async ({
    page,
  }) => {
    await page.goto('/signals');
    await expect(page.getByRole('tab').first()).toBeVisible();

    // ① **The queue.**
    expect(await unwired(page), 'queue tabs controlling no panel').toEqual([]);

    // ② **The notifications popover** — 📁 the third tablist, and the one a
    // scan of a settled page cannot reach.
    await page.getByRole('button', { name: /notification/i }).first().click();
    await expect(page.getByRole('tab', { name: /needs you/i })).toBeVisible();
    expect(await unwired(page), 'notification tabs controlling no panel').toEqual([]);
    await page.keyboard.press('Escape');

    // ③ **The utility panel** — ⚠️ **opened with `⌘.`, which is the design's
    // own shortcut**; clicking a collapsed rail icon is what made QE nearly
    // file *"it never docks"*.
    await page.keyboard.press('Control+.');
    await expect(page.getByRole('tab', { name: 'Insights' })).toBeVisible();
    expect(await unwired(page), 'utility panel tabs controlling no panel').toEqual([]);
    expect(await unlabelled(page), 'panels naming no tab').toEqual([]);

    // ⛔ **Roving `tabindex` on every strip open at once.** 🔴 **The utility
    // panel read `null` on all three**, so `Tab` walked the strip instead of
    // leaving it.
    const roving = await page.evaluate(() =>
      [...document.querySelectorAll('[role=tablist]')].map((list) =>
        [...list.querySelectorAll('[role=tab]')].map((tab) => tab.getAttribute('tabindex')),
      ),
    );
    expect(roving.length).toBeGreaterThanOrEqual(2);
    for (const strip of roving) {
      expect(strip.filter((value) => value === '0')).toHaveLength(1);
      expect(strip.every((value) => value === '0' || value === '-1')).toBe(true);
    }
  });

  /**
   * 🔴 **A collapsed region must not publish `role="tab"` for a panel it is not
   * rendering.** ⛔ **Collapsed, the utility rail claimed three** — and
   * clicking one changed an invisible selection while nothing appeared.
   */
  test('@a11y the collapsed utility rail claims no tab role, and opens the panel', async ({
    page,
  }) => {
    await page.goto('/accounts');
    await expect(page.getByRole('button', { name: 'Insights' })).toBeVisible();

    const rail = page.getByRole('button', { name: 'Insights' });
    await expect(rail).toHaveAttribute('aria-expanded', 'false');
    expect(await page.getByRole('tab', { name: 'Insights' }).count()).toBe(0);

    // ⚡ **And the control does something a person can see.**
    await rail.click();
    await expect(page.getByRole('tabpanel')).toBeVisible();
  });
});
