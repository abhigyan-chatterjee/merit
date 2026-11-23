import React, { useEffect, useMemo, useRef, useState } from "react";
import { ClerkProvider, SignIn, SignUp, useAuth as useClerkAuth } from "@clerk/clerk-react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { SIGNOUT_PENDING_KEY, useAuth } from "../store/AuthContext";
import { useTheme } from "../store/ProgressContext";
import { ApiError } from "../utils/api";
import { isSafeLoginDestination } from "../utils/redirect";

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;
// Optional custom Clerk JWT template name (must expose an email claim).
// When unset, the default Clerk session token is exchanged instead.
const JWT_TEMPLATE = import.meta.env.VITE_CLERK_JWT_TEMPLATE as string | undefined;
const OAUTH_STATE_KEY = "merit.oauth.state";
// The destination has to survive a full-page trip to Clerk and back, so it is
// stashed next to the state nonce rather than passed through the component.
const OAUTH_NEXT_KEY = "merit.oauth.next";

export const isClerkConfigured = (): boolean => Boolean(PUBLISHABLE_KEY);

const oauthErrorMessage = (error: unknown): string => {
  const code = error instanceof ApiError ? error.code : (error as { code?: unknown })?.code;
  if (code === "OAUTH_EMAIL_MISSING" || code === "OAUTH_EMAIL_UNVERIFIED") {
    return "Your sign-in didn't include a verified email. Try another method or contact support.";
  }
  if (code === "OAUTH_NOT_CONFIGURED") {
    return "Sign-in is temporarily unavailable.";
  }
  return "Sign-in failed. Please try again.";
};

interface BridgeProps {
  mode: "signin" | "signup";
}

const ClerkBridge: React.FC<BridgeProps> = ({ mode }) => {
  const { isLoaded, isSignedIn, signOut } = useClerkAuth();
  const { user: meritUser } = useAuth();
  const signOutStartedRef = useRef(false);

  const [state] = useState(
    () => sessionStorage.getItem(OAUTH_STATE_KEY) || crypto.randomUUID(),
  );

  useEffect(() => {
    if (sessionStorage.getItem(OAUTH_STATE_KEY) !== state) {
      sessionStorage.setItem(OAUTH_STATE_KEY, state);
    }
  }, [state]);

  const inSsoCallback = typeof window !== "undefined" && window.location.hash.includes("sso-callback");

  useEffect(() => {
    if (!inSsoCallback && isLoaded && isSignedIn && !meritUser && !signOutStartedRef.current) {
      signOutStartedRef.current = true;
      try {
        sessionStorage.removeItem(OAUTH_STATE_KEY);
        sessionStorage.removeItem(SIGNOUT_PENDING_KEY);
      } catch {
        // ignore
      }
      void signOut().catch(() => {
        // ignore sign-out errors
      });
    }
  }, [inSsoCallback, isLoaded, isSignedIn, meritUser, signOut]);

  if (!inSsoCallback && isLoaded && isSignedIn && !meritUser) {
    return (
      <div className="flex flex-col items-center justify-center gap-3 text-center py-8">
        <RefreshCw className="w-6 h-6 text-mint animate-spin" />
        <span className="text-xs font-mono text-muted">Signing out…</span>
      </div>
    );
  }

  const callbackUrl = `/sso-callback?state=${encodeURIComponent(state)}`;

  return mode === "signin" ? (
    <SignIn
      appearance={{ elements: { footerAction: "hidden" } }}
      forceRedirectUrl={callbackUrl}
      signUpForceRedirectUrl={callbackUrl}
    />
  ) : (
    <SignUp
      appearance={{ elements: { footerAction: "hidden" } }}
      forceRedirectUrl={callbackUrl}
      signInForceRedirectUrl={callbackUrl}
    />
  );
};

interface ClerkOAuthSectionProps {
  mode: "signin" | "signup";
  /**
   * Where to land after sign-in. Stashed in sessionStorage because Clerk
   * redirects through a full page load, so a React callback cannot carry it.
   */
  next?: string;
}

/**
 * Social login via Clerk (Google/GitHub). Rendered ONLY on /login and
 * /register. Returns null when no `VITE_CLERK_PUBLISHABLE_KEY` is configured,
 * leaving password-only auth.
 */
export const ClerkOAuthSection: React.FC<ClerkOAuthSectionProps> = ({ mode, next }) => {
  if (!isClerkConfigured()) return null;
  return <ClerkOAuthInner mode={mode} next={next} />;
};

