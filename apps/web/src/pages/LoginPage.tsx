import React from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { ClerkOAuthSection, isClerkConfigured } from "../components/ClerkOAuth";
import { SectionLabel } from "../components/ui/SectionLabel";
import { Reveal } from "../components/ui/Reveal";

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();

  const from = (location.state as { from?: string })?.from || "/dashboard";

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
            <ClerkOAuthSection mode="signin" onSuccess={() => navigate(from, { replace: true })} />
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
              Don&apos;t have an account yet?{" "}
              <Link
                to="/register"
                className="text-mint hover:underline font-mono font-medium inline-flex items-center gap-1"
              >
                <span>Register here</span>
                <ArrowRight className="w-3 h-3" />
              </Link>
            </p>
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
