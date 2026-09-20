import React from "react";

export const PrivacyPolicy: React.FC = () => {
  return (
    <article className="max-w-4xl mx-auto px-4 py-14 md:py-20">
      <header className="mb-10 space-y-3">
        <p className="text-[10px] font-mono uppercase tracking-[0.16em] text-mint">Legal</p>
        <h1 className="text-3xl sm:text-5xl font-bold tracking-[-0.03em] text-ink">
          Privacy Policy
        </h1>
        <p className="text-sm text-muted">Effective September 20, 2026</p>
      </header>

      <div className="space-y-10 text-sm leading-7 text-muted">
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">What we collect</h2>
          <p>
            Merit is free student DSA preparation software. When you create an account, we receive
            your email address and name through Clerk. We also store code submissions, quiz
            attempts, and learning progress associated with your account so the app can provide its
            core features.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Tutor keys and cookies</h2>
          <p>
            AI tutor keys you provide are kept on your device and are used only for the request you
            make. They are not stored by Merit. Requests may pass through our proxy to the provider
            you select, but we do not retain your key.
          </p>
          <p>
            Merit uses an httpOnly session cookie to keep you signed in. We do not use advertising
            or analytics cookies.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Service providers</h2>
          <p>
            Clerk provides account authentication, and Neon provides database hosting for account
            and learning data. Merit has no advertising or analytics service enabled.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Your choices</h2>
          <p>
            You can export your learning data or delete your account from the Data section of your
            Profile. Deleting your account removes the account data Merit holds for you, subject to
            limited records we may need to retain for security or legal reasons.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Contact</h2>
          <p>
            Questions about privacy or a data request can be sent to{" "}
            <a className="text-mint hover:underline" href="mailto:abhi@nullbit.in">
              abhi@nullbit.in
            </a>
            .
          </p>
        </section>
      </div>
    </article>
  );
};
