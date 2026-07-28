import { afterEach, vi } from 'vitest';

/**
 * Shared test setup.
 *
 * Runs for every file, including the node-environment unit tests, so
 * anything DOM-specific is guarded rather than assumed — importing
 * jest-dom unconditionally would fail the node tests at collection.
 */
if (typeof window !== 'undefined') {
  await import('@testing-library/jest-dom/vitest');
  const { cleanup } = await import('@testing-library/react');

  // Unmount between tests. Without it, queries match elements left behind
  // by a previous test and failures point at the wrong component.
  afterEach(cleanup);

  // jsdom implements neither of these, and shipped code uses both:
  // matchMedia by theme resolution, showModal by Dialog.
  Object.defineProperty(window, 'matchMedia', {
    writable: true,
    value: (query: string) => ({
      matches: false,
      media: query,
      onchange: null,
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      dispatchEvent: vi.fn(),
    }),
  });

  if (!HTMLDialogElement.prototype.showModal) {
    HTMLDialogElement.prototype.showModal = function showModal(this: HTMLDialogElement) {
      this.open = true;
    };
    HTMLDialogElement.prototype.close = function close(this: HTMLDialogElement) {
      this.open = false;
    };
  }
}
