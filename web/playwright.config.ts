import { defineConfig } from "@playwright/test";
import { resolve } from "node:path";

export default defineConfig({
  testDir: "./e2e",
  timeout: 40_000,
  workers: 2,
  use: { baseURL: "http://localhost:3000", trace: "retain-on-failure" },
  projects: [
    { name: "desktop", use: { browserName: "chromium", viewport: { width: 1440, height: 1000 } } },
    { name: "mobile", use: { browserName: "chromium", viewport: { width: 320, height: 800 }, isMobile: true, hasTouch: true } },
  ],
  webServer: [
    { command: ".venv/bin/python -m uvicorn beready.api:app --host 127.0.0.1 --port 8000", env: { CONDITIONS_ENABLED: "false" }, cwd: resolve(__dirname, ".."), port: 8000, reuseExistingServer: false },
    { command: `npm run ${process.env.E2E_PRODUCTION === "true" ? "start" : "dev"} -- --port 3000`, env: { BEREADY_API_URL: "http://127.0.0.1:8000", APP_URL: "http://localhost:3000", SUPABASE_URL: "", BILLING_ENABLED: "false" }, port: 3000, reuseExistingServer: false },
  ],
});
