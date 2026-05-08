from flask import Blueprint, render_template, session, redirect, url_for

main_bp = Blueprint("main", __name__)

@main_bp.route("/")
def index():
    if "usuario_id" in session:
        return redirect(url_for("main.dashboard"))
    return render_template("page.html")

@main_bp.route('/login')
def login():
    return render_template('index.html')

@main_bp.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")