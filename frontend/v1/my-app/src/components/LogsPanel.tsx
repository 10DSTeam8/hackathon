import { useLogs } from "@/api/hooks";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

type Col = "scheduled" | "patient" | "type" | "message" | "reply";

const COLS: { key: Col; label: string; className: string }[] = [
  { key: "scheduled", label: "Scheduled", className: "col-span-2" },
  { key: "patient",   label: "Patient",   className: "col-span-3" },
  { key: "type",      label: "Event",     className: "col-span-2" },
  { key: "message",   label: "Message / Outcome", className: "col-span-4" },
];

function ReplyChip({ reply }: { reply?: string | null }) {
  if (!reply) return null;
  const map: Record<string, string> = {
    yes: "bg-emerald-50 text-emerald-700 border border-emerald-200",
    no: "bg-rose-50 text-rose-700 border border-rose-200",
    no_reply_eod: "bg-amber-50 text-amber-800 border border-amber-200",
  };
  return <Badge className={map[reply] ?? "bg-neutral-100 text-neutral-700"}>{reply}</Badge>;
}

export function LogsPanel({ dateISO }: { dateISO: string }) {
  const { data, isLoading, isError } = useLogs(dateISO);

  return (
    <Card className="rounded-2xl h-full p-0 overflow-hidden">
      <div className="p-4 pb-3">
        <div className="text-lg font-semibold">Logs — Appointments on {dateISO}</div>
      </div>

      <div className="h-[calc(100%-52px)] overflow-y-auto overflow-x-auto">
        <div className="min-w-[980px]">
          <div className="sticky top-0 z-10 bg-white/95 backdrop-blur px-4 py-2 border-y">
            <div className="grid grid-cols-12 gap-2 text-xs font-medium uppercase tracking-wide text-[var(--muted-fg)]">
              {COLS.map((c) => (
                <div key={c.key} className={c.className}>{c.label}</div>
              ))}
            </div>
          </div>

          <div className="px-4 py-2">
            {isLoading ? (
              <p className="text-sm">Loading…</p>
            ) : isError ? (
              <p className="text-sm text-rose-600">Failed to load logs.</p>
            ) : !data || data.length === 0 ? (
              <div className="rounded-xl border p-6 text-center text-sm opacity-70">
                No logs for this day.
              </div>
            ) : (
              <ul className="divide-y rounded-xl border overflow-hidden">
                {data.map((l, idx) => (
                  <li
                    key={l.id}
                    className={`grid grid-cols-12 gap-2 items-center px-3 py-2 ${
                      idx % 2 ? "bg-[var(--brand-50)]/35" : ""
                    }`}
                  >
                    <div className="col-span-2 font-mono text-xs sm:text-sm opacity-80 whitespace-nowrap">
                      {l.scheduled_date_iso}
                    </div>

                    <div className="col-span-3 truncate text-sm" title={l.patient_name}>
                      <span className="font-medium">{l.patient_name}</span>
                    </div>

                    <div className="col-span-2 flex items-center gap-2 whitespace-nowrap overflow-hidden">
                      <Badge
                        className="capitalize bg-[var(--brand-50)] text-[var(--brand-700)] border border-[var(--brand-100)]"
                      >
                        {l.type}
                      </Badge>
                      {l.variant && (
                        <span className="rounded bg-[var(--brand-50)] text-[var(--brand-700)] border border-[var(--brand-100)] px-1.5 py-0.5 text-[10px] flex-shrink-0">
                          Variant {l.variant}
                        </span>
                      )}
                    </div>

                    <div
                      className="col-span-4 text-sm truncate"
                      title={l.type === "outcome" && l.outcome ? `Outcome: ${l.outcome}` : l.message}
                    >
                      {l.type === "outcome" && l.outcome ? `Outcome: ${l.outcome}` : l.message}
                    </div>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>
      </div>
    </Card>
  );
}