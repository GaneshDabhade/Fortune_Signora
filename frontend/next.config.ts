import type { NextConfig } from 'next';

const config: NextConfig = {
  reactStrictMode: true,
  // Emits a self-contained server bundle with only the node_modules it
  // actually imports, so the production image carries no dev toolchain and
  // no unused dependency tree.
  output: 'standalone',
  // Fail the build on type or lint errors rather than shipping them.
  // A build that succeeds despite errors trains everyone to ignore them.
  typescript: { ignoreBuildErrors: false },
  eslint: { ignoreDuringBuilds: false },
};

export default config;
