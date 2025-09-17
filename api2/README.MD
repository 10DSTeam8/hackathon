

# SETUP AND RUN:
python -m venv .venv && . .venv/bin/activate
pip install -r requirements.txt
export FLASK_APP=app.py FLASK_ENV=development
flask run --port 5001

NHS ATTEND — Mock API (Flask)

README & Route Guide (drop-in)

This README explains how to run the API and use every route to simulate the full NHS ATTEND storyboard (seeded appointments, strategies with A/B, comms + replies, live risk, logs, simulation, outcomes).

⸻

0) Quick Start

python -m venv .venv
# macOS/Linux
source .venv/bin/activate
# Windows (PowerShell)
.venv\Scripts\Activate.ps1

pip install -r requirements.txt

# Run (port 5001 by default)
python app.py
# or:
export FLASK_APP=app.py FLASK_ENV=development
flask run --port 5001

Optional (real model):

export SAGEMAKER_ENDPOINT_NAME=your-endpoint
export AWS_REGION=eu-west-1

	•	Appointments are seeded for Day 0–2 at startup; no booking endpoints.
	•	Base URL: http://localhost:5001/api

⸻

1) Simulation at a Glance
	•	State: todayIndex (0-based) is the simulation pointer.
	•	Deploy strategies to a target day (e.g., Day 2).
	•	Simulate day-by-day to apply scheduled comms, fill end-of-day “no_reply_eod”, and finalize outcomes for the day that just ended.
	•	Live Day (when dayIndex == todayIndex): apply same-day live adjustments once (confirmations ↓ risk; silence slight ↑ risk), then show accuracy and allow manual actions (send SMS / call).
	•	Pred vs Obs and A/B outcomes show when you view the day after a day is completed.

⸻

2) Data Model (simplified overview)

Appointment (full detail)

{
  "id": "uuid",
  "patient": {"name":"…","age":42,"phone":"+44…","email":"…"},
  "datetime": "2025-09-16T10:00:00+00:00",
  "dayIndex": 0,
  "features": {...},
  "static_risk": 0.28,
  "live_adjusted_risk": 0.25,
  "predicted_outcome_static": "attend|dna",
  "predicted_outcome_live": "attend|dna",
  "strategy_variant": "A|B|null",
  "strategy_applied_ids": ["strat-1"],
  "comms_history": [{"ts":"…","type":"sms|call","variant":"A|B","note":"…"}],
  "outcome": "unknown|attended|no_show"
}

Strategy

{
  "id": "strat-1",
  "name": "High Risk Outreach",
  "is_default": false,
  "segment": {"age_min":18,"age_max":30,"risk_min":0.3,"risk_max":1.0},
  "ab": {
    "split": 0.5,
    "A": {"type":"sms","days_of_action":[-1]},
    "B": {"type":"call","days_of_action":[-1]}
  }
}

Log Entry

{
  "id":"log-uuid",
  "ts":"2025-09-16T09:00:00Z",
  "dayIndex":1,
  "appointment_id":"uuid",
  "patient_name":"Jane Doe",
  "type":"sms|call|reply",
  "variant":"A|B|null",
  "message":"string",
  "reply":"yes|no|no_reply_eod|null"
}


⸻

3) Routes (complete)

All routes are prefixed with /api.
Example: GET /api/health

3.1 Health / Seeding

GET /api/health

Check API status and see simulation pointers.

Response 200

{
  "ok": true,
  "todayIndex": 0,
  "startDateISO": "2025-09-16"
}


⸻

3.2 Day Summary

GET /api/day/:dayIndex/summary

Return metrics for a specific day.
	•	Applies one-time live-day adjustments if dayIndex == todayIndex.
	•	Includes:
	•	avg_static_risk, pred_no_show_rate_static
	•	avg_live_risk, pred_no_show_rate_live
	•	dist_live (buckets)
	•	strategies_applied
	•	If today: outcomes_recorded_today, accuracy_today
	•	For last completed day: pred_vs_obs and ab_outcomes
	•	todayIndex (global pointer)

Example

curl http://localhost:5001/api/day/0/summary

Response 200 (example)

