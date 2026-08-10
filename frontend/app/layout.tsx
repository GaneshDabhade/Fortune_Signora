import type { Metadata } from 'next';
import { Archivo } from 'next/font/google';

import { ToastProvider } from '@/components/ui/toast';
import { THEME_INIT_SCRIPT } from '@/lib/design/theme';
import { QueryProvider } from '@/lib/query/client';
import { ThemeProvider } from '@/lib/state/theme-provider';

import './globals.css';

/**
 * **Archivo — the Design System's body face**, and the reason it is loaded
 * here rather than declared and hoped for.
 *
 * `Fortune Signora Design System v2.dc.html` names it in its own token:
 * `--font-body: "Archivo", system-ui, sans-serif`. **Setting the token alone
 * left the face unavailable**, so the product rendered the system stack while
 * asserting it rendered Archivo — the class of defect §2 calls worse than the
 * absent version, because it is trusted.
 *
 * `next/font` self-hosts the files at build time and emits no request to a
 * third party at runtime, which is what keeps this compatible with §20c-2 and
 * with a customer's content policy.
 */
const archivo = Archivo({
  subsets: ['latin'],
  display: 'swap',
  variable: '--font-archivo',
});

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
      <body className={`${archivo.variable} min-h-screen antialiased`}>
        <QueryProvider>
          <ThemeProvider>
            <ToastProvider>{children}</ToastProvider>
          </ThemeProvider>
        </QueryProvider>
      </body>
    </html>
  );
}
