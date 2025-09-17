import { faker } from "@faker-js/faker/locale/en_GB";

export type Appointment = {
  id: string;
  patient: { name: string; age: number; phone: string; email: string };
  datetime: string;  // ISO
  dayIndex: number;
  features: {
    age: number;
    prev_no_shows: number;
    distance_km: number;
    slot_hour: number;
    new_patient: boolean;
    weekday: number;
  };

  baseline_risk: number;              // raw SageMaker risk at booking
  live_adjusted_risk: number;         // baseline + comms (+ same-day signals if today)

  strategy_variant: "A" | "B" | null;
  strategy_applied_ids: string[];
  comms_history: { ts: string; type: "sms" | "call"; variant?: "A" | "B"; note?: string }[];
  outcome: "unknown" | "attended" | "no_show";
};

export type Strategy = {
  id: string;
  name: string;
  is_default: boolean;
  segment?: { age_min: number; age_max: number; risk_min: number; risk_max: number };
  ab: {
    split: number; // 0..1
    A: { type: "sms" | "call"; days_of_action: number[] };
    B: { type: "sms" | "call"; days_of_action: number[] };
  };
};

export type Deployment = { id: string; target_day: number; strategy_ids: string[] };

export const STATE = {
  todayIndex: 0,
  startDateISO: new Date().toISOString().slice(0, 10),
  appointments: new Map<string, Appointment>(),
  strategies: new Map<string, Strategy>(),
  deployments: new Map<string, Deployment>(),
};

function clamp01(x: number) {
  return Math.min(0.99, Math.max(0.01, x));
}
function heuristicRisk(feat: Appointment["features"]) {
  let base = 0.15 + 0.05 * feat.prev_no_shows + 0.01 * feat.distance_km;
  if (feat.new_patient) base += 0.06;
  if (feat.slot_hour < 9 || feat.slot_hour > 16) base += 0.03;
  return Number(clamp01(base).toFixed(3));
}
function dayToDate(dayIndex: number) {
  const base = new Date(STATE.startDateISO + "T00:00:00Z");
  base.setUTCDate(base.getUTCDate() + dayIndex);
  return base;
}

export function seedStrategies() {
  const s1: Strategy = {
    id: "strat-1",
    name: "High Risk Outreach",
    is_default: false,
    segment: { age_min: 18, age_max: 80, risk_min: 0.5, risk_max: 1.0 },
    ab: { split: 0.5, A: { type: "sms", days_of_action: [-1] }, B: { type: "call", days_of_action: [-1] } },
  };
  const s2: Strategy = {
    id: "strat-2",
    name: "Young Cohort SMS",
    is_default: false,
    segment: { age_min: 18, age_max: 30, risk_min: 0.3, risk_max: 1.0 },
    ab: { split: 0.5, A: { type: "sms", days_of_action: [-1] }, B: { type: "sms", days_of_action: [-1] } },
  };
  const sDefault: Strategy = {
    id: "strat-default",
    name: "Default Safety Net",
    is_default: true,
    ab: { split: 1, A: { type: "sms", days_of_action: [-1] }, B: { type: "sms", days_of_action: [-1] } },
  };
  [s1, s2, sDefault].forEach((s) => STATE.strategies.set(s.id, s));
}

export function seedAppointments() {
  const perDay = [10, 10, 10]; // Day 0..2
  for (let d = 0; d <= 2; d++) {
    const date = dayToDate(d);
    for (let i = 0; i < perDay[d]; i++) {
      const hour = 8 + (i % 9); // 8..16
      const dt = new Date(date);
      dt.setUTCHours(hour, 0, 0, 0);

      const name = faker.person.fullName();
      const age = faker.number.int({ min: 18, max: 85 });
      const patient = { name, age, phone: faker.phone.number(), email: faker.internet.email({ firstName: name.split(" ")[0] }) };

      const features = {
        age,
        prev_no_shows: faker.number.int({ min: 0, max: 2 }),
        distance_km: faker.number.float({ min: 0, max: 20, precision: 0.1 }),
        slot_hour: hour,
        new_patient: faker.datatype.boolean(),
        weekday: dt.getUTCDay(),
      };
      const baseline = heuristicRisk(features);

      const appt: Appointment = {
        id: crypto.randomUUID(),
        patient,
        datetime: dt.toISOString(),
        dayIndex: d,
        features,
        baseline_risk: baseline,
        live_adjusted_risk: baseline, // start at baseline; comms/live updates will modify
        strategy_variant: null,
        strategy_applied_ids: [],
        comms_history: [],
        outcome: "unknown",
      };
      STATE.appointments.set(appt.id, appt);
    }
  }
}