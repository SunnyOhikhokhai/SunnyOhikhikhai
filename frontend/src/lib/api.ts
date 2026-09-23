/** Fetch wrapper for the NIPAM API: cookie session + CSRF double-submit. */

export class ApiError extends Error {
  status: number;
  code: string;
  fields?: Record<string, string>;
  constructor(status: number, code: string, message: string, fields?: Record<string, string>) {
    super(message);
    this.status = status;
    this.code = code;
    this.fields = fields;
  }
}

export interface Paged<T> {
  data: T[];
  meta: { page: number; page_size: number; total: number; total_pages: number; unread?: number };
}

function readCookie(name: string) {
  return document.cookie
    .split("; ")
    .find((c) => c.startsWith(name + "="))
    ?.split("=")[1];
}

let csrfPromise: Promise<void> | null = null;
async function ensureCsrf() {
  if (readCookie("nipam_csrf")) return;
  csrfPromise ??= fetch("/api/auth/csrf", { credentials: "include" }).then(() => undefined);
  await csrfPromise;
  csrfPromise = null;
}

type Query = Record<string, string | number | boolean | null | undefined>;

export function qs(params?: Query) {
  if (!params) return "";
  const p = new URLSearchParams();
  Object.entries(params).forEach(([k, v]) => {
    if (v !== undefined && v !== null && v !== "") p.set(k, String(v));
  });
  const s = p.toString();
  return s ? `?${s}` : "";
}

async function request<T>(method: string, url: string, body?: unknown, raw = false): Promise<T> {
  const headers: Record<string, string> = { Accept: "application/json" };
  const unsafe = method !== "GET";
  if (unsafe) {
    await ensureCsrf();
    headers["X-CSRF-Token"] = decodeURIComponent(readCookie("nipam_csrf") ?? "");
  }
  let payload: BodyInit | undefined;
  if (body instanceof FormData) payload = body;
  else if (body !== undefined) {
    headers["Content-Type"] = "application/json";
    payload = JSON.stringify(body);
  }
  let res: Response;
  try {
    res = await fetch(url, { method, headers, body: payload, credentials: "include" });
  } catch {
    throw new ApiError(0, "network_error", "You appear to be offline. Check your connection and try again.");
  }
  if (raw && res.ok) return res as unknown as T;
  const json = await res.json().catch(() => ({}));
  if (!res.ok) {
    const err = json?.error ?? {};
    throw new ApiError(res.status, err.code ?? "error", err.message ?? "Something went wrong.", err.details?.fields);
  }
  return json as T;
}

export const api = {
  get: <T>(url: string, params?: Query) => request<T>("GET", url + qs(params)),
  post: <T>(url: string, body?: unknown) => request<T>("POST", url, body),
  put: <T>(url: string, body?: unknown) => request<T>("PUT", url, body),
  patch: <T>(url: string, body?: unknown) => request<T>("PATCH", url, body),
  del: <T>(url: string, body?: unknown) => request<T>("DELETE", url, body),
  download: (url: string) => request<Response>("GET", url, undefined, true),
};

/** Unwrap {"data": ...} envelopes. */
export const getData = async <T>(url: string, params?: Query) => (await api.get<{ data: T }>(url, params)).data;
