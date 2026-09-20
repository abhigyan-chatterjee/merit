import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";

const loginWithClerk = vi.fn();
const getToken = vi.fn();
let clerkState = { isLoaded: true, isSignedIn: true };
let signInProps: Record<string, unknown> = {};
let signUpProps: Record<string, unknown> = {};

vi.mock("@clerk/clerk-react", () => ({
  ClerkProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  SignIn: (props: Record<string, unknown>) => {
    signInProps = props;
    return <div>Mock Sign In</div>;
  },
  SignUp: (props: Record<string, unknown>) => {
    signUpProps = props;
    return <div>Mock Sign Up</div>;
  },
  useAuth: () => ({ ...clerkState, getToken }),
}));

vi.mock("../src/store/AuthContext", () => ({
  useAuth: () => ({ loginWithClerk }),
}));

describe("Clerk OAuth exchange", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_CLERK_PUBLISHABLE_KEY", "pk_test_callback");
    vi.resetModules();
    loginWithClerk.mockReset();
    getToken.mockReset();
    clerkState = { isLoaded: true, isSignedIn: true };
    signInProps = {};
    signUpProps = {};
    sessionStorage.clear();
  });

  it("exchanges a callback session and navigates to the dashboard", async () => {
    sessionStorage.setItem("merit.oauth.state", "test-state");
    getToken.mockResolvedValue("clerk-token");
    loginWithClerk.mockResolvedValue(undefined);
    const { ClerkSsoCallback } = await import("../src/components/ClerkOAuth");
    const LocationProbe = () => {
      const location = useLocation();
      return <span data-testid="location">{location.pathname}</span>;
    };

    render(
      <MemoryRouter initialEntries={["/sso-callback?state=test-state"]}>
        <ClerkSsoCallback />
        <LocationProbe />
      </MemoryRouter>
    );

    await waitFor(() => {
      expect(loginWithClerk).toHaveBeenCalledWith("clerk-token");
      expect(screen.getByTestId("location")).toHaveTextContent("/dashboard");
    });
  });

  it("shows the exchange error and a login link", async () => {
    sessionStorage.setItem("merit.oauth.state", "test-state");
    getToken.mockResolvedValue("clerk-token");
    loginWithClerk.mockRejectedValue(
      new (class extends Error {
        code = "OAUTH_NOT_CONFIGURED";
      })("Configure a Clerk JWT template before deploying")
    );
    const { ClerkSsoCallback } = await import("../src/components/ClerkOAuth");

    render(
      <MemoryRouter initialEntries={["/sso-callback?state=test-state"]}>
        <ClerkSsoCallback />
      </MemoryRouter>
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Sign-in is temporarily unavailable.");
    expect(screen.queryByText("Configure a Clerk JWT template before deploying")).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /Back to login/i })).toHaveAttribute("href", "/login");
  });

  it("forwards the callback URL to both Clerk widgets", async () => {
    const { ClerkOAuthSection } = await import("../src/components/ClerkOAuth");

    render(
      <ClerkOAuthSection mode="signin" onSuccess={vi.fn()} />
    );
    expect(signInProps.afterSignInUrl).toMatch(/^\/sso-callback\?state=.+/);

    render(
      <ClerkOAuthSection mode="signup" onSuccess={vi.fn()} />
    );
    expect(signUpProps.afterSignUpUrl).toMatch(/^\/sso-callback\?state=.+/);
  });

  it("aborts a callback with a missing or tampered state", async () => {
    sessionStorage.setItem("merit.oauth.state", "expected-state");
    getToken.mockResolvedValue("clerk-token");
    const { ClerkSsoCallback } = await import("../src/components/ClerkOAuth");

    render(
      <MemoryRouter initialEntries={["/sso-callback?state=tampered-state"]}>
        <ClerkSsoCallback />
      </MemoryRouter>
    );

    expect(await screen.findByRole("alert")).toHaveTextContent(
      "This sign-in attempt is invalid or has expired."
    );
    expect(loginWithClerk).not.toHaveBeenCalled();
    expect(sessionStorage.getItem("merit.oauth.state")).toBeNull();
  });
});
