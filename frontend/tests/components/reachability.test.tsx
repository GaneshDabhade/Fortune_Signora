/**
 * Every screen a customer can reach, and the ones nothing leads to.
 *
 * **The decisive test is the first one.** It reconstructs `/settings/connections`
 * exactly as it was before CX-01: two inbound links, both from the OAuth
 * redirect helpers *inside the connection flow itself*, and no door from
 * anywhere else. That shipped, passed every gate, and was found by a human
 * reading routes — so a check that does not catch it is not worth having.
 *
 * The live repository is asserted last and deliberately loosely: it passes today
 * and would pass identically with the rule deleted. **The constructed cases are
 * what prove the rule works.**
 */

import { execFileSync } from 'node:child_process';
import { mkdtempSync, mkdirSync, writeFileSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

import { afterEach, describe, expect, it } from 'vitest';

const REPO = join(__dirname, '..', '..', '..');
const scratch: string[] = [];

afterEach(() => {
  for (const path of scratch.splice(0)) rmSync(path, { recursive: true, force: true });
});

/**
 * Build an app tree and ask the checker what it makes of it.
 *
 * `extras` are files that are **not** routes — a navigation module, a guard
 * declaration — written into the same tree the checker scans, so a test can
 * assert what does *and does not* count as an entrance.
 */
function analyse(
  pages: Record<string, string>,
  extras: Record<string, string> = {},
): {
  reachable: string[];
  declared: string[];
  unreachable: string[];
} {
  const root = mkdtempSync(join(tmpdir(), 'reach-'));
  scratch.push(root);
  const app = join(root, 'app');
  for (const [route, source] of Object.entries(pages)) {
    const directory = join(app, route);
    mkdirSync(directory, { recursive: true });
    writeFileSync(join(directory, 'page.tsx'), source);
  }
  for (const [path, source] of Object.entries(extras)) {
    const file = join(app, path);
    mkdirSync(join(file, '..'), { recursive: true });
    writeFileSync(file, source);
  }
  const script = `
import json, sys, importlib.util
from pathlib import Path
spec = importlib.util.spec_from_file_location("reach", ${JSON.stringify(join(REPO, 'infra', 'reachability.py'))})
m = importlib.util.module_from_spec(spec); sys.modules["reach"] = m; spec.loader.exec_module(m)
app = Path(${JSON.stringify(app)})
reachable, declared, unreachable, _ = m.analyse(app=app, roots=(app,))
print(json.dumps({"reachable": reachable, "declared": declared, "unreachable": unreachable}))
`;
  return JSON.parse(execFileSync('python3', ['-c', script], { encoding: 'utf-8' }));
}

describe('a route nothing leads to', () => {
  it('catches the Connection Center exactly as it shipped', () => {
    // Before CX-01: the only links to /settings/connections were the two OAuth
    // redirect helpers inside the connection flow. A closed loop with no door.
    const result = analyse({
      '(app)/settings': 'export default () => <a href="/settings/products">Products</a>;',
      '(app)/settings/products': 'export default () => <p>products</p>;',
      '(app)/settings/connections':
        'export default () => <a href="/settings/connections">retry</a>;',
      '(app)/settings/connections/callback':
        'export default () => <a href="/settings/connections">back</a>;',
    });

    expect(result.unreachable).toContain('/settings/connections');
  });

  it('a naive inbound-link rule would have passed it — which is why the rule is stricter', () => {
    const result = analyse({
      '(app)/settings/connections':
        'export default () => <a href="/settings/connections">retry</a>;',
      '(app)/settings/connections/callback':
        'export default () => <a href="/settings/connections">back</a>;',
    });

    // Two inbound links exist. Both are inside the route's own subtree.
    expect(result.unreachable).toContain('/settings/connections');
  });

  it('one link from outside the subtree is a door', () => {
    // This is CX-01: Settings gained a Connections card.
    const result = analyse({
      '(app)/settings': 'export default () => <a href="/settings/connections">Connections</a>;',
      '(app)/settings/connections': 'export default () => <p>connections</p>;',
    });

    expect(result.reachable).toContain('/settings/connections');
    expect(result.unreachable).not.toContain('/settings/connections');
  });
});

describe('what counts as navigation', () => {
  it('a dynamic route is reached by a template literal', () => {
    const result = analyse({
      '(app)': 'export default () => <a href={`/accounts/${id}`}>open</a>;',
      '(app)/accounts/[accountId]': 'export default () => <p>brief</p>;',
    });

    expect(result.reachable).toContain('/accounts/[accountId]');
  });

  it('router.push is an entrance', () => {
    const result = analyse({
      '(app)': "export default () => { router.push('/settings'); };",
      '(app)/settings': 'export default () => <p>settings</p>;',
    });

    expect(result.reachable).toContain('/settings');
  });

  it('a query string does not hide the route', () => {
    const result = analyse({
      '(auth)/sign-in': "export default () => { router.push('/verify-email?email=x'); };",
      '(auth)/verify-email': 'export default () => <p>verify</p>;',
    });

    expect(result.reachable).toContain('/verify-email');
  });

  it('route groups never appear in a URL', () => {
    const result = analyse({ '(app)': 'export default () => <p>home</p>;' });

    expect([...result.reachable, ...result.declared, ...result.unreachable]).toContain('/');
  });
});

describe('the sidebar, which this check could not see until CX-05', () => {
  it('counts a route listed in a navigation array', () => {
    // **navigation.tsx holds its routes in an array** and renders them through
    // `<Link href={item.href}>`, so neither half matched any pattern. The
    // product's primary source of doors was invisible to the check that exists
    // to find missing doors.
    const result = analyse({
      '(app)': "export default () => <nav><Link href={i.href}>x</Link></nav>;",
      '(app)/business': 'export default () => <p>what we sell</p>;',
    });

    expect(result.unreachable).toContain('/business');

    const withNav = analyse({
      '(app)': `
        const ITEMS = [{ href: '/business', label: 'Your business' }];
        export default () => <nav>{ITEMS.map((i) => <Link href={i.href}>{i.label}</Link>)}</nav>;
      `,
      '(app)/business': 'export default () => <p>what we sell</p>;',
    });

    expect(withNav.reachable).toContain('/business');
  });

  it('reconstructs why nobody noticed — /settings had exactly one literal door', () => {
    // `/` is linked from six places and `/settings` from precisely one:
    // no-workspace.tsx. Delete that file and the check called the most-used
    // screen in the product an orphan.
    const result = analyse({
      '(app)': `
        const ITEMS = [{ href: '/settings', label: 'Settings' }];
        export default () => <nav>{ITEMS.map((i) => <Link href={i.href} />)}</nav>;
      `,
      '(app)/settings': 'export default () => <p>settings</p>;',
    });

    expect(result.unreachable).not.toContain('/settings');
  });

  it('does not mistake a guard declaration for an entrance', () => {
    // **GUARDED_ROUTES has the identical shape and the opposite meaning.**
    // Naming a route there restricts it; counting it would make a route
    // reachable because something forbade it. The rule that separates them is
    // whether the file renders links at all.
    const result = analyse(
      { '(app)/secret': 'export default () => <p>nobody sends you here</p>;' },
      {
        'permissions.ts':
          "export const GUARDED_ROUTES = [{ href: '/secret', requires: 'workspace:update' }];",
      },
    );

    expect(result.unreachable).toContain('/secret');
  });

  it('and the same declaration in a file that renders links is a door', () => {
    // The pair that makes the rule load-bearing rather than decorative: one
    // character of difference in the file, opposite verdicts.
    const result = analyse(
      { '(app)/secret': 'export default () => <p>a door leads here</p>;' },
      {
        'sidebar.tsx':
          "const ITEMS = [{ href: '/secret' }];\nexport const Nav = () => <Link href={ITEMS[0].href} />;",
      },
    );

    expect(result.unreachable).not.toContain('/secret');
  });
});

describe('routes entered from outside the product', () => {
  it('are declared with a reason rather than silently exempt', () => {
    const result = analyse({ '(auth)/reset-password': 'export default () => <p>reset</p>;' });

    // Reached from an email, by design — a decision, not an omission.
    expect(result.declared).toContain('/reset-password');
    expect(result.unreachable).not.toContain('/reset-password');
  });

  it('an undeclared route with no entrance is still a defect', () => {
    const result = analyse({ '(app)/orphan': 'export default () => <p>nobody sends you here</p>;' });

    expect(result.unreachable).toEqual(['/orphan']);
  });
});

describe('the live repository', () => {
  it('has no route without an entrance', () => {
    const output = execFileSync('python3', [join(REPO, 'infra', 'reachability.py')], {
      encoding: 'utf-8',
    });

    expect(output).toMatch(/No entrance at all\s+0/);
  });
});
