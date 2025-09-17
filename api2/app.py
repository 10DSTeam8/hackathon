# app.py  (DROP-IN REPLACEMENT)

from __future__ import annotations
from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta, timezone
from dateutil import tz
import os, json, random, uuid
from typing import Dict, Any, List, Optional, Tuple

# ---------------------------
# Configuration / Constants
# ---------------------------

LONDON_TZ = tz.gettz("Europe/London")  # single clinic / single timezone
RAND = random.Random()                 # deterministic if you set a seed: RAND.seed(42)

BUCKETS: List[Tuple[float, float]] = [
    (0.0, 0.2), (0.2, 0.4), (0.4, 0.6), (0.6, 0.8), (0.8, 1.0)
]

SMS_FACTOR = 0.90
CALL_FACTOR = 0.80
CONFIRM_12H_FACTOR = 0.60
SILENCE_LIFT = 0.05
PRED_THRESHOLD = 0.50

# Reply RNG (mock)
REPLY_PROB_YES = 0.35
REPLY_PROB_NO  = 0.10

# ---------------------------
# In-memory State
# ---------------------------

STATE: Dict[str, Any] = {
    "startDateISO": None,       # YYYY-MM-DD for Day 0
    "todayIndex": 0,            # simulation pointer (internal)
    "appointments": {},         # id -> appointment dict
    "strategies": {},           # id -> strategy dict
    "deployments": {},          # id -> deployment dict
    "logs": [],                 # list of log dicts
    # Intraday traversal state
    "intraday": {"dayIndex": None, "order": [], "next_idx": 0, "last_processed_id": None},
    # Avoid re-sending same-day comms twice
    "same_day_comms_done": set(),
}

# ---------------------------
# Utilities
# ---------------------------

def clamp01(x: float) -> float:
    return max(0.01, min(0.99, x))

def iso_date_for_day(day_index: int) -> str:
    base = datetime.fromisoformat(STATE["startDateISO"] + "T00:00:00+00:00")
    dt = base + timedelta(days=day_index)
    return dt.date().isoformat()

def day_index_from_date(date_iso: str) -> int:
    base = datetime.fromisoformat(STATE["startDateISO"] + "T00:00:00+00:00").date()
    target = datetime.fromisoformat(date_iso + "T00:00:00+00:00").date()
    return (target - base).days

def dt_for_day_and_hour(day_index: int, hour: int) -> datetime:
    base = datetime.fromisoformat(STATE["startDateISO"] + "T00:00:00+00:00")
    return base + timedelta(days=day_index, hours=hour)

def rand_name() -> str:
    first = RAND.choice(["Alex","Sam","Chris","Taylor","Jordan","Morgan","Jamie","Charlie","Casey","Riley","Rowan","Harper","Avery"])
    last  = RAND.choice(["Smith","Jones","Brown","Taylor","Wilson","Evans","Thompson","Johnson","Walker","Wright","Hughes","Green"])
    return f"{first} {last}"

def heuristic_predict(features: Dict[str, Any]) -> float:
    base = 0.15 + 0.05*features.get("prev_no_shows", 0) + 0.01*features.get("distance_km", 0.0)
    if features.get("new_patient"): base += 0.06
    if features.get("slot_hour", 12) < 9 or features.get("slot_hour", 12) > 16: base += 0.03
    return round(clamp01(base), 3)

def predicted_outcome_from_risk(p: float) -> str:
    return "dna" if p >= PRED_THRESHOLD else "attend"

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def parse_iso(ts: str) -> datetime:
    try:
        return datetime.fromisoformat(ts)
    except ValueError:
        if ts.endswith("Z"):
            return datetime.fromisoformat(ts.replace("Z", "+00:00"))
        raise

