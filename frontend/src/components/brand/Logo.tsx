import { cn } from "@/lib/utils";

/**
 * NIPAM brand mark. Replace the paths below (and /public/brand/*.svg) with the
 * official NIPAM logo artwork when supplied; the component API stays the same.
 */
export function LogoMark({ className, onDark = false, title = "NIPAM" }: { className?: string; onDark?: boolean; title?: string }) {
  return (
    <svg viewBox="0 0 64 64" className={cn("size-10 shrink-0", className)} role="img" aria-label={title}>
      <circle cx="32" cy="32" r="31" fill="#063B66" stroke={onDark ? "#FFFFFF" : "none"} strokeWidth={onDark ? 2 : 0} />
      <circle cx="32" cy="32" r="27.2" fill="none" stroke="#9AA0A6" strokeWidth="1.1" opacity=".75" />
      <path d="M13.5 41.5a18.5 18.5 0 0 1 37 0" fill="none" stroke="#079447" strokeWidth="2.6" strokeLinecap="round" />
      <circle cx="20.6" cy="28.2" r="3.4" fill="#079447" />
      <path d="M14.6 43.2c.6-6.4 3-9.8 6-9.8s5.4 3.4 6 9.8z" fill="#079447" />
      <circle cx="43.4" cy="28.2" r="3.4" fill="#079447" />
      <path d="M37.4 43.2c.6-6.4 3-9.8 6-9.8s5.4 3.4 6 9.8z" fill="#079447" />
      <circle cx="32" cy="22.4" r="4.3" fill="#FFFFFF" />
      <path d="M23.8 43.2c.8-8.6 4-12.9 8.2-12.9s7.4 4.3 8.2 12.9z" fill="#FFFFFF" />
      <rect x="15" y="45.2" width="34" height="2.4" rx="1.2" fill="#9AA0A6" />
      <path d="M32 9.6l1.1 2.3 2.5.3-1.8 1.7.4 2.5-2.2-1.2-2.2 1.2.4-2.5-1.8-1.7 2.5-.3z" fill="#FFFFFF" opacity=".9" />
    </svg>
  );
}

type Variant = "full" | "with-name" | "compact";

export function Logo({
  variant = "full",
  tone = "light",
  className,
}: {
  variant?: Variant;
  /** light = for white backgrounds; dark = for navy/green backgrounds */
  tone?: "light" | "dark";
  className?: string;
}) {
  const dark = tone === "dark";
  if (variant === "compact") return <LogoMark className={className} onDark={dark} />;
  return (
    <span className={cn("inline-flex items-center gap-2.5", className)}>
      <LogoMark onDark={dark} className={variant === "with-name" ? "size-12" : "size-10"} />
      <span className="flex flex-col leading-none">
        <span className={cn("font-display text-[1.45rem] font-extrabold tracking-[0.08em]", dark ? "text-white" : "text-navy")}>
          NIP<span className={dark ? "text-green-300" : "text-green-500"}>A</span>M
        </span>
        {variant === "with-name" && (
          <span className={cn("mt-1 max-w-[14rem] text-[10px] font-semibold uppercase leading-tight tracking-[0.12em]", dark ? "text-navy-100" : "text-silver-dark")}>
            Non-Indigenes for Philip Aduda Movement
          </span>
        )}
      </span>
    </span>
  );
}
