import React, { useEffect, useState } from "react";
import { ClerkProvider, SignIn, SignUp, useAuth as useClerkAuth } from "@clerk/clerk-react";
import { AlertCircle, RefreshCw } from "lucide-react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../store/AuthContext";
import { ApiError } from "../utils/api";

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;
// Optional custom Clerk JWT template name (must expose an email claim).
// When unset, the default Clerk session token is exchanged instead.
const JWT_TEMPLATE = import.meta.env.VITE_CLERK_JWT_TEMPLATE as string | undefined;
const OAUTH_STATE_KEY = "merit.oauth.state";

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
  const [state] = useState(() => {
    const value = crypto.randomUUID();
    sessionStorage.setItem(OAUTH_STATE_KEY, value);
    return value;
  });

  return mode === "signin" ? (
    <SignIn
      appearance={{ elements: { footerAction: "hidden" } }}
      afterSignInUrl={`/sso-callback?state=${encodeURIComponent(state)}`}
    />
  ) : (
    <SignUp
      appearance={{ elements: { footerAction: "hidden" } }}
      afterSignUpUrl={`/sso-callback?state=${encodeURIComponent(state)}`}
    />
  );
};

interface ClerkOAuthSectionProps {
  mode: "signin" | "signup";
  onSuccess: () => void;
}

/**
 * Social login via Clerk (Google/GitHub). Rendered ONLY on /login and
 * /register, alongside the untouched password form. Returns null when no
 * `VITE_CLERK_PUBLISHABLE_KEY` is configured, leaving password-only auth.
 */
export const ClerkOAuthSection: React.FC<ClerkOAuthSectionProps> = ({ mode, onSuccess }) => {
  if (!isClerkConfigured()) return null;
  return <ClerkOAuthInner mode={mode} onSuccess={onSuccess} />;
};

const ClerkOAuthInner: React.FC<ClerkOAuthSectionProps> = ({ mode }) => {
  return (
    <div className="space-y-4">
      <div className="flex justify-center">
        <ClerkProvider
          publishableKey={PUBLISHABLE_KEY as string}
          appearance={{
            variables: {
              colorBackground: '#12181f',
              colorInputBackground: '#0d1117',
              colorText: '#e6edf3',
              colorTextSecondary: '#8b949e',
              colorPrimary: '#3fb950',
              colorInputText: '#e6edf3',
              borderRadius: '0.75rem',
            },
            elements: {
              card: "bg-surface border border-line shadow-none",
              headerTitle: "text-ink",
              headerSubtitle: "text-muted",
              socialButtonsBlockButton: "bg-canvas border border-line text-ink hover:bg-surface-elevated",
              formFieldLabel: "text-ink",
              formFieldInput: "bg-canvas border-line text-ink",
              footer: "bg-surface border-t border-line",
              footerActionText: "text-muted",
              footerActionLink: "text-mint hover:underline",
            },
          }}
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
  const [attempted, setAttempted] = useState(false);

  useEffect(() => {
    if (!isLoaded || attempted) return;
    const expectedState = sessionStorage.getItem(OAUTH_STATE_KEY);
    const returnedState = new URLSearchParams(location.search).get("state");
    sessionStorage.removeItem(OAUTH_STATE_KEY);
    if (!expectedState || !returnedState || returnedState !== expectedState) {
      setError("This sign-in attempt is invalid or has expired. Please sign in again.");
      return;
    }
    if (!isSignedIn) {
      setError("No active Clerk session was found. Please sign in again.");
      return;
    }

    setAttempted(true);
    (async () => {
      const token = await getToken(JWT_TEMPLATE ? { template: JWT_TEMPLATE } : undefined);
      if (!token) {
        throw new Error("Could not retrieve a Clerk session token.");
      }
      await loginWithClerk(token);
      navigate("/dashboard", { replace: true });
    })().catch((err: unknown) => {
      setError(oauthErrorMessage(err));
    });
  }, [attempted, getToken, isLoaded, isSignedIn, location.search, loginWithClerk, navigate]);

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
