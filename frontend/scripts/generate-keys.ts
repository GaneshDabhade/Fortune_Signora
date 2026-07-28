/**
 * Generates an RS256 key pair for local development.
 *
 * Prints to stdout rather than writing files, so key material never lands on
 * disk by accident and never gets committed. In every deployed environment
 * keys come from AWS Secrets Manager (ADR-0022) and this script is not used.
 *
 * Usage:  npm run keys:generate
 */

import { generateKeyPair, exportPKCS8, exportSPKI } from 'jose';

const MODULUS_BITS = 2048;

async function main(): Promise<void> {
  const { privateKey, publicKey } = await generateKeyPair('RS256', {
    modulusLength: MODULUS_BITS,
    extractable: true,
  });

  const privatePem = await exportPKCS8(privateKey);
  const publicPem = await exportSPKI(publicKey);

  // Escaped to single lines so the output can be pasted directly into a .env
  // file, which is where this most often ends up going.
  const escape = (pem: string): string => pem.trim().replace(/\n/g, '\\n');

  process.stdout.write(
    [
      '# --- Local development signing keys (RS256) ---',
      '# NEVER commit these. NEVER use them in a deployed environment.',
      '# Production keys come from AWS Secrets Manager (ADR-0022).',
      '',
      '# frontend/.env.local — Next.js is the only tier that may hold the private key.',
      `SIGNORA_JWT_PRIVATE_KEY="${escape(privatePem)}"`,
      `SIGNORA_JWT_PUBLIC_KEY="${escape(publicPem)}"`,
      '',
      '# backend/.env — the API gets the PUBLIC key only, and must never be',
      '# given the private half (ADR-0026, 18-authentication.md).',
      `SIGNORA_JWT_PUBLIC_KEY="${escape(publicPem)}"`,
      '',
    ].join('\n'),
  );
}

main().catch((error: unknown) => {
  process.stderr.write(`Key generation failed: ${String(error)}\n`);
  process.exit(1);
});
