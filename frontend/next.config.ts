import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // Produces a small self-contained server in .next/standalone for the container image.
  output: "standalone",
};

export default nextConfig;
