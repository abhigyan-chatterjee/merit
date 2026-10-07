import { test, expect, Page } from "@playwright/test";

/**
 * Judge round-trip through the real stack (web -> API -> sandbox).
 *
 * Guests may run and submit (both endpoints use optional auth), so no
 * Clerk test user is needed. These exercise the actual Python sandbox,
 * which is where the interesting failure modes live.
 */
const PROBLEM_URL = "/problems/arrays-hashing/two-sum";

const ACCEPTED = `def solve(nums, target):
    seen = {}
    for i, n in enumerate(nums):
        if target - n in seen:
            return [seen[target - n], i]
        seen[n] = i
    return []
`;

const WRONG = `def solve(nums, target):
    return [99, 99]
`;

async function submitCode(page: Page, code: string) {
  await page.goto(PROBLEM_URL);
  const editor = page.getByLabel("Code Editor");
  await expect(editor).toBeVisible();
  await editor.fill(code);
  await page.getByRole("button", { name: "Submit" }).click();
}

test.describe("judge round-trip", () => {
  test("accepts a correct solution", async ({ page }) => {
    await submitCode(page, ACCEPTED);
    await expect(page.getByText(/Accepted \(AC\)/)).toBeVisible({ timeout: 30_000 });
  });

  test("rejects a wrong solution", async ({ page }) => {
    await submitCode(page, WRONG);
    await expect(page.getByText(/Wrong Answer \(WA\)/)).toBeVisible({ timeout: 30_000 });
    await expect(page.getByText(/Accepted \(AC\)/)).toHaveCount(0);
  });

  test("runs samples without submitting", async ({ page }) => {
    await page.goto(PROBLEM_URL);
    await page.getByLabel("Code Editor").fill(WRONG);
    await page.getByRole("button", { name: /Run Samples/i }).click();
    // Either a verdict badge or the per-case results appear; the run must
    // not silently do nothing.
    await expect(
      page.getByText(/Wrong Answer \(WA\)|Accepted \(AC\)/),
    ).toBeVisible({ timeout: 30_000 });
  });
});
