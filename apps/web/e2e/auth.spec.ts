import { test, expect, Page } from "@playwright/test";
import { setupClerkTestingToken } from "@clerk/testing/playwright";

/**
 * Auth e2e against Clerk.
 *
 * Prerequisites:
 *   1. Build with a publishable key — VITE_CLERK_PUBLISHABLE_KEY in the
 *      environment or apps/web/.env (gitignored). Vite only inlines VITE_*
 *      vars, and only from apps/web, so the compose-root .env cannot reach the
 *      build.
 *   2. A test user with a password in the same Clerk instance, exported as
 *      CLERK_TEST_EMAIL / CLERK_TEST_PASSWORD.
 *   3. Optional but recommended: CLERK_PUBLISHABLE_KEY and CLERK_SECRET_KEY, so
 *      e2e/global.setup.ts can fetch a Testing Token and the sign-in is not
 *      blocked by Clerk's bot detection. Without them these specs still run,
 *      just without a token.
 *
 * The suite skips when CLERK_TEST_EMAIL / CLERK_TEST_PASSWORD are absent, so an
 * environment with no Clerk test instance still runs everything else.
 */
const TEST_EMAIL = process.env.CLERK_TEST_EMAIL ?? "";
const TEST_PASSWORD = process.env.CLERK_TEST_PASSWORD ?? "";

async function signIn(page: Page): Promise<void> {
  // Must precede navigation: it installs the route that carries the token.
  if (process.env.CLERK_TESTING_TOKEN) {
    await setupClerkTestingToken({ page });
  }

  await page.goto("/login");

  // A build without a publishable key renders the fallback panel instead of the
  // Clerk form. Name that cause here, or this fails as a bare missing-element
  // error that says nothing about the actual mistake.
  await expect(
    page.getByText("Sign-in is not available in this environment"),
    "the built bundle has no VITE_CLERK_PUBLISHABLE_KEY — rebuild with it set",
  ).toHaveCount(0);

  // This instance presents sign-in as two steps: email, then password. The
  // submit reads "Continue" on the first and may read either on the second, so
  // match both — anchored, or it would also catch "Sign in with GitHub".
  const submit = () =>
    page.getByRole("button", { name: /^(continue|sign in)$/i });

  await page.getByLabel(/email address/i).fill(TEST_EMAIL);
  await submit().click();

  // By name, not label: Clerk renders a "Show password" button whose accessible
  // name also matches /password/i, and getByLabel resolves to both.
  const password = page.locator('input[name="password"]');
  await password.waitFor({ state: "visible" });
  await password.fill(TEST_PASSWORD);
  await submit().click();

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
