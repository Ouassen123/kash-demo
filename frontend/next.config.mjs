/** @type {import('next').NextConfig} */
import { fileURLToPath } from 'url';
const __filename = fileURLToPath(import.meta.url);

const nextConfig = {
  reactStrictMode: false,
  compress: true,
  poweredByHeader: false,
  devIndicators: { buildActivity: false },
  assetPrefix: process.env.NEXT_PUBLIC_CDN_URL || undefined,
  experimental: {
    optimizePackageImports: ['lucide-react', 'recharts'],
  },
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      config.cache = {
        type: 'filesystem',
        buildDependencies: { config: [__filename] },
      };
    }
    return config;
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: '**.githubusercontent.com',
      },
    ],
  },
};

export default nextConfig;
