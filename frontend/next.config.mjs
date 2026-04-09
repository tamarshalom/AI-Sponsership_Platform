/** @type {import('next').NextConfig} */
const backendInternalUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig = {
  allowedDevOrigins: ["*.replit.dev", "*.kirk.replit.dev"],
  async rewrites() {
    return [
      {
        source: "/api/backend/:path*",
        destination: `${backendInternalUrl}/:path*`,
      },
    ];
  },
};

export default nextConfig;
