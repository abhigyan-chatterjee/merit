import React from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { ShieldCheck } from "lucide-react";
import { ClerkOAuthSection, isClerkConfigured } from "../components/ClerkOAuth";
import { SectionLabel } from "../components/ui/SectionLabel";
import { Reveal } from "../components/ui/Reveal";

export const isSafeLoginDestination = (value: string): boolean => {
  if (!value || !value.startsWith("/") || value.startsWith("//")) return false;
  if (/[\\\u0000-\u001f\u007f]/.test(value)) return false;
  try {
    const parsed = new URL(value, window.location.origin);
    return (
      parsed.origin === window.location.origin &&
      parsed.pathname.startsWith("/") &&
      !parsed.pathname.startsWith("//")
    );
  } catch {
    return false;
  }
};

export const getLoginDestination = (location: { search: string; state: unknown }): string => {
  const from = (location.state as { from?: string })?.from || "/dashboard";
  const requestedNext = new URLSearchParams(location.search).get("next");
  if (requestedNext && isSafeLoginDestination(requestedNext)) return requestedNext;
  return isSafeLoginDestination(from) ? from : "/dashboard";
};

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const next = getLoginDestination(location);

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        <Reveal>
          <div className="text-center space-y-2">
            <SectionLabel title="Account Authentication" />
            <h1 className="text-2xl font-mono font-bold text-ink tracking-tight">
              Sign in to MERIT
            </h1>
            <p className="text-xs text-muted">
              Sync your problem submissions, quiz exposure, and learning progress.
            </p>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          {isClerkConfigured() ? (
            <ClerkOAuthSection mode="signin" onSuccess={() => navigate(next, { replace: true })} />
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
          <div className="flex justify-center text-center text-xs">
            <div className="flex items-center gap-2 text-[11px] text-muted/70 font-mono">
              <ShieldCheck className="w-3.5 h-3.5 text-mint" />
              <span>Secure Clerk authentication · Zero tracking</span>
            </div>
          </div>
        </Reveal>
      </div>
    </div>
  );
};
