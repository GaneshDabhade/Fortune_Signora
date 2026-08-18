/**
 * **The entry resolver's loading boundary** —
 * 📁 `Fortune Signora Authenticated Entry.dc.html`.
 *
 * ⛔ **It renders nothing visible, and that is the specification.** 📁 The
 * sole-workspace rule is *"enter it. **No confirmation, no picker, no
 * interstitial**"* — and a skeleton on the way to a redirect is an interstitial
 * that flashes on every sign-in.
 *
 * ⚡ **The shell is already painted around this.** 📁 The design's budget is
 * *"shell painted under 400ms from resolution"*; the rail, top bar and frame
 * are the layout's, and this segment only decides where to go next.
 *
 * ♿ **A live region rather than an empty fragment**, so a screen-reader user
 * hears that something is happening instead of silence — the same sentence
 * [`page.tsx`](./page.tsx) uses once the segment has mounted.
 */
export default function Loading() {
  return (
    <div aria-busy="true" className="sr-only">
      <p role="status">Opening your organization.</p>
    </div>
  );
}
