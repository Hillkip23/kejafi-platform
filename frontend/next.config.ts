import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  reactStrictMode: true,
  // Suppress hydration warnings from browser extensions
  onRecoverableError: (error) => {
    // Ignore hydration mismatch errors from extensions
    if (error.message?.includes("hydration") || error.message?.includes("fdprocessedid")) {
      return;
    }
    console.error(error);
  },
};

export default nextConfig;
