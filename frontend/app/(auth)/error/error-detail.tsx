'use client';

import { Copy } from 'lucide-react';
import { useSearchParams } from 'next/navigation';
import { useState } from 'react';

import { Button } from '@/components/ui';

/**
 * What the identity provider actually said.
 *
 * ⚡ **Both values are Better Auth's own query parameters** — `error` and
 * `error_description`, the OAuth 2.0 fields the provider returned, passed
 * through unchanged. **Nothing here is composed**: the design quotes the
 * provider verbatim (*"your identity provider returned: user not assigned to
 * this application"*) because a paraphrase is a claim about somebody else's
 * system.
 *
 * ⛔ **The design's heading names the provider — *"Okta rejected the
 * sign-in"* — and this one cannot.** Better Auth's error redirect carries no
 * provider, and the sign-in that failed is over. **Naming a guess would put a
 * wrong vendor in front of an IT team**, so the heading says what is certain
 * and the code below says the rest.
 */
export function ErrorDetail() {
  const params = useSearchParams();
  const code = params?.get('error') ?? null;
  const description = params?.get('error_description') ?? null;
  const [copied, setCopied] = useState(false);

  const reference = [code, description].filter(Boolean).join(' — ');

  return (
    <div className="flex flex-col gap-5">
      <p className="text-sm leading-6 text-content-muted">
        {description !== null ? (
          <>
            Your identity provider returned:{' '}
            <span className="font-medium text-content">{description}</span>. Signora
            cannot grant access your provider refuses — your IT team assigns it.
          </>
        ) : (
          // ⚠️ **The honest version of the same sentence when the provider sent
          // no description.** Inventing one would be putting words in another
          // company's system, and an IT team acts on the code either way.
          <>
            Your identity provider refused the sign-in and sent no reason. Signora
            cannot grant access your provider refuses — your IT team assigns it.
          </>
        )}
      </p>

      {reference === '' ? null : (
        <div className="flex items-center gap-2 rounded-lg bg-surface-sunken px-3 py-2.5">
          {/* The reference an IT team pastes into a ticket. It is the
              provider's own code, not one this screen made up — a generated
              identifier would be meaningless to the only people who can act
              on it. */}
          <code className="flex-1 break-all text-xs text-content-muted">{reference}</code>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            onClick={() => {
              void navigator.clipboard?.writeText(reference).then(() => setCopied(true));
            }}
          >
            <Copy aria-hidden className="h-3.5 w-3.5" />
            {copied ? 'Copied' : 'Copy'}
          </Button>
        </div>
      )}
    </div>
  );
}
