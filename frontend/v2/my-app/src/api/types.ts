// src/api/types.ts  (DROP-IN REPLACEMENT)

export type DayBucket = { bucket: string; count: number };

export type ABVariantStat = {
  variant: "A" | "B";
  count: number;
  pred_no_show_rate: number;
  obs_no_show_rate: number;
};

export type ABOutcome = {
  dayIndex: number;
  strategy_id: string;
  strategy_name: string;
  variant_stats: ABVariantStat[];
};

export type ABTodayVariant = {
  total: number;              // total scheduled for today in this variant
  completed: number;          // completed so far
  success_observed: number;   // attendance rate among completed [0..1]
  pred_no_show_rate: number;  // mean live risk among completed [0..1]
};

export type ABToday = {
  strategy_id: string;
  strategy_name: string;
  A: ABTodayVariant;
  B: ABTodayVariant;
};

export type PredVsObs = {
  dayIndex: number;
  pred_no_show_rate: number;
  obs_no_show_rate: number;
} | null;

export type TodayPredVsObs = {
  completed: number;
  pred_no_show_rate: number;
  obs_no_show_rate: number;
} | null;

export type DaySummary = {
  dayIndex: number;
  date_iso: string;

  avg_static_risk: number;
  pred_no_show_rate_static: number;
  avg_live_risk: number;
  pred_no_show_rate_live: number;

  dist_live: DayBucket[];
  strategies_applied: { id: string; name: string }[];

  // Today-only (running)
  outcomes_recorded_today: number | null;
  accuracy_today: number | null;
  today_pred_vs_obs: TodayPredVsObs;

  // Previous day fully-settled
  pred_vs_obs: PredVsObs;
  ab_outcomes: ABOutcome[];

  // Today A/B running
  ab_today: ABToday[];

  todayIndex: number;
};

export type Patient = {
  name: string;
  age: number;
  phone: string;
  email: string;
};

export type AppointmentSummary = {
  id: string;
  patient: Patient;
  time: string; // HH:mm

  // List view shows live risk + live prediction
  live_adjusted_risk: number;
  predicted_outcome_live: "attend" | "dna";

  // Real outcome (populates live as stepping progresses)
  outcome: "unknown" | "attended" | "no_show";

  // Present in API but not shown in list
  strategy_variant: "A" | "B" | null;
};

export type Appointment = {
  id: string;
  patient: Patient;
  datetime: string;
  dayIndex: number;

  static_risk: number;
  live_adjusted_risk: number;
  predicted_outcome_static: "attend" | "dna";
  predicted_outcome_live: "attend" | "dna";

  strategy_variant: "A" | "B" | null;
  strategy_applied_ids: string[];

  comms_history: { ts: string; type: "sms" | "call"; variant?: "A" | "B" | null; note?: string }[];

  outcome: "unknown" | "attended" | "no_show";
};

export type Strategy = {
  id: string;
  name: string;
  is_default: boolean;
  segment?: {
    age_min?: number;
    age_max?: number;
    risk_min?: number;
    risk_max?: number;
  } | null;
  ab: {
    split: number; // 0..1
    A: { type: "sms" | "call"; days_of_action: number[] };
    B: { type: "sms" | "call"; days_of_action: number[] };
  };
};

export type Deployment = {
  id: string;
  target_day: number;
  strategy_ids: string[];
};

export type LogEntry = {
  id: string;
  ts: string;
  send_day_index: number;
  appointment_day_index: number;
  scheduled_date_iso: string;
  appointment_date_iso: string;
  appointment_id: string;
  patient_name: string;
  type: "sms" | "call" | "reply" | "outcome";
  variant: "A" | "B" | null;
  message: string;
  reply: "yes" | "no" | "no_reply_eod" | null;
  outcome?: "attended" | "no_show";
};

export type SimStatus = {
  todayIndex: number;
  todayDateISO: string;
  total: number;
  next_idx: number;
  remaining: number;
  next_appointment: null | { id: string; patient_name: string; time: string; live_adjusted_risk: number };
  last_processed_id: string | null;
};

export type TickResult = {
  processed: null | { id: string; outcome: "attended" | "no_show"; live_adjusted_risk: number };
  status: {
    todayIndex: number;
    todayDateISO: string;
    total: number;
    next_idx: number;
    remaining: number;
    last_processed_id: string | null;
  };
};