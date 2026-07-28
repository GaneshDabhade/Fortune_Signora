import { loadAuthConfig, configuredProviders } from '@/lib/auth/config';

import { SignInButtons } from './sign-in-buttons';

/**
 * Sign-in page.
 *
 * Only providers with complete credentials are offered — rendering a button
 * for a half-configured provider produces a failure at the OAuth callback,
 * which is worse than not offering it at all.
 */
export default function SignInPage() {
  const providers = configuredProviders(loadAuthConfig());

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <div className="w-full max-w-sm space-y-6 rounded-lg border border-slate-200 bg-white p-8 shadow-sm">
        <div className="space-y-1">
          <h1 className="text-xl font-semibold">Sign in to Signora</h1>
          <p className="text-sm text-slate-500">AI Revenue Intelligence Platform</p>
        </div>

        {providers.length === 0 ? (
          <p className="rounded border border-amber-200 bg-amber-50 p-3 text-sm text-amber-800">
            No sign-in provider is configured. Set Google or Microsoft OAuth credentials.
          </p>
        ) : (
          <SignInButtons providers={providers} />
        )}
      </div>
    </main>
  );
}
