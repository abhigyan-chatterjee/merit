import React from "react";
import { Link, useNavigate } from "react-router-dom";
import { ArrowRight, ShieldCheck } from "lucide-react";
import { ClerkOAuthSection } from "../components/ClerkOAuth";
import { SectionLabel } from "../components/ui/SectionLabel";
import { Reveal } from "../components/ui/Reveal";

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div className="min-h-[calc(100vh-4rem)] flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md space-y-6">
        <Reveal>
          <div className="text-center space-y-2">
            <SectionLabel title="New Student Registration" />
            <h1 className="text-2xl font-mono font-bold text-ink tracking-tight">
              Create a MERIT Account
            </h1>
            <p className="text-xs text-muted">
              Get an isolated, verified workspace for placement practice.
            </p>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <ClerkOAuthSection
            mode="signup"
            onSuccess={() => navigate("/dashboard", { replace: true })}
          />
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
