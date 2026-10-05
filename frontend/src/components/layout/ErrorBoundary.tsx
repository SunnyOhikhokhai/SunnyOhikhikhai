import { Component, type ReactNode } from "react";
import { useLocation } from "react-router-dom";

const RELOAD_KEY = "nipam-chunk-reload";

/** A newer version of the site was loaded while this page was open. */
function isStaleBundle(error: Error) {
  return /dynamically imported module|Importing a module script failed|Outdated Optimize Dep|Loading chunk|error loading dynamically/i.test(
    `${error.name} ${error.message}`,
  );
}

class Boundary extends Component<{ children: ReactNode }, { error: Error | null }> {
  state = { error: null as Error | null };

  static getDerivedStateFromError(error: Error) {
    return { error };
  }

  componentDidCatch(error: Error) {
    console.error(error);
    // Reload once to pick up the new files; never loop.
    try {
      if (isStaleBundle(error) && !sessionStorage.getItem(RELOAD_KEY)) {
        sessionStorage.setItem(RELOAD_KEY, "1");
        window.location.reload();
        return;
      }
      sessionStorage.removeItem(RELOAD_KEY);
    } catch {
      /* storage unavailable */
    }
  }

  render() {
    const { error } = this.state;
    if (!error) return this.props.children;
    return (
      <main role="alert" className="mx-auto flex min-h-screen max-w-xl flex-col items-center justify-center gap-4 px-4 text-center">
        <h1 className="text-2xl font-extrabold text-navy">Something went wrong on this page</h1>
        <p className="text-slate-600">Reloading usually fixes it. If it keeps happening, send the NIPAM team a screenshot of this message.</p>
        <div className="flex flex-wrap justify-center gap-3">
          <button
            type="button"
            onClick={() => window.location.reload()}
            className="rounded-xl bg-green-600 px-5 py-2.5 font-semibold text-white hover:bg-green-700"
          >
            Reload page
          </button>
          <a href="/" className="rounded-xl px-5 py-2.5 font-semibold text-navy ring-1 ring-border hover:bg-surface">
            Go to the homepage
          </a>
        </div>
        <pre className="max-w-full overflow-x-auto whitespace-pre-wrap rounded-xl bg-surface p-3 text-left text-xs text-slate-500">
          {error.name}: {error.message}
        </pre>
      </main>
    );
  }
}

/** Shows a message instead of a blank page when a page crashes. Resets when the user navigates. */
export function ErrorBoundary({ children }: { children: ReactNode }) {
  const { pathname } = useLocation();
  return <Boundary key={pathname}>{children}</Boundary>;
}
