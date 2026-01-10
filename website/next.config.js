/** @type {import('next').NextConfig} */
const path = require('path');

const nextConfig = {
  output: 'export',
  basePath: '/WikiGraph',
  assetPrefix: '/WikiGraph/',
  images: {
    unoptimized: true,
  },
  webpack: (config) => {
    config.resolve.alias = {
      ...config.resolve.alias,
      'three': path.resolve(__dirname, 'node_modules/three'),
    };
    return config;
  },
};

module.exports = nextConfig;