{
  "dayIndex": 0,
  "date_iso": "2025-09-16",
  "avg_static_risk": 0.24,
  "pred_no_show_rate_static": 0.24,
  "avg_live_risk": 0.22,
  "pred_no_show_rate_live": 0.22,
  "dist_live": [{"bucket":"0.0-0.2","count":5}, ...],
  "strategies_applied": [{"id":"strat-1","name":"High Risk Outreach"}],
  "outcomes_recorded_today": 0,
  "accuracy_today": null,
  "pred_vs_obs": null,
  "ab_outcomes": [],
  "todayIndex": 0
}


⸻

3.3 Appointments

GET /api/appointments?dayIndex=<int>

List summary rows for a day, sorted by time.
	•	When dayIndex == todayIndex, applies one-time live adjustments.
	•	Fields: time, static_risk, predicted_outcome_static, live_adjusted_risk, predicted_outcome_live, strategy_variant.

Example

curl "http://localhost:5001/api/appointments?dayIndex=2"

Response 200

[
  {
    "id": "a1",
    "patient": {"name":"Jane Doe","age":23,"phone":"+44…","email":"jane@…"},
    "time":"10:00",
    "static_risk":0.62,
    "predicted_outcome_static":"dna",
    "live_adjusted_risk":0.49,
    "predicted_outcome_live":"attend",
    "strategy_variant":"B"
  }
]

GET /api/appointments/:id

Full appointment detail.

Example

curl http://localhost:5001/api/appointments/<APPT_ID>

Response 200

{ "... full Appointment object ..." }

404 if not found.

⸻

3.4 Strategies

GET /api/strategies

List all strategies (including defaults).

curl http://localhost:5001/api/strategies

POST /api/strategies

Create a strategy.

Request

{
  "name": "High Risk Outreach",
  "is_default": false,
  "segment": {"age_min":18,"age_max":80,"risk_min":0.5,"risk_max":1.0},
  "ab": {
    "split": 0.5,
    "A": {"type":"sms","days_of_action":[-1]},
    "B": {"type":"call","days_of_action":[-1]}
  }
}

Response 201

{ "... created strategy ..." }

400 if invalid payload.

PATCH /api/strategies/:id

Update name, default flag, segment, A/B settings.

Request (example)

{
  "name": "High Risk Outreach v2",
  "ab": { "split": 0.6, "A": {"days_of_action":[-2,-1]} }
}

Response 200

{ "... updated strategy ..." }

404 if not found.

⸻

3.5 Deploy

POST /api/deploy

Assign one or more strategies to a target day (A/B split per appointment).

Rules
	•	max(|days_of_action|) across A & B must be <= (target_day - todayIndex).

Request

{ "target_day": 2, "strategy_ids": ["strat-1","strat-2","strat-default"] }

Response 200

{ "id":"dep-uuid", "target_day":2, "strategy_ids":["strat-1","strat-2","strat-default"] }

400 if strategy window exceeds available days.

⸻

3.6 Actions (log-only)

POST /api/actions/send_sms

Log an SMS action for an appointment and optionally RNG a reply.

Request

{ "appointment_id": "uuid", "template": "Hi {{name}}, reply YES to confirm" }

Response 200

{ "ok": true }

404 if appointment not found.

POST /api/actions/call_now

Log a call action for an appointment.

Request

{ "appointment_id": "uuid" }

Response 200

{ "ok": true }

404 if appointment not found.

⸻

3.7 Logs

GET /api/logs?dayIndex=<int>

Return all logs for that day: comms + replies (sorted ascending).

Example

curl "http://localhost:5001/api/logs?dayIndex=1"

Response 200

[
  {
    "id":"log-1",
    "ts":"2025-09-16T09:00:00Z",
    "dayIndex":1,
    "appointment_id":"a1",
    "patient_name":"Jane Doe",
    "type":"sms",
    "variant":"A",
    "message":"Hi Jane, your appointment is on 17/09 at 10:00. Reply YES to confirm.",
    "reply": null
  },
  {
    "id":"log-2",
    "ts":"2025-09-16T13:42:00Z",
    "dayIndex":1,
    "appointment_id":"a1",
    "patient_name":"Jane Doe",
    "type":"reply",
    "variant":"A",
    "message":"Patient reply",
    "reply":"yes"
  }
]


⸻

3.8 Predict (model or fallback)

POST /api/predict

Predict risk from a compact feature set.
Used internally during seeding; available for testing.

Request

{ "features": { "age": 32, "prev_no_shows": 1, "distance_km": 10.5, "slot_hour": 17, "new_patient": true, "weekday": 2 } }

Response 200

{ "risk": 0.32 }


