"""Space & terrestrial weather simulation, stats, and risk assessment."""
import random
import statistics
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

PARAM_GLOSSARY = {
    "wind_speed": ("Solar wind speed", "km/s", "Speed of charged particles from the Sun. Faster wind increases geomagnetic effects."),
    "wind_density": ("Solar wind density", "particles/cm³", "Particle density; with speed drives dynamic pressure on the magnetosphere."),
    "imf_bz": ("IMF Bz", "nT", "North-south IMF. Negative (southward) couples to Earth's field and fuels storms."),
    "flare_class": ("Solar flare class", "A–X", "Soft X-ray class. X is strongest; each letter ≈ 10× previous."),
    "cme_prob": ("CME probability", "%", "Estimated chance of an Earth-directed coronal mass ejection."),
    "e_part": ("Energetic particles", "pfu", "High-energy proton flux — relevant for radiation exposure."),
    "cosmic": ("Cosmic ray level", "index", "Galactic cosmic rays; often anti-correlated with solar activity."),
    "kp": ("Kp index", "0–9", "Global geomagnetic activity. Kp ≥ 5 = geomagnetic storm."),
    "dst": ("Dst index", "nT", "Ring-current strength. More negative = stronger storm."),
    "radio": ("F10.7 radio flux", "sfu", "Solar radio flux proxy for overall solar activity."),
    "euv": ("EUV flux", "index", "Extreme UV heating of the upper atmosphere."),
    "tec": ("Total Electron Content", "TECU", "Ionospheric electrons; high TEC degrades GPS."),
    "aurora": ("Aurora chance", "%", "Likelihood of visible auroras and reach toward mid-latitudes."),
    "temp": ("Air temperature", "°C", "Surface air temperature (terrestrial)."),
    "pressure": ("Pressure", "hPa", "Surface atmospheric pressure."),
    "humidity": ("Humidity", "%", "Relative humidity."),
}

NUMERIC_KEYS = [
    "wind_speed", "wind_density", "imf_bz", "cme_prob", "e_part", "cosmic",
    "kp", "dst", "radio", "euv", "tec", "aurora", "temp", "pressure", "humidity",
]


def generate_sample_history(n: int = 12) -> List[Dict[str, Any]]:
    """NOAA-style sample storm recovery sequence (educational)."""
    base = datetime(2015, 3, 17, 12, 0)
    samples = [
        {"wind_speed": 680, "wind_density": 12.5, "imf_bz": -12, "flare_class": "M", "cme_prob": 70, "e_part": 1800, "cosmic": 0.85, "kp": 7, "dst": -98, "radio": 145, "euv": 0.12, "tec": 85, "aurora": 92, "temp": 12, "pressure": 1008, "humidity": 58},
        {"wind_speed": 720, "wind_density": 14.2, "imf_bz": -15, "flare_class": "M", "cme_prob": 80, "e_part": 2200, "cosmic": 0.82, "kp": 8, "dst": -120, "radio": 150, "euv": 0.14, "tec": 110, "aurora": 98, "temp": 11, "pressure": 1006, "humidity": 62},
        {"wind_speed": 750, "wind_density": 16.0, "imf_bz": -18, "flare_class": "X", "cme_prob": 95, "e_part": 3500, "cosmic": 0.78, "kp": 8, "dst": -145, "radio": 168, "euv": 0.17, "tec": 130, "aurora": 100, "temp": 10, "pressure": 1004, "humidity": 65},
        {"wind_speed": 730, "wind_density": 15.0, "imf_bz": -14, "flare_class": "X", "cme_prob": 90, "e_part": 2800, "cosmic": 0.80, "kp": 8, "dst": -132, "radio": 160, "euv": 0.15, "tec": 120, "aurora": 99, "temp": 11, "pressure": 1005, "humidity": 63},
        {"wind_speed": 690, "wind_density": 13.0, "imf_bz": -10, "flare_class": "M", "cme_prob": 75, "e_part": 1900, "cosmic": 0.84, "kp": 7, "dst": -105, "radio": 152, "euv": 0.13, "tec": 95, "aurora": 94, "temp": 12, "pressure": 1007, "humidity": 60},
        {"wind_speed": 650, "wind_density": 11.0, "imf_bz": -8, "flare_class": "M", "cme_prob": 60, "e_part": 1400, "cosmic": 0.87, "kp": 6, "dst": -82, "radio": 140, "euv": 0.11, "tec": 80, "aurora": 85, "temp": 13, "pressure": 1009, "humidity": 56},
        {"wind_speed": 620, "wind_density": 9.5, "imf_bz": -5, "flare_class": "C", "cme_prob": 45, "e_part": 900, "cosmic": 0.90, "kp": 5, "dst": -58, "radio": 130, "euv": 0.09, "tec": 65, "aurora": 70, "temp": 14, "pressure": 1010, "humidity": 52},
        {"wind_speed": 580, "wind_density": 8.0, "imf_bz": -2, "flare_class": "C", "cme_prob": 30, "e_part": 500, "cosmic": 0.93, "kp": 4, "dst": -35, "radio": 120, "euv": 0.07, "tec": 50, "aurora": 45, "temp": 15, "pressure": 1012, "humidity": 48},
        {"wind_speed": 540, "wind_density": 6.5, "imf_bz": 1, "flare_class": "B", "cme_prob": 15, "e_part": 200, "cosmic": 0.96, "kp": 3, "dst": -18, "radio": 110, "euv": 0.05, "tec": 35, "aurora": 25, "temp": 16, "pressure": 1013, "humidity": 45},
        {"wind_speed": 510, "wind_density": 5.0, "imf_bz": 2, "flare_class": "B", "cme_prob": 5, "e_part": 80, "cosmic": 0.98, "kp": 2, "dst": -5, "radio": 100, "euv": 0.04, "tec": 25, "aurora": 10, "temp": 17, "pressure": 1015, "humidity": 42},
        {"wind_speed": 480, "wind_density": 4.0, "imf_bz": 3, "flare_class": "A", "cme_prob": 0, "e_part": 30, "cosmic": 1.00, "kp": 1, "dst": 0, "radio": 90, "euv": 0.03, "tec": 18, "aurora": 5, "temp": 18, "pressure": 1016, "humidity": 40},
        {"wind_speed": 450, "wind_density": 3.5, "imf_bz": 4, "flare_class": "A", "cme_prob": 0, "e_part": 20, "cosmic": 1.02, "kp": 1, "dst": 2, "radio": 85, "euv": 0.02, "tec": 15, "aurora": 2, "temp": 19, "pressure": 1017, "humidity": 38},
    ]
    out = []
    for i, vals in enumerate(samples[:n]):
        out.append({"timestamp": base + timedelta(hours=i), **vals})
    return out


def simulate_live() -> Dict[str, Any]:
    wind = random.randint(320, 800)
    density = round(random.uniform(1.5, 30), 1)
    bz = round(random.uniform(-18, 18), 1)
    flare = random.choices(["A", "B", "C", "M", "X"], weights=[15, 40, 30, 10, 1])[0]
    cme = random.randint(0, 100)
    e_part = random.randint(0, 6000)
    cosmic = round(random.uniform(0.7, 1.3), 2)
    kp = random.randint(0, 9)
    dst = random.randint(-250, 30)
    radio = random.randint(60, 260)
    euv = round(random.uniform(0.005, 0.25), 3)
    tec = random.randint(5, 200)
    aurora = min(100, int((wind / 800) * 100 + kp * 6 + (15 if bz < -5 else 0)))
    return {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "wind_speed": wind,
        "wind_density": density,
        "imf_bz": bz,
        "flare_class": flare,
        "cme_prob": cme,
        "e_part": e_part,
        "cosmic": cosmic,
        "kp": kp,
        "dst": dst,
        "radio": radio,
        "euv": euv,
        "tec": tec,
        "aurora": aurora,
        "temp": random.randint(-20, 35),
        "pressure": random.randint(980, 1040),
        "humidity": random.randint(5, 95),
    }


def assess_risk(d: Dict[str, Any]) -> Dict[str, Any]:
    risk = "LOW"
    if d.get("wind_speed", 0) > 600 or d.get("flare_class") in ("M", "X") or d.get("kp", 0) >= 5 or d.get("dst", 0) < -50:
        risk = "MODERATE"
    if d.get("wind_speed", 0) > 700 or d.get("flare_class") == "X" or d.get("kp", 0) >= 7 or d.get("dst", 0) < -100:
        risk = "HIGH"

    sectors = []

    def add(icon, label, level, msg):
        sectors.append({"icon": icon, "label": label, "level": level, "message": msg})

    if risk == "HIGH":
        add("⚡", "Power grids", "HIGH", "GICs may stress transformers. Reduce critical power flows.")
    elif risk == "MODERATE":
        add("⚡", "Power grids", "MODERATE", "Voltage fluctuations possible. Precautionary measures advised.")
    else:
        add("⚡", "Power grids", "LOW", "Grid operations nominal.")

    tec = d.get("tec", 0)
    if tec > 80 or risk == "HIGH":
        add("📡", "GPS", "HIGH", "Position errors may exceed 10 m. Avoid precision navigation.")
    elif tec > 50 or risk == "MODERATE":
        add("📡", "GPS", "MODERATE", "Expect 3–10 m inaccuracies.")
    else:
        add("📡", "GPS", "LOW", "Nominal (<3 m errors).")

    e_part = d.get("e_part", 0)
    if e_part > 1000 or d.get("flare_class") in ("M", "X"):
        add("✈️", "Aviation", "HIGH", "Radiation / HF blackout risk on polar routes.")
    elif e_part > 500:
        add("✈️", "Aviation", "MODERATE", "Monitor SEP alerts; consider lower flight levels.")
    else:
        add("✈️", "Aviation", "LOW", "Background radiation normal.")

    if d.get("kp", 0) >= 7 or e_part > 3000:
        add("🛰️", "Satellites", "HIGH", "Charging / SEU risk elevated. Postpone sensitive ops.")
    elif d.get("kp", 0) >= 5:
        add("🛰️", "Satellites", "MODERATE", "Single-event upsets possible.")
    else:
        add("🛰️", "Satellites", "LOW", "Normal operations.")

    if d.get("flare_class") == "X":
        add("📻", "HF radio", "HIGH", "Widespread blackouts (R3+) possible.")
    elif d.get("flare_class") == "M":
        add("📻", "HF radio", "MODERATE", "Some bands degraded (R1–R2).")
    else:
        add("📻", "HF radio", "LOW", "Propagation normal.")

    aurora = d.get("aurora", 0)
    if aurora > 70:
        add("✨", "Aurora", "HIGH", f"Excellent chance ({aurora}%) — mid-latitudes possible.")
    elif aurora > 30:
        add("✨", "Aurora", "MODERATE", f"Fair chance ({aurora}%) near polar circles.")
    else:
        add("✨", "Aurora", "LOW", f"Low ({aurora}%).")

    return {"overall": risk, "sectors": sectors, "generated_at": datetime.now().isoformat(timespec="seconds")}


