import { expect, test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import type { Plan, SavedPlan } from "../lib/types";

// Browser state tests deliberately stub account transport. Actual owner RLS is
// exercised in PostgreSQL tests, and real OTP/provider staging remains a gate.
test("workspace restores logs, handles failure, exports, deletes and clears logout state", async ({ page, request }) => {
  const start = new Date(); start.setUTCDate(start.getUTCDate() - 7);
  const response = await request.post("/api/plan", { data: { trail_id: "laugavegur", fitness: 1, weeks: 2, start_date: start.toISOString().slice(0, 10) } });
  expect(response.ok()).toBe(true);
  const plan: Plan = await response.json();
  const id = "aaaaaaaa-aaaa-4aaa-8aaa-aaaaaaaaaaaa";
  let signedIn = true, removed = false, failed = true;
  let logs: SavedPlan["logs"] = [];
  const detail = (): SavedPlan => ({ id, plan, logs, progress: { score: logs.length ? 17 : 0, completed: logs.length, total: 6, on_track: false, streak: 0, this_week_completed: 0, this_week_total: 3, label: "Keep building the habit" } });
  await page.route("**/api/auth", async (route) => {
    if (route.request().method() === "DELETE") signedIn = false;
    await route.fulfill({ json: { configured: true, user: signedIn ? { id: "owner" } : null } });
  });
  await page.route("**/api/workspace", (route) => route.fulfill({ json: { company: { id: "company", name: "Test walking group" }, billing_enabled: false } }));
  await page.route("**/api/plans", (route) => route.fulfill({ json: { plans: removed ? [] : [{ id, trail_id: plan.trail_id, trip_date: plan.trip_date }] } }));
  await page.route(`**/api/plans/${id}`, async (route) => {
    if (route.request().method() === "PATCH") {
      if (failed) { failed = false; await route.fulfill({ status: 503, json: { error: { code: "UNAVAILABLE", message: "Could not save this session. Try again." } } }); return; }
      const body = route.request().postDataJSON();
      logs = body.done ? [{ session_id: body.session_id, done_at: new Date().toISOString().slice(0, 10) }] : [];
    }
    if (route.request().method() === "DELETE") removed = true;
    await route.fulfill({ json: detail() });
  });
  await page.goto("/workspace");
  const open = () => page.getByRole("button", { name: `${plan.trail_id}, trip ${plan.trip_date}`, exact: true }).click();
  await open();
  const check = page.locator('.session input[type="checkbox"]').first();
  await check.click();
  await expect(page.getByRole("status")).toContainText("Could not save this session");
  await expect(check).not.toBeChecked();
  await check.click();
  await expect(check).toBeChecked();
  await expect(page.getByText("1 of 6 planned sessions completed.", { exact: false })).toBeVisible();
  await page.reload(); await open();
  await expect(page.locator('.session input[type="checkbox"]').first()).toBeChecked();
  await expect(page.locator('.session input:disabled')).not.toHaveCount(0);
  const ring = await page.locator(".ring").boundingBox();
  expect(Math.abs(ring!.width - ring!.height)).toBeLessThan(1);
  const exportBox = await page.getByRole("link", { name: "Export plan JSON" }).boundingBox();
  const deleteBox = await page.getByRole("button", { name: "Delete this plan", exact: true }).boundingBox();
  expect(exportBox!.y + exportBox!.height <= deleteBox!.y || exportBox!.x + exportBox!.width <= deleteBox!.x).toBe(true);
  const downloadPromise = page.waitForEvent("download");
  await page.getByRole("link", { name: "Export plan JSON" }).click();
  expect((await downloadPromise).suggestedFilename()).toBe("beready-plan.json");
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
  await page.screenshot({ path: `../docs/screenshots/${test.info().project.name}-workspace-progress.png`, fullPage: true });
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Delete this plan", exact: true }).click();
  await expect(page.getByText("No saved plans yet.", { exact: true })).toBeVisible();
  await page.evaluate(() => sessionStorage.setItem("beready:pending-plan", '{"version":1}'));
  await page.getByRole("button", { name: "Sign out", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Sign in to your workspace" })).toBeVisible();
  await expect(page.getByText("Test walking group", { exact: true })).toHaveCount(0);
  expect(await page.evaluate(() => sessionStorage.getItem("beready:pending-plan"))).toBeNull();
});

test("dated forecast displays measurements, source and freshness without clearance", async ({ page }) => {
  const trip = new Date(); trip.setUTCDate(trip.getUTCDate() + 7);
  const date = trip.toISOString().slice(0, 10);
  await page.route("**/api/conditions?*", (route) => route.fulfill({ json: {
    status: "live", date, checked_at: "2026-09-12T12:00:00+00:00", source: "Open-Meteo", source_url: "https://open-meteo.com/",
    summary: "Forecast for a representative point, not the entire route.", season_note: "Check local advice.", closure_status: "unknown",
    temperature_min: 2, temperature_max: 8, precipitation_mm: 3, wind_kmh: 25,
  } }));
  await page.goto("/plan?trail=laugavegur&fitness=1&weeks=6");
  await page.getByLabel("Optional hike date").fill(date);
  await expect(page.getByRole("heading", { name: "Forecast available", exact: true })).toBeVisible();
  await expect(page.getByText("2 to 8 °C", { exact: true })).toBeVisible();
  await expect(page.getByText("25 km/h", { exact: true })).toBeVisible();
  await expect(page.getByRole("link", { name: "Open-Meteo", exact: true })).toHaveAttribute("href", "https://open-meteo.com/");
  await expect(page.locator('time[dateTime="2026-09-12T12:00:00+00:00"]')).toBeVisible();
  await expect(page.getByText("Closure status is unknown.", { exact: false })).toBeVisible();
});

test("conditions transport failure leaves free plan usable", async ({ page }) => {
  await page.route("**/api/conditions?*", (route) => route.fulfill({ status: 503, json: { error: { code: "UNAVAILABLE", message: "Conditions are temporarily unavailable." } } }));
  await page.goto("/plan?trail=laugavegur&fitness=1&weeks=6");
  await expect(page.getByRole("heading", { name: "6-week preparation plan", exact: true })).toBeVisible();
  const trip = new Date(); trip.setUTCDate(trip.getUTCDate() + 14);
  await page.getByLabel("Optional hike date").fill(trip.toISOString().slice(0, 10));
  await expect(page.getByText("We could not load dated conditions. Your plan is still available.", { exact: true })).toBeVisible();
  await expect(page.getByRole("button", { name: "Save this plan", exact: true })).toBeEnabled();
});
