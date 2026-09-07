import React, { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { UserPlus, Mail, Lock, User, AlertCircle, ArrowRight, ShieldCheck } from "lucide-react";
import { useAuth } from "../store/AuthContext";
import { Panel } from "../components/ui/Panel";
import { SectionLabel } from "../components/ui/SectionLabel";
import { Reveal } from "../components/ui/Reveal";

export const RegisterPage: React.FC = () => {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (displayName.trim().length < 2) {
      setError("Display name must be at least 2 characters.");
      return;
    }

    if (password.length < 10) {
      setError("Password must be at least 10 characters long.");
      return;
    }

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    setLoading(true);
    try {
      await register(email.trim(), password, displayName.trim());
      navigate("/dashboard", { replace: true });
    } catch (err: unknown) {
      if (err instanceof Error) {
        setError(err.message);
      } else {
        setError("Registration failed. Please check your inputs.");
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
            <SectionLabel label="New Student Registration" />
            <h1 className="text-2xl font-mono font-bold text-ink tracking-tight">
              Create an ALGOVISTA Account
            </h1>
            <p className="text-xs text-muted">
              Get an isolated, verified workspace for placement practice.
            </p>
          </div>
        </Reveal>

        <Reveal delay={0.1}>
          <Panel bracket label="Profile Details">
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
                  htmlFor="reg-name"
                  className="block text-xs font-mono text-muted uppercase tracking-wider"
                >
                  Display Name
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="reg-name"
                    type="text"
                    required
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Ada Lovelace"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-line bg-canvas text-xs text-ink placeholder-muted/60 focus:outline-none focus:border-mint transition font-mono"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="reg-email"
                  className="block text-xs font-mono text-muted uppercase tracking-wider"
                >
                  Email Address
                </label>
                <div className="relative">
                  <Mail className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="reg-email"
                    type="email"
                    autoComplete="email"
                    required
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    placeholder="ada@example.org"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-line bg-canvas text-xs text-ink placeholder-muted/60 focus:outline-none focus:border-mint transition font-mono"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="reg-password"
                  className="block text-xs font-mono text-muted uppercase tracking-wider"
                >
                  Password (10+ characters)
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="reg-password"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    placeholder="••••••••••••"
                    className="w-full pl-9 pr-3 py-2 rounded-lg border border-line bg-canvas text-xs text-ink placeholder-muted/60 focus:outline-none focus:border-mint transition font-mono"
                  />
                </div>
              </div>

              <div className="space-y-1.5">
                <label
                  htmlFor="reg-confirm-password"
                  className="block text-xs font-mono text-muted uppercase tracking-wider"
                >
                  Confirm Password
                </label>
                <div className="relative">
                  <Lock className="w-4 h-4 text-muted absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    id="reg-confirm-password"
                    type="password"
                    autoComplete="new-password"
                    required
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
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
                  <span>Registering…</span>
                ) : (
                  <>
                    <UserPlus className="w-3.5 h-3.5" />
                    <span>Create Account</span>
                  </>
                )}
              </button>
            </form>
          </Panel>
        </Reveal>

        <Reveal delay={0.2}>
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
              <span>Encrypted with Argon2id · Secure HTTP-only cookies</span>
            </div>
          </div>
        </Reveal>
      </div>
    </div>
  );
};
