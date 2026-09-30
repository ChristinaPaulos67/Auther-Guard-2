from flask import Blueprint, render_template, current_app
from flask_login import login_required, current_user
from app.services.ai_client import AI_MODELS
from app.services.weather_engine import PARAM_GLOSSARY

main_bp = Blueprint("main", __name__)


@main_bp.route("/")
def index():
    if current_user.is_authenticated:
        return render_template("dashboard.html", user=current_user)
    return render_template("landing.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html", user=current_user, glossary=PARAM_GLOSSARY)


@main_bp.route("/analyzer")
@login_required
def analyzer():
    return render_template("analyzer.html", glossary=PARAM_GLOSSARY)


@main_bp.route("/prediction")
@login_required
def prediction():
    return render_template("prediction.html", glossary=PARAM_GLOSSARY)


@main_bp.route("/teach")
@login_required
def teach():
    return render_template("teach.html", models=AI_MODELS)


@main_bp.route("/chat")
@login_required
def chat():
    return render_template("chat.html", models=AI_MODELS)


@main_bp.route("/settings")
@login_required
def settings():
    return render_template("settings.html", models=AI_MODELS)


@main_bp.route("/ml")
@login_required
def ml_lab():
    return render_template("ml.html")
