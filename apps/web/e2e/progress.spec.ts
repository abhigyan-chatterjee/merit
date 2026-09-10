import { test, expect } from '@playwright/test';

test.describe('Progress Sync and Guest Import', () => {
  test('syncs problem progress across reloads for authenticated user', async ({ page }) => {
    const timestamp = Date.now();
    const user = {
      displayName: 'Progress Tester',
      email: `progresstester_${timestamp}@algovista.org`,
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

    // Visit two-sum problem detail page
    await page.goto('/problems/arrays-hashing/two-sum');
    await expect(page.getByRole('heading', { name: 'Two Sum' })).toBeVisible();

    // Toggle status to "Done"
    await page.getByLabel('Problem Status').selectOption('Done');

    // Reload page and verify status persists
    await page.reload();
    await expect(page.getByRole('heading', { name: 'Two Sum' })).toBeVisible();

    // Return to dashboard and verify 1/30 solved and Two Sum in resume section
    await page.goto('/dashboard');
    await expect(page.getByText('1/30').first()).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Two Sum' })).toBeVisible();
  });
});