def summary(entries: List[dict], key: str, period: Optional[str] = None) -> dict:
    subset = entries
    if period and entries:
        now = datetime.now()
        delta = {"week": timedelta(days=7), "month": timedelta(days=30), "year": timedelta(days=365)}.get(period)
        if delta:
            subset = []
            for e in entries:
                ts = e.get("timestamp")
                if isinstance(ts, str):
                    try:
                        ts = datetime.fromisoformat(ts)
                    except Exception:
                        continue
                if isinstance(ts, datetime) and ts >= now - delta:
                    subset.append(e)
    vals = [e[key] for e in subset if isinstance(e.get(key), (int, float))]
    if not vals:
        return {"count": 0, "key": key}
    return {
        "key": key,
        "count": len(vals),
        "min": min(vals),
        "max": max(vals),
        "mean": statistics.mean(vals),
        "stdev": statistics.pstdev(vals) if len(vals) > 1 else 0.0,
        "range": max(vals) - min(vals),
    }


def time_series(entries: List[dict], key: str) -> dict:
    ts, vals = [], []
    for e in entries:
        v = e.get(key)
        if isinstance(v, (int, float)):
            t = e.get("timestamp")
            if isinstance(t, datetime):
                t = t.isoformat()
            ts.append(t)
            vals.append(v)
    return {"timestamps": ts, "values": vals, "key": key}


def predict_simple(d: Dict[str, Any], mode: str = "learner") -> Dict[str, Any]:
    """Shared prediction lab: same numbers, learner vs technical wording."""
    risk = assess_risk(d)
    kp = d.get("kp", 0)
    dst = d.get("dst", 0)
    bz = d.get("imf_bz", 0)
    wind = d.get("wind_speed", 400)

    if mode == "technical":
        narrative = (
            f"Heuristic forecast from current drivers: Vsw={wind} km/s, Bz={bz} nT, "
            f"Kp={kp}, Dst={dst} nT, flare={d.get('flare_class')}. "
            f"Overall risk classified **{risk['overall']}**. "
            "This is a rule-based educational estimate, not an operational NOAA product."
        )
    else:
        narrative = (
            f"Right now the storm risk looks **{risk['overall']}**. "
            f"Solar wind is about {wind} km/s, and Earth's magnetic activity score (Kp) is {kp}/9. "
            f"If Kp stays high and the Sun's magnetic field points south (Bz negative), auroras and "
            "GPS glitches become more likely. This is a teaching estimate — always check official alerts for decisions."
        )
    return {
        "mode": mode,
        "risk": risk,
        "narrative": narrative,
        "inputs": {k: d.get(k) for k in NUMERIC_KEYS + ["flare_class"]},
        "glossary_hint": "See PARAM_GLOSSARY for plain-language parameter definitions.",
    }
