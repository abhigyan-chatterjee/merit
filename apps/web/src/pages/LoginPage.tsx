import React from "react";
import { useLocation } from "react-router-dom";
import { ClerkOAuthSection, isClerkConfigured } from "../components/ClerkOAuth";
import { Reveal } from "../components/ui/Reveal";
import { getLoginDestination } from "../utils/redirect";

// Re-exported so existing callers and tests keep their import path.
export { getLoginDestination, isSafeLoginDestination } from "../utils/redirect";

export const LoginPage: React.FC = () => {
  const location = useLocation();

  const next = getLoginDestination(location);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        <Reveal>
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-mono font-bold text-ink tracking-tight">
              Sign in
            </h1>
            <p className="text-xs text-muted">
              Sync your progress across devices.
            </p>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          {isClerkConfigured() ? (
            <ClerkOAuthSection mode="signin" next={next} />
          ) : (
            <div className="rounded-lg border border-line bg-surface p-5 text-center">
              <p className="font-mono text-sm font-medium text-ink">
                Sign-in is not available in this environment.
              </p>
              <p className="mt-2 text-xs text-muted">
                Set VITE_CLERK_PUBLISHABLE_KEY and rebuild.
              </p>
            </div>
          )}
        </Reveal>
      </div>
    </div>
  );
};
