import type { NextConfig } from "next";

const production = process.env.NODE_ENV === "production";
const csp = [
  "default-src 'self'", "base-uri 'self'", "object-src 'none'", "frame-ancestors 'none'",
  "form-action 'self'", "img-src 'self' data:", "font-src 'self' data:",
  "style-src 'self' 'unsafe-inline'",
  // Next hydration uses inline scripts. No untrusted HTML is rendered. A nonce
  // policy is a further deployment hardening option for fully dynamic hosting.
  `script-src 'self' 'unsafe-inline'${production ? "" : " 'unsafe-eval'"}`,
  `connect-src 'self'${production ? "" : " ws: wss:"}`,
].join("; ");

const nextConfig: NextConfig = {
  reactStrictMode: true,
  devIndicators: false,
  poweredByHeader: false,
  async headers() {
    return [{ source: "/(.*)", headers: [
      { key: "Content-Security-Policy", value: csp },
      { key: "X-Content-Type-Options", value: "nosniff" },
      { key: "X-Frame-Options", value: "DENY" },
      { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
      { key: "Permissions-Policy", value: "camera=(), microphone=(), geolocation=()" },
      ...(production ? [{ key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" }] : []),
    ] }];
  },
};
export default nextConfig;
