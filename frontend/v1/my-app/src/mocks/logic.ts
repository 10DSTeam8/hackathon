import { STATE, type Appointment, type Strategy, type Deployment } from "./data";

// Buckets for live-adjusted distribution
const BUCKETS: [number, number][] = [
  [0.0, 0.2],
  [0.2, 0.4],
  [0.4, 0.6],
  [0.6, 0.8],
  [0.8, 1.0],
];

function clamp01(x: number) {
  return Math.min(0.99, Math.max(0.01, x));
}

function inSegment(a: Appointment, s: Strategy) {
  if (!s.segment) return true;
  const r = a.baseline_risk; // segmentation by baseline
  const age = a.patient.age;
  return (
    age >= s.segment.age_min &&
    age <= s.segment.age_max &&
    r >= s.segment.risk_min &&
    r <= s.segment.risk_max
  );
}

function pickVariant(split: number): "A" | "B" {
  return Math.random() < split ? "A" : "B";
}

export function deployStrategies(dep: Deployment) {
  const chosen = dep.strategy_ids.map((id) => STATE.strategies.get(id)).filter(Boolean) as Strategy[];
  const target = dep.target_day;

  const targetAppts = [...STATE.appointments.values()].filter((a) => a.dayIndex === target);
  const matched = new Set<string>();

  // specific strategies
  for (const strat of chosen.filter((s) => !s.is_default)) {
    for (const a of targetAppts) {
      if (inSegment(a, strat)) {
        a.strategy_variant = pickVariant(strat.ab.split);
        a.strategy_applied_ids.push(strat.id);
        matched.add(a.id);
      }
    }
  }
  // default fallback
  const def = chosen.find((s) => s.is_default);
  if (def) {
    for (const a of targetAppts) {
      if (!matched.has(a.id)) {
        a.strategy_variant = pickVariant(def.ab.split);
        a.strategy_applied_ids.push(def.id);
      }
    }
  }
}

function applyCommsEffect(a: Appointment, kind: "sms" | "call") {
  const factor = kind === "sms" ? 0.9 : 0.8; // comms effect
  a.live_adjusted_risk = clamp01(Number((a.live_adjusted_risk * factor).toFixed(3)));
}

export function runScheduledCommsForDay(t: number) {
  // Execute any days_of_action where (offset === a.dayIndex - t)
  for (const a of STATE.appointments.values()) {
    for (const stratId of a.strategy_applied_ids) {
      const strat = STATE.strategies.get(stratId)!;
      const variantDef = strat.ab[a.strategy_variant ?? "A"];
      for (const offset of variantDef.days_of_action) {
        if (offset === a.dayIndex - t) {
          a.comms_history.push({
            ts: new Date().toISOString(),
            type: variantDef.type,
            variant: a.strategy_variant ?? "A",
            note: "scheduled",
          });
          // Apply effect to live_adjusted_risk (pre-day adjustments)
          applyCommsEffect(a, variantDef.type);
        }
      }
    }
  }
}

export function computeLiveAdjustmentsForToday() {
  const t = STATE.todayIndex;
  for (const a of STATE.appointments.values()) {
    if (a.dayIndex !== t) continue;

    // Start from current live_adjusted_risk (already includes comms effects)
    let live = a.live_adjusted_risk;

    // Same-day heuristics:
    // - confirmed sms in last 12h -> *0.6
    // - else if live > 0.4 -> +0.05
    const last12h = Date.now() - 12 * 3600 * 1000;
    const recentConfirm = a.comms_history
      .filter((c) => c.type === "sms")
      .some((c) => new Date(c.ts).getTime() >= last12h && /confirmed/i.test(c.note ?? ""));
    if (recentConfirm) live = Math.max(0.01, Number((live * 0.6).toFixed(3)));
    else if (live > 0.4) live = Math.min(0.99, Number((live + 0.05).toFixed(3)));

    a.live_adjusted_risk = live;
  }
}

export function closeDayAndGenerateOutcomes(dayJustEnded: number) {
  for (const a of STATE.appointments.values()) {
    if (a.dayIndex === dayJustEnded && a.outcome === "unknown") {
      const p = a.live_adjusted_risk; // outcomes based on live-adjusted
      a.outcome = Math.random() < p ? "no_show" : "attended";
    }
  }
}

