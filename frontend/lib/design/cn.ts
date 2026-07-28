import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

/**
 * Merges class names, with later Tailwind utilities winning over earlier
 * ones in the same group.
 *
 * Plain `clsx` would emit `px-4 px-6` and leave the outcome to CSS source
 * order, which is not something a caller can reason about. `twMerge`
 * resolves it to `px-6`, so a component's `className` prop reliably
 * overrides its defaults — the property every variant-based component here
 * depends on.
 */
export function cn(...inputs: ClassValue[]): string {
  return twMerge(clsx(inputs));
}
