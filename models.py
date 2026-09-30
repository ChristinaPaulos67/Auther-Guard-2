from datetime import datetime, timezone
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from app.database import db


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    role = db.Column(db.String(20), default="observer")
    preferred_ai = db.Column(db.String(20), default="Local")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    def set_password(self, password: str):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        return check_password_hash(self.password_hash, password)


class WeatherRecord(db.Model):
    __tablename__ = "weather_records"
    id = db.Column(db.Integer, primary_key=True)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc), index=True)
    wind_speed = db.Column(db.Float)
    wind_density = db.Column(db.Float)
    imf_bz = db.Column(db.Float)
    flare_class = db.Column(db.String(4))
    cme_prob = db.Column(db.Float)
    e_part = db.Column(db.Float)
    cosmic = db.Column(db.Float)
    kp = db.Column(db.Integer)
    dst = db.Column(db.Float)
    radio = db.Column(db.Float)
    euv = db.Column(db.Float)
    tec = db.Column(db.Float)
    aurora = db.Column(db.Float)
    temp = db.Column(db.Float)
    pressure = db.Column(db.Float)
    humidity = db.Column(db.Float)
    source = db.Column(db.String(40), default="simulation")

    def to_dict(self):
        return {
            "id": self.id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "wind_speed": self.wind_speed,
            "wind_density": self.wind_density,
            "imf_bz": self.imf_bz,
            "flare_class": self.flare_class,
            "cme_prob": self.cme_prob,
            "e_part": self.e_part,
            "cosmic": self.cosmic,
            "kp": self.kp,
            "dst": self.dst,
            "radio": self.radio,
            "euv": self.euv,
            "tec": self.tec,
            "aurora": self.aurora,
            "temp": self.temp,
            "pressure": self.pressure,
            "humidity": self.humidity,
            "source": self.source,
        }


class ChatLog(db.Model):
    __tablename__ = "chat_logs"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    model = db.Column(db.String(20))
    question = db.Column(db.Text)
    answer = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))
