import { test, expect } from "@playwright/test";

/**
 * Browse and exam flows. Signed-in paths need a Clerk test-mode user
 * (see auth.spec.ts); these cover the guest-visible surface plus the
 * navigation between list and detail.
 */
test.describe("problem browsing", () => {
  test("navigates from a topic list into a problem", async ({ page }) => {
    await page.goto("/problems/arrays-hashing");
    await page.getByRole("link", { name: "Two Sum", exact: true }).click();

    await expect(page).toHaveURL(/\/problems\/arrays-hashing\/two-sum$/);
    await expect(page.getByRole("heading", { name: "Two Sum" })).toBeVisible();
  });

  test("records a status change end-to-end", async ({ page }) => {
    await page.goto("/problems/arrays-hashing/two-sum");
    await page.getByLabel("Problem Status").selectOption("Done");
    await page.reload();
    // The choice is persisted client-side, so it survives the reload.
    await expect(page.getByLabel("Problem Status")).toHaveValue("Done");
  });
});

test.describe("exams", () => {
  test("lists the targeted exams", async ({ page }) => {
    await page.goto("/exams");
    await expect(page.getByRole("heading", { name: /Targeted exams/i })).toBeVisible();
    await expect(page.getByText(/Foundational DSA/i)).toBeVisible();
  });

  test("asks a guest to sign in before starting an exam", async ({ page }) => {
    await page.goto("/exams/foundational-dsa");
    await expect(page.getByRole("heading", { name: /Foundational DSA/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /Sign in to start exam/i })).toBeVisible();
  });
});
