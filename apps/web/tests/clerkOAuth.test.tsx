import { StrictMode } from "react";
import { describe, expect, it, vi, beforeEach } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";

const loginWithClerk = vi.fn();
const getToken = vi.fn();
const clerkSignOut = vi.fn().mockResolvedValue(undefined);
let clerkState: { isLoaded: boolean; isSignedIn: boolean } = { isLoaded: true, isSignedIn: true };
let meritUser: unknown = null;
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
  useAuth: () => ({ ...clerkState, getToken, signOut: clerkSignOut }),
}));

vi.mock("../src/store/AuthContext", () => ({
  SIGNOUT_PENDING_KEY: "merit.clerk.signout_pending",
  useAuth: () => ({ loginWithClerk, user: meritUser }),
}));

describe("Clerk OAuth exchange", () => {
  beforeEach(() => {
    vi.stubEnv("VITE_CLERK_PUBLISHABLE_KEY", "pk_test_callback");
    vi.resetModules();
    loginWithClerk.mockReset();
    getToken.mockReset();
    clerkSignOut.mockReset();
    clerkSignOut.mockResolvedValue(undefined);
    clerkState = { isLoaded: true, isSignedIn: true };
    meritUser = null;
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
    clerkState = { isLoaded: true, isSignedIn: false };
    const { ClerkOAuthSection } = await import("../src/components/ClerkOAuth");

    render(
      <ClerkOAuthSection mode="signin" />
    );
    expect(signInProps.forceRedirectUrl).toMatch(/^\/sso-callback\?state=.+/);
    expect(signInProps.signUpForceRedirectUrl).toEqual(signInProps.forceRedirectUrl);

    render(
      <ClerkOAuthSection mode="signup" />
    );
    expect(signUpProps.forceRedirectUrl).toMatch(/^\/sso-callback\?state=.+/);
    expect(signUpProps.signInForceRedirectUrl).toEqual(signUpProps.forceRedirectUrl);
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

  it("keeps the state nonce in sync with sessionStorage under React StrictMode", async () => {
    clerkState = { isLoaded: true, isSignedIn: false };
    const { ClerkOAuthSection } = await import("../src/components/ClerkOAuth");

    render(
      <StrictMode>
        <ClerkOAuthSection mode="signin" />
      </StrictMode>
    );

    const url = String(signInProps.forceRedirectUrl ?? "");
    const urlState = new URLSearchParams(url.split("?")[1]).get("state");
    expect(urlState).toBeTruthy();
    expect(sessionStorage.getItem("merit.oauth.state")).toBe(urlState);
  });

  it("preserves an in-flight state nonce when Clerk returns to /login#/sso-callback", async () => {
    clerkState = { isLoaded: true, isSignedIn: false };
    sessionStorage.setItem("merit.oauth.state", "in-flight-nonce");
    const { ClerkOAuthSection } = await import("../src/components/ClerkOAuth");

    render(<ClerkOAuthSection mode="signin" />);

    expect(sessionStorage.getItem("merit.oauth.state")).toBe("in-flight-nonce");
    expect(signInProps.forceRedirectUrl).toBe("/sso-callback?state=in-flight-nonce");
  });

  it("completes the SSO callback cleanly under React StrictMode without invalidating state", async () => {
    sessionStorage.setItem("merit.oauth.state", "strict-state");
    getToken.mockResolvedValue("clerk-token");
    loginWithClerk.mockResolvedValue(undefined);
    const { ClerkSsoCallback } = await import("../src/components/ClerkOAuth");
    const LocationProbe = () => {
      const location = useLocation();
      return <span data-testid="location">{location.pathname}</span>;
    };

    render(
      <StrictMode>
        <MemoryRouter initialEntries={["/sso-callback?state=strict-state"]}>
          <ClerkSsoCallback />
          <LocationProbe />
        </MemoryRouter>
      </StrictMode>
    );

    await waitFor(() => {
      expect(loginWithClerk).toHaveBeenCalledTimes(1);
      expect(loginWithClerk).toHaveBeenCalledWith("clerk-token");
      expect(screen.getByTestId("location")).toHaveTextContent("/dashboard");
    });
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
  });

  it("when Clerk is signed in but Merit user is null on login, signs out Clerk and does not show SignIn", async () => {
    clerkState = { isLoaded: true, isSignedIn: true };
    meritUser = null;
    const { ClerkOAuthSection } = await import("../src/components/ClerkOAuth");

    render(<ClerkOAuthSection mode="signin" />);

    await waitFor(() => {
      expect(clerkSignOut).toHaveBeenCalled();
    });
    expect(screen.queryByText("Mock Sign In")).not.toBeInTheDocument();
    expect(screen.getByText(/Signing out/i)).toBeInTheDocument();
  });

  it("under StrictMode, shows error alert if loginWithClerk rejects during sso-callback", async () => {
    sessionStorage.setItem("merit.oauth.state", "strict-state");
    getToken.mockResolvedValue("clerk-token");
    loginWithClerk.mockRejectedValue(
      new (class extends Error {
        code = "OAUTH_NOT_CONFIGURED";
      })("Configure a Clerk JWT template before deploying")
    );
    const { ClerkSsoCallback } = await import("../src/components/ClerkOAuth");

    render(
      <StrictMode>
        <MemoryRouter initialEntries={["/sso-callback?state=strict-state"]}>
          <ClerkSsoCallback />
        </MemoryRouter>
      </StrictMode>
    );

    expect(await screen.findByRole("alert")).toHaveTextContent("Sign-in is temporarily unavailable.");
  });
});
