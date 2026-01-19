/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: '/WikiGraph',
  // assetPrefix removed to prevent potential path resolution conflicts
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;