import { Download, RefreshCw, X } from "lucide-react";
import { useEffect, useState } from "react";
import { useRegisterSW } from "virtual:pwa-register/react";
import { LogoMark } from "@/components/brand/Logo";
import { Button } from "@/components/ui/button";

interface BeforeInstallPromptEvent extends Event {
  prompt: () => Promise<void>;
  userChoice: Promise<{ outcome: "accepted" | "dismissed" }>;
}

const DISMISS_KEY = "nipam-install-dismissed";

export function PwaPrompts() {
  const [deferred, setDeferred] = useState<BeforeInstallPromptEvent | null>(null);
  const [showInstall, setShowInstall] = useState(false);
  const {
    needRefresh: [needRefresh, setNeedRefresh],
    updateServiceWorker,
  } = useRegisterSW();

  useEffect(() => {
    const handler = (e: Event) => {
      e.preventDefault();
      setDeferred(e as BeforeInstallPromptEvent);
      const dismissed = Number(localStorage.getItem(DISMISS_KEY) ?? 0);
      if (Date.now() - dismissed > 1000 * 60 * 60 * 24 * 14) setTimeout(() => setShowInstall(true), 20_000);
    };
    window.addEventListener("beforeinstallprompt", handler);
    return () => window.removeEventListener("beforeinstallprompt", handler);
  }, []);

  const install = async () => {
    if (!deferred) return;
    await deferred.prompt();
    await deferred.userChoice;
    setDeferred(null);
    setShowInstall(false);
  };
  const dismiss = () => {
    localStorage.setItem(DISMISS_KEY, String(Date.now()));
    setShowInstall(false);
  };

  if (needRefresh)
    return (
      <div role="status" className="fixed inset-x-3 bottom-3 z-50 mx-auto flex max-w-md items-center gap-3 rounded-2xl bg-navy p-4 text-white shadow-lift sm:bottom-6">
        <RefreshCw className="size-5 shrink-0 text-green-300" />
        <p className="flex-1 text-sm">A new version of NIPAM is available.</p>
        <Button size="sm" onClick={() => updateServiceWorker(true)}>
          Update
        </Button>
        <button onClick={() => setNeedRefresh(false)} aria-label="Dismiss" className="rounded-lg p-1 text-navy-200 hover:text-white">
          <X className="size-4" />
        </button>
      </div>
    );

  if (!showInstall || !deferred) return null;
  return (
    <div role="dialog" aria-label="Install NIPAM" className="fixed inset-x-3 bottom-3 z-50 mx-auto flex max-w-md items-center gap-3 rounded-2xl border border-border bg-white p-4 shadow-lift animate-fade-up sm:bottom-6">
      <LogoMark className="size-11" />
      <div className="flex-1">
        <p className="text-sm font-bold text-navy">Install the NIPAM app</p>
        <p className="text-xs text-muted-foreground">Quick access from your home screen, even with a weak connection.</p>
      </div>
      <Button size="sm" onClick={install}>
        <Download /> Install
      </Button>
      <button onClick={dismiss} aria-label="Not now" className="rounded-lg p-1 text-slate-400 hover:text-navy">
        <X className="size-4" />
      </button>
    </div>
  );
}