def log_event(*, send_day_index: int, appointment_id: str, patient_name: str,
              type: str, variant: Optional[str], message: str,
              reply: Optional[str] = None, extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Store logs with BOTH when the event was sent and the appointment's day.
    Also attach convenient ISO dates for UI: scheduled_date_iso, appointment_date_iso.
    """
    appt = STATE["appointments"].get(appointment_id)
    appointment_day_index = appt["dayIndex"] if appt else send_day_index
    entry = {
        "id": str(uuid.uuid4()),
        "ts": now_iso(),
        "send_day_index": send_day_index,
        "appointment_day_index": appointment_day_index,
        "scheduled_date_iso": iso_date_for_day(send_day_index),
        "appointment_date_iso": iso_date_for_day(appointment_day_index),
        "appointment_id": appointment_id,
        "patient_name": patient_name,
        "type": type,               # sms | call | reply | outcome
        "variant": variant,         # A | B | null
        "message": message,
        "reply": reply              # yes | no | no_reply_eod | null
    }
    if extra:
        entry.update(extra)
    STATE["logs"].append(entry)
    return entry

def sagemaker_predict(features: Dict[str, Any]) -> float:
    endpoint = os.getenv("SAGEMAKER_ENDPOINT_NAME")
    if not endpoint:
        return heuristic_predict(features)
    import boto3, json
    sm = boto3.client("sagemaker-runtime", region_name=os.getenv("AWS_REGION", "eu-west-1"))
    resp = sm.invoke_endpoint(
        EndpointName=endpoint,
        ContentType='application/json',
        Body=json.dumps({"features": features})
    )
    data = json.loads(resp["Body"].read().decode("utf-8"))
    return float(data.get("risk", heuristic_predict(features)))

# ---------------------------
# Seeding
# ---------------------------

def seed_strategies():
    strategies = [
        {
            "id": "strat-1",
            "name": "High Risk Outreach",
            "is_default": False,
            "segment": {"age_min": 18, "age_max": 80, "risk_min": 0.5, "risk_max": 1.0},
            "ab": {"split": 0.5, "A": {"type": "sms", "days_of_action": [-1]}, "B": {"type": "call", "days_of_action": [-1]}}
        },
        {
            "id": "strat-2",
            "name": "Young Cohort SMS",
            "is_default": False,
            "segment": {"age_min": 18, "age_max": 30, "risk_min": 0.3, "risk_max": 1.0},
            "ab": {"split": 0.5, "A": {"type": "sms", "days_of_action": [-1]}, "B": {"type": "sms", "days_of_action": [-1]}}
        },
        {
            "id": "strat-default",
            "name": "Default Safety Net",
            "is_default": True,
            "segment": None,
            "ab": {"split": 1.0, "A": {"type": "sms", "days_of_action": [-1]}, "B": {"type": "sms", "days_of_action": [-1]}}
        }
    ]
    for s in strategies:
        STATE["strategies"][s["id"]] = s

def seed_appointments():
    # Seed 10 appointments per day for Day 2 (adjust as needed)
    for d in [2]:
        for i in range(10):
            hour = 9 + (i % 9)  # 9..17
            patient_name = rand_name()
            age = RAND.randint(18, 85)
            features = {
                "age": age,
                "prev_no_shows": RAND.randint(0, 2),
                "distance_km": round(RAND.uniform(0, 20), 1),
                "slot_hour": hour,
                "new_patient": bool(RAND.randint(0, 1)),
                "weekday": dt_for_day_and_hour(d, hour).astimezone(LONDON_TZ).weekday()
            }
            static = sagemaker_predict(features)
            appt_id = str(uuid.uuid4())
            appt = {
                "id": appt_id,
                "patient": {"name": patient_name, "age": age, "phone": "+44 7000 000000", "email": f"{patient_name.split()[0].lower()}@example.com"},
                "datetime": dt_for_day_and_hour(d, hour).isoformat(),
                "dayIndex": d,
                "features": features,

                "static_risk": static,
                "live_adjusted_risk": static,
                "predicted_outcome_static": predicted_outcome_from_risk(static),
                "predicted_outcome_live": predicted_outcome_from_risk(static),

                "strategy_variant": None,
                "strategy_applied_ids": [],
                "comms_history": [],
                "outcome": "unknown",

                "_live_adjustment_applied": False
            }
            STATE["appointments"][appt_id] = appt

def ensure_seed():
    if not STATE["startDateISO"]:
        today_london = datetime.now(LONDON_TZ).date().isoformat()
        STATE["startDateISO"] = today_london
        STATE["todayIndex"] = 0
        seed_strategies()
        seed_appointments()

# ---------------------------
# Intraday helpers
# ---------------------------

def init_intraday_for_today(force: bool = False):
    t = STATE["todayIndex"]
    intr = STATE.get("intraday") or {}
    if not force and intr.get("dayIndex") == t and intr.get("order"):
        return
    appts = [a for a in STATE["appointments"].values() if a["dayIndex"] == t]
    appts.sort(key=lambda a: a["datetime"])
    STATE["intraday"] = {"dayIndex": t, "order": [a["id"] for a in appts], "next_idx": 0, "last_processed_id": None}

def run_same_day_comms_once():
    """If any strategy has offset 0 for today, fire it ONCE on entering today."""
    t = STATE["todayIndex"]
    if t in STATE["same_day_comms_done"]:
        return
    for appt in STATE["appointments"].values():
        if appt["dayIndex"] != t:
            continue
        for sid in appt["strategy_applied_ids"]:
            strat = STATE["strategies"][sid]
            variant_key = appt["strategy_variant"] or "A"
            variant = strat["ab"][variant_key]
            if 0 in (variant["days_of_action"] or []):
                kind = variant["type"]  # sms|call
                appt["comms_history"].append({"ts": now_iso(), "type": kind, "variant": appt["strategy_variant"], "note": "scheduled"})
                # apply effect
                factor = SMS_FACTOR if kind == "sms" else CALL_FACTOR
                appt["live_adjusted_risk"] = round(clamp01(appt["live_adjusted_risk"] * factor), 3)
                appt["predicted_outcome_live"] = predicted_outcome_from_risk(appt["live_adjusted_risk"])
                log_event(
                    send_day_index=t,
                    appointment_id=appt["id"],
                    patient_name=appt["patient"]["name"],
                    type=kind,
                    variant=appt["strategy_variant"],
                    message=f"{kind.upper()} sent (offset 0)",
                )
    STATE["same_day_comms_done"].add(t)

# ---------------------------
# Strategy & Deployment Logic
# ---------------------------

def in_segment(appt: Dict[str, Any], strat: Dict[str, Any]) -> bool:
    seg = strat.get("segment")
    if not seg:
        return True
    age = appt["patient"]["age"]
    r = appt["static_risk"]
    ok_age = ("age_min" not in seg or age >= seg["age_min"]) and ("age_max" not in seg or age <= seg["age_max"])
    ok_risk = ("risk_min" not in seg or r >= seg["risk_min"]) and ("risk_max" not in seg or r <= seg["risk_max"])
    return ok_age and ok_risk

def pick_variant(split: float) -> str:
    return "A" if RAND.random() < split else "B"

def deploy(dep: Dict[str, Any]) -> Dict[str, Any]:
    dep_id = dep.get("id", f"dep-{uuid.uuid4()}")
    target = int(dep["target_day"])
    chosen = [STATE["strategies"][sid] for sid in dep["strategy_ids"] if sid in STATE["strategies"]]

    appts = [a for a in STATE["appointments"].values() if a["dayIndex"] == target]
    matched = set()

    for strat in [s for s in chosen if not s["is_default"]]:
        for a in appts:
            if in_segment(a, strat):
                a["strategy_variant"] = pick_variant(strat["ab"]["split"])
                if strat["id"] not in a["strategy_applied_ids"]:
                    a["strategy_applied_ids"].append(strat["id"])
                matched.add(a["id"])

    default = next((s for s in chosen if s["is_default"]), None)
    if default:
        for a in appts:
            if a["id"] not in matched:
                a["strategy_variant"] = pick_variant(default["ab"]["split"])
                if default["id"] not in a["strategy_applied_ids"]:
                    a["strategy_applied_ids"].append(default["id"])

    dep_rec = {"id": dep_id, "target_day": target, "strategy_ids": [s["id"] for s in chosen]}
    STATE["deployments"][dep_id] = dep_rec
    return dep_rec

# ---------------------------
# Communications & Risk Pipeline
# ---------------------------

def apply_comms_effect(appt: Dict[str, Any], kind: str):
    factor = SMS_FACTOR if kind == "sms" else CALL_FACTOR
    appt["live_adjusted_risk"] = round(clamp01(appt["live_adjusted_risk"] * factor), 3)
    appt["predicted_outcome_live"] = predicted_outcome_from_risk(appt["live_adjusted_risk"])

def run_scheduled_comms_for_day(t: int):
    """
    Execute comms for which offset == (t - appt.dayIndex).
    Example: appt.dayIndex=2, t=1 => offset=-1  (day before the appointment)
    """
    for appt in STATE["appointments"].values():
        for sid in appt["strategy_applied_ids"]:
            strat = STATE["strategies"][sid]
            variant_key = appt["strategy_variant"] or "A"
            variant = strat["ab"][variant_key]
            for offset in variant["days_of_action"]:
                if offset == (t - appt["dayIndex"]):
                    kind = variant["type"]
                    appt["comms_history"].append({"ts": now_iso(), "type": kind, "variant": appt["strategy_variant"], "note": "scheduled"})
                    apply_comms_effect(appt, kind)
                    log_event(
                        send_day_index=t,
                        appointment_id=appt["id"],
                        patient_name=appt["patient"]["name"],
                        type=kind,
                        variant=appt["strategy_variant"],
                        message=f"{kind.upper()} sent (offset {offset})",
                    )
                    r = RAND.random()
                    if r < REPLY_PROB_YES:
                        log_event(
                            send_day_index=t,
                            appointment_id=appt["id"],
                            patient_name=appt["patient"]["name"],
                            type="reply",
                            variant=appt["strategy_variant"],
                            message="reply received",
                            reply="yes"
                        )
                    elif r < REPLY_PROB_YES + REPLY_PROB_NO:
                        log_event(
                            send_day_index=t,
                            appointment_id=appt["id"],
                            patient_name=appt["patient"]["name"],
                            type="reply",
                            variant=appt["strategy_variant"],
                            message="reply received",
                            reply="no"
                        )

def end_of_day_fill_no_reply_eod(t: int):
    sent_ids = set(l["appointment_id"] for l in STATE["logs"] if l["send_day_index"] == t and l["type"] in ("sms","call"))
    for appt_id in sent_ids:
        any_reply = any(l for l in STATE["logs"] if l["send_day_index"] == t and l["appointment_id"] == appt_id and l["type"] == "reply")
        if not any_reply:
            appt = STATE["appointments"][appt_id]
            log_event(
                send_day_index=t,
                appointment_id=appt_id,
                patient_name=appt["patient"]["name"],
                type="reply",
                variant=appt.get("strategy_variant"),
                message="no reply by end of day",
                reply="no_reply_eod"
            )

def compute_live_adjustments_for_today():
    t = STATE["todayIndex"]
    # Run same-day comms (offset 0) once on entry
    run_same_day_comms_once()
    twelve_hours_ago = datetime.now(timezone.utc) - timedelta(hours=12)
    for appt in STATE["appointments"].values():
        if appt["dayIndex"] != t or appt.get("_live_adjustment_applied"):
            continue

        live = appt["live_adjusted_risk"]
        confirmed = any(
            (log["type"] == "reply" and log["reply"] == "yes" and parse_iso(log["ts"]) >= twelve_hours_ago)
            for log in STATE["logs"] if log["appointment_id"] == appt["id"]
        )
        if confirmed:
            live = round(clamp01(live * CONFIRM_12H_FACTOR), 3)
        else:
            any_reply_recent = any(
                (log["type"] == "reply" and log["reply"] in ("yes","no"))
                for log in STATE["logs"] if log["appointment_id"] == appt["id"]
            )
            if (not any_reply_recent) and live > 0.4:
                live = round(clamp01(live + SILENCE_LIFT), 3)

        appt["live_adjusted_risk"] = live
        appt["predicted_outcome_live"] = predicted_outcome_from_risk(live)
        appt["_live_adjustment_applied"] = True

    # Initialize intraday queue on entry
    init_intraday_for_today()

def settle_outcomes_for_day(day_just_ended: int):
    for appt in STATE["appointments"].values():
        if appt["dayIndex"] == day_just_ended and appt["outcome"] == "unknown":
            p = appt["live_adjusted_risk"]
            appt["outcome"] = "no_show" if RAND.random() < p else "attended"

# ---------------------------
# Summaries
# ---------------------------

def _dist_from_values(values: List[float]) -> List[Dict[str, Any]]:
    out = []
    for lo, hi in BUCKETS:
        count = sum(1 for v in values if lo <= v < hi)
        out.append({"bucket": f"{lo:.1f}-{hi:.1f}", "count": count})
    return out

def summarize_day(day_index: int) -> Dict[str, Any]:
    appts = [a for a in STATE["appointments"].values() if a["dayIndex"] == day_index]
    date_iso = iso_date_for_day(day_index)

    if not appts:
        return {
            "dayIndex": day_index,
            "date_iso": date_iso,
            "avg_static_risk": 0.0,
            "pred_no_show_rate_static": 0.0,
            "avg_live_risk": 0.0,
            "pred_no_show_rate_live": 0.0,
            "dist_live": _dist_from_values([]),
            "strategies_applied": [],
            "outcomes_recorded_today": 0 if day_index == STATE["todayIndex"] else None,
            "accuracy_today":  None if day_index == STATE["todayIndex"] else None,
            "today_pred_vs_obs": None,
            "pred_vs_obs": None,
            "ab_outcomes": [],
            "ab_today": [],
            "todayIndex": STATE["todayIndex"]
        }

    avg_static = sum(a["static_risk"] for a in appts) / len(appts)
    avg_live = sum(a["live_adjusted_risk"] for a in appts) / len(appts)

    # strategies applied
    strat_ids = set(sid for a in appts for sid in a["strategy_applied_ids"])
    strategies_applied = [{"id": sid, "name": STATE["strategies"][sid]["name"]} for sid in strat_ids if sid in STATE["strategies"]]

    # Today-only running metrics
    outcomes_recorded_today = None
    accuracy_today = None
    today_pred_vs_obs = None
    if day_index == STATE["todayIndex"]:
        finished = [a for a in appts if a["outcome"] != "unknown"]
        outcomes_recorded_today = len(finished)
        if finished:
            # accuracy = fraction of correct individual predictions (live) vs observed outcome
            correct = sum(1 for a in finished
                          if (a["outcome"] == "no_show" and a["predicted_outcome_live"] == "dna") or
                             (a["outcome"] == "attended" and a["predicted_outcome_live"] == "attend"))
            accuracy_today = round(correct / len(finished), 3)

            # Pred vs Obs (today) among completed so far
            pred = sum(a["live_adjusted_risk"] for a in finished) / len(finished)
            obs = sum(1 for a in finished if a["outcome"] == "no_show") / len(finished)
            today_pred_vs_obs = {
                "completed": len(finished),
                "pred_no_show_rate": round(pred, 3),
                "obs_no_show_rate": round(obs, 3),
            }

    # pred vs obs for last completed previous day (unchanged)
    pred_vs_obs = None
    if day_index - 1 >= 0:
        prev = [a for a in STATE["appointments"].values() if a["dayIndex"] == day_index - 1]
        if prev and all(a["outcome"] != "unknown" for a in prev):
            pred = sum(a["live_adjusted_risk"] for a in prev) / len(prev)
            obs = sum(1 for a in prev if a["outcome"] == "no_show") / len(prev)
            pred_vs_obs = {
                "dayIndex": day_index - 1,
                "pred_no_show_rate": round(pred, 3),
                "obs_no_show_rate": round(obs, 3)
            }

    # A/B outcomes for last completed day (unchanged)
    ab_outcomes = []
    if pred_vs_obs:
        d = pred_vs_obs["dayIndex"]
        prev = [a for a in STATE["appointments"].values() if a["dayIndex"] == d]
        # By strategy
        by_strat: Dict[str, Dict[str, Any]] = {}
        for a in prev:
            for sid in a["strategy_applied_ids"]:
                if sid not in by_strat:
                    by_strat[sid] = {"name": STATE["strategies"][sid]["name"], "A": [], "B": []}
                bucket = a["strategy_variant"] or "A"
                by_strat[sid][bucket].append(a)
        for sid, grp in by_strat.items():
            def stat(arr: List[Dict[str, Any]]):
                if not arr:
                    return {"count": 0, "pred_no_show_rate": 0.0, "obs_no_show_rate": 0.0}
                pred = sum(a["live_adjusted_risk"] for a in arr) / len(arr)
                obs = sum(1 for a in arr if a["outcome"] == "no_show") / len(arr)
                return {"count": len(arr), "pred_no_show_rate": round(pred, 3), "obs_no_show_rate": round(obs, 3)}
            ab_outcomes.append({
                "dayIndex": d,
                "strategy_id": sid,
                "strategy_name": grp["name"],
                "variant_stats": [
                    {"variant": "A", **stat(grp["A"])},
                    {"variant": "B", **stat(grp["B"])}
                ]
            })

    # A/B (today): observed success and predicted rate per variant (among completed)
    ab_today = []
    if day_index == STATE["todayIndex"]:
        by_strat: Dict[str, Dict[str, Any]] = {}
        for a in appts:
            for sid in a["strategy_applied_ids"]:
                if sid not in by_strat:
                    by_strat[sid] = {"name": STATE["strategies"][sid]["name"], "A": [], "B": []}
                bucket = a["strategy_variant"] or "A"
                by_strat[sid][bucket].append(a)

        for sid, grp in by_strat.items():
            def agg(arr: List[Dict[str, Any]]):
                total = len(arr)
                completed = [x for x in arr if x["outcome"] != "unknown"]
                c = len(completed)
                if c == 0:
                    return {"total": total, "completed": 0, "success_observed": 0.0, "pred_no_show_rate": 0.0}
                pred = sum(x["live_adjusted_risk"] for x in completed) / c
                obs_ns = sum(1 for x in completed if x["outcome"] == "no_show") / c
                success_observed = 1.0 - obs_ns  # attendance rate among completed
                return {
                    "total": total,
                    "completed": c,
                    "success_observed": round(success_observed, 3),
                    "pred_no_show_rate": round(pred, 3),
                }
            A = agg(grp["A"])
            B = agg(grp["B"])
            ab_today.append({
                "strategy_id": sid,
                "strategy_name": grp["name"],
                "A": A,
                "B": B
            })

    return {
        "dayIndex": day_index,
        "date_iso": date_iso,
        "avg_static_risk": round(avg_static, 3),
        "pred_no_show_rate_static": round(avg_static, 3),
        "avg_live_risk": round(avg_live, 3),
        "pred_no_show_rate_live": round(avg_live, 3),
        "dist_live": _dist_from_values([a["live_adjusted_risk"] for a in appts]),
        "strategies_applied": strategies_applied,
        "outcomes_recorded_today": outcomes_recorded_today,
        "accuracy_today": accuracy_today,
        "today_pred_vs_obs": today_pred_vs_obs,
        "pred_vs_obs": pred_vs_obs,
        "ab_outcomes": ab_outcomes,
        "ab_today": ab_today,
        "todayIndex": STATE["todayIndex"]
    }

def list_appointments_summary(day_index: int) -> List[Dict[str, Any]]:
    appts = [a for a in STATE["appointments"].values() if a["dayIndex"] == day_index]
    appts.sort(key=lambda a: a["datetime"])
    out = []
    for a in appts:
        dt = datetime.fromisoformat(a["datetime"])
        hh = str(dt.astimezone(timezone.utc).hour).zfill(2)
        mm = str(dt.astimezone(timezone.utc).minute).zfill(2)
        out.append({
            "id": a["id"],
            "patient": a["patient"],
            "time": f"{hh}:{mm}",
            "live_adjusted_risk": a["live_adjusted_risk"],
            "predicted_outcome_live": a["predicted_outcome_live"],
            "outcome": a["outcome"],  # "unknown" | "attended" | "no_show"
            "strategy_variant": a["strategy_variant"],
        })
    return out

# ---------------------------
# Flask App / Routes (unchanged from your latest except for summarize_day changes)
# ---------------------------

app = Flask(__name__)
CORS(app)

@app.before_request
def _seed_once():
    ensure_seed()

@app.get("/api/health")
def health():
    return jsonify({
        "ok": True,
        "todayIndex": STATE["todayIndex"],
        "startDateISO": STATE["startDateISO"],
        "todayDateISO": iso_date_for_day(STATE["todayIndex"])
    })

@app.get("/api/day/summary")
def day_summary_by_date():
    date = request.args.get("date")
    if not date:
        return jsonify({"error": "date is required (YYYY-MM-DD)"}), 400
    d = day_index_from_date(date)
    if d == STATE["todayIndex"]:
        compute_live_adjustments_for_today()
    return jsonify(summarize_day(d))

@app.get("/api/day/<int:dayIndex>/summary")
def day_summary_by_index(dayIndex: int):
    if dayIndex == STATE["todayIndex"]:
        compute_live_adjustments_for_today()
    return jsonify(summarize_day(dayIndex))

@app.get("/api/appointments")
def appointments_list():
    date = request.args.get("date")
    if date:
        d = day_index_from_date(date)
    else:
        d = int(request.args.get("dayIndex", STATE["todayIndex"]))
    if d == STATE["todayIndex"]:
        compute_live_adjustments_for_today()
    return jsonify(list_appointments_summary(d))

@app.get("/api/appointments/<appt_id>")
def appointment_detail(appt_id: str):
    appt = STATE["appointments"].get(appt_id)
    if not appt:
        return jsonify({"error": "Not found"}), 404
    return jsonify(appt)

@app.get("/api/strategies")
def strategies_list():
    return jsonify(list(STATE["strategies"].values()))

@app.post("/api/strategies")
def strategies_create():
    data = request.get_json(force=True)
    name = data.get("name")
    ab = data.get("ab")
    if not name or not ab or "A" not in ab or "B" not in ab or "split" not in ab:
        return jsonify({"error": "Invalid payload"}), 400
    s_id = data.get("id", f"strat-{uuid.uuid4()}")
    strat = {
        "id": s_id,
        "name": name,
        "is_default": bool(data.get("is_default", False)),
        "segment": data.get("segment"),
        "ab": {
            "split": float(ab["split"]),
            "A": {"type": ab["A"]["type"], "days_of_action": list(ab["A"]["days_of_action"])},
            "B": {"type": ab["B"]["type"], "days_of_action": list(ab["B"]["days_of_action"])},
        }
    }
    STATE["strategies"][s_id] = strat
    return jsonify(strat), 201

@app.patch("/api/strategies/<sid>")
def strategies_patch(sid: str):
    strat = STATE["strategies"].get(sid)
    if not strat:
        return jsonify({"error": "Not found"}), 404
    data = request.get_json(force=True)
    for k in ("name","is_default","segment"):
        if k in data:
            strat[k] = data[k]
    if "ab" in data:
        ab = data["ab"]
        if "split" in ab: strat["ab"]["split"] = float(ab["split"])
        if "A" in ab:
            strat["ab"]["A"]["type"] = ab["A"].get("type", strat["ab"]["A"]["type"])
            if "days_of_action" in ab["A"]:
                strat["ab"]["A"]["days_of_action"] = list(ab["A"]["days_of_action"])
        if "B" in ab:
            strat["ab"]["B"]["type"] = ab["B"].get("type", strat["ab"]["B"]["type"])
            if "days_of_action" in ab["B"]:
                strat["ab"]["B"]["days_of_action"] = list(ab["B"]["days_of_action"])
    return jsonify(strat)

@app.post("/api/deploy")
def deploy_route():
    data = request.get_json(force=True)
    strat_ids = data.get("strategy_ids") or []
    if not strat_ids:
        return jsonify({"error": "strategy_ids required"}), 400
    if "target_date" in data:
        target_day = day_index_from_date(data["target_date"])
    else:
        target_day = int(data.get("target_day"))

    max_window = 0
    for sid in strat_ids:
        s = STATE["strategies"].get(sid)
        if not s: continue
        mx = max([abs(x) for x in (s["ab"]["A"]["days_of_action"] + s["ab"]["B"]["days_of_action"])] or [0])
        if mx > max_window: max_window = mx
    if max_window > (target_day - STATE["todayIndex"]):
        return jsonify({"error": "strategy window exceeds available days",
                        "max_window": max_window,
                        "available": (target_day - STATE["todayIndex"]) }), 400

    dep_rec = deploy({"target_day": target_day, "strategy_ids": strat_ids})
    return jsonify(dep_rec)

@app.post("/api/actions/send_sms")
def action_send_sms():
    data = request.get_json(force=True)
    appt_id = data.get("appointment_id")
    template = data.get("template","")
    appt = STATE["appointments"].get(appt_id)
    if not appt:
        return jsonify({"error": "Not found"}), 404
    appt["comms_history"].append({"ts": now_iso(), "type": "sms", "variant": appt.get("strategy_variant"), "note": "manual_send"})
    log_event(
        send_day_index=STATE["todayIndex"],
        appointment_id=appt_id,
        patient_name=appt["patient"]["name"],
        type="sms",
        variant=appt.get("strategy_variant"),
        message=template,
    )
    r = RAND.random()
    if r < REPLY_PROB_YES:
        log_event(
            send_day_index=STATE["todayIndex"],
            appointment_id=appt_id,
            patient_name=appt["patient"]["name"],
            type="reply",
            variant=appt.get("strategy_variant"),
            message="reply received",
            reply="yes"
        )
    elif r < REPLY_PROB_YES + REPLY_PROB_NO:
        log_event(
            send_day_index=STATE["todayIndex"],
            appointment_id=appt_id,
            patient_name=appt["patient"]["name"],
            type="reply",
            variant=appt.get("strategy_variant"),
            message="reply received",
            reply="no"
        )
    compute_live_adjustments_for_today()
    return jsonify({"ok": True})

@app.post("/api/actions/call_now")
def action_call_now():
    data = request.get_json(force=True)
    appt_id = data.get("appointment_id")
    appt = STATE["appointments"].get(appt_id)
    if not appt:
        return jsonify({"error": "Not found"}), 404
    appt["comms_history"].append({"ts": now_iso(), "type": "call", "variant": appt.get("strategy_variant"), "note": "manual_call"})
    log_event(
        send_day_index=STATE["todayIndex"],
        appointment_id=appt_id,
        patient_name=appt["patient"]["name"],
        type="call",
        variant=appt.get("strategy_variant"),
        message="call logged",
    )
    compute_live_adjustments_for_today()
    return jsonify({"ok": True})

@app.get("/api/logs")
def logs_list():
    date = request.args.get("date")
    if not date:
        return jsonify({"error": "date is required (YYYY-MM-DD)"}), 400
    d = day_index_from_date(date)
    items = [l for l in STATE["logs"] if l["appointment_day_index"] == d]
    items.sort(key=lambda x: x["ts"])
    return jsonify(items)

@app.post("/api/predict")
def predict_route():
    payload = request.get_json(force=True) or {}
    features = payload.get("features", {})
    risk = sagemaker_predict(features)
    return jsonify({"risk": round(risk, 3)})

# Enforce +1 day advance (as per your previous instruction)
@app.post("/api/simulate/advance")
def simulate_advance():
    data = request.get_json(silent=True) or {}
    start = STATE["todayIndex"]
    expected_target = start + 1

    if "toDate" in data:
        provided = day_index_from_date(data["toDate"])
        if provided != expected_target:
            return jsonify({"error": "Only +1 day advance is allowed"}), 400
    if "toDayIndex" in data:
        provided = int(data["toDayIndex"])
        if provided != expected_target:
            return jsonify({"error": "Only +1 day advance is allowed"}), 400

    t = start
    run_scheduled_comms_for_day(t)
    end_of_day_fill_no_reply_eod(t)
    settle_outcomes_for_day(t)
    STATE["todayIndex"] = t + 1
    compute_live_adjustments_for_today()

    return jsonify({
        "ok": True,
        "todayIndex": STATE["todayIndex"],
        "todayDateISO": iso_date_for_day(STATE["todayIndex"])
    })

@app.get("/api/simulate/status")
def simulate_status():
    t = STATE["todayIndex"]
    init_intraday_for_today()
    intr = STATE["intraday"]
    order = intr["order"]
    next_idx = intr["next_idx"]
    total = len(order)
    next_appt = None
    if 0 <= next_idx < total:
        appt = STATE["appointments"][order[next_idx]]
        next_appt = {
            "id": appt["id"],
            "patient_name": appt["patient"]["name"],
            "time": datetime.fromisoformat(appt["datetime"]).time().strftime("%H:%M"),
            "live_adjusted_risk": appt["live_adjusted_risk"],
        }
    return jsonify({
        "todayIndex": t,
        "todayDateISO": iso_date_for_day(t),
        "total": total,
        "next_idx": next_idx,
        "remaining": max(0, total - next_idx),
        "next_appointment": next_appt,
        "last_processed_id": intr.get("last_processed_id"),
    })

@app.post("/api/simulate/tick_today")
def simulate_tick_today():
    t = STATE["todayIndex"]
    init_intraday_for_today()
    intr = STATE["intraday"]
    order = intr["order"]
    idx = intr["next_idx"]
    total = len(order)

    processed = None
    if idx < total:
        appt_id = order[idx]
        appt = STATE["appointments"][appt_id]
        if appt["outcome"] == "unknown":
            p = appt["live_adjusted_risk"]
            appt["outcome"] = "no_show" if RAND.random() < p else "attended"
            log_event(
                send_day_index=t,
                appointment_id=appt_id,
                patient_name=appt["patient"]["name"],
                type="outcome",
                variant=appt.get("strategy_variant"),
                message="finalized",
                extra={"outcome": appt["outcome"]},
            )
        intr["next_idx"] = idx + 1
        intr["last_processed_id"] = appt["id"]
        processed = {"id": appt["id"], "outcome": appt["outcome"], "live_adjusted_risk": appt["live_adjusted_risk"]}

    if intr["next_idx"] >= total:
        end_of_day_fill_no_reply_eod(t)

    return jsonify({
        "processed": processed,
        "status": {
            "todayIndex": t,
            "todayDateISO": iso_date_for_day(t),
            "total": total,
            "next_idx": intr["next_idx"],
            "remaining": max(0, total - intr["next_idx"]),
            "last_processed_id": intr.get("last_processed_id"),
        }
    })

# ---------------------------
# Entrypoint
# ---------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "5001")), debug=True)