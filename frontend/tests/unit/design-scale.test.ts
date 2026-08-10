import { readFileSync } from 'node:fs';
import { join } from 'node:path';

import { describe, expect, it } from 'vitest';

/**
 * **The type and radius scales, against the design document itself** —
 * [TASK-1453](../../../docs/BACKLOG.md).
 *
 * ⛔ **This test does not carry the design's numbers.** It parses them out of
 * 📁 `docs/design-snapshot/screens/Fortune Signora Design System v2.dc.html`
 * and compares. 📁 [D-137](../../../docs/DECISION_REGISTER.md): *"each can
 * drift from the approved design, and the copy is always the one somebody
 * reads."* ⚡ **A test asserting `26` would be exactly that copy** — it would
 * keep passing after a design refresh changed the value.
 *
 * ⚠️ **This is the first test in the repository to pin a design VALUE.**
 * 📁 [D-154](../../../docs/DECISION_REGISTER.md)'s audit observed that
 * `design-tokens.test.tsx` *"pins no value, only the discipline"* — ✅ **that
 * was an observation of what existed, and this row makes the values the
 * point**: [TASK-1453](../../../docs/BACKLOG.md)'s Definition of Done is
 * *"every role in §04's `typeRows` exists as a token at the design's value."*
 * ⛔ **The discipline test is untouched and still governs membership.**
 */

const ROOT = join(process.cwd(), '..');
const DESIGN = join(
  ROOT,
  'docs/design-snapshot/screens/Fortune Signora Design System v2.dc.html',
);
const CSS = join(process.cwd(), 'app/globals.css');

/** 📁 §04 `typeRows` — `['Display', '--text-display', spec, size, …]`. */
function designTypeRows(): { name: string; px: number }[] {
  const source = readFileSync(DESIGN, 'utf8');
  const block = source.slice(source.indexOf('typeRows: ['));
  const rows = block.slice(0, block.indexOf('].map('));
  return [...rows.matchAll(/\['([^']+)',\s*'--[a-z-]+',\s*'[^']*',\s*([\d.]+),/g)].map(
    ([, name, px]) => ({ name: name as string, px: Number(px) }),
  );
}