⸻

3.9 Simulate

POST /api/simulate/advance

Advance the simulation pointer day-by-day.

What happens at each step:
	1.	Execute scheduled comms where offset == (t - appt.dayIndex); apply risk effects (SMS×0.9, Call×0.8); log comms; maybe RNG replies.
	2.	End-of-day: if a comm was sent but no reply, record reply=no_reply_eod.
	3.	Settle outcomes for the day that just ended (Bernoulli with live_adjusted_risk).
	4.	Move todayIndex to t+1.
	5.	On entering the new todayIndex, apply one-time live-day adjustment.

Request

{ "toDayIndex": 2 }

Response 200

{ "ok": true, "todayIndex": 2 }

400 if toDayIndex < todayIndex.

⸻

4) Typical Demo Flow (cURL)

# 1) Health (seeds Day 0–2 automatically)
curl http://localhost:5001/api/health

# 2) Day 0 summary
curl http://localhost:5001/api/day/0/summary

# 3) (Optional) Redeploy to Day 2
curl -X POST http://localhost:5001/api/deploy \
  -H "Content-Type: application/json" \
  -d '{"target_day":2,"strategy_ids":["strat-1","strat-2","strat-default"]}'

# 4) Simulate to Day 1 (scheduled comms fire; replies RNG)
curl -X POST http://localhost:5001/api/simulate/advance \
  -H "Content-Type: application/json" \
  -d '{"toDayIndex":1}'

# 5) Logs for Day 1
curl "http://localhost:5001/api/logs?dayIndex=1"

# 6) Check Day 2 appointments (live risk adjusted by comms so far)
curl "http://localhost:5001/api/appointments?dayIndex=2"

# 7) Simulate to Day 2 (Live Day; applies live-day heuristics)
curl -X POST http://localhost:5001/api/simulate/advance \
  -H "Content-Type: application/json" \
  -d '{"toDayIndex":2}'

# 8) Day 2 summary (shows outcomes_recorded_today/accuracy as hours pass)
curl "http://localhost:5001/api/day/2/summary"

# 9) Manual action (SMS) for a specific appointment (replace APPT_ID)
curl -X POST http://localhost:5001/api/actions/send_sms \
  -H "Content-Type: application/json" \
  -d '{"appointment_id":"APPT_ID","template":"Hi {{name}}, reply YES to confirm"}'

# 10) Close Day 2 by advancing to Day 3 (Pred vs Obs for Day 2 will appear on Day 3 summary)
curl -X POST http://localhost:5001/api/simulate/advance \
  -H "Content-Type: application/json" \
  -d '{"toDayIndex":3}'

curl "http://localhost:5001/api/day/3/summary"


⸻

5) How risks & predictions are computed
	•	Static risk (static_risk): model (SageMaker if configured, else heuristic) at seeding.
	•	Comms effects: each SMS multiplies risk by 0.9, each Call by 0.8 (clamped to [0.01, 0.99]).
	•	Live-Day heuristics (applied once when a day becomes “today”):
	•	Confirmed (reply yes) in last 12h → × 0.6
	•	No reply and risk > 0.4 → + 0.05 (clamped)
	•	Predictions:
	•	predicted_outcome_static = static_risk >= 0.5 ? "dna" : "attend"
	•	predicted_outcome_live   = live_adjusted_risk >= 0.5 ? "dna" : "attend"
	•	Outcomes: on day close, no_show ~ Bernoulli(p=live_adjusted_risk).

⸻

6) Troubleshooting
	•	CORS: Enabled by default (Flask-Cors), so you can call the API from your Vite dev server.
	•	Seed repeats? Seeding runs once per process; restart your API to reset.
	•	Live adjustments compounding? They won’t—guarded by an internal flag to apply once per live day.
	•	Strategy window error: The API validates max(|days_of_action|) <= (target_day - todayIndex). Deploy further ahead or shorten offsets.

⸻

7) Frontend pointers
	•	Use these endpoints directly with TanStack Query.
	•	Day View sequence:
	1.	GET /day/:dayIndex/summary
	2.	GET /appointments?dayIndex=:n
	3.	GET /logs?dayIndex=:n
	4.	POST /simulate/advance to move days
	5.	Actions: POST /actions/send_sms or POST /actions/call_now

⸻

That’s it! With this README and the provided app.py, you can simulate the full system end-to-end for your hackathon MVP.