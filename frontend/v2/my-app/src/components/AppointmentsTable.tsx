import type { AppointmentSummary } from "@/api/types";
import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import {
  Table, TableBody, TableCell, TableHead, TableHeader, TableRow,
} from "@/components/ui/table";
import { AppointmentModal } from "@/modals/AppointmentModal";

function PredBadge({ pred }: { pred: "attend" | "dna" }) {
  if (pred === "dna") {
    return <Badge variant="destructive">Pred: DNA</Badge>;
  }
  return <Badge variant="secondary">Pred: Attend</Badge>;
}

function OutcomeBadge({ outcome }: { outcome: "unknown" | "attended" | "no_show" }) {
  if (outcome === "unknown") return <span className="opacity-60">—</span>;
  if (outcome === "no_show") return <Badge >DNA</Badge>;
  return <Badge variant="default">Attended</Badge>;
}

export function AppointmentsTable({
  rows,
  activeId = null,
}: {
  rows: AppointmentSummary[];
  activeId?: string | null;
}) {
  const [openId, setOpenId] = useState<string | null>(null);

  return (
    <>
      {/* Scroll container to keep the quadrant height stable */}
      <div className="rounded-2xl border h-full max-h-[300px] md:max-h-[340px] overflow-y-auto">
        <Table className="table-fixed">
          <TableHeader className="sticky top-0 z-10 bg-white/95 dark:bg-neutral-900/95 backdrop-blur">
            <TableRow>
              <TableHead className="w-16">Time</TableHead>
              <TableHead className="w-48">Patient</TableHead>
              <TableHead className="w-28">Outcome</TableHead>
              <TableHead className="w-36">Live Prediction</TableHead>
              <TableHead className="w-32">Live Risk</TableHead>
              <TableHead className="text-right w-24">Actions</TableHead>
            </TableRow>
          </TableHeader>

          <TableBody>
            {rows.map((r) => {
              const isActive = activeId === r.id;
              return (
                <TableRow
                  key={r.id}
                  className={[
                    "align-middle transition-colors",
                    isActive
                      ? "bg-blue-50 dark:bg-blue-950/20 ring-2 ring-blue-500/40"
                      : "",
                  ].join(" ")}
                >
                  <TableCell className="truncate">{r.time}</TableCell>
                  <TableCell className="truncate">{r.patient.name}</TableCell>
                  <TableCell><OutcomeBadge outcome={r.outcome} /></TableCell>
                  <TableCell><PredBadge pred={r.predicted_outcome_live} /></TableCell>
                  <TableCell>{(r.live_adjusted_risk * 100).toFixed(0)}%</TableCell>
                  <TableCell className="text-right">
                    <Button variant="outline" size="sm" onClick={() => setOpenId(r.id)}>
                      View
                    </Button>
                  </TableCell>
                </TableRow>
              );
            })}
          </TableBody>
        </Table>
      </div>

      <AppointmentModal openId={openId} onOpenChange={setOpenId} />
    </>
  );
}