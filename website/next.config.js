/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  basePath: '/WikiGraph',
  assetPrefix: '/WikiGraph/',
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;