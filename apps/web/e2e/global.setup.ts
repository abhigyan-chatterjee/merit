import { clerkSetup } from "@clerk/testing/playwright";
import { test as setup } from "@playwright/test";

// Project-based setup, not a function-based globalSetup: clerkSetup exports
// CLERK_FAPI and CLERK_TESTING_TOKEN, and those only reach the test workers
// when the setup runs as its own Playwright project. A function-based
// globalSetup runs in a separate process and the vars are lost.
setup.describe.configure({ mode: "serial" });

setup("fetch the Clerk testing token", async () => {
  // @clerk/testing reads CLERK_PUBLISHABLE_KEY; the repo's env file carries the
  // same value under a different name, so accept that rather than making the
  // owner rename a working key.
  process.env.CLERK_PUBLISHABLE_KEY ??= process.env.CLERK_TEST_PUBLISHABLE_KEY;

  // The token is what lets an automated sign-in past Clerk's bot detection. It
  // is fetched with the Secret Key, so with no secret key there is nothing to
  // fetch: skip instead of failing the run, since the auth specs already skip
  // themselves when CLERK_TEST_EMAIL / CLERK_TEST_PASSWORD are unset.
  setup.skip(
    !process.env.CLERK_PUBLISHABLE_KEY || !process.env.CLERK_SECRET_KEY,
    "CLERK_PUBLISHABLE_KEY / CLERK_SECRET_KEY not set — running without a testing token",
  );

  await clerkSetup();
});
