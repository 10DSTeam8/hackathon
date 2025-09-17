// src/pages/DayView.tsx  (DROP-IN REPLACEMENT)

import { useEffect, useMemo, useRef, useState } from "react";
import {
  useAdvanceDay,
  useAppointments,
  useDaySummary,
  useHealth,
  useSimStatus,
  useTickToday,
} from "@/api/hooks";
import { RiskDistributionChart } from "@/components/RiskDistributionChart";
import { AppointmentsTable } from "@/components/AppointmentsTable";
import { DaySummaryCards } from "@/components/DaySummaryCards";
import { StrategiesModal } from "@/modals/StrategiesModal";
import { StrategyBuilderModal } from "@/modals/StrategyBuilderModal";
import { DeployModal } from "@/modals/DeployModal";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { LogsPanel } from "@/components/LogsPanel";
import { addDaysISO } from "@/api/client";
import type { SimStatus } from "@/api/types";

function useDateNav(initialDate: string) {
  const [date, setDate] = useState<string>(initialDate);
  const next = () => setDate((d) => addDaysISO(d, 1));
  const prev = () => setDate((d) => addDaysISO(d, -1));
  const to = (iso: string) => setDate(iso);
  return { date, setDate: to, prev, next };
}

export default function DayView() {
  const health = useHealth();
  const startDate = health.data?.startDateISO ?? new Date().toISOString().slice(0, 10);
  const todayDate = health.data?.todayDateISO ?? startDate;

  const { date, setDate, prev, next } = useDateNav(todayDate);

  const summaryQ = useDaySummary(date);
  const apptsQ = useAppointments(date);

  const advance = useAdvanceDay();
  const statusQ = useSimStatus();
  const tick = useTickToday();

  const latestStatusRef = useRef<SimStatus | undefined>(statusQ.data);
  useEffect(() => {
    latestStatusRef.current = statusQ.data;
  }, [statusQ.data]);

  const [flashId, setFlashId] = useState<string | null>(null);
  const flashTimerRef = useRef<number | null>(null);

  useEffect(() => {
    if (todayDate && date !== todayDate) setDate(todayDate);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [todayDate]);

  const s = summaryQ.data;
  const isToday = s ? s.date_iso === todayDate : true;

  // auto-tick once/second on today
  useEffect(() => {
    if (!isToday) return;

    let intervalId: number | null = null;

    const start = () => {
      if (intervalId != null) return;
      intervalId = window.setInterval(() => {
        const st = latestStatusRef.current;
        const canTick =
          !tick.isPending && !!st && !!st.next_appointment && st.remaining > 0;

        if (canTick) {
          tick.mutate(undefined, {
            onSuccess: (res) => {
              const id = res.processed?.id ?? res.status.last_processed_id ?? null;
              if (id) {
                setFlashId(id);
                if (flashTimerRef.current) window.clearTimeout(flashTimerRef.current);
                flashTimerRef.current = window.setTimeout(
                  () => setFlashId(null),
                  900
                ) as unknown as number;
              }
            },
          });
        }
      }, 1000);
    };

    const stop = () => {
      if (intervalId != null) window.clearInterval(intervalId);
      intervalId = null;
    };

    start();
    return () => {
      stop();
      if (flashTimerRef.current) window.clearTimeout(flashTimerRef.current);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isToday, tick.isPending]);

  // Modals
  const [openStrategies, setOpenStrategies] = useState(false);
  const [openBuilder, setOpenBuilder] = useState(false);
  const [openDeploy, setOpenDeploy] = useState(false);

  const grid = useMemo(() => {
    if (summaryQ.isLoading || apptsQ.isLoading) return <p>Loading…</p>;
    if (summaryQ.isError || apptsQ.isError)
      return <p className="text-red-600 dark:text-red-400">Failed to load data.</p>;

    const rows = apptsQ.data!;
    const sum = summaryQ.data!;

    return (
      <>
        {/* Top grid: Strategies + Appointments */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Strategies */}
          <Card className="rounded-2xl h-[420px] md:h-[460px] p-4">
            <div className="flex items-center justify-between">
              <div className="text-lg font-semibold">Strategies Applied</div>
              <div className="flex gap-2">
                <Button variant="outline" size="sm" onClick={() => setOpenStrategies(true)}>
                  All Strategies
                </Button>
                <Button size="sm" onClick={() => setOpenDeploy(true)}>Deploy…</Button>
              </div>
            </div>
            <div className="mt-3 flex flex-wrap gap-2">
              {sum.strategies_applied.length === 0 ? (
                <span className="text-sm opacity-70">None</span>
              ) : (
                sum.strategies_applied.map((x) => (
                  <Badge
                    key={x.id}
                    variant="secondary"
                    className="bg-[var(--brand-50)] text-[var(--brand-700)] border border-[var(--brand-100)]"
                  >
                    {x.name}
                  </Badge>
                ))
              )}
            </div>
          </Card>



          {/* Appointments */}
          <div className="h-[420px] md:h-[460px]">
            <Card className="rounded-2xl h-full p-4">
              <div className="text-lg font-semibold mb-3">Appointments</div>
              <AppointmentsTable
                rows={rows}
                activeId={flashId ?? statusQ.data?.next_appointment?.id ?? null}
              />
            </Card>
          </div>
        </section>

        {/* General metrics (full-width) */}
        <section className="mt-4">
          <DaySummaryCards s={sum} />
        </section>

        {/* Second row: Live Risk Distribution and Logs */}
        <section className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
          <Card className="rounded-2xl h-[420px] md:h-[460px] p-4">
            <div className="text-lg font-semibold mb-3">Live Risk Distribution</div>
            <div className="h-[calc(100%-40px)]">
              <RiskDistributionChart data={sum.dist_live} />
            </div>
          </Card>

          <div className="h-[420px] md:h-[460px]">
            <LogsPanel dateISO={date} />
          </div>
        </section>
      </>
    );
  }, [
    summaryQ.isLoading,
    apptsQ.isLoading,
    summaryQ.isError,
    apptsQ.isError,
    summaryQ.data,
    apptsQ.data,
    date,
    isToday,
    statusQ.data?.next_appointment?.id,
    flashId,
  ]);

  return (
    <main className="min-h-screen p-6 bg-[var(--bg)] text-[var(--fg)]">
      <section className="max-w-6xl mx-auto">
        {/* Top bar: title + day nav + simulate */}
        <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
          <div className="flex items-center gap-3">
            <div>
              <h1 className="text-2xl font-semibold">NHS ATTEND</h1>
              <p className="text-sm text-neutral-500 dark:text-neutral-400">Single clinic</p>
            </div>
          </div>

          <div className="flex flex-col gap-2 md:flex-row md:items-center md:gap-4">
            {/* Day browsing */}
            <div className="flex items-center gap-2">
              <Button variant="outline" onClick={prev}>Prev</Button>
              <div className="flex items-center gap-2 w-fit text-sm py-2 px-3 rounded-lg border">
                <span>{s?.date_iso ?? date}</span>
                {isToday && <Badge variant="secondary">Today</Badge>}
              </div>
              <Button variant="outline" onClick={next}>Next</Button>
            </div>

            {/* SIMULATE +1 day */}
            <div className="flex items-center gap-2">
              <Button size="sm" disabled={advance.isPending} onClick={() => advance.mutate()}>
                {advance.isPending ? "Advancing…" : "Advance +1 day"}
              </Button>
            </div>
          </div>
        </div>

        <Separator className="my-4" />
        {grid}
      </section>

      {/* Modals */}
      <StrategiesModal
        open={openStrategies}
        onOpenChange={setOpenStrategies}
        onCreate={() => {
          setOpenStrategies(false);
          setOpenBuilder(true);
        }}
        onDeploy={() => {
          setOpenStrategies(false);
          setOpenDeploy(true);
        }}
      />
      <StrategyBuilderModal open={openBuilder} onOpenChange={setOpenBuilder} />
      <DeployModal open={openDeploy} onOpenChange={setOpenDeploy} defaultTargetDate={date} />
    </main>
  );
}