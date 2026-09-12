import { expect, test, type Page } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

async function choose(page: Page, weeks = 6) {
  await page.goto("/quickcheck");
  await page.getByRole("combobox", { name: "Trail", exact: true }).selectOption("laugavegur");
  await page.getByRole("radio", { name: "I don’t train", exact: true }).check();
  await page.getByRole("slider").fill(String(weeks));
}
async function screenshot(page: Page, state: string) {
  await page.screenshot({ path: `../docs/screenshots/${test.info().project.name}-${state}.png`, fullPage: true });
}
async function accessible(page: Page) {
  expect((await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa", "wcag21aa"]).analyze()).violations).toEqual([]);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
}

test.beforeEach(async ({ page }) => {
  page.on("pageerror", (error) => { throw error; });
});

test("initial state has facts but no selected level, verdict or date", async ({ page }) => {
  const response = await page.goto("/quickcheck");
  expect(response?.headers()["x-frame-options"]).toBe("DENY");
  expect(response?.headers()["content-security-policy"]).toContain("frame-ancestors 'none'");
  await expect(page.getByRole("heading", { name: "Choose your training level" })).toBeVisible();
  expect(await page.locator('input[type="radio"]:checked').count()).toBe(0);
  await expect(page.locator('input[type="date"]')).toHaveCount(0);
  await screenshot(page, "initial");
  await accessible(page);
  await page.getByRole("radio", { name: "I don’t train", exact: true }).focus();
  await page.keyboard.press("Space");
  await expect(page.getByRole("radio", { name: "I don’t train", exact: true })).toBeChecked();
});

test("all verdict states, real runway ticks and adaptive motivation", async ({ page }) => {
  await choose(page, 2);
  await expect(page.getByRole("heading", { name: "Too soon this time", exact: true })).toBeVisible();
  await screenshot(page, "too-soon");
  await page.getByRole("slider").fill("6");
  await expect(page.getByRole("heading", { name: "Tough but doable", exact: true })).toBeVisible();
  await expect(page.getByText("6 wk minimum", { exact: true })).toBeVisible();
  await expect(page.getByText("12 wk comfortable", { exact: true })).toBeVisible();
  const initialCrux = await page.locator(".challenge-list").innerText();
  await screenshot(page, "tight-runway");
  await accessible(page);
  await page.getByRole("slider").fill("12");
  await expect(page.getByRole("heading", { name: "Enough time to prepare", exact: true })).toBeVisible();
  await screenshot(page, "enough-time");
  await page.getByRole("radio", { name: "I train regularly", exact: true }).check();
  await expect(page.getByRole("heading", { name: "You're ready", exact: true })).toBeVisible();
  expect(await page.locator(".challenge-list").innerText()).not.toEqual(initialCrux);
  await screenshot(page, "ready");
});

test("full free plan and dates work without auth, with honest save and conditions states", async ({ page }) => {
  await choose(page);
  await page.getByRole("button", { name: "See my prep plan", exact: true }).click();
  await expect(page.getByRole("heading", { name: "6-week preparation plan", exact: true })).toBeVisible();
  await expect(page.getByText("Week 6", { exact: true })).toBeVisible();
  await expect(page.getByLabel("Email to save this plan")).toHaveCount(0);
  await page.getByRole("button", { name: "Save this plan", exact: true }).click();
  await expect(page.locator("main").getByRole("alert")).toContainText("Saving is unavailable");
  await screenshot(page, "free-plan");
  const date = new Date(); date.setUTCDate(date.getUTCDate() + 14);
  await page.getByLabel("Optional hike date").fill(date.toISOString().slice(0, 10));
  await expect(page.getByRole("heading", { name: "2-week preparation plan", exact: true })).toBeVisible();
  await expect(page.getByRole("heading", { name: "Too soon this time", exact: true })).toBeVisible();
  await expect(page.getByText("Live conditions unavailable", { exact: true })).toBeVisible();
  await screenshot(page, "dated-plan-conditions");
  await accessible(page);
});

test("discovery is static, keeps too-soon by default, filters and compares three", async ({ page }) => {
  await page.route("**/api/discover", () => { throw new Error("Discovery must not require the backend"); });
  await page.goto("/discover");
  await expect(page.locator(".trail-row")).toHaveCount(9);
  await expect(page.locator(".trail-row .status")).toHaveCount(0);
  await page.getByRole("radio", { name: "I don’t train", exact: true }).check();
  await page.getByRole("slider").fill("1");
  await expect(page.locator(".trail-row.toosoon")).toHaveCount(8);
  await page.getByLabel("Reachable in my time", { exact: true }).check();
  await expect(page.locator(".trail-row")).toHaveCount(1);
  await expect(page.locator(".trail-row")).toContainText("Dalsnuten");
  await page.getByLabel("In typical season now", { exact: true }).check();
  await expect(page.locator(".trail-row")).toHaveCount(1);
  await page.getByLabel("Reachable in my time", { exact: true }).uncheck();
  await page.getByLabel("In typical season now", { exact: true }).uncheck();
  await expect(page.locator(".trail-row")).toHaveCount(9);
  await screenshot(page, "discovery");
  const choices = page.locator('.trail-row input[type="checkbox"]');
  await choices.nth(0).check(); await choices.nth(1).check(); await choices.nth(2).check();
  await expect(choices.nth(3)).toBeDisabled();
  await page.getByRole("link", { name: "Compare selected trails", exact: true }).click();
  await expect(page.getByRole("heading", { name: "Compare trails", exact: true })).toBeVisible();
  await expect(page.getByRole("rowheader", { name: "Weeks needed", exact: true })).toBeVisible();
  await expect(page.getByRole("rowheader", { name: "Why it is worth it", exact: true })).toBeVisible();
  await screenshot(page, "compare-three");
  await accessible(page);
});

test("route validation and provider absence are recoverable", async ({ page }) => {
  await page.goto("/plan?trail=laugavegur&fitness=1&weeks=6");
  await expect(page.getByRole("heading", { name: "6-week preparation plan", exact: true })).toBeVisible();
  await screenshot(page, "plan-route");
  await page.goto("/plan?trail=unknown&fitness=0&weeks=6");
  await expect(page.getByRole("link", { name: /quick check/i })).toBeVisible();
  await page.goto("/workspace");
  await expect(page.getByRole("heading", { name: "Saving is not configured", exact: true })).toBeVisible();
  await screenshot(page, "workspace-unconfigured");
  await accessible(page);
});

test("guarded natural-language discovery does not replace explicit input state", async ({ page }) => {
  await page.goto("/discover");
  await page.getByLabel("Your question", { exact: true }).fill("What can I handle in Norway in eight weeks? I don't train");
  await page.getByRole("button", { name: "Ask BeReady", exact: true }).click();
  await expect(page.getByRole("status", { name: "Discovery answer" })).toContainText("Ranked by your readiness");
  await expect(page.getByRole("status", { name: "Discovery answer" }).locator("li")).toHaveCount(7);
  await expect(page.locator('.fitness input:checked')).toHaveCount(0);
  await screenshot(page, "ask-discovery");
});
