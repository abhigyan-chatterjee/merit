import { test, expect } from '@playwright/test';

test.describe('Judge Sandboxed Execution and Submission', () => {
  test('runs sample test cases and submits solution to obtain AC', async ({ page }) => {
    const timestamp = Date.now();
    const user = {
      displayName: 'Judge E2E Tester',
      email: `judgetester_${timestamp}@algovista.org`,
      password: 'StrongPassword123!',
    };

    // Register user
    await page.goto('/register');
    await page.getByLabel(/Display Name/i).fill(user.displayName);
    await page.getByLabel(/Email Address/i).fill(user.email);
    await page.getByLabel(/^Password/i).fill(user.password);
    await page.getByLabel(/Confirm Password/i).fill(user.password);
    await page.getByRole('button', { name: /Create Account/i }).click();
    await page.waitForURL('**/dashboard');

    // Go to Two Sum
    await page.goto('/problems/arrays-hashing/two-sum');
    await expect(page.getByRole('heading', { name: 'Two Sum' })).toBeVisible();

    // The starter code for two-sum in content is already correct!
    // Let's click "Run Samples"
    const runBtn = page.getByRole('button', { name: /Run Samples/i });
    await runBtn.click();

    // Verify AC verdict appears on sample run
    await expect(page.getByText(/Accepted \(AC\)/i)).toBeVisible({ timeout: 10000 });

    // Click "Submit"
    const submitBtn = page.getByRole('button', { name: /Submit/i });
    await submitBtn.click();

    // Verify submission succeeds and shows AC
    await expect(page.getByText(/Accepted \(AC\)/i)).toBeVisible({ timeout: 10000 });

    // Open Submissions tab
    await page.getByRole('button', { name: /Submissions/i }).click();
    await expect(page.getByText('AC', { exact: true }).first()).toBeVisible();

    // Check dashboard to verify problem solved
    await page.goto('/dashboard');
    await expect(page.getByText('1/30').first()).toBeVisible();
  });
});
