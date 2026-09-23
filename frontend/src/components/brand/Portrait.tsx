import { cn } from "@/lib/utils";

/** Portrait of the principal, or a branded placeholder until a photo is uploaded. */
export function Portrait({ src, alt, className }: { src?: string | null; alt?: string | null; className?: string }) {
  if (src) return <img src={src} alt={alt ?? "Sen. Philip Aduda"} className={cn("object-cover", className)} />;
  return (
    <div className={cn("relative isolate flex items-end justify-center overflow-hidden bg-gradient-to-b from-navy-600 to-navy-900", className)} role="img" aria-label="Photo of Sen. Philip Aduda to be added">
      <div className="absolute -right-10 -top-10 size-48 rounded-full border-[18px] border-green-500/25" />
      <svg viewBox="0 0 200 220" className="relative w-3/4 text-white/15" aria-hidden>
        <circle cx="100" cy="70" r="42" fill="currentColor" />
        <path d="M18 220c4-62 38-96 82-96s78 34 82 96z" fill="currentColor" />
      </svg>
      <span className="absolute bottom-3 left-1/2 -translate-x-1/2 whitespace-nowrap rounded-full bg-white/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-wider text-white/80 ring-1 ring-white/20">
        Official photo to be added
      </span>
      <div className="absolute inset-x-0 bottom-0 h-1.5 bg-green-500" />
    </div>
  );
}
