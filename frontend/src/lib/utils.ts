import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const TZ = "Africa/Lagos";

export function formatDate(iso?: string | null, opts: Intl.DateTimeFormatOptions = { day: "numeric", month: "short", year: "numeric" }) {
  if (!iso) return "";
  return new Intl.DateTimeFormat("en-NG", { timeZone: TZ, ...opts }).format(new Date(iso));
}

export function formatTime(iso?: string | null) {
  if (!iso) return "";
  return new Intl.DateTimeFormat("en-NG", { timeZone: TZ, hour: "numeric", minute: "2-digit" }).format(new Date(iso));
}

export function formatDateTime(iso?: string | null) {
  if (!iso) return "";
  return `${formatDate(iso, { weekday: "short", day: "numeric", month: "short", year: "numeric" })} · ${formatTime(iso)}`;
}

export function timeAgo(iso?: string | null) {
  if (!iso) return "";
  const s = Math.round((Date.now() - new Date(iso).getTime()) / 1000);
  if (s < 60) return "just now";
  const units: [number, string][] = [[60, "minute"], [3600, "hour"], [86400, "day"], [604800, "week"]];
  for (let i = units.length - 1; i >= 0; i--) {
    const [secs, name] = units[i];
    if (s >= secs) {
      if (name === "week" && s >= 604800 * 5) return formatDate(iso);
      const n = Math.floor(s / secs);
      return `${n} ${name}${n > 1 ? "s" : ""} ago`;
    }
  }
  return formatDate(iso);
}

export function initials(name?: string | null) {
  return (name ?? "?")
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase())
    .join("");
}

/** yyyy-MM-ddTHH:mm in Lagos time, for <input type="datetime-local">. */
export function toLocalInput(iso?: string | null) {
  if (!iso) return "";
  const d = new Date(new Date(iso).getTime() + 60 * 60 * 1000); // WAT = UTC+1, no DST
  return d.toISOString().slice(0, 16);
}

export function fromLocalInput(v: string) {
  return v ? `${v}:00+01:00` : null;
}
