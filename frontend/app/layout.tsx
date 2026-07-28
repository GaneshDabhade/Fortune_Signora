import type { Metadata } from 'next';

import { ToastProvider } from '@/components/feedback/toast';
import { THEME_INIT_SCRIPT } from '@/lib/design/theme';
import { QueryProvider } from '@/lib/query/client';
import { ThemeProvider } from '@/lib/state/theme-provider';

import './globals.css';

export const metadata: Metadata = {
  title: 'Signora',
  description: 'AI Revenue Intelligence Platform',
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    // suppressHydrationWarning because the inline script below mutates
    // `data-theme` before React hydrates. The attribute is expected to
    // differ from the server-rendered value; warning about it would train
    // everyone to ignore hydration warnings generally.
    <html lang="en" suppressHydrationWarning>
      <head>
        {/*
          Applies the stored theme before first paint. Without it the page
          renders light, then flips — and no amount of React-side work can
          prevent that, because hydration happens after the user has
          already seen the wrong colours.
        */}
        <script dangerouslySetInnerHTML={{ __html: THEME_INIT_SCRIPT }} />
      </head>
      <body className="min-h-screen antialiased">
        <QueryProvider>
          <ThemeProvider>
            <ToastProvider>{children}</ToastProvider>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
