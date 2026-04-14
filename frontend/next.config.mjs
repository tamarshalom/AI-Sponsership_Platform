/** @type {import('next').NextConfig} */
const backendInternalUrl =
  process.env.BACKEND_INTERNAL_URL ?? "http://localhost:8000";

const nextConfig = {
  allowedDevOrigins: ["*.replit.dev", "*.kirk.replit.dev"],
  /** When file watchers fail (e.g. EMFILE on macOS), use `npm run dev:poll` so routes compile. */
  webpack(config, { dev }) {
    if (dev && process.env.WATCHPACK_POLLING === "true") {
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
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
