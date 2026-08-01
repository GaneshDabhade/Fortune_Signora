'use client';

import type { ProductCatalog } from '@/lib/api/types';

/**
 * The catalog is the authority on which declarations still exist.
 *
 * **B-005.** Every declaration that cites a product is saved as a *complete
 * statement*, so each editor sends everything it holds — while rendering only
 * the entries whose product is still in the catalog. The two agreed until
 * somebody removed a product, and then the editor was sending an entry the
 * customer could not see. The server refused the whole request, correctly,
 * naming a product that was not on the screen; the customer's own edit never
 * reached the wire.
 *
 * **The rule, in one place because it is one rule.** Three editors need it and
 * three hand-written copies would be three chances to get it wrong — the same
 * reasoning that put `latest()` and `sold_products()` in one place on the
 * backend.
 *
 * ### Dropping is correct, and silence is not
 *
 * A customer who removes a product has said they no longer sell it, so its
 * description is history — and a version is a complete statement, which means
 * the next one simply does not carry it. **What would be wrong is doing that
 * quietly**: an entry disappearing from a stored declaration is exactly the
 * kind of change a customer is entitled to see coming, so the notice below
 * says it before the save rather than after.
 */
export function keptForCatalog<Entry>(
  entries: readonly Entry[],
  catalog: ProductCatalog,
  productIdOf: (entry: Entry) => string,
): { kept: Entry[]; dropped: number } {
  const sold = new Set(catalog.products.map((product) => product.id));
  const kept = entries.filter((entry) => sold.has(productIdOf(entry)));

  return { kept, dropped: entries.length - kept.length };
}

/**
 * What is about to be left behind, said before it happens.
 *
 * `role="status"` rather than `alert`: nothing is wrong and nothing has been
 * lost. It is a consequence of something the customer already chose to do, and
 * the last sentence is the one that matters — **the version holding it is
 * still stored**, which is the module's whole discipline made visible at the
 * one moment a customer might doubt it.
 */
export function DroppedWithTheirProduct({ count }: { count: number }) {
  if (count === 0) return null;

  return (
    <p role="status" className="text-sm leading-6 text-content-muted">
      {count === 1
        ? 'One entry here belongs to a product you no longer sell. Your next save will not carry it —'
        : `${count} entries here belong to products you no longer sell. Your next save will not carry them —`}{' '}
      the version that holds {count === 1 ? 'it' : 'them'} is kept.
    </p>
  );
}
