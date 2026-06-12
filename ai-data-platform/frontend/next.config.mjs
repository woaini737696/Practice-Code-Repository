/** @type {import('next').NextConfig} */
const nextConfig = {
  basePath: '/ai-data',
  output: 'export',
  trailingSlash: true,
  images: {
    unoptimized: true,
  },
};

export default nextConfig;
