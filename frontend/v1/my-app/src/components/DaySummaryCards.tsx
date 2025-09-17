// src/components/DaySummaryCards.tsx  (DROP-IN REPLACEMENT)

import { fmtPct } from "@/api/client";
import type { DaySummary, ABToday } from "@/api/types";
import { Card } from "@/components/ui/card";
import { Info } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  LabelList,
  CartesianGrid,
} from "recharts";

function LabelWithInfo({
  label,
  info,
}: {
  label: string;
  info: string;
}) {
  return (
    <div className="flex items-start gap-2">
      <span className="text-sm font-medium">{label}</span>
      <Info className="h-4 w-4 mt-[2px] opacity-60" aria-label="More info" />
    </div>
  );
}

function Metric({
  title,
  value,
  info,
  sub,
}: {
  title: string;
  value: string;
  info: string;
  sub?: string;
}) {
  return (
    <Card className="rounded-2xl p-4">
      <LabelWithInfo label={title} info={info} />
      <div className="mt-2 text-2xl font-semibold">{value}</div>
      {sub && <div className="mt-1 text-xs opacity-70">{sub}</div>}
    </Card>
  );
}

function StrategyABChart({ g }: { g: ABToday }) {
  // Build two rows (A and B)
  const base = [
    { variant: "A:", value: g.A?.success_observed ?? 0, completed: g.A?.completed ?? 0, total: g.A?.total ?? 0 },
    { variant: "B:", value: g.B?.success_observed ?? 0, completed: g.B?.completed ?? 0, total: g.B?.total ?? 0 },
  ];

  const dataA = base.filter((d) => d.variant === "A:");
  const dataB = base.filter((d) => d.variant === "B:");

  return (
    <div className="rounded-xl border p-3">
      <div className="text-sm font-semibold mb-2">{g.strategy_name}</div>
      <div className="h-36">
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={base} layout="vertical" margin={{ top: 8, right: 16, bottom: 8, left: 8 }}>
            <CartesianGrid horizontal={false} stroke="var(--chart-grid)" />
            <XAxis
              type="number"
              domain={[0, 1]}
              tickFormatter={(v) => `${Math.round((v as number) * 100)}%`}
              tick={{ fontSize: 12 }}
              stroke="var(--muted-fg)"
            />
            <YAxis type="category" dataKey="variant" width={85} tick={{ fontSize: 12 }} stroke="var(--muted-fg)" />
            <Tooltip
              formatter={(val: number, _name, props) => {
                const rec = (props?.payload ?? {}) as (typeof base)[number];
                return [`${Math.round((val ?? 0) * 100)}%`, `Success (obs) • ${rec.completed}/${rec.total} done`];
              }}
              labelFormatter={() => ""}
              wrapperStyle={{ zIndex: 30, borderRadius: 12, border: "1px solid var(--border)" }}
            />
            {/* A (brand blue) */}
            <Bar dataKey="value" fill="var(--chart-bar)" radius={[4, 4, 4, 4]}>
              <LabelList
                dataKey="value"
                position="right"
                formatter={(label: React.ReactNode) => {
                  const value = typeof label === "number" ? label : Number(label);
                  return `${Math.round((value ?? 0) * 100)}%`;
                }}
                className="text-xs"
              />
            </Bar>
            {/* B (green) */}
            <Bar dataKey="value" fill="var(--chart-bar-b)" radius={[4, 4, 4, 4]}>
              <LabelList
                dataKey="value"
                position="right"
                formatter={(label: React.ReactNode) => {
                  const value = typeof label === "number" ? label : Number(label);
                  return `${Math.round((value ?? 0) * 100)}%`;
                }}
                className="text-xs"
              />
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-2 grid grid-cols-2 gap-2 text-xs opacity-70">
        <div>A: {g.A?.completed ?? 0}/{g.A?.total ?? 0} completed</div>
        <div className="text-right">B: {g.B?.completed ?? 0}/{g.B?.total ?? 0} completed</div>
      </div>
    </div>
  );
}

export function DaySummaryCards({ s }: { s: DaySummary }) {
  return (
    <section className="grid grid-cols-1 lg:grid-cols-12 gap-4">
      {/* Left column: core metrics */}
      <div className="lg:col-span-6 grid grid-cols-1 sm:grid-cols-2 gap-4">
        <Metric
          title="Predicted no-show % (average static risk)"
          value={fmtPct(s.pred_no_show_rate_static, 0)}
          info="Average of the model's static no-show probabilities before any live adjustments or outreach."
        />
        <Metric
          title="Predicted no-show % (average live risk)"
          value={fmtPct(s.pred_no_show_rate_live, 0)}
          info="Average of the model's current no-show probabilities after live-day adjustments and any outreach effects."
        />
        <>
          <Metric
            title="Outcomes recorded"
            value={`${s.outcomes_recorded_today ?? 0}`}
            info="Number of appointments for this day that have already happened (final outcome known)."
          />
          <Metric
            title="Accuracy"
            value={s.accuracy_today != null ? fmtPct(s.accuracy_today, 0) : "—"}
            info="Share of completed appointments where the live prediction (attend/DNA) matched the observed outcome."
          />
        </>
      </div>

      {/* Right column: Pred vs Obs + A/B */}
      <div className="lg:col-span-6 grid grid-cols-1 gap-4">
        <Card className="rounded-2xl p-4">
          <LabelWithInfo
            label="Predicted vs Observed — Today"
            info="Running comparison for today's completed appointments only. Predicted = mean live no-show probability; Observed = empirical no-show rate."
          />
          {s.today_pred_vs_obs ? (
            <div className="mt-2 grid grid-cols-3 gap-4">
              <div>
                <div className="text-xs opacity-70">Completed</div>
                <div className="text-xl font-semibold">{s.today_pred_vs_obs.completed}</div>
              </div>
              <div>
                <div className="text-xs opacity-70">Predicted no-show (live risk)</div>
                <div className="text-xl font-semibold">{fmtPct(s.today_pred_vs_obs.pred_no_show_rate, 0)}</div>
              </div>
              <div>
                <div className="text-xs opacity-70">Observed no-show</div>
                <div className="text-xl font-semibold">{fmtPct(s.today_pred_vs_obs.obs_no_show_rate, 0)}</div>
              </div>
            </div>
          ) : (
            <p className="mt-2 text-sm opacity-70">No completed appointments yet.</p>
          )}
        </Card>

        <Card className="rounded-2xl p-4">
          <div className="flex items-start justify-between">
            <LabelWithInfo
              label="A/B testing — Today"
              info="Per strategy deployed on this day. Each chart compares observed attendance (success) for Variant A vs Variant B among completed appointments."
            />
            <Badge
              variant="secondary"
              className="bg-[var(--brand-50)] text-[var(--brand-700)] border border-[var(--brand-100)]"
            >
              {s.ab_today.length} strategies
            </Badge>
          </div>
          {s.ab_today.length === 0 ? (
            <p className="mt-2 text-sm opacity-70">No strategies applied today.</p>
          ) : (
            <div className="mt-3 max-h-60 overflow-auto pr-1 space-y-3">
              {s.ab_today.map((g) => (
                <StrategyABChart key={g.strategy_id} g={g} />
              ))}
            </div>
          )}
        </Card>
      </div>
    </section>
  );
}