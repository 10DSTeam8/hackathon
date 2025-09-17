import { http, HttpResponse } from "msw";
import { STATE, seedAppointments, seedStrategies, type Deployment } from "./data";
import {
  deployStrategies,
  runScheduledCommsForDay,
  computeLiveAdjustmentsForToday,
  closeDayAndGenerateOutcomes,
  summarizeDay,
  listAppointmentsSummary,
} from "./logic";

let seeded = false;
function ensureSeed() {
  if (!seeded) {
    seedStrategies();
    seedAppointments();
    seeded = true;
    // Pre-deploy some defaults to Day 2
    const dep: Deployment = { id: "dep-1", target_day: 2, strategy_ids: ["strat-1", "strat-2", "strat-default"] };
    deployStrategies(dep);
    computeLiveAdjustmentsForToday();
  }
}

export const handlers = [
  http.get("/api/day/:dayIndex/summary", ({ params }) => {
    ensureSeed();
    const dayIndex = Number(params.dayIndex);
    if (dayIndex === STATE.todayIndex) computeLiveAdjustmentsForToday();
    const body = summarizeDay(dayIndex);
    return HttpResponse.json(body);
  }),

  http.get("/api/appointments", ({ request }) => {
    ensureSeed();
    const url = new URL(request.url);
    const dayIndex = Number(url.searchParams.get("dayIndex") || "0");
    if (dayIndex === STATE.todayIndex) computeLiveAdjustmentsForToday();
    return HttpResponse.json(listAppointmentsSummary(dayIndex));
  }),

  http.get("/api/appointments/:id", ({ params }) => {
    ensureSeed();
    const id = String(params.id);
    const a = [...STATE.appointments.values()].find((x) => x.id === id);
    if (!a) return HttpResponse.json({ error: "Not found" }, { status: 404 });
    return HttpResponse.json(a);
  }),

  // Actions
  http.post("/api/actions/send_sms", async ({ request }) => {
    ensureSeed();
    const { appointment_id, template } = (await request.json()) as { appointment_id: string; template: string };
    const a = [...STATE.appointments.values()].find((x) => x.id === appointment_id);
    if (!a) return HttpResponse.json({ error: "Not found" }, { status: 404 });
    a.comms_history.push({ ts: new Date().toISOString(), type: "sms", note: template.includes("YES") ? "sent (awaiting confirm)" : "sent" });
    // optional: simulate confirmations sometimes
    if (Math.random() < 0.5 && /YES/.test(template)) {
      a.comms_history.push({ ts: new Date().toISOString(), type: "sms", note: "confirmed" });
    }
    computeLiveAdjustmentsForToday();
    return HttpResponse.json({ ok: true });
  }),

  http.post("/api/actions/call_now", async ({ request }) => {
    ensureSeed();
    const { appointment_id } = (await request.json()) as { appointment_id: string };
    const a = [...STATE.appointments.values()].find((x) => x.id === appointment_id);
    if (!a) return HttpResponse.json({ error: "Not found" }, { status: 404 });
    a.comms_history.push({ ts: new Date().toISOString(), type: "call", note: "call logged" });
    computeLiveAdjustmentsForToday();
    return HttpResponse.json({ ok: true });
  }),

  http.post("/api/deploy", async ({ request }) => {
    ensureSeed();
    const dep = (await request.json()) as Deployment;
    deployStrategies(dep);
    return HttpResponse.json({ ok: true });
  }),

  http.post("/api/simulate/advance", async ({ request }) => {
    ensureSeed();
    const { toDayIndex } = (await request.json()) as { toDayIndex: number };
    const start = STATE.todayIndex;
    const target = Math.max(toDayIndex, start);
    for (let t = start; t < target; t++) {
      runScheduledCommsForDay(t);        // comms effects -> live_adjusted_risk
      closeDayAndGenerateOutcomes(t);    // outcomes based on live_adjusted_risk
      STATE.todayIndex = t + 1;
    }
    computeLiveAdjustmentsForToday();     // add same-day signals for new today
    return HttpResponse.json({ ok: true, toDayIndex: STATE.todayIndex });
  }),
];