import { Suspense, useEffect } from "react";
import { Outlet, useLocation } from "react-router-dom";
import { Skeleton } from "@/components/ui/skeleton";
import { CookieNotice } from "./CookieNotice";
import { PwaPrompts } from "./PwaPrompts";
import { SiteFooter } from "./SiteFooter";
import { SiteHeader } from "./SiteHeader";

export function ScrollToTop() {
  const { pathname } = useLocation();
  useEffect(() => {
    window.scrollTo({ top: 0, behavior: "instant" as ScrollBehavior });
  }, [pathname]);
  return null;
}

export function PageFallback() {
  return (
    <div className="container space-y-6 py-16" role="status" aria-label="Loading page">
      <Skeleton className="h-10 w-2/3 max-w-xl" />
      <Skeleton className="h-4 w-full max-w-2xl" />
      <div className="grid gap-6 pt-6 sm:grid-cols-2 lg:grid-cols-3">
        {[0, 1, 2].map((i) => (
          <Skeleton key={i} className="h-64" />
        ))}
      </div>
    </div>
  );
}

export function PublicLayout() {
  return (
    <div className="flex min-h-dvh flex-col overflow-x-clip">
      <a href="#main" className="skip-link">
        Skip to main content
      </a>
      <SiteHeader />
      <main id="main" className="flex-1" tabIndex={-1}>
        <Suspense fallback={<PageFallback />}>
          <Outlet />
        </Suspense>
      </main>
      <SiteFooter />
      <PwaPrompts />
      <CookieNotice />
    </div>
  );
}
