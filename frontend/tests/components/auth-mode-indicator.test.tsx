/**
 * **The mode a developer can read off the running app** —
 * [TASK-473](../../../docs/BACKLOG.md).
 *
 * ⚡ **The resolution is tested in `tests/unit/auth-mode.test.ts`.** ⛔ **These
 * are the two things only the rendered component can get wrong**: whether it
 * DISAPPEARS in production, and whether a screen reader user can hear what a
 * two-word badge means.
 */
import { render, screen } from '@testing-library/react';
import { afterEach, describe, expect, it } from 'vitest';

import { AuthModeIndicator } from '@/components/ui/auth-mode-indicator';

function inEnvironment(value: string | undefined) {
  if (value === undefined) delete process.env.SIGNORA_ENVIRONMENT;
  else process.env.SIGNORA_ENVIRONMENT = value;
  return render(<AuthModeIndicator />);
}

const original = process.env.SIGNORA_ENVIRONMENT;
afterEach(() => {
  if (original === undefined) delete process.env.SIGNORA_ENVIRONMENT;
  else process.env.SIGNORA_ENVIRONMENT = original;
});

describe('🔴 absent in production, and absent means absent', () => {
  it('⛔ renders NOTHING — not an empty wrapper a stylesheet could bring back', () => {
    // 📁 The row's Definition of Done: "the indicator is absent in production
    // builds, asserted by a test." A hidden element is not absent; it is one
    // `display: block` away from shipping.
    const { container } = inEnvironment('production');
    expect(container).toBeEmptyDOMElement();
  });

  it('⚡ and the same holds for any deployed environment, not just the word', () => {
    const { container } = inEnvironment('staging');
    expect(container).toBeEmptyDOMElement();
  });
});

describe('✅ it names the mode where a developer can see it', () => {
  it('an unconfigured clone says Development', () => {
    inEnvironment(undefined);
    expect(screen.getByText('Development')).toBeInTheDocument();
  });

  it('🔴 a demo stack says Demo data, which is the failure this row exists for', () => {
    /**
     * ⚠️ **A reviewer walking the first hour cannot otherwise tell whether
     * they signed in as a seeded account or created one**, and
     * 📁 [C-320](../../../docs/LANE_COORDINATION.md) measured that going
     * unnoticed for three days — *"every account that has ever existed in
     * Signora was created by `demo-users.ts`."*
     */
    inEnvironment('demo');
    expect(screen.getByText('Demo data')).toBeInTheDocument();
  });

  it('⚡ demo is the one that warns, and development is not', () => {
    // Tone is meaning here, not decoration: a developer knows where they are,
    // a reviewer looking at seeded data does not.
    const demo = inEnvironment('demo');
    const warned = demo.container.querySelector('[data-auth-mode="demo"]');
    expect(warned?.className).toContain('warning');

    const dev = inEnvironment('local');
    const neutral = dev.container.querySelector('[data-auth-mode="development"]');
    expect(neutral?.className).not.toContain('warning');
  });
});

describe('♿ two words with no sentence around them need an accessible name', () => {
  it('⚡ the name carries the question the badge answers, and the environment', () => {
    inEnvironment('demo');
    expect(
      screen.getByLabelText('Authentication mode: Demo data (demo)'),
    ).toBeInTheDocument();
  });
});
