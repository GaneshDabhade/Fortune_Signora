/**
 * **The pages that must render with the application down** —
 * [TASK-1437](../../../docs/BACKLOG.md).
 *
 * > 📁 **System States, *Static fallback***: ***"Maintenance and platform
 * > outage pages are served from static hosting with no dependency on the
 * > application, its API or its session."***
 *
 * 🔴 **The constraint IS the row**, so these tests assert the absence of
 * things rather than the presence of them. ⛔ **A maintenance page that
 * imports the app is a maintenance page that is down during maintenance.**
 *
 * ## ⚠️ The guard reads CODE, not prose — and it had to, immediately
 *
 * **The first version of this scan matched `<script` and fired on
 * `maintenance.html` line 22**, which is a COMMENT reading *"no `<script>` —
 * nothing to execute, nothing to fail"*. ⛔ **That is
 * [B-318](../../../docs/BUGS.md)'s class** — *a Security Invariant matches
 * text, so a comment fails it* — **and [B-162](../../../docs/BUGS.md) is the
 * same defect in the other direction**, where stripping comments carelessly
 * hid real matches. ✅ **So the comments are removed first, and a fire-test
 * proves the scan still catches a real occurrence.**
 */
import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

const PAGES = ['maintenance.html', 'outage.html'] as const;

function read(page: string): string {
  return readFileSync(join(process.cwd(), 'public', page), 'utf8');
}

/**
 * ⛔ **HTML comments only** — `<!-- … -->` cannot nest and cannot appear
 * inside a string in HTML, so this needs none of
 * [B-162](../../../docs/BUGS.md)'s quote tracking. ⚡ **The reason it is
 * simple is stated so nobody later assumes it was overlooked.**
 */
function code(html: string): string {
  return html.replace(/<!--[\s\S]*?-->/g, '');
}

describe('🔴 no dependency on the application, its API or its session', () => {
  it.each(PAGES)('%s executes nothing', (page) => {
    const html = code(read(page));
    // Nothing to run means nothing that can fail while everything else has.
    expect(html).not.toMatch(/<script/i);
    expect(html).not.toMatch(/\bon[a-z]+\s*=/i); // inline handlers
    expect(html).not.toMatch(/javascript:/i);
  });

  it.each(PAGES)('%s asks nothing of the network at load', (page) => {
    const html = code(read(page));
    // ⛔ The API is the thing that is unavailable; a webfont request to a down
    // origin blocks paint on the one page that must always paint.
    expect(html).not.toMatch(/fetch\(|XMLHttpRequest/i);
    expect(html).not.toMatch(/<link[^>]+stylesheet/i);
    expect(html).not.toMatch(/@import/i);
    expect(html).not.toMatch(/fonts\.(googleapis|gstatic)/i);
    expect(html).not.toMatch(/<img[^>]+src=["']http/i);
  });

  it.each(PAGES)('%s reads no session', (page) => {
    const html = code(read(page));
    expect(html).not.toMatch(/localStorage|sessionStorage|document\.cookie/i);
  });

  it.each(PAGES)('%s needs no build step — it is a file', (page) => {
    const html = read(page);
    // ⚡ Renders when opened from disk: a doctype, a head and a body, and
    // nothing that a bundler has to resolve first.
    expect(html.trimStart().toLowerCase()).toMatch(/^<!doctype html>/);
    expect(html).not.toMatch(/\{\{|\bimport\s|from ['"]/);
  });
});

describe('⚡ the guard can fire, which is the half a passing scan does not prove', () => {
  it('🔴 a real <script> in the body is caught', () => {
    // B-162's lesson: proving the scan passes on correct input says nothing
    // about whether it would catch bad input. Both halves, deliberately.
    const withScript = code('<!doctype html><body><script>alert(1)</script></body>');
    expect(withScript).toMatch(/<script/i);
  });

  it('⛔ and the WORD script inside a comment is not', () => {
    const commentOnly = code('<!doctype html><!-- no <script> here --><body></body>');
    expect(commentOnly).not.toMatch(/<script/i);
    // ⚠️ And the comment really was the thing being stripped, rather than the
    // input being empty — the failure mode of a strip that removes too much.
    expect(commentOnly).toMatch(/<body>/);
  });
});

describe('📁 the design’s grammar survives having no stylesheet', () => {
  it.each(PAGES)('%s names what happened in an h1', (page) => {
    // 📁 1.3.1 — "an h1 that names what happened, not 'Error'."
    const h1 = /<h1[^>]*>([^<]+)<\/h1>/.exec(code(read(page)));
    expect(h1).not.toBeNull();
    expect(h1?.[1]).not.toMatch(/^(error|500|503|oops)$/i);
  });

  it('⚡ severity differs between them, because a planned event is not a failure', () => {
    // 📁 "Severity picks the colour… brand for planned events, risk for
    // genuine failure." Maintenance is announced; an outage is not.
    const maintenance = code(read('maintenance.html'));
    const outage = code(read('outage.html'));
    const brand = (html: string) => /--brand:\s*(#[0-9a-f]{6})/i.exec(html)?.[1];
    expect(brand(maintenance)).toBeDefined();
    expect(brand(outage)).toBeDefined();
    expect(brand(maintenance)).not.toBe(brand(outage));
  });

  it('⛔ neither invents a duration', () => {
    /**
     * 📁 ***"Estimates are measured: every duration shown comes from real p75
     * telemetry."*** ⚡ **An unplanned outage has no telemetry to draw one
     * from — the system producing it is the system that is down** — so a
     * number here would be invented, and an invented estimate that overruns
     * is worse than none.
     */
    for (const page of PAGES) {
      const html = code(read(page));
      expect(html).not.toMatch(/back (in|within) \d+/i);
      expect(html).not.toMatch(/\b\d+\s*(minutes?|hours?)\b/i);
    }
  });
});
