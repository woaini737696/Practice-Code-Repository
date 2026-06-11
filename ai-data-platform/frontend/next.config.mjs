/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/ai-data',
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: 'http://127.0.0.1:8787/api/:path*',
      },
      {
        source: '/health',
        destination: 'http://127.0.0.1:8787/health',
      },
    ];
  },
};

export default nextConfig;
