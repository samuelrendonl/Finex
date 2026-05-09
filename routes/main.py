from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint("main", __name__)


# ===== PÁGINA PRINCIPAL =====
@main_bp.route("/")
def index():
    return render_template("page.html")


@main_bp.route("/login")
def login():
    return render_template("index.html")

# ===== DASHBOARD PERSONA =====
@main_bp.route("/dashboard")
def dashboard():

    if "usuario_id" not in session:
        return redirect(url_for("main.index"))

    return render_template("dashboard.html")


# ===== DASHBOARD EMPRESA =====
@main_bp.route("/dashboard-empresa")
def dashboard_empresa():

    if "usuario_id" not in session:
        return redirect(url_for("main.index"))

    return render_template("dashboardE.html")