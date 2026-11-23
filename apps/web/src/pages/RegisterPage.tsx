import React from "react";
import { Link, useLocation } from "react-router-dom";
import { ArrowRight } from "lucide-react";
import { ClerkOAuthSection, isClerkConfigured } from "../components/ClerkOAuth";
import { Reveal } from "../components/ui/Reveal";
import { getLoginDestination } from "../utils/redirect";

export const RegisterPage: React.FC = () => {
  const location = useLocation();
  const next = getLoginDestination(location);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        <Reveal>
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-mono font-bold text-ink tracking-tight">
              Create account
            </h1>
            <p className="text-xs text-muted">
              Track your practice and revision in one place.
            </p>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          {isClerkConfigured() ? (
            <ClerkOAuthSection mode="signup" next={next} />
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

        <Reveal delay={0.15}>
          <div className="flex flex-col items-center gap-3 text-center text-xs">
            <p className="text-muted">
              Already have an account?{" "}
              <Link
                to="/login"
                className="text-mint hover:underline font-mono font-medium inline-flex items-center gap-1"
              >
                <span>Sign in</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </p>
          </div>
        </Reveal>
      </div>
    </div>
  );
};
