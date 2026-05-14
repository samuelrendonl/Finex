"""Rutas de autenticacion: login normal, registro, OAuth y cierre de sesion."""
import os
from flask import Blueprint, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from oauth_config import oauth
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)


def _empresa_id_for_user(cursor, usuario_id):
    cursor.execute("SELECT id FROM empresas WHERE usuario_id=%s ORDER BY id LIMIT 1", (usuario_id,))
    row = cursor.fetchone()
    return row["id"] if row else None


def _company_name_for_user(cursor, usuario_id):
    cursor.execute("SELECT id, nombre_empresa, razon_social, nit FROM empresas WHERE usuario_id=%s ORDER BY id LIMIT 1", (usuario_id,))
    row = cursor.fetchone()
    if not row:
        return None, None, None
    return row["id"], (row.get("nombre_empresa") or row.get("razon_social") or "Empresa"), row.get("nit")


def _set_session(usuario_id, email, tipo_cuenta, nombre, empresa_id=None):
    session.permanent = True
    session["usuario_id"] = usuario_id
    session["usuario_email"] = email
    session["usuario_tipo"] = tipo_cuenta
    session["usuario_nombre"] = nombre or email
    if empresa_id:
        session["empresa_id"] = empresa_id
    else:
        session.pop("empresa_id", None)


def _redirect_for(tipo_cuenta):
    return url_for("persona.dashboard") if tipo_cuenta == "persona" else url_for("finex.index")


def _login_oauth_user(provider, email, nombre, provider_id=None, foto=None):
    """Crea o actualiza una cuenta OAuth y deja la sesion iniciada."""
    id_column = "google_id" if provider == "google" else "microsoft_id"
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, tipo_cuenta FROM usuarios WHERE email=%s LIMIT 1", (email,))
            usuario = cursor.fetchone()
            if usuario:
                usuario_id = usuario["id"]
                tipo_cuenta = usuario["tipo_cuenta"]
                cursor.execute(f"UPDATE usuarios SET {id_column}=%s, foto=COALESCE(%s, foto) WHERE id=%s", (provider_id, foto, usuario_id))
            else:
                cursor.execute(f"""
                    INSERT INTO usuarios (email, contraseña, {id_column}, foto, tipo_cuenta, activo, fecha_creacion)
                    VALUES (%s,NULL,%s,%s,'persona',1,NOW())
                """, (email, provider_id, foto))
                usuario_id = cursor.lastrowid
                tipo_cuenta = "persona"
                parts = (nombre or email).split(" ", 1)
                cursor.execute("INSERT INTO personas (usuario_id, nombre, apellido, documento_identidad, telefono) VALUES (%s,%s,%s,%s,%s)", (usuario_id, parts[0], parts[1] if len(parts) > 1 else "", "OAuth", "0000000000"))
            empresa_id = _empresa_id_for_user(cursor, usuario_id) if tipo_cuenta == "empresa" else None
            if tipo_cuenta == "empresa":
                empresa_id, nombre_empresa, _ = _company_name_for_user(cursor, usuario_id)
                nombre = nombre_empresa or nombre
            connection.commit()
        _set_session(usuario_id, email, tipo_cuenta, nombre, empresa_id)
        return redirect(_redirect_for(tipo_cuenta))
    finally:
        connection.close()


def _dev_oauth_fallback(provider):
    """Evita errores en local cuando no hay credenciales OAuth configuradas."""
    email = f"{provider}.demo@finex.local"
    nombre = f"{provider.title()} Demo"
    flash(f"Inicio con {provider.title()} en modo local. Para OAuth real configura las credenciales en .env.", "success")
    return _login_oauth_user(provider, email, nombre, f"dev-{provider}")


@auth_bp.route("/login/google")
def login_google():
    # Redirige al selector real de cuentas de Google.
    google = oauth.create_client("google")
    if not google or not os.getenv("GOOGLE_CLIENT_ID") or not os.getenv("GOOGLE_CLIENT_SECRET"):
        flash("Para iniciar con Google debes configurar GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET en el archivo .env.", "error")
        return redirect(url_for("main.login"))
    return google.authorize_redirect(url_for("auth.callback_google", _external=True), prompt="select_account")


@auth_bp.route("/login/google/callback")
def callback_google():
    google = oauth.create_client("google")
    try:
        google.authorize_access_token()
        user = google.get("https://openidconnect.googleapis.com/v1/userinfo").json()
        return _login_oauth_user("google", user.get("email"), user.get("name") or user.get("email"), user.get("sub"), user.get("picture"))
    except Exception as e:
        flash(f"No se pudo iniciar con Google: {e}", "error")
        return redirect(url_for("main.login"))


