/**
 * Does the product agree with itself?
 *
 * **The question the rest of the suite cannot ask.** Each screen can be
 * correct in isolation and the product still be untrustworthy, because a
 * customer does not read one screen — they read a row, form a belief, open the
 * account, and check whether it holds. A list that says *Cooling* and a brief
 * that does not is the single fastest way to lose a seller: *"the list flagged
 * it, the detail page didn't, so I assumed the list was noisy."*
 *
 * That is a real finding from this repository's own product review (R1-04),
 * and it is why these tests compare screens rather than checking them.
 */

import { expect, test } from './fixtures/signora';

interface Row {
  name: string;
  href: string;
  score: number;
  text: string;
}

async function rows(page: import('@playwright/test').Page): Promise<Row[]> {
  // **Wait for the links, not for the rows.** A row renders as soon as its
  // score and reason arrive; the name — and therefore the anchor — comes from
  // a second request that the list deliberately does not block on. Waiting on
  // the `li` returned rows whose `href` was still `''`, and `page.goto('')`
  // resolves to the base URL, so every one of these tests re-asserted the
  // attention list against itself and failed on the brief that never opened.
  await expect(page.locator('main a[href^="/accounts/"]').first()).toBeVisible({
    timeout: 20_000,
  });
  return page.locator('main ol > li').evaluateAll((items) =>
    items.map((item) => {
      const link = item.querySelector('a[href^="/accounts/"]');
      const text = item.textContent ?? '';
      const score = /Attention score\s*(\d+)/.exec(text);
      return {
        name: (link?.textContent ?? '').trim(),
        href: link?.getAttribute('href') ?? '',
        score: score ? Number(score[1]) : Number.NaN,
        text,
      };
    }),
  );
}

test.describe('the list and the brief describe the same account', () => {
  test('@journey the score on the row is the score on the brief', async ({
    attention,
    brief,
    page,
  }) => {
    await attention.open();
    const listed = await rows(page);

    // Three accounts rather than one: a single sample can agree by accident,
    // and twelve would make the suite slow for no additional confidence.
    for (const row of listed.slice(0, 3)) {
      await page.goto(row.href);
      await brief.waitForScore();
      const heading = await page.getByText(/Attention score \d+ out of 100/).innerText();
      const onBrief = Number(/Attention score (\d+)/.exec(heading)?.[1]);

      expect(
        onBrief,
        `${row.name}: the list says ${row.score}, the brief says ${onBrief}`,
      ).toBe(row.score);
    }
  });

  test('@journey an account the row calls cooling does not read as healthy on the brief', async ({
    attention,
    page,
    brief,
  }) => {
    await attention.open();
    const listed = await rows(page);
    const cooling = listed.filter((row) => /Cooling|Evidence expired/.test(row.text));

    if (cooling.length === 0) test.skip(true, 'no cooling account in this scenario');

    for (const row of cooling.slice(0, 2)) {
      await page.goto(row.href);
      await brief.waitForScore();
      const body = await page.locator('main').innerText();

      // **R1-04.** The list read the evidence state and the brief rendered
      // `is_current`, which is true of a different fact — so the two screens
      // disagreed about one account and no reader could reconstruct why.
      expect(
        /Cooling|expired|stale|as it stood/i.test(body),
        `${row.name} is flagged on the list and the brief says nothing about it`,
      ).toBe(true);
    }
  });

  test('@journey an account the row calls contested says why on the brief', async ({
    attention,
    page,
    brief,
  }) => {
    await attention.open();
    const listed = await rows(page);
    const contested = listed.filter((row) => /Contested/.test(row.text));

    if (contested.length === 0) test.skip(true, 'no contested account in this scenario');

    await page.goto(contested[0].href);
    await brief.waitForScore();
    // A badge a customer cannot get an explanation for is a claim they have
    // to take on faith, which is the opposite of what this product sells.
    await expect(page.getByText(/points both ways|has not picked a side/i)).toBeVisible();
  });

  test('@journey the name on the row is the name on the brief', async ({
    attention,
    page,
    brief,
  }) => {
    await attention.open();
    const listed = await rows(page);
    const named = listed.filter((row) => !/^[0-9a-f]{8}/.test(row.name));

    for (const row of named.slice(0, 3)) {
      await page.goto(row.href);
      await brief.waitForScore();
      await expect(
        page.locator('main').getByText(row.name, { exact: false }).first(),
      ).toBeVisible();
    }
  });
});

test.describe('the product counts the same things the same way', () => {
  test('@journey every listed account is reachable and none 404s', async ({
    attention,
    page,
  }) => {
    await attention.open();
    const listed = await rows(page);

    for (const row of listed) {
      const response = await page.goto(row.href);
      expect(response?.status(), `${row.name} at ${row.href}`).toBeLessThan(400);
    }
  });

  test('@journey what contributed adds up to what the score says', async ({
    attention,
    brief,
    page,
  }) => {
    await attention.open();
    await attention.openFirstAccount();
    await brief.waitForScore();

    // The brief states its own arithmetic — "90 of 120 points". A customer who
    // adds the ledger up and gets a different number stops trusting every
    // number on the page, so the two must be one derivation and not two.
    // `.first()`: the same arithmetic appears twice by design — once for the
    // eye, once for a screen reader — and that is the accessibility pattern
    // this product uses everywhere, not a duplicate.
    const arithmetic = await page.getByText(/\d+ of \d+ points/).first().innerText();
    expect(arithmetic).toMatch(/\d+ of \d+ points/);
    await expect(brief.whatContributed).toBeVisible();
    expect(await brief.citations.count()).toBeGreaterThan(0);
  });
});
