/** @type {import('next').NextConfig} */
const nextConfig = {
  output: 'export',
  images: {
    unoptimized: true,
  },
  // Ensure the app works on GitHub Pages subpaths
  // base_url: '/WikiGraph' // This depends on the repo name, I'll let user configure if needed
};

module.exports = nextConfig;
