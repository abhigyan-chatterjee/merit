import { test, expect, Page } from "@playwright/test";

/**
 * Auth e2e against Clerk's test mode.
 *
 * Prerequisites (both live in your Clerk dashboard, test-mode instance):
 *   1. Build with a test-mode publishable key — set
 *      VITE_CLERK_PUBLISHABLE_KEY in the environment or
 *      apps/web/.env (gitignored) before running the suite.
 *   2. Create a test user with a password in the test-mode
 *      instance, then export its credentials:
 *      CLERK_TEST_EMAIL, CLERK_TEST_PASSWORD
 *
 * The suite skips these tests when the credentials are absent,
 * so environments without a Clerk test instance still run
 * everything else. The specs are unverified against real Clerk
 * until a test-mode user exists — treat first run as the review.
 */
const TEST_EMAIL = process.env.CLERK_TEST_EMAIL ?? "";
const TEST_PASSWORD = process.env.CLERK_TEST_PASSWORD ?? "";

async function signIn(page: Page): Promise<void> {
  await page.goto("/login");

  // A build without a publishable key renders the fallback panel
  // instead of the Clerk form — fail loudly rather than time out
  // on selectors that can never appear.
  await expect(
    page.getByText("Sign-in is not available in this environment"),
  ).toHaveCount(0);

  await page.getByLabel(/email address/i).fill(TEST_EMAIL);
  await page.getByLabel(/password/i).fill(TEST_PASSWORD);
  await page.getByRole("button", { name: /sign in/i }).click();

  // Clerk redirects through /sso-callback (session-token exchange
  // against the API), then the app navigates to the dashboard.
  await page.waitForURL("**/dashboard", { timeout: 30_000 });
}

test.describe("auth (Clerk test mode)", () => {
  test.skip(
    !TEST_EMAIL || !TEST_PASSWORD,
    "CLERK_TEST_EMAIL / CLERK_TEST_PASSWORD not set (Clerk test-mode user)",
  );

  test("signs in through the Clerk form", async ({ page }) => {
    await signIn(page);

    // The navbar's account toggle carries the signed-in identity
    // in its title: "Signed in as <displayName> (<email>)".
    const account = page.getByTitle(/^Signed in as /);
    await expect(account).toBeVisible();

    const escaped = TEST_EMAIL.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
    await expect(account).toHaveAttribute(
      "title",
      expect.stringMatching(new RegExp(escaped)),
    );
  });

  test("session survives a reload", async ({ page }) => {
    await signIn(page);
    await page.reload();
    // AuthProvider restores the user from the httpOnly session
    // cookie via GET /auth/me on mount.
    await expect(page.getByTitle(/^Signed in as /)).toBeVisible();
  });

  test("signing out clears the session", async ({ page }) => {
    await signIn(page);

    await page.getByRole("button", { name: "Account menu" }).click();
    await page.getByRole("button", { name: "Sign out" }).click();

    // The account menu is rendered only for an authenticated user.
    await expect(page.getByRole("button", { name: "Account menu" })).toHaveCount(
      0,
    );
  });
});
