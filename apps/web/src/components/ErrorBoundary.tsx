import React from 'react';

interface Props {
  children: React.ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * ErrorBoundary — the last thing between a render crash and a blank page.
 *
 * Without this, any exception thrown during render unmounts the whole app and
 * leaves an empty document. The user sees a white screen with no way back and
 * no way to report it. Here the shell survives, explains what happened, and
 * offers both a retry and a copyable error reference.
 */
export class ErrorBoundary extends React.Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: React.ErrorInfo) {
    // Keep the detail in the console for whoever is debugging; the UI only
    // shows a short reference so it stays calm.
    console.error('Merit render error:', error, info.componentStack);
  }

  private handleReset = () => {
    this.setState({ error: null });
  };

  private handleReload = () => {
    window.location.reload();
  };

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;

    const reference = `ref ${Date.now().toString(36).slice(-6)}`;

    return (
      <div className="min-h-screen flex items-center justify-center px-4 bg-canvas text-ink">
        <div className="max-w-md w-full text-center">
          <span className="font-mono text-xs uppercase tracking-[0.16em] text-mint">
            Something broke
          </span>
          <h1 className="mt-2 text-2xl sm:text-3xl font-bold tracking-tight">
            This page failed to render
          </h1>
          <p className="mt-3 text-sm text-muted leading-relaxed">
            The rest of the app is still loaded. Retrying usually clears it. If it keeps
            happening, quote the reference below in a bug report.
          </p>

          <code className="mt-4 inline-block px-2 py-1 rounded border border-line bg-surface font-mono text-[11px] text-muted">
            {reference}
          </code>

          <div className="mt-6 flex flex-wrap items-center justify-center gap-3">
            <button
              type="button"
              onClick={this.handleReset}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg bg-mint text-canvas font-medium text-xs hover:brightness-110 transition-colors cursor-pointer"
            >
              Try again
            </button>
            <button
              type="button"
              onClick={this.handleReload}
              className="inline-flex items-center gap-2 px-4 py-2 rounded-lg border border-line text-xs text-muted hover:text-ink hover:border-steel transition-colors cursor-pointer"
            >
              Reload the app
            </button>
          </div>
        </div>
      </div>
    );
  }
}
