import os
from datetime import datetime
from flask import Blueprint, jsonify, request, session, current_app, send_file
from flask_login import login_required, current_user
from app.database import db
from app.models import WeatherRecord, ChatLog
from app.services import weather_engine as we
from app.services.ai_client import MultiAIClient, AI_MODELS
from app.services.crypto_store import encrypt_data, decrypt_data, entries_to_csv_bytes, csv_bytes_to_entries
import io

api_bp = Blueprint("api", __name__)


def _records_as_dicts(limit=500):
    rows = WeatherRecord.query.order_by(WeatherRecord.timestamp.desc()).limit(limit).all()
    return [r.to_dict() for r in reversed(rows)]


@api_bp.route("/health")
def health():
    return jsonify({"status": "ok", "app": "Auther Guard AI", "demo_mode": current_app.config.get("DEMO_MODE", True)})


@api_bp.route("/live", methods=["GET", "POST"])
@login_required
def live():
    """Generate a new simulated observation and persist it."""
    data = we.simulate_live()
    rec = WeatherRecord(
        timestamp=datetime.fromisoformat(data["timestamp"]),
        wind_speed=data["wind_speed"],
        wind_density=data["wind_density"],
        imf_bz=data["imf_bz"],
        flare_class=data["flare_class"],
        cme_prob=data["cme_prob"],
        e_part=data["e_part"],
        cosmic=data["cosmic"],
        kp=data["kp"],
        dst=data["dst"],
        radio=data["radio"],
        euv=data["euv"],
        tec=data["tec"],
        aurora=data["aurora"],
        temp=data["temp"],
        pressure=data["pressure"],
        humidity=data["humidity"],
        source="simulation",
    )
    db.session.add(rec)
    db.session.commit()
    risk = we.assess_risk(data)
    return jsonify({"observation": data, "risk": risk, "id": rec.id})


@api_bp.route("/latest")
@login_required
def latest():
    rec = WeatherRecord.query.order_by(WeatherRecord.timestamp.desc()).first()
    if not rec:
        # seed sample if empty
        for e in we.generate_sample_history():
            r = WeatherRecord(
                timestamp=e["timestamp"],
                wind_speed=e["wind_speed"],
                wind_density=e["wind_density"],
                imf_bz=e["imf_bz"],
                flare_class=e["flare_class"],
                cme_prob=e["cme_prob"],
                e_part=e["e_part"],
                cosmic=e["cosmic"],
                kp=e["kp"],
                dst=e["dst"],
                radio=e["radio"],
                euv=e["euv"],
                tec=e["tec"],
                aurora=e["aurora"],
                temp=e["temp"],
                pressure=e["pressure"],
                humidity=e["humidity"],
                source="sample_noaa_style",
            )
            db.session.add(r)
        db.session.commit()
        rec = WeatherRecord.query.order_by(WeatherRecord.timestamp.desc()).first()
    d = rec.to_dict()
    return jsonify({"observation": d, "risk": we.assess_risk(d)})


@api_bp.route("/history")
@login_required
def history():
    limit = min(int(request.args.get("limit", 100)), 1000)
    return jsonify({"count": WeatherRecord.query.count(), "records": _records_as_dicts(limit)})


@api_bp.route("/series/<key>")
@login_required
def series(key):
    records = _records_as_dicts(500)
    return jsonify(we.time_series(records, key))


@api_bp.route("/summary/<key>")
@login_required
def summary(key):
    period = request.args.get("period")
    records = _records_as_dicts(2000)
    # convert timestamps for filtering
    for r in records:
        if isinstance(r.get("timestamp"), str):
            try:
                r["timestamp"] = datetime.fromisoformat(r["timestamp"])
            except Exception:
                pass
    return jsonify(we.summary(records, key, period))


@api_bp.route("/predict", methods=["POST"])
@login_required
def predict():
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "learner")
    # use provided params or latest
    obs = data.get("observation")
    if not obs:
        rec = WeatherRecord.query.order_by(WeatherRecord.timestamp.desc()).first()
        obs = rec.to_dict() if rec else we.simulate_live()
    return jsonify(we.predict_simple(obs, mode=mode))


@api_bp.route("/glossary")
def glossary():
    return jsonify(we.PARAM_GLOSSARY)


