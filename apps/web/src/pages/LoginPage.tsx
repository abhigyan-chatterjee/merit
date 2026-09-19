import React, { useState } from "react";
import { Link, useNavigate, useLocation } from "react-router-dom";
import { LogIn, Mail, Lock, AlertCircle, ArrowRight, ShieldCheck } from "lucide-react";
import { useAuth } from "../store/AuthContext";
import { ClerkOAuthSection } from "../components/ClerkOAuth";
import { Panel } from "../components/ui/Panel";
import { SectionLabel } from "../components/ui/SectionLabel";
import { Reveal } from "../components/ui/Reveal";

export const LoginPage: React.FC = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const from = (location.state as { from?: string })?.from || "/dashboard";

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError("Please fill in both email and password.");
      return;
    }

    setLoading(true);
    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Failed to sign in. Please verify your credentials.");
      }
    } finally {
      setLoading(false);
    }
  };

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
          <Panel bracket label="Credentials">
            <form onSubmit={handleSubmit} noValidate className="space-y-4">
              {error && (
                <div
                  role="alert"
                  className="flex items-start gap-2.5 p-3 rounded-lg border border-rose/30 bg-rose/10 text-rose text-xs"
                >
                  <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                  <span className="font-mono">{error}</span>
                </div>
              )}

              <div className="space-y-1.5">
                <label
                  htmlFor="login-email"
                  className="block text-xs font-mono text-muted uppercase tracking-wider"
                >
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="login-email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="student@merit.org"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-line bg-canvas text-xs text-ink placeholder-muted/60 focus:outline-none focus:border-mint transition font-mono"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="login-password"
                  className="block text-xs font-mono text-muted uppercase tracking-wider"
                >
                  Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="login-password"
                    type="password"
                    autoComplete="current-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-line bg-canvas text-xs text-ink placeholder-muted/60 focus:outline-none focus:border-mint transition font-mono"
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={loading}
                className="w-full mt-2 inline-flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg bg-mint text-canvas font-mono font-semibold text-xs hover:bg-mint/90 transition cursor-pointer disabled:opacity-50"
              >
                {loading ? (
                  <span>Signing in…</span>
                ) : (
                  <>
                    <LogIn className="w-3.5 h-3.5" />
                    <span>Sign In</span>
                  </>
                )}
              </button>
            </form>
          </Panel>
        </Reveal>

        <Reveal delay={0.15}>
          <ClerkOAuthSection mode="signin" onSuccess={() => navigate(from, { replace: true })} />
        </Reveal>

        <Reveal delay={0.2}>
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
              <span>Argon2id + HTTP-only session cookies · Zero tracking</span>
            </div>
          </div>
        </Reveal>
      </div>
    </div>
  );
};
