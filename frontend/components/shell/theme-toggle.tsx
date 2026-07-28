'use client';

import { Monitor, Moon, Sun } from 'lucide-react';

import { cn } from '@/lib/design/cn';
import { THEMES, type Theme } from '@/lib/design/theme';
import { useTheme } from '@/lib/state/theme-provider';

const ICONS: Record<Theme, typeof Sun> = {
  light: Sun,
  dark: Moon,
  system: Monitor,
};

const LABELS: Record<Theme, string> = {
  light: 'Light theme',
  dark: 'Dark theme',
  system: 'Match system theme',
};

/**
 * A three-way segmented control rather than a two-way switch.
 *
 * "System" is a distinct choice, not the absence of one: a binary toggle
 * silently pins the user to whichever value they last touched and stops
 * following their OS, which people notice at dusk and cannot explain.
 */
export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div
      role="group"
      aria-label="Theme"
      className="inline-flex rounded border border-border bg-surface p-0.5"
    >
      {THEMES.map((option) => {
        const Icon = ICONS[option];
        const isActive = theme === option;
        return (
          <button
            key={option}
            type="button"
            aria-label={LABELS[option]}
            aria-pressed={isActive}
            onClick={() => setTheme(option)}
            className={cn(
              'rounded-sm p-1.5 transition-colors',
              isActive
                ? 'bg-accent text-accent-contrast'
                : 'text-content-muted hover:text-content',
            )}
          >
            <Icon className="h-4 w-4" />
          </button>
        );
      })}
    </div>
  );
}
