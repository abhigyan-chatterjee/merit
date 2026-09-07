import React from 'react';
import { Link } from 'react-router-dom';
import { Compass, ArrowLeft, Home } from 'lucide-react';

interface NotFoundProps {
  title?: string;
  message?: string;
  backTo?: string;
  backLabel?: string;
}

export const NotFound: React.FC<NotFoundProps> = ({
  title = 'Page Not Found',
  message = "The resource or page you requested doesn't exist or has moved.",
  backTo = '/',
  backLabel = 'Return to Home',
}) => {
  return (
    <div
      data-testid="not-found-page"
      className="min-h-[60vh] flex flex-col items-center justify-center text-center px-4 py-16"
    >
      <div className="w-16 h-16 rounded-2xl bg-white/5 border border-line flex items-center justify-center mb-6 text-mint">
        <Compass className="w-8 h-8 animate-pulse" />
      </div>

      <span className="font-mono text-xs uppercase tracking-widest text-mint mb-2">404 Error</span>
      <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-ink mb-3">{title}</h1>
      <p className="text-sm text-muted max-w-md mb-8 leading-relaxed">{message}</p>

      <div className="flex flex-wrap items-center justify-center gap-3">
        <Link
          to={backTo}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-mint text-canvas font-medium text-xs hover:bg-mint/90 transition-colors"
        >
          <Home className="w-4 h-4" />
          {backLabel}
        </Link>
        <button
          onClick={() => window.history.back()}
          className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-line text-xs text-muted hover:text-ink hover:bg-white/5 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" />
          Go Back
        </button>
      </div>
    </div>
  );
};