@api_bp.route("/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json(silent=True) or {}
    question = (data.get("question") or "").strip()
    model = data.get("model") or "Local"
    if not question:
        return jsonify({"error": True, "message": "Question required"}), 400
    # optional session keys override
    keys = session.get("ai_keys", {})
    client = MultiAIClient(keys)
    answer = client.ask(model, question)
    try:
        log = ChatLog(user_id=current_user.id, model=model, question=question, answer=answer)
        db.session.add(log)
        db.session.commit()
    except Exception:
        db.session.rollback()
    return jsonify({"model": model, "question": question, "answer": answer, "meta": AI_MODELS.get(model, {})})


@api_bp.route("/settings/keys", methods=["POST"])
@login_required
def set_keys():
    data = request.get_json(silent=True) or {}
    keys = session.get("ai_keys", {})
    for m in AI_MODELS:
        if m in data and data[m] is not None:
            keys[m] = str(data[m]).strip()
    session["ai_keys"] = keys
    return jsonify({"ok": True, "configured": [k for k, v in keys.items() if v]})


@api_bp.route("/export/ag", methods=["POST"])
@login_required
def export_ag():
    password = session.get("ag_password") or request.json.get("password") if request.is_json else None
    if not password:
        return jsonify({"error": True, "message": "Session password missing — re-login."}), 400
    records = _records_as_dicts(5000)
    if not records:
        return jsonify({"error": True, "message": "No data"}), 400
    # normalize timestamps
    for r in records:
        if r.get("timestamp") and not isinstance(r["timestamp"], datetime):
            try:
                r["timestamp"] = datetime.fromisoformat(r["timestamp"])
            except Exception:
                pass
    raw = entries_to_csv_bytes(records)
    encrypted = encrypt_data(raw, password)
    path = current_app.config["UPLOAD_FOLDER"] / f"snapshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.AG"
    path.write_bytes(encrypted)
    return send_file(path, as_attachment=True, download_name=path.name)


@api_bp.route("/import/ag", methods=["POST"])
@login_required
def import_ag():
    if "file" not in request.files:
        return jsonify({"error": True, "message": "No file"}), 400
    password = request.form.get("password") or session.get("ag_password")
    if not password:
        return jsonify({"error": True, "message": "Password required"}), 400
    f = request.files["file"]
    try:
        encrypted = f.read()
        plain = decrypt_data(encrypted, password)
        entries = csv_bytes_to_entries(plain)
        for e in entries:
            ts = e.get("timestamp") or datetime.now()
            if isinstance(ts, str):
                ts = datetime.fromisoformat(ts)
            rec = WeatherRecord(
                timestamp=ts,
                wind_speed=e.get("wind_speed"),
                wind_density=e.get("wind_density"),
                imf_bz=e.get("imf_bz"),
                flare_class=str(e.get("flare_class", "")),
                cme_prob=e.get("cme_prob"),
                e_part=e.get("e_part"),
                cosmic=e.get("cosmic"),
                kp=e.get("kp"),
                dst=e.get("dst"),
                radio=e.get("radio"),
                euv=e.get("euv"),
                tec=e.get("tec"),
                aurora=e.get("aurora"),
                temp=e.get("temp"),
                pressure=e.get("pressure"),
                humidity=e.get("humidity"),
                source="imported_ag",
            )
            db.session.add(rec)
        db.session.commit()
        return jsonify({"ok": True, "imported": len(entries)})
    except Exception as ex:
        db.session.rollback()
        return jsonify({"error": True, "message": str(ex)}), 400


@api_bp.route("/ml/train", methods=["POST"])
@login_required
def ml_train():
    """Educational: train simple risk classifier from stored records."""
    try:
        from sklearn.ensemble import RandomForestClassifier
        from sklearn.model_selection import train_test_split
        from sklearn.metrics import accuracy_score
        import joblib
        import numpy as np
    except ImportError:
        return jsonify({"error": True, "message": "scikit-learn not installed"}), 500

    records = _records_as_dicts(2000)
    X, y = [], []
    for r in records:
        if r.get("kp") is None:
            continue
        X.append([
            r.get("wind_speed") or 0,
            r.get("wind_density") or 0,
            r.get("imf_bz") or 0,
            r.get("e_part") or 0,
            r.get("dst") or 0,
            r.get("tec") or 0,
        ])
        # label: storm if kp >= 5
        y.append(1 if (r.get("kp") or 0) >= 5 else 0)
    if len(X) < 20:
        # synthetic boost
        for _ in range(80):
            d = we.simulate_live()
            X.append([d["wind_speed"], d["wind_density"], d["imf_bz"], d["e_part"], d["dst"], d["tec"]])
            y.append(1 if d["kp"] >= 5 else 0)
    X = np.array(X)
    y = np.array(y)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, random_state=42)
    clf = RandomForestClassifier(n_estimators=60, random_state=42)
    clf.fit(Xtr, ytr)
    pred = clf.predict(Xte)
    acc = float(accuracy_score(yte, pred))
    model_dir = current_app.config["DATA_DIR"] / "models"
    model_dir.mkdir(parents=True, exist_ok=True)
    path = model_dir / "storm_rf.joblib"
    joblib.dump(clf, path)
    return jsonify({
        "ok": True,
        "accuracy": acc,
        "n_train": len(Xtr),
        "n_test": len(Xte),
        "features": ["wind_speed", "wind_density", "imf_bz", "e_part", "dst", "tec"],
        "target": "kp>=5 storm flag",
        "path": str(path),
        "disclaimer": "Educational classifier on simulated/sample data — not operational.",
    })
