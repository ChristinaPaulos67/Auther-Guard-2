import re
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.database import db
from app.models import User

auth_bp = Blueprint("auth", __name__)


def is_strong_password(password: str) -> bool:
    return (
        len(password) > 13
        and re.search(r"[A-Z]", password)
        and re.search(r"[a-z]", password)
        and re.search(r"\d", password)
        and re.search(r"[!@#$%^&*(),.?\":{}|<>]", password)
    )


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.dashboard"))
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username:
            flash("Username required.", "danger")
            return render_template("auth/login.html")
        if not is_strong_password(password):
            flash(
                "Password must be >13 chars with upper, lower, digit, and special character.",
                "warning",
            )
            return render_template("auth/login.html")
        user = User.query.filter_by(username=username).first()
        if not user:
            # First login creates account (same UX as original desktop app)
            user = User(username=username, role="observer")
            user.set_password(password)
            db.session.add(user)
            db.session.commit()
            flash("Account created. Welcome to Auther Guard AI.", "success")
        elif not user.check_password(password):
            flash("Invalid password.", "danger")
            return render_template("auth/login.html")
        login_user(user, remember=True)
        session["ag_password"] = password  # used only for .AG encrypt/decrypt this session
        return redirect(url_for("main.dashboard"))
    return render_template("auth/login.html")


@auth_bp.route("/logout")
@login_required
def logout():
    session.pop("ag_password", None)
    logout_user()
    return redirect(url_for("auth.login"))