@auth_bp.route("/login/microsoft")
def login_microsoft():
    # Redirige al selector real de cuentas de Microsoft.
    microsoft = oauth.create_client("microsoft")
    if not microsoft or not os.getenv("MICROSOFT_CLIENT_ID") or not os.getenv("MICROSOFT_CLIENT_SECRET"):
        flash("Para iniciar con Microsoft debes configurar MICROSOFT_CLIENT_ID y MICROSOFT_CLIENT_SECRET en el archivo .env.", "error")
        return redirect(url_for("main.login"))
    return microsoft.authorize_redirect(url_for("auth.callback_microsoft", _external=True), prompt="select_account")


@auth_bp.route("/login/microsoft/callback")
def callback_microsoft():
    microsoft = oauth.create_client("microsoft")
    try:
        token = microsoft.authorize_access_token()
        user = token.get("userinfo") or microsoft.get("https://graph.microsoft.com/oidc/userinfo").json()
        email = user.get("email") or user.get("preferred_username")
        return _login_oauth_user("microsoft", email, user.get("name") or email, user.get("sub") or user.get("oid"))
    except Exception as e:
        flash(f"No se pudo iniciar con Microsoft: {e}", "error")
        return redirect(url_for("main.login"))


@auth_bp.route("/api/registro", methods=["POST"])
def registro():
    connection = None
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        contraseña = data.get("contraseña") or ""
        tipo_cuenta = data.get("tipo_cuenta") or "empresa"
        if not email or not contraseña:
            return jsonify({"error": "Email y contraseña son obligatorios"}), 400

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
            if cursor.fetchone():
                return jsonify({"error": "Email ya existe"}), 400
            cursor.execute("""
                INSERT INTO usuarios (email, contraseña, tipo_cuenta, activo, fecha_creacion)
                VALUES (%s,%s,%s,1,NOW())
            """, (email, generate_password_hash(contraseña), tipo_cuenta))
            usuario_id = cursor.lastrowid
            empresa_id = None

            if tipo_cuenta == "persona":
                nombre = (data.get("nombre") or "").strip()
                apellido = (data.get("apellido") or "").strip()
                documento = (data.get("documento_identidad") or "").strip()
                telefono = (data.get("telefono") or "").strip()
                cursor.execute("""
                    INSERT INTO personas (usuario_id, nombre, apellido, documento_identidad, telefono)
                    VALUES (%s,%s,%s,%s,%s)
                """, (usuario_id, nombre, apellido, documento, telefono))
                nombre_sesion = f"{nombre} {apellido}".strip() or email
            else:
                nombre_contacto = (data.get("nombre") or "").strip()
                nombre_empresa = (data.get("razon_social") or "FINEX").strip()
                nit = (data.get("nit") or "Sin configurar").strip()
                telefono = (data.get("telefono") or "").strip()
                ciudad = (data.get("ciudad") or "").strip()
                direccion = (data.get("direccion") or "").strip()
                cursor.execute("""
                    INSERT INTO empresas (usuario_id, nombre_contacto, razon_social, nombre_empresa, nit, telefono, ciudad, direccion, email_contacto)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (usuario_id, nombre_contacto, nombre_empresa, nombre_empresa, nit, telefono, ciudad, direccion, email))
                empresa_id = cursor.lastrowid
                nombre_sesion = nombre_empresa
            connection.commit()
        _set_session(usuario_id, email, tipo_cuenta, nombre_sesion, empresa_id)
        return jsonify({"success": True, "message": "Registro exitoso", "redirect": _redirect_for(tipo_cuenta)})
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route("/api/login", methods=["POST"])
def login():
    connection = None
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        contraseña = data.get("contraseña") or ""
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, email, contraseña, tipo_cuenta, activo FROM usuarios WHERE email=%s LIMIT 1", (email,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "Usuario no existe"}), 401
            if not user.get("contraseña"):
                return jsonify({"error": "Esta cuenta usa Google o Microsoft. Inicia sesión con ese proveedor."}), 401
            if not check_password_hash(user["contraseña"], contraseña):
                return jsonify({"error": "Contraseña incorrecta"}), 401
            usuario_id = user["id"]
            tipo_cuenta = user["tipo_cuenta"]
            empresa_id = None
            if tipo_cuenta == "persona":
                cursor.execute("SELECT nombre, apellido FROM personas WHERE usuario_id=%s LIMIT 1", (usuario_id,))
                perfil = cursor.fetchone()
                nombre_sesion = (f"{perfil['nombre']} {perfil['apellido']}".strip() if perfil else email)
            else:
                empresa_id, nombre_sesion, _ = _company_name_for_user(cursor, usuario_id)
                nombre_sesion = nombre_sesion or email
        _set_session(usuario_id, email, tipo_cuenta, nombre_sesion, empresa_id)
        return jsonify({"success": True, "message": "Inicio de sesión exitoso", "redirect": _redirect_for(tipo_cuenta)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route("/api/logout", methods=["POST", "GET"])
@auth_bp.route("/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    if request.method == "POST" and request.path == "/api/logout":
        return jsonify({"success": True, "redirect": url_for("main.login")})
    return redirect(url_for("main.login"))
