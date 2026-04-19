/**
 * @file next.config.ts
 * Next.js configuration for RAG Q&A Demo frontend.
 * - Enables strict mode, SWC minify, and experimental App Router features.
 * - Configures backend API proxying and CORS for local Docker Compose.
 * - Loads environment variables for runtime config.
 */

import type { NextConfig } from 'next';

// Read backend URL from env or fallback to Docker Compose default
const BACKEND_URL =
  process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000';

const nextConfig: NextConfig = {
  reactStrictMode: true,
  swcMinify: true,
  experimental: {
    appDir: true,
    typedRoutes: true,
  },
  // Enable CORS and API proxying for local development (Docker Compose)
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${BACKEND_URL}/api/:path*`,
      },
    ];
  },
  env: {
    NEXT_PUBLIC_BACKEND_URL: BACKEND_URL,
  },
  // Allow images from backend if needed (e.g., for citations with images)
  images: {
    remotePatterns: [
      {
        protocol: 'http',
        hostname: 'backend',
        port: '8000',
        pathname: '/**',
      },
      {
        protocol: 'http',
        hostname: 'localhost',
        port: '8000',
        pathname: '/**',
      },
    ],
  },
};

export default nextConfig;
