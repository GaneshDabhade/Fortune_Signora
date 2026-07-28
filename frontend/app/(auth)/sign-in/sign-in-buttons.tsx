'use client';

import { useState } from 'react';

import { signIn } from '@/lib/auth/client';

const LABELS: Record<string, string> = {
  google: 'Continue with Google',
  microsoft: 'Continue with Microsoft',
};

export function SignInButtons({ providers }: { providers: string[] }) {
  const [pending, setPending] = useState<string | null>(null);

  return (
    <div className="space-y-3">
      {providers.map((provider) => (
        <button
          key={provider}
          type="button"
          disabled={pending !== null}
          onClick={() => {
            setPending(provider);
            void signIn(provider);
          }}
          className="w-full rounded-md border border-slate-300 bg-white px-4 py-2.5 text-sm font-medium transition hover:bg-slate-50 disabled:opacity-50"
        >
          {pending === provider ? 'Redirecting…' : (LABELS[provider] ?? provider)}
        </button>
      ))}
    </div>
  );
}
