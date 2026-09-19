import React, { useEffect, useState } from "react";
import { ClerkProvider, SignIn, SignUp, useAuth as useClerkAuth } from "@clerk/clerk-react";
import { AlertCircle } from "lucide-react";
import { useAuth } from "../store/AuthContext";

const PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;
// Optional custom Clerk JWT template name (must expose an email claim).
// When unset, the default Clerk session token is exchanged instead.
const JWT_TEMPLATE = import.meta.env.VITE_CLERK_JWT_TEMPLATE as string | undefined;

export const isClerkConfigured = (): boolean => Boolean(PUBLISHABLE_KEY);

interface BridgeProps {
  mode: "signin" | "signup";
  onSuccess: () => void;
  onError: (message: string) => void;
}

const ClerkBridge: React.FC<BridgeProps> = ({ mode, onSuccess, onError }) => {
  const { isSignedIn, getToken } = useClerkAuth();
  const { loginWithClerk } = useAuth();
  const [exchanged, setExchanged] = useState(false);

  useEffect(() => {
    if (!isSignedIn || exchanged) return;
    setExchanged(true);
    (async () => {
      const token = await getToken(JWT_TEMPLATE ? { template: JWT_TEMPLATE } : undefined);
      if (!token) {
        throw new Error("Could not retrieve a Clerk session token.");
      }
      await loginWithClerk(token);
      onSuccess();
    })().catch((err: unknown) => {
      setExchanged(false);
      onError(err instanceof Error ? err.message : "Social sign-in failed. Please try again.");
    });
  }, [isSignedIn, exchanged, getToken, loginWithClerk, onSuccess, onError]);

  return mode === "signin" ? <SignIn /> : <SignUp />;
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

const ClerkOAuthInner: React.FC<ClerkOAuthSectionProps> = ({ mode, onSuccess }) => {
  const [error, setError] = useState<string | null>(null);

  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <span className="h-px flex-1 bg-line" />
        <span className="text-[11px] font-mono uppercase tracking-wider text-muted">
          or continue with Google / GitHub
        </span>
        <span className="h-px flex-1 bg-line" />
      </div>
      {error && (
        <div
          role="alert"
          className="flex items-start gap-2.5 p-3 rounded-lg border border-rose/30 bg-rose/10 text-rose text-xs"
        >
          <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
          <span className="font-mono">{error}</span>
        </div>
      )}
      <div className="flex justify-center">
        <ClerkProvider publishableKey={PUBLISHABLE_KEY as string}>
          <ClerkBridge mode={mode} onSuccess={onSuccess} onError={setError} />
        </ClerkProvider>
      </div>
    </div>
  );
};
