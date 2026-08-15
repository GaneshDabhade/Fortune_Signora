'use client';

import { useCallback, useEffect, useState } from 'react';

import {
  type Band,
  bandFor,
  bandForcesCollapse,
  collapseKey,
  deviceClassFor,
  railIsCollapsed,
  type DeviceClass,
} from './rail';

/**
 * **Rail collapse, remembered** — [TASK-1408](../../../docs/BACKLOG.md).
 *
 * > 📁 ***"`[` toggles collapse; the state persists per user, per device
 * > class."***
 *
 * ## ⚡ Why it starts expanded and corrects itself
 *
 * ⛔ **Reading `localStorage` during render breaks hydration**: the server has
 * no storage, so the markup it produced and the markup React expects would
 * disagree, and Next replaces the tree. **So the first paint is always the
 * expanded rail** and the stored preference is applied in an effect.
 *
 * ⚠️ **That means a collapsed rail flashes open for one frame**, and it is the
 * right trade: **the alternative is the rail being absent on the server**,
 * which moves the whole page and is far more visible than a rail that settles.
 *
 * ## ⛔ Why a failed read is not a failed hook
 *
 * `localStorage` throws in private modes and when a quota is exhausted. **A
 * navigation rail that disappears because a preference could not be read is a
 * worse outcome than a preference silently not applying**, so the failure is
 * swallowed *here specifically* — this is a cosmetic preference, and the
 * comparison is with [`copyable-id.tsx`](../../components/ui/copyable-id.tsx),
 * where a failed clipboard write is REPORTED because the person is relying on
 * it having happened.
 */
export interface RailCollapse {
  /** ⚡ **The EFFECTIVE state** — the band's answer where it has one, the
   * person's otherwise. 📁 [TASK-1473](../../../docs/BACKLOG.md), rule ⓐ. */
  collapsed: boolean;
  toggle: () => void;
  device: DeviceClass;
  /**
   * ⛔ **`false` where the band decides and the person cannot.**
   *
   * 📁 **At 1024–1279 the band forces 56px**, so a toggle would be a control
   * that changes nothing. ⚡ **The shell hides it rather than disabling it** —
   * *absent, never disabled*, the same rule the roster applies to a control
   * the server would refuse.
   */
  canToggle: boolean;
}

export function useRailCollapse(userId: string | null): RailCollapse {
  // ⚡ **The stored preference, which is NOT the same thing as the state.**
  // 📁 [TASK-1473](../../../docs/BACKLOG.md): at 1024–1279 the band overrides
  // it, and ⛔ **overriding it must not overwrite it** — somebody who prefers
  // an expanded rail keeps that preference while working on a small laptop,
  // and gets it back at 1280.
  const [preference, setPreference] = useState(false);
  const [device, setDevice] = useState<DeviceClass>('regular');
  // ⚡ **The band, measured alongside the device class**, because rule ⓐ needs
  // 1280 and the device class only knows 1024.
  const [band, setBand] = useState<Band>('laptop');

  // Device class first: the key depends on it, so a resize across the
  // breakpoint reads a different preference rather than rewriting one.
  useEffect(() => {
    const measure = () => {
      setDevice(deviceClassFor(window.innerWidth));
      setBand(bandFor(window.innerWidth));
    };
    measure();
    window.addEventListener('resize', measure);
    return () => window.removeEventListener('resize', measure);
  }, []);

  useEffect(() => {
    if (userId === null || userId === '') return;
    try {
      setPreference(window.localStorage.getItem(collapseKey(userId, device)) === 'true');
    } catch {
      // See the note above: a cosmetic preference must never cost the rail.
    }
  }, [userId, device]);

  const toggle = useCallback(() => {
    // ⛔ **Inert where the band decides.** 📁 Rule ⓐ — writing a preference the
    // person cannot see take effect would be a control reporting success for
    // nothing, and `[` reaches this the same way the button does.
    if (bandForcesCollapse(band)) return;
    setPreference((was) => {
      const next = !was;
      if (userId !== null && userId !== '') {
        try {
          window.localStorage.setItem(collapseKey(userId, device), String(next));
        } catch {
          // The toggle still works for this session; only the memory is lost.
        }
      }
      return next;
    });
  }, [userId, device, band]);

  // 📁 *"`[` toggles collapse."* ⛔ **Ignored while a field has focus** — a
  // seller typing an account name into search must not fold the navigation.
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key !== '[' || e.metaKey || e.ctrlKey || e.altKey) return;
      const el = document.activeElement;
      const typing =
        el instanceof HTMLInputElement ||
        el instanceof HTMLTextAreaElement ||
        (el instanceof HTMLElement && el.isContentEditable);
      if (typing) return;
      e.preventDefault();
      toggle();
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [toggle]);

  return {
    collapsed: railIsCollapsed(band, preference),
    toggle,
    device,
    canToggle: !bandForcesCollapse(band),
  };
}
