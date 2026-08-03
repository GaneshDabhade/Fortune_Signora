/**
 * What this company sells, read by somebody who cannot change it.
 *
 * **The screen that closes [C-008](../../../docs/LANE_COORDINATION.md)** — five
 * `member` read grants in `policy.csv` that reached no seller for a day short of
 * a year of the product's life, because every one of them landed on a screen
 * behind `workspace:update`.
 *
 * These assertions are what stop it becoming the authoring screen again: it
 * offers nothing a member cannot do, it grades nothing, and its emptiness
 * teaches rather than reports.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { CommercialProfile } from '@/components/commercial/profile';
import type {
  BuyingCommittee,
  CommercialFocus,
  IcpDeclaration,
  ProductCatalog,
  TargetAccountList,
} from '@/lib/api/types';

const DECLARED = '2026-07-14T00:00:00Z';

function catalog(overrides: Partial<ProductCatalog> = {}): ProductCatalog {
  return {
    version: 1,
    products: [{ id: 'p1', name: 'Signora Core', description: 'Commercial intelligence.' }],
    updated_at: DECLARED,
    updated_by: 'u1',
    ...overrides,
  };
}

function icp(overrides: Partial<IcpDeclaration> = {}): IcpDeclaration {
  return { version: 0, profiles: [], updated_at: null, updated_by: null, ...overrides };
}

function committee(overrides: Partial<BuyingCommittee> = {}): BuyingCommittee {
  return { version: 0, committees: [], updated_at: null, updated_by: null, ...overrides };
}

function focus(overrides: Partial<CommercialFocus> = {}): CommercialFocus {
  return {
    version: 0,
    products: [],
    objective: '',
    updated_at: null,
    updated_by: null,
    ...overrides,
  };
}

function targets(overrides: Partial<TargetAccountList> = {}): TargetAccountList {
  return { version: 0, accounts: [], updated_at: null, updated_by: null, ...overrides };
}

function profile(over: Partial<Parameters<typeof CommercialProfile>[0]> = {}) {
  return render(
    <CommercialProfile
      catalog={catalog()}
      icp={icp()}
      committee={committee()}
      focus={focus()}
      targets={targets()}
      authoringHref={null}
      {...over}
    />,
  );
}

describe('a business nobody has described', () => {
  it('says so once rather than five times', () => {
    // **Five declarations, one absence.** Five separate "not declared yet"
    // notes would be the same fact said five times to somebody who cannot act
    // on any of them.
    profile({ catalog: catalog({ version: 0, products: [], updated_at: null, updated_by: null }) });

    expect(screen.getByText(/nothing declared yet/i)).toBeInTheDocument();
  });

  it('teaches a member why the rest of the product is thin, and who can fix it', () => {
    // Principle 4: an empty state teaches rather than reports absence. A member
    // cannot author, so the useful thing to tell them is who can.
    profile({ catalog: catalog({ version: 0, products: [], updated_at: null, updated_by: null }) });

    expect(screen.getByText(/an owner can/i)).toBeInTheDocument();
  });

  it('offers an owner the way to fix it', () => {
    profile({
      catalog: catalog({ version: 0, products: [], updated_at: null, updated_by: null }),
      authoringHref: '/settings/products',
    });

    expect(screen.getByRole('link', { name: /declare what you sell/i })).toHaveAttribute(
      'href',
      '/settings/products',
    );
  });

  it('never offers a member a link the server would refuse', () => {
    // **A control that goes nowhere costs more trust than an absent one**
    // (principle 8) — the reasoning that refused option A for this whole item.
    profile({ catalog: catalog({ version: 0, products: [], updated_at: null, updated_by: null }) });

    expect(screen.queryByRole('link')).not.toBeInTheDocument();
  });
});

describe('what we sell', () => {
  it('names each product and what it does', () => {
    profile();

    expect(screen.getByText('Signora Core')).toBeInTheDocument();
    expect(screen.getByText('Commercial intelligence.')).toBeInTheDocument();
  });

  it('joins who buys it into one scannable line', () => {
    profile({
      icp: icp({
        version: 1,
        updated_at: DECLARED,
        profiles: [
          {
            product_id: 'p1',
            industries: ['Logistics'],
            countries: ['Germany'],
            employees: { minimum: 200, maximum: 2000 },
            notes: '',
          },
        ],
      }),
    });

    expect(screen.getByText(/Logistics · Germany · 200–2,000 people/)).toBeInTheDocument();
  });

  it('states a size the customer left half open', () => {
    profile({
      icp: icp({
        version: 1,
        updated_at: DECLARED,
        profiles: [
          {
            product_id: 'p1',
            industries: [],
            countries: [],
            employees: { minimum: 500, maximum: null },
            notes: '',
          },
        ],
      }),
    });

    expect(screen.getByText(/500\+ people/)).toBeInTheDocument();
  });

  it('names who has to agree, in the customer"s words', () => {
    profile({
      committee: committee({
        version: 1,
        updated_at: DECLARED,
        committees: [
          {
            product_id: 'p1',
            roles: [{ title: 'VP of Revenue Operations', part: 'economic_buyer' }],
          },
        ],
      }),
    });

    expect(screen.getByText('VP of Revenue Operations')).toBeInTheDocument();
    expect(screen.getByText('Economic buyer')).toBeInTheDocument();
  });

  it('never puts a pipeline word in front of a seller', () => {
    // ADR-0034. `economic_buyer` is the API's spelling; the reader gets theirs.
    const { container } = profile({
      committee: committee({
        version: 1,
        updated_at: DECLARED,
        committees: [{ product_id: 'p1', roles: [{ title: 'CFO', part: 'economic_buyer' }] }],
      }),
    });

    expect(container.textContent).not.toContain('economic_buyer');
    expect(container.textContent).not.toContain('product_id');
  });
});

describe('a fact true of every product is said once, not once per product', () => {
  it('states a missing ideal customer at the section when no product has one', () => {
    profile({
      catalog: catalog({
        products: [
          { id: 'p1', name: 'Core', description: '' },
          { id: 'p2', name: 'Signals', description: '' },
        ],
      }),
    });

    // One line, not two. Repeated identical notes are what a reader learns to
    // skip — and skipping is how they miss the one that appears later.
    expect(screen.getAllByText(/nobody has described who buys these yet/i)).toHaveLength(1);
    expect(screen.queryByText(/nobody has said yet/i)).not.toBeInTheDocument();
  });

  it('names the product that is missing one when another product has it', () => {
    profile({
      catalog: catalog({
        products: [
          { id: 'p1', name: 'Core', description: '' },
          { id: 'p2', name: 'Signals', description: '' },
        ],
      }),
      icp: icp({
        version: 1,
        updated_at: DECLARED,
        profiles: [
          { product_id: 'p1', industries: ['Logistics'], countries: [], employees: null, notes: '' },
        ],
      }),
    });

    // Now the absence is informative: one product has a buyer described and
    // one does not, which is a difference a seller can act on.
    expect(screen.getByText(/nobody has said yet/i)).toBeInTheDocument();
    expect(screen.queryByText(/nobody has described who buys these yet/i)).not.toBeInTheDocument();
  });
});

describe('what we are pushing', () => {
  it('is absent when nothing has been declared', () => {
    // **Absent, never present at zero** (R1-06 · D6) — a section that always
    // renders the same thing teaches people to skip that part of the page.
    profile();

    expect(screen.queryByText(/what we are pushing/i)).not.toBeInTheDocument();
  });

  it('leads when there is one, because it is the only declaration that expires', () => {
    profile({
      focus: focus({
        version: 1,
        objective: 'Land three logistics accounts before October.',
        products: ['p1'],
        updated_at: DECLARED,
      }),
    });

    expect(screen.getByText(/land three logistics accounts/i)).toBeInTheDocument();
  });

  it('names the products by name rather than by identifier', () => {
    const { container } = profile({
      focus: focus({ version: 1, objective: '', products: ['p1'], updated_at: DECLARED }),
    });

    // Twice: once here, once in the catalog below. The identifier is what the
    // declaration actually stores, and it must never reach the reader.
    expect(screen.getAllByText('Signora Core')).toHaveLength(2);
    expect(container.textContent).not.toContain('p1');
  });
});

describe('companies we are chasing', () => {
  it('is absent when none have been named', () => {
    profile();

    expect(screen.queryByText(/companies we are chasing/i)).not.toBeInTheDocument();
  });

  it('lists them when they have', () => {
    profile({
      targets: targets({
        version: 1,
        updated_at: DECLARED,
        accounts: [
          { id: 't1', name: 'Northwind Traders' },
          { id: 't2', name: 'Contoso' },
        ],
      }),
    });

    expect(screen.getByText(/Northwind Traders · Contoso/)).toBeInTheDocument();
  });
});

describe('provenance', () => {
  it('says when somebody last declared it', () => {
    // Principle 2. On a page a seller is asked to sell from, *how old is this*
    // is the question that decides whether they trust it.
    profile();

    expect(screen.getByText(/last declared/i)).toBeInTheDocument();
  });

  it('says nothing at version 0, where there is no date to give', () => {
    profile({ catalog: catalog({ version: 0, updated_at: null, updated_by: null }) });

    expect(screen.queryByText(/last declared/i)).not.toBeInTheDocument();
  });
});

describe('it reads; it never matches', () => {
  it('shows no score, rank or verdict about any account', () => {
    // **The boundary between stage 1 and stage 2 of the C-008 ruling.**
    // Comparing a real company to a description is matching, matching has no
    // owner (C-002), and Commercial Profile computes nothing (ADR-0035).
    const { container } = profile({
      icp: icp({
        version: 1,
        updated_at: DECLARED,
        profiles: [
          { product_id: 'p1', industries: ['Logistics'], countries: [], employees: null, notes: '' },
        ],
      }),
      targets: targets({
        version: 1,
        updated_at: DECLARED,
        accounts: [{ id: 't1', name: 'Northwind Traders' }],
      }),
    });

    const text = container.textContent?.toLowerCase() ?? '';
    for (const verdict of ['fit', 'match', 'score', 'rank', 'qualified']) {
      expect(text).not.toContain(verdict);
    }
  });
});
