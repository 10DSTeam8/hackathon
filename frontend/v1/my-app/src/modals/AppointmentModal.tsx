import { useAppointment } from "@/api/hooks";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";

export function AppointmentModal({
  openId,
  onOpenChange,
}: {
  openId: string | null;
  onOpenChange: (id: string | null) => void;
}) {
  const { data, isLoading, isError } = useAppointment(openId ?? undefined);

  return (
    <Dialog open={!!openId} onOpenChange={(v) => !v && onOpenChange(null)}>
      <DialogContent className="rounded-2xl max-w-lg">
        <DialogHeader>
          <DialogTitle>Appointment</DialogTitle>
        </DialogHeader>
        {isLoading ? (
          <p>Loading…</p>
        ) : isError ? (
          <p className="text-red-600 dark:text-red-400">Failed to load appointment.</p>
        ) : data ? (
          <div className="space-y-2 text-sm">
            <div><span className="font-medium">Patient:</span> {data.patient.name} ({data.patient.age})</div>
            <div><span className="font-medium">Time:</span> {new Date(data.datetime).toLocaleString()}</div>
            <div><span className="font-medium">Static risk:</span> {(data.static_risk * 100).toFixed(0)}%</div>
            <div><span className="font-medium">Live risk:</span> {(data.live_adjusted_risk * 100).toFixed(0)}%</div>
            <div><span className="font-medium">Pred (Static):</span> {data.predicted_outcome_static.toUpperCase()}</div>
            <div><span className="font-medium">Pred (Live):</span> {data.predicted_outcome_live.toUpperCase()}</div>
            <div><span className="font-medium">Variant:</span> {data.strategy_variant ?? "—"}</div>
            <div><span className="font-medium">Outcome:</span> {data.outcome}</div>
            <div className="pt-2">
              <span className="font-medium">Comms history:</span>
              <ul className="list-disc pl-5 mt-1 space-y-1">
                {data.comms_history.map((c, i) => (
                  <li key={i}>
                    {c.ts} — {c.type}
                    {c.variant ? ` (${c.variant})` : ""} {c.note ? `— ${c.note}` : ""}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        ) : null}
      </DialogContent>
    </Dialog>
  );
}