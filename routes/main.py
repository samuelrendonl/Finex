from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    return render_template("page.html")

@main_bp.route("/login")
def login():
    return render_template("index.html")

@main_bp.route("/dashboard")
def dashboard():
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    return redirect(url_for("persona.dashboard"))

@main_bp.route("/empresa")
def empresa_alias():
    return redirect(url_for("finex.index"))
