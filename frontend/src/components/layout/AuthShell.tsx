import type { ReactNode } from "react";
import { Link } from "react-router-dom";
import { SkylineArt } from "@/components/brand/Artwork";
import { Logo } from "@/components/brand/Logo";

export function AuthShell({ title, subtitle, children, aside }: { title: string; subtitle?: ReactNode; children: ReactNode; aside?: ReactNode }) {
  return (
    <div className="grid min-h-[calc(100dvh-4rem)] lg:grid-cols-[1fr_minmax(0,34rem)] xl:grid-cols-[1fr_minmax(0,38rem)]">
      <div className="relative hidden overflow-hidden bg-navy lg:block">
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,rgba(7,148,71,0.35),transparent_60%)]" />
        <SkylineArt className="absolute inset-x-0 bottom-0 h-56 w-full opacity-90" />
        <div className="relative flex h-full flex-col p-12 text-white">
          <Link to="/" aria-label="NIPAM home"><Logo variant="with-name" tone="dark" /></Link>
          <div className="mt-auto mb-56 max-w-md">
            {aside ?? (
              <>
                <p className="text-sm font-semibold uppercase tracking-[0.16em] text-green-300">Community · Information · Participation</p>
                <p className="mt-4 font-display text-3xl font-extrabold leading-tight text-white">Connecting residents across the six Area Councils of the FCT.</p>
              </>
            )}
          </div>
        </div>
      </div>
      <div className="flex items-start justify-center bg-white px-4 py-10 sm:px-8 lg:items-center">
        <div className="w-full max-w-md">
          <h1 className="text-3xl font-extrabold">{title}</h1>
          {subtitle && <p className="mt-2 text-muted-foreground">{subtitle}</p>}
          <div className="mt-8">{children}</div>
        </div>
      </div>
    </div>
  );
}
