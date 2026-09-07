import { test, expect } from "@playwright/test";

test("landing page loads and displays title", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/Algovista/i);
});
