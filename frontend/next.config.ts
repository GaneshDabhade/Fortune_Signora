import type { NextConfig } from 'next';

const config: NextConfig = {
  reactStrictMode: true,
  // Fail the build on type or lint errors rather than shipping them.
  // A build that succeeds despite errors trains everyone to ignore them.
  typescript: { ignoreBuildErrors: false },
  eslint: { ignoreDuringBuilds: false },
};

export default config;
