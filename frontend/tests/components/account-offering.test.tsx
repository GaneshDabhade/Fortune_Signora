/**
 * What your company sells, read on one account's page.
 *
 * **Stage 2 of C-008**, and the risk it carries is not layout — it is a claim
 * nobody made. The same catalog appears on every account, so a section that
 * implied otherwise would have Signora saying *this company is a candidate for
 * this product*, which is matching, which has no owner (C-002). Most of these
 * tests are about the sentence that prevents it, and about the declaration the
 * ruling deliberately left off this page.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { WhatYouSell } from '@/components/intelligence/offering';
import type { BuyingCommittee, ProductCatalog } from '@/lib/api/types';

const SIGNAL = '11111111-1111-4111-8111-111111111111';
const RELAY = '22222222-2222-4222-8222-222222222222';

function catalog(overrides: Partial<ProductCatalog> = {}): ProductCatalog {
  return {
    version: 4,
    products: [
      { id: SIGNAL, name: 'Signal Cloud', description: 'Pipeline intelligence.' },
      { id: RELAY, name: 'Relay', description: '' },
    ],
    updated_at: new Date().toISOString(),
    updated_by: '33333333-3333-4333-8333-333333333333',
    ...overrides,
  };
}

function committee(overrides: Partial<BuyingCommittee> = {}): BuyingCommittee {
  return {
    version: 2,
    committees: [
      {
        product_id: SIGNAL,
        roles: [
          { title: 'VP of Revenue Operations', part: 'economic_buyer' },
          { title: 'Head of Sales', part: 'champion' },
        ],
      },
    ],
    updated_at: new Date().toISOString(),
    updated_by: '33333333-3333-4333-8333-333333333333',
    ...overrides,
  };
}

describe('the catalog is shown as a declaration, never as a finding', () => {
  it('names what the customer declared', () => {
    render(<WhatYouSell catalog={catalog()} committee={committee()} />);

    expect(screen.getByText('Signal Cloud')).toBeInTheDocument();
    expect(screen.getByText('Relay')).toBeInTheDocument();
  });

  it('says it is the same on every account', () => {
    /**
     * **The load-bearing sentence**, and the same job the competitor section's
     * first line does. Without it a reader takes a workspace declaration for
     * an account finding, and the product has asserted something it never
     * concluded.
     */
    render(<WhatYouSell catalog={catalog()} committee={committee()} />);

    expect(screen.getByText(/same on every account/i)).toBeInTheDocument();
  });

  it('says outright that no candidacy has been claimed', () => {
    render(<WhatYouSell catalog={catalog()} committee={committee()} />);

    expect(
      screen.getByText(/has not said this account is a candidate/i),
    ).toBeInTheDocument();
  });

  it('grades nothing', () => {
    // No fit, no verdict, no rank. `commercial_profile` records and computes
    // nothing (ADR-0035), and there is no field on either contract that could
    // carry a judgement.
    const { container } = render(
      <WhatYouSell catalog={catalog()} committee={committee()} />,
    );

    for (const verdict of ['match', 'fit', 'score', 'rank', 'recommend']) {
      expect(container.textContent?.toLowerCase()).not.toContain(verdict);
    }
  });
});

describe('the ideal customer is not on this page', () => {
  it('renders no ICP even though /business does', () => {
    /**
     * **The one decision here a later change must not quietly reverse.** An
     * ICP beside a real company is a comparison the reader completes whether
     * or not the product does — and C-008's ruling names two declarations
     * rather than three for exactly that reason. A seller who wants it opens
     * `/business` and compares knowingly.
     *
     * The component takes no ICP at all, so this asserts the *contract*: there
     * is no prop through which one could arrive.
     */
    const { container } = render(
      <WhatYouSell catalog={catalog()} committee={committee()} />,
    );

    for (const icp of ['who buys', 'ideal customer', 'industries', 'employees']) {
      expect(container.textContent?.toLowerCase()).not.toContain(icp);
    }
  });
});

describe('who has to agree', () => {
  it('names the roles declared for a product', () => {
    render(<WhatYouSell catalog={catalog()} committee={committee()} />);

    expect(screen.getByText('VP of Revenue Operations')).toBeInTheDocument();
    expect(screen.getByText('Head of Sales')).toBeInTheDocument();
  });

  it('says which part of the decision each role holds', () => {
    // The label comes from `components/commercial/vocabulary`, which is where
    // /business reads it. A second mapping here would be a second vocabulary.
    render(<WhatYouSell catalog={catalog()} committee={committee()} />);

    expect(screen.getByText(/economic buyer/i)).toBeInTheDocument();
  });

  it('names no individual, because Signora holds none', () => {
    // A role, never a person. No person's name enters the platform from any
    // source — ADR-0400's own first question, answered no — and naming who
    // holds a seat is Epic C's, not this slice's.
    render(<WhatYouSell catalog={catalog()} committee={committee()} />);

    expect(screen.queryByText(/@/)).not.toBeInTheDocument();
  });

  it('says nothing per product when no committee is declared at all', () => {
    // A fact true of every product is said once, not once per product — five
    // identical "nobody has said" lines is noise a reader learns to skip.
    render(
      <WhatYouSell catalog={catalog()} committee={committee({ committees: [] })} />,
    );

    expect(screen.queryByText(/nobody has said/i)).not.toBeInTheDocument();
  });

  it('says so on a product without one, once another product has one', () => {
    // Now the absence is informative: a colleague described one product and
    // not the other, and that gap is worth seeing.
    render(<WhatYouSell catalog={catalog()} committee={committee()} />);

    expect(screen.getByText(/nobody has said who has to agree/i)).toBeInTheDocument();
  });
});

describe('an undeclared catalog and a failed read are different facts', () => {
  it('renders nothing at all when nothing has been declared', () => {
    /**
     * Version 0 is the state every workspace starts in. A section explaining
     * its own absence on every account of a workspace that has not filled this
     * in would be noise on the page a seller lives on — the declaration screen
     * is where that prompt belongs.
     */
    const { container } = render(
      <WhatYouSell
        catalog={catalog({ version: 0, products: [], updated_at: null, updated_by: null })}
        committee={committee()}
      />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('renders nothing while the declaration is still loading', () => {
    const { container } = render(
      <WhatYouSell catalog={undefined} committee={undefined} />,
    );

    expect(container).toBeEmptyDOMElement();
  });

  it('says so when the read failed, rather than falling silent', () => {
    /**
     * **[C-226](../../../docs/LANE_COORDINATION.md)'s class.** Silence would
     * make an outage indistinguishable from a workspace that has declared
     * nothing — on the one screen where a seller would act on the difference.
     */
    render(<WhatYouSell catalog={undefined} committee={undefined} isError />);

    expect(screen.getByText(/could not load what your organization sells/i)).toBeVisible();
  });

  it('does not tell a customer their declaration was lost', () => {
    // The read failed; nothing was written. A sentence implying otherwise
    // would send somebody to re-type a catalog that is still there.
    render(<WhatYouSell catalog={undefined} committee={undefined} isError />);

    expect(screen.getByText(/has been lost/i)).toHaveTextContent(/nothing.*has been lost/i);
  });
});