/** 📁 §05 `radii` — `{ v: '999px', token: '--r-full', use: … }`. */
function designRadii(): { token: string; px: number }[] {
  const source = readFileSync(DESIGN, 'utf8');
  const block = source.slice(source.indexOf('radii: ['));
  const rows = block.slice(0, block.indexOf('\n      ],'));
  return [...rows.matchAll(/\{\s*v:\s*'(\d+)px',\s*token:\s*'(--r-[a-z]+)'/g)].map(
    ([, px, token]) => ({ token: token as string, px: Number(px) }),
  );
}

/** The value of a custom property in `globals.css`, in pixels. */
function tokenPx(name: string): number | null {
  const css = readFileSync(CSS, 'utf8');
  const match = css.match(new RegExp(`^\\s*${name}:\\s*([\\d.]+)(rem|px);`, 'm'));
  if (!match) return null;
  const [, value, unit] = match;
  return unit === 'rem' ? Number(value) * 16 : Number(value);
}

/**
 * 📁 **The internal name each design role is implemented under.**
 *
 * ⛔ **`Section` and `Body` map to names that do NOT match the design's
 * words, and that is correct** — 📁 [D-220](../../../docs/DECISION_REGISTER.md)
 * §10: *"if the implementation uses a different internal name but faithfully
 * implements the design, do not create a task."* ⚡ **Renaming them is churn
 * across the whole product for no visible change**, and it is
 * [TASK-1453](../../../docs/BACKLOG.md)'s own named risk.
 */
const ROLE_TOKEN: Readonly<Record<string, string>> = {
  Display: '--text-display',
  Title: '--text-title',
  Section: '--text-lg',
  Metric: '--text-metric',
  Body: '--text-sm',
  'Body strong': '--text-sm', // ⚡ Same size, different weight — not a step.
  Label: '--text-label',
  Caption: '--text-xs',
  'Column head': '--text-2xs',
};

describe('📁 the type scale is the design\'s, role for role', () => {
  it('⚡ the design document is readable and names nine roles', () => {
    // **Vacuity guard.** If the parse returned nothing, every assertion below
    // would iterate an empty list and pass over a scale that matched nothing.
    const rows = designTypeRows();
    expect(rows.length).toBe(9);
    expect(rows.map((r) => r.name)).toContain('Title');
  });

  it('✅ every role the design names has a token at the design\'s value', () => {
    for (const { name, px } of designTypeRows()) {
      const token = ROLE_TOKEN[name];
      // ⛔ **Asserted rather than asserted-away.** A design role this map does
      // not know is a role nothing implements, and `?? ''` would have hidden
      // it behind a null token lookup.
      expect(token, `no token mapped for design role "${name}"`).toBeDefined();
      expect(tokenPx(token as string), `${name} → ${token}`).toBe(px);
    }
  });

  it('🔴 the three this row added or corrected, named individually', () => {
    // ⚡ Stated separately from the loop above so a regression names itself.
    // ⛔ `Display` was 36px against the design's 40 — D-218 recorded the token
    // layer as exact, and D-220 corrects that to the COLOUR tokens only.
    expect(tokenPx('--text-display')).toBe(40);
    expect(tokenPx('--text-title')).toBe(26);
    expect(tokenPx('--text-metric')).toBe(30);
  });

  it('⛔ Section and Body keep their internal names', () => {
    /**
     * 🔴 **This row's named risk, asserted rather than remembered**: 📁
     * *"Renaming `--text-lg` and `--text-sm` to the design's words. They are
     * correct; renaming them is churn across the whole product and
     * [D-220](../../../docs/DECISION_REGISTER.md) §10 explicitly forbids it."*
     */
    const css = readFileSync(CSS, 'utf8');
    expect(css).toContain('--text-lg:');
    expect(css).toContain('--text-sm:');
    expect(css).not.toContain('--text-section:');
    expect(css).not.toContain('--text-body:');
  });
});

describe('📁 the radius scale, and the step that was missing', () => {
  it('⚡ the design names six radii', () => {
    const radii = designRadii();
    expect(radii.length).toBe(6);
    expect(radii.map((r) => r.token)).toContain('--r-full');
  });

  it('✅ --radius-full is 999px, the design\'s value', () => {
    /**
     * ⚠️ **The gap was not latent when this landed.** 📁
     * [TASK-1440](../../../docs/BACKLOG.md) shipped the account menu's avatar
     * on Tailwind's own `rounded-full` — 9999px, controlled by no token —
     * hours before this token existed. ⛔ **§05 assigns 999px to exactly that
     * control**: *"Avatar, status dot, count badge, progress track."*
     */
    const full = designRadii().find((r) => r.token === '--r-full');
    expect(full?.px).toBe(999);
    expect(tokenPx('--radius-full')).toBe(999);
  });

  it('✅ the dialog is at the design\'s 16px plane, not 12px', () => {
    // 📁 §05 gives `--r-xl` = 16px to *"Table plane, dialog, drawer, assistant
    // panel"*. ⛔ `dialog.tsx` was `rounded-lg` = 12px.
    const dialog = readFileSync(join(process.cwd(), 'components/ui/dialog.tsx'), 'utf8');
    expect(dialog).toContain('rounded-xl');
    expect(tokenPx('--radius-xl')).toBe(16);
  });

  it('✅ card padding is 20px on both axes', () => {
    // 📁 §05 `spacing`: *"Card padding — 20–24px, was 16px in v1."*
    // ⛔ It was `px-5 py-4` — the horizontal value migrated to v2 and the
    // vertical one did not, which is the shape of a half-finished migration.
    const card = readFileSync(join(process.cwd(), 'components/ui/card.tsx'), 'utf8');

    // ⚠️ **Over the class strings, not over the file.** ⛔ **A plain
    // `toContain('py-4')` failed on this file's own COMMENT**, which quotes
    // the old value to explain the change — **a test that reads prose is a
    // test that fails when the prose is right.**
    const classes = [...card.matchAll(/cn\('([^']*)'/g)].map(([, c]) => c as string);
    expect(classes.length).toBeGreaterThan(0);
    expect(classes.some((c) => /\bpy-4\b/.test(c))).toBe(false);
    expect(classes.some((c) => /\bp-5\b/.test(c))).toBe(true);
  });
});
