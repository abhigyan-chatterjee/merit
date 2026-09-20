import React from "react";

export const TermsOfService: React.FC = () => {
  return (
    <article className="max-w-4xl mx-auto px-4 py-14 md:py-20">
      <header className="mb-10 space-y-3">
        <p className="text-[10px] font-mono uppercase tracking-[0.16em] text-mint">Legal</p>
        <h1 className="text-3xl sm:text-5xl font-bold tracking-[-0.03em] text-ink">
          Terms of Service
        </h1>
        <p className="text-sm text-muted">Effective September 20, 2026</p>
      </header>

      <div className="space-y-10 text-sm leading-7 text-muted">
        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Educational service</h2>
          <p>
            Merit is a free educational service for learning data structures and algorithms through
            visualizers, problems, quizzes, exams, and guided paths. There are no payments or
            advertisements.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Your account</h2>
          <p>
            Keep your sign-in details secure and make sure the information on your account is
            accurate. You are responsible for activity carried out through your account and for
            using Merit only when you are permitted to do so.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Acceptable use</h2>
          <p>
            Do not disrupt the service, submit malicious code, attempt to access another
            person&apos;s data, or use the judge or tutor to attack, overload, or probe other
            systems. Respect the rate limits shown by the judge and tutor features; do not bypass
            those limits or evade safeguards.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Content</h2>
          <p>
            Merit&apos;s lessons, explanations, questions, and study material are original material
            prepared for this service. They are provided for learning and do not promise a
            particular interview, exam, or employment result.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Availability and termination</h2>
          <p>
            Merit is provided as available, without warranties that it will always be uninterrupted,
            error-free, or suitable for every purpose. We may suspend or terminate access when an
            account abuses the service, violates these terms, or puts users or infrastructure at
            risk.
          </p>
        </section>

        <section className="space-y-3">
          <h2 className="text-lg font-semibold text-ink">Contact</h2>
          <p>
            Questions about these terms can be sent to{" "}
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
