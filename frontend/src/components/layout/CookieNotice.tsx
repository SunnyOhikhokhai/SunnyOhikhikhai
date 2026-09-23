import { Cookie } from "lucide-react";
import { useState } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";

const KEY = "nipam-cookie-notice";

/**
 * NIPAM uses only strictly-necessary cookies (session + security token) and no
 * advertising or third-party tracking, so no opt-in is required; this notice
 * informs users and links to the Privacy Policy.
 */
export function CookieNotice() {
  const [open, setOpen] = useState(() => {
    try {
      return !localStorage.getItem(KEY);
    } catch {
      return false;
    }
  });
  if (!open) return null;
  const close = () => {
    try {
      localStorage.setItem(KEY, new Date().toISOString());
    } catch {
      /* storage unavailable */
    }
    setOpen(false);
  };
  return (
    <div role="region" aria-label="Cookie notice" className="fixed inset-x-3 bottom-3 z-40 mx-auto max-w-2xl rounded-2xl border border-border bg-white p-4 shadow-lift sm:bottom-6 sm:flex sm:items-center sm:gap-4">
      <div className="flex gap-3">
        <Cookie className="mt-0.5 size-5 shrink-0 text-green-600" />
        <p className="text-sm text-slate-600">
          NIPAM uses only <strong className="text-navy">essential cookies</strong> to keep you signed in and protect your account. We do not use advertising
          or tracking cookies. <Link to="/privacy#cookies" className="font-semibold text-green-600 underline-offset-2 hover:underline">Learn more</Link>
        </p>
      </div>
      <Button size="sm" variant="navy" className="mt-3 w-full shrink-0 sm:mt-0 sm:w-auto" onClick={close}>
        Got it
      </Button>
    </div>
  );
}
