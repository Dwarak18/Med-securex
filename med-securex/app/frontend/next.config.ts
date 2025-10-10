import type {NextConfig} from 'next';

const nextConfig: NextConfig = {
  /* config options here */
  typescript: {
    ignoreBuildErrors: true,
  },
  eslint: {
    ignoreDuringBuilds: true,
  },
  images: {
    remotePatterns: [
      {
        protocol: 'https',
        hostname: 'picsum.photos',
        port: '',
        pathname: '/**',
      },
    ],
  },
  allowedDevOrigins: ["https://6000-firebase-afterlogo-1757784212134.cluster-yylgzpipxrar4v4a72liastuqy.cloudworkstations.dev"],
  experimental: {
  },
};

export default nextConfig;
