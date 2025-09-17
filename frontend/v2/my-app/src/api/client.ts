// Tiny REST client with base URL + helpers

export const API_BASE = import.meta.env.VITE_API_BASE ?? "http://localhost:5001/api";

async function req<T>(path: string, opts?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...opts,
  });
  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new Error(`${res.status} ${res.statusText}: ${text}`);
  }
  return res.json() as Promise<T>;
}

export const http = {
  get: <T>(path: string) => req<T>(path),
  post: <T>(path: string, body?: unknown) => req<T>(path, { method: "POST", body: JSON.stringify(body ?? {}) }),
  patch: <T>(path: string, body?: unknown) => req<T>(path, { method: "PATCH", body: JSON.stringify(body ?? {}) }),
};

export const fmtPct = (v: number | null | undefined, dp = 0) =>
  v == null ? "—" : `${(v * 100).toFixed(dp)}%`;

// Date helpers
export function addDaysISO(dateISO: string, days: number): string {
  const d = new Date(dateISO + "T00:00:00Z");
  d.setUTCDate(d.getUTCDate() + days);
  return d.toISOString().slice(0, 10);
}