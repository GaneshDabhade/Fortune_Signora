/**
 * Mints a token using the real production issuance path, for the cross-tier
 * contract test.
 *
 * Deliberately imports `issueAccessToken` rather than reimplementing the
 * claim set: a hand-written token here would pass while production drifted,
 * which is precisely the failure this test exists to catch.
 *
 * Usage: tsx tests/contract/mint-token.ts <privateKeyPem> <issuer> <audience>
 * Emits the token on stdout.
 */

import { issueAccessToken } from '../../lib/auth/jwt';
import { loadPrivateKey } from '../../lib/auth/keys';

async function main(): Promise<void> {
  const [privatePem, issuer, audience] = process.argv.slice(2);

  if (!privatePem || !issuer || !audience) {
    process.stderr.write('usage: mint-token.ts <privateKeyPem> <issuer> <audience>\n');
    process.exit(2);
  }

  const token = await issueAccessToken(
    {
      userId: '3f6c8a1e-0000-4000-8000-000000000001',
      sessionId: 'sess_contract_test',
      email: 'contract@signora.test',
      emailVerified: true,
      activeWorkspaceId: '8b0f2c4d-0000-4000-8000-000000000002',
    },
    {
      issuer,
      audience,
      privateKey: await loadPrivateKey(privatePem),
    },
  );

  process.stdout.write(token);
}

main().catch((error: unknown) => {
  process.stderr.write(`mint failed: ${String(error)}\n`);
  process.exit(1);
});