const ClerkOAuthInner: React.FC<ClerkOAuthSectionProps> = ({ mode, next }) => {
  const theme = useTheme();
  // Recorded before the redirect so the callback can restore it. Validated
  // again on read, since sessionStorage is not a trusted source.
  useEffect(() => {
    if (window.location.hash.includes("sso-callback")) return;
    if (next && isSafeLoginDestination(next)) {
      sessionStorage.setItem(OAUTH_NEXT_KEY, next);
    } else {
      sessionStorage.removeItem(OAUTH_NEXT_KEY);
    }
  }, [next]);

  const appearance = useMemo(() => ({
    variables: theme === 'dark' ? {
      colorBackground: '#12181f',
      colorInputBackground: '#0d1117',
      colorText: '#e6edf3',
      colorTextSecondary: '#8b949e',
      colorPrimary: '#3fb950',
      colorInputText: '#e6edf3',
      borderRadius: '0.75rem',
    } : {
      colorBackground: '#ffffff',
      colorInputBackground: '#f6f8fa',
      colorText: '#1f2328',
      colorTextSecondary: '#656d76',
      colorPrimary: '#1a7f37',
      colorInputText: '#1f2328',
      borderRadius: '0.75rem',
    },
    elements: {
      card: "bg-surface border border-line shadow-none",
      headerTitle: "text-ink",
      headerSubtitle: "text-muted",
      socialButtonsBlockButton: "bg-canvas border border-line text-ink hover:bg-surface",
      formFieldLabel: "text-ink",
      formFieldInput: "bg-canvas border-line text-ink",
      footer: "bg-surface border-t border-line",
      footerActionText: "text-muted",
      footerActionLink: "text-mint hover:underline",
    },
  }), [theme]);

  return (
    <div className="space-y-4">
      <div className="flex justify-center">
        <ClerkProvider
          publishableKey={PUBLISHABLE_KEY as string}
          appearance={appearance}
        >
          <ClerkBridge mode={mode} />
        </ClerkProvider>
      </div>
    </div>
  );
};

const ClerkSsoCallbackInner: React.FC = () => {
  const { isLoaded, isSignedIn, getToken } = useClerkAuth();
  const { loginWithClerk } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [error, setError] = useState<string | null>(null);
  const exchangePromiseRef = useRef<Promise<{ destination: string } | { error: string }> | null>(null);

  useEffect(() => {
    let cancelled = false;
    if (!isLoaded) return;
    if (!exchangePromiseRef.current) {
      exchangePromiseRef.current = (async () => {
        const expectedState = sessionStorage.getItem(OAUTH_STATE_KEY);
        const returnedState = new URLSearchParams(location.search).get("state");
        try {
          sessionStorage.removeItem(OAUTH_STATE_KEY);
        } catch {
          // ignore
        }
        if (!expectedState || !returnedState || returnedState !== expectedState) {
          return { error: "This sign-in attempt is invalid or has expired. Please sign in again." };
        }
        if (!isSignedIn) {
          return { error: "No active Clerk session was found. Please sign in again." };
        }
        try {
          const token = await getToken(JWT_TEMPLATE ? { template: JWT_TEMPLATE } : undefined);
          if (!token) {
            throw new Error("Could not retrieve a Clerk session token.");
          }
          await loginWithClerk(token);
          const stashedNext = sessionStorage.getItem(OAUTH_NEXT_KEY);
          try {
            sessionStorage.removeItem(OAUTH_NEXT_KEY);
          } catch {
            // ignore
          }
          const destination =
            stashedNext && isSafeLoginDestination(stashedNext) ? stashedNext : "/dashboard";
          return { destination };
        } catch (err: unknown) {
          return { error: oauthErrorMessage(err) };
        }
      })();
    }
    exchangePromiseRef.current.then((result) => {
      if (cancelled) return;
      if ("error" in result) {
        setError(result.error);
      } else {
        navigate(result.destination, { replace: true });
      }
    });
    return () => {
      cancelled = true;
    };
  }, [getToken, isLoaded, isSignedIn, location.search, loginWithClerk, navigate]);

  if (error) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center px-4">
        <div className="w-full max-w-md space-y-4 text-center">
          <div
            role="alert"
            className="flex items-start gap-2.5 p-3 rounded-lg border border-rose/30 bg-rose/10 text-rose text-xs text-left"
          >
            <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
            <span className="font-mono">{error}</span>
          </div>
          <Link to="/login" className="text-mint hover:underline font-mono text-xs">
            Back to login
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="flex min-h-[50vh] flex-col items-center justify-center gap-3 text-center">
      <RefreshCw className="w-6 h-6 text-mint animate-spin" />
      <span className="text-xs font-mono text-muted">Signing you in…</span>
    </div>
  );
};

export const ClerkSsoCallback: React.FC = () => {
  if (!isClerkConfigured()) {
    return (
      <div className="flex min-h-[50vh] items-center justify-center">
        <Link to="/login" className="text-mint hover:underline font-mono text-xs">
          Back to login
        </Link>
      </div>
    );
  }

  return (
    <ClerkProvider publishableKey={PUBLISHABLE_KEY as string}>
      <ClerkSsoCallbackInner />
    </ClerkProvider>
  );
};
