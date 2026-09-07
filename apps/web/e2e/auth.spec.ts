import { test, expect } from '@playwright/test';

test.describe('Authentication and User Isolation', () => {
  const timestamp = Date.now();
  const userA = {
    displayName: 'Alice Engineer',
    email: `alice_${timestamp}@algovista.org`,
    password: 'Password123!',
  };

  test('registers a new user, signs out, and logs in', async ({ page }) => {
    // 1. Visit Register page
    await page.goto('/register');
    await expect(page.getByRole('heading', { name: /Create an ALGOVISTA Account/i })).toBeVisible();

    // 2. Fill registration form
    await page.getByLabel(/Display Name/i).fill(userA.displayName);
    await page.getByLabel(/Email Address/i).fill(userA.email);
    await page.getByLabel(/^Password/i).fill(userA.password);
    await page.getByLabel(/Confirm Password/i).fill(userA.password);
    await page.getByRole('button', { name: /Create Account/i }).click();

    // 3. Should redirect to dashboard and show user in navbar
    await page.waitForURL('**/dashboard');
    await expect(page.getByText(userA.displayName)).toBeVisible();

    // 4. Sign out
    await page.getByTitle(/Sign out/i).click();
    await expect(page.getByRole('link', { name: /Sign In/i })).toBeVisible();

    // 5. Sign in
    await page.getByRole('link', { name: /Sign In/i }).click();
    await page.waitForURL('**/login');
    await page.getByLabel(/Email Address/i).fill(userA.email);
    await page.getByLabel(/^Password/i).fill(userA.password);
    await page.getByRole('button', { name: /Sign In/i }).click();

    // 6. Should redirect to dashboard and show user again
    await page.waitForURL('**/dashboard');
    await expect(page.getByText(userA.displayName)).toBeVisible();
  });

  test('multi-user session isolation across browser contexts', async ({ browser }) => {
    const contextA = await browser.newContext();
    const contextB = await browser.newContext();

    const pageA = await contextA.newPage();
    const pageB = await contextB.newPage();

    // Register user in context A
    const userUnique = {
      displayName: 'Bob Isolator',
      email: `bob_${Date.now()}@algovista.org`,
      password: 'StrongPassword123!',
    };

    await pageA.goto('/register');
    await pageA.getByLabel(/Display Name/i).fill(userUnique.displayName);
    await pageA.getByLabel(/Email Address/i).fill(userUnique.email);
    await pageA.getByLabel(/^Password/i).fill(userUnique.password);
    await pageA.getByLabel(/Confirm Password/i).fill(userUnique.password);
    await pageA.getByRole('button', { name: /Create Account/i }).click();
    await pageA.waitForURL('**/dashboard');
    await expect(pageA.getByText(userUnique.displayName)).toBeVisible();

    // Context B should NOT see user A and should be a guest
    await pageB.goto('/dashboard');
    await expect(pageB.getByRole('link', { name: /Sign In/i })).toBeVisible();
    await expect(pageB.getByText(userUnique.displayName)).not.toBeVisible();

    await contextA.close();
    await contextB.close();
  });
});