export function summarizeDay(dayIndex: number) {
  const appts = [...STATE.appointments.values()].filter((a) => a.dayIndex === dayIndex);
  const avg =
    appts.length === 0 ? 0 : appts.reduce((s, a) => s + a.live_adjusted_risk, 0) / appts.length;

  const dist = BUCKETS.map(([lo, hi]) => {
    const label = `${lo.toFixed(1)}-${hi.toFixed(1)}`;
    const count = appts.filter((a) => a.live_adjusted_risk >= lo && a.live_adjusted_risk < hi).length;
    return { bucket: label, count };
  });

  // strategies applied
  const ids = new Set<string>();
  for (const a of appts) for (const sid of a.strategy_applied_ids) ids.add(sid);
  const strategies_applied = [...ids].map((id) => {
    const s = STATE.strategies.get(id)!;
    return { id: s.id, name: s.name };
  });

  // For last completed day (dayIndex-1): pred_vs_obs + A/B outcomes, computed from live_adjusted_risk
  let pred_vs_obs = null as { dayIndex: number; pred_no_show_rate: number; obs_no_show_rate: number } | null;
  const ab_outcomes: {
    dayIndex: number;
    strategy_id: string;
    strategy_name: string;
    variant_stats: { variant: "A" | "B"; count: number; pred_no_show_rate: number; obs_no_show_rate: number }[];
  }[] = [];

  if (dayIndex - 1 >= 0) {
    const d = dayIndex - 1;
    const prev = [...STATE.appointments.values()].filter((a) => a.dayIndex === d);
    if (prev.length > 0 && prev.every((a) => a.outcome !== "unknown")) {
      const pred = prev.reduce((s, a) => s + a.live_adjusted_risk, 0) / prev.length;
      const obs = prev.filter((a) => a.outcome === "no_show").length / prev.length;
      pred_vs_obs = { dayIndex: d, pred_no_show_rate: Number(pred.toFixed(3)), obs_no_show_rate: Number(obs.toFixed(3)) };

      const byStrategy = new Map<string, { name: string; A: Appointment[]; B: Appointment[] }>();
      for (const a of prev) {
        for (const sid of a.strategy_applied_ids) {
          if (!byStrategy.has(sid)) byStrategy.set(sid, { name: STATE.strategies.get(sid)!.name, A: [], B: [] });
          const bucket = byStrategy.get(sid)!;
          if (a.strategy_variant === "B") bucket.B.push(a);
          else bucket.A.push(a);
        }
      }
      for (const [sid, obj] of byStrategy) {
        const stat = (arr: Appointment[]) => {
          const count = arr.length;
          const pred =
            count === 0 ? 0 : arr.reduce((s, a) => s + a.live_adjusted_risk, 0) / count;
          const obs = count === 0 ? 0 : arr.filter((a) => a.outcome === "no_show").length / count;
          return { count, pred_no_show_rate: Number(pred.toFixed(3)), obs_no_show_rate: Number(obs.toFixed(3)) };
        };
        ab_outcomes.push({
          dayIndex: d,
          strategy_id: sid,
          strategy_name: obj.name,
          variant_stats: [
            { variant: "A", ...stat(obj.A) },
            { variant: "B", ...stat(obj.B) },
          ],
        });
      }
    }
  }

  const dateISO = new Date(
    new Date(STATE.startDateISO + "T00:00:00Z").getTime() + dayIndex * 24 * 3600 * 1000
  ).toISOString().slice(0, 10);

  return {
    dayIndex,
    date_iso: dateISO,
    avg_risk_live_adj: Number(avg.toFixed(3)),
    dist_live_adj: dist,
    strategies_applied,
    pred_vs_obs,
    ab_outcomes,
    todayIndex: STATE.todayIndex,
  };
}

export function listAppointmentsSummary(dayIndex: number) {
  const appts = [...STATE.appointments.values()]
    .filter((a) => a.dayIndex === dayIndex)
    .sort((a, b) => a.datetime.localeCompare(b.datetime));

  return appts.map((a) => {
    const dt = new Date(a.datetime);
    const hh = String(dt.getUTCHours()).padStart(2, "0");
    const mm = String(dt.getUTCMinutes()).padStart(2, "0");
    return {
      id: a.id,
      patient: a.patient,
      time: `${hh}:${mm}`,
      baseline_risk: a.baseline_risk,
      live_adjusted_risk: a.live_adjusted_risk,
      strategy_variant: a.strategy_variant,
    };
  });
}