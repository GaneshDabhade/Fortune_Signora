/**
 * **The avatar area** — 📁 `Fortune Signora User Profile.dc.html` §01.
 *
 * 🔴 **Nothing rendered this component**, and it carried a paragraph
 * describing an interaction nobody can start.
 */
import { render, screen } from '@testing-library/react';
import { describe, expect, it } from 'vitest';

import { AvatarArea } from '@/app/(app)/profile/avatar-area';

describe('📁 what the avatar area may say about a capability that does not exist', () => {
  it('✅ it states the absence once, in the place the controls would be', () => {
    /**
     * 📁 **The design draws *Upload photo* and *Choose colour*, and Signora has
     * neither** — no image endpoint, no object-storage port reachable from the
     * frontend, nothing on the person's record carrying an avatar or a colour.
     *
     * ⛔ **So they are not rendered as disabled buttons** — 📁 this repository
     * has paid for that twice: *"an entry that leads nowhere advertises
     * absence"* and *"a disabled control would invite the question of who may
     * enable it."*
     */
    render(<AvatarArea name="Aurélie Duval" email="a.duval@northwind.com" />);

    expect(
      screen.getByText(/Uploading a photo and choosing a colour are not available yet/),
    ).toBeInTheDocument();
    expect(screen.queryByRole('button')).toBeNull();
    // ⛔ **And no file input substituted for the buttons**, which would be the
    // generic placeholder standing in for a designed control.
    expect(document.querySelector('input[type="file"]')).toBeNull();
  });

  it('⛔ and it does NOT describe the crop that upload would open', () => {
    /**
     * 🔴 **Removed 2026-08-27.** ⛔ *"Uploads open a square crop with pinch,
     * drag and a zoom slider"* sat directly beneath the sentence saying
     * uploading is unavailable. ⚠️ **One screen making both statements is the
     * screen contradicting itself**, and the reader who believes the second
     * goes looking for a control that is not there.
     *
     * 📁 **It is the design's own copy, and that is not sufficient**: in the
     * document it sits immediately below the two upload buttons, so it exists
     * to explain them. **Shipped without them it explains nothing reachable.**
     *
     * ⚠️ **DELETE THIS TEST when upload ships** — the panel comes back from the
     * design unchanged, and this assertion is then the wrong one.
     */
    const { container } = render(
      <AvatarArea name="Aurélie Duval" email="a.duval@northwind.com" />,
    );
    const text = container.textContent ?? '';

    expect(text).not.toContain('square crop');
    expect(text).not.toContain('Cropping');
    // ⚡ **The vacuity half** — the component must still render the parts that
    // describe what the avatar IS.
    expect(text).toContain('Initials on your brand colour');
  });

  it('⚡ the initials come from the name, because an address cannot produce them', () => {
    // 📁 The design draws *"AD"* for *Aurélie Duval*.
    render(<AvatarArea name="Aurélie Duval" email="a.duval@northwind.com" />);
    expect(screen.getByText('AD')).toBeInTheDocument();
  });

  it('⛔ and fall back to the address rather than to nothing', () => {
    // ⚡ **Somebody with no name is every SSO identity that publishes only an
    // address** — 📁 the absence must not render as an empty circle.
    const named = render(<AvatarArea name="Aurélie Duval" email="a.duval@northwind.com" />);
    const withName = named.container.textContent ?? '';
    named.unmount();

    const { container } = render(<AvatarArea name={null} email="a.duval@northwind.com" />);
    const withoutName = container.textContent ?? '';

    expect(withoutName).not.toContain('undefined');
    // ⛔ **The initials must still be SOMETHING** — ⚡ and something DIFFERENT
    // from the named case, or this passes on a component that ignores the
    // fallback entirely.
    expect(withoutName).not.toBe(withName);
    expect(withoutName).toContain('Avatar');
  });
});
