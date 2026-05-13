from flask import Blueprint, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from oauth_config import oauth
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)

def _empresa_id_for_user(cursor, usuario_id):
    cursor.execute("SELECT id FROM empresas WHERE usuario_id=%s ORDER BY id LIMIT 1", (usuario_id,))
    row = cursor.fetchone()
    return row["id"] if row else None

def _set_session(usuario_id, email, tipo_cuenta, nombre, empresa_id=None):
    session.permanent = True
    session["usuario_id"] = usuario_id
    session["usuario_email"] = email
    session["usuario_tipo"] = tipo_cuenta
    session["usuario_nombre"] = nombre or email
    if empresa_id:
        session["empresa_id"] = empresa_id
    elif "empresa_id" in session:
        session.pop("empresa_id", None)

def _redirect_for(tipo_cuenta):
    if tipo_cuenta == "persona":
        return url_for("persona.dashboard")
    return url_for("finex.index")

def _oauth_unavailable(provider):
    flash(f"Inicio con {provider} no configurado. Revisa las variables de entorno en el archivo .env.", "error")
    return redirect(url_for("main.login"))

@auth_bp.route("/login/google")
def login_google():
    google = oauth.create_client("google")
    if not google:
        return _oauth_unavailable("Google")
    return google.authorize_redirect(url_for("auth.callback_google", _external=True))

@auth_bp.route("/login/google/callback")
def callback_google():
    google = oauth.create_client("google")
    if not google:
        return _oauth_unavailable("Google")
    try:
        google.authorize_access_token()
        user = google.get("https://openidconnect.googleapis.com/v1/userinfo").json()
        email = user.get("email")
        if not email:
            flash("Google no devolvio un correo valido para iniciar sesion.", "error")
            return redirect(url_for("main.login"))
        nombre = user.get("name") or email
        google_id = user.get("sub")
        foto = user.get("picture")
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, tipo_cuenta FROM usuarios WHERE email=%s LIMIT 1", (email,))
            usuario = cursor.fetchone()
            if usuario:
                usuario_id = usuario["id"]
                tipo_cuenta = usuario["tipo_cuenta"]
                cursor.execute("UPDATE usuarios SET google_id=%s, foto=COALESCE(%s, foto) WHERE id=%s", (google_id, foto, usuario_id))
            else:
                cursor.execute("""
                    INSERT INTO usuarios (email, contraseña, google_id, foto, tipo_cuenta, activo, fecha_creacion)
                    VALUES (%s,NULL,%s,%s,'persona',1,NOW())
                """, (email, google_id, foto))
                usuario_id = cursor.lastrowid
                tipo_cuenta = "persona"
                cursor.execute("INSERT INTO personas (usuario_id, nombre, apellido) VALUES (%s,%s,%s)", (usuario_id, nombre, ""))
            empresa_id = _empresa_id_for_user(cursor, usuario_id) if tipo_cuenta == "empresa" else None
            connection.commit()
        connection.close()
        _set_session(usuario_id, email, tipo_cuenta, nombre, empresa_id)
        return redirect(_redirect_for(tipo_cuenta))
    except Exception as e:
        flash(f"No se pudo completar el inicio con Google: {e}", "error")
        return redirect(url_for("main.login"))

@auth_bp.route("/login/microsoft")
def login_microsoft():
    microsoft = oauth.create_client("microsoft")
    if not microsoft:
        return _oauth_unavailable("Microsoft")
    return microsoft.authorize_redirect(url_for("auth.callback_microsoft", _external=True))

@auth_bp.route("/login/microsoft/callback")
def callback_microsoft():
    microsoft = oauth.create_client("microsoft")
    if not microsoft:
        return _oauth_unavailable("Microsoft")
    try:
        token = microsoft.authorize_access_token()
        user = token.get("userinfo") or microsoft.get("https://graph.microsoft.com/oidc/userinfo").json()
        email = user.get("email") or user.get("preferred_username")
        if not email:
            flash("Microsoft no devolvio un correo valido para iniciar sesion.", "error")
            return redirect(url_for("main.login"))
        nombre = user.get("name") or email
        microsoft_id = user.get("sub") or user.get("oid")
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, tipo_cuenta FROM usuarios WHERE email=%s LIMIT 1", (email,))
            usuario = cursor.fetchone()
            if usuario:
                usuario_id = usuario["id"]
                tipo_cuenta = usuario["tipo_cuenta"]
                cursor.execute("UPDATE usuarios SET microsoft_id=%s WHERE id=%s", (microsoft_id, usuario_id))
            else:
                cursor.execute("""
                    INSERT INTO usuarios (email, contraseña, microsoft_id, tipo_cuenta, activo, fecha_creacion)
                    VALUES (%s,NULL,%s,'persona',1,NOW())
                """, (email, microsoft_id))
                usuario_id = cursor.lastrowid
                tipo_cuenta = "persona"
                cursor.execute("INSERT INTO personas (usuario_id, nombre, apellido) VALUES (%s,%s,%s)", (usuario_id, nombre, ""))
            empresa_id = _empresa_id_for_user(cursor, usuario_id) if tipo_cuenta == "empresa" else None
            connection.commit()
        connection.close()
        _set_session(usuario_id, email, tipo_cuenta, nombre, empresa_id)
        return redirect(_redirect_for(tipo_cuenta))
    except Exception as e:
        flash(f"No se pudo completar el inicio con Microsoft: {e}", "error")
        return redirect(url_for("main.login"))

@auth_bp.route("/api/registro", methods=["POST"])
def registro():
    connection = None
    try:
        data = request.get_json() or {}
        email = data.get("email")
        contraseña = data.get("contraseña")
        tipo_cuenta = data.get("tipo_cuenta") or "empresa"
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
            if cursor.fetchone():
                return jsonify({"error": "Email ya existe"}), 400
            password_hash = generate_password_hash(contraseña or "")
            cursor.execute("""
                INSERT INTO usuarios (email, contraseña, tipo_cuenta, activo, fecha_creacion)
                VALUES (%s,%s,%s,1,NOW())
            """, (email, password_hash, tipo_cuenta))
            usuario_id = cursor.lastrowid
            empresa_id = None
            if tipo_cuenta == "persona":
                nombre = data.get("nombre") or ""
                apellido = data.get("apellido") or ""
                documento_identidad = data.get("documento_identidad")
                cursor.execute("""
                    INSERT INTO personas (usuario_id, nombre, apellido, documento_identidad)
                    VALUES (%s,%s,%s,%s)
                """, (usuario_id, nombre, apellido, documento_identidad))
                nombre_sesion = f"{nombre} {apellido}".strip() or email
            else:
                nombre_contacto = data.get("nombre") or "Administrador"
                razon_social = data.get("razon_social") or "FINEX"
                nit = data.get("nit") or "Sin configurar"
                telefono = data.get("telefono")
                ciudad = data.get("ciudad")
                direccion = data.get("direccion")
                cursor.execute("""
                    INSERT INTO empresas (usuario_id, nombre_contacto, razon_social, nombre_empresa, nit, telefono, ciudad, direccion, email_contacto)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """, (usuario_id, nombre_contacto, razon_social, razon_social, nit, telefono, ciudad, direccion, email))
                empresa_id = cursor.lastrowid
                nombre_sesion = razon_social or nombre_contacto
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
        email = data.get("email")
        contraseña = data.get("contraseña")
        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, email, contraseña, tipo_cuenta, activo FROM usuarios WHERE email=%s LIMIT 1", (email,))
            user = cursor.fetchone()
            if not user:
                return jsonify({"error": "Usuario no existe"}), 401
            if not user.get("contraseña"):
                return jsonify({"error": "Esta cuenta usa Google o Microsoft. Inicia sesión con ese proveedor."}), 401
            if not check_password_hash(user["contraseña"], contraseña or ""):
                return jsonify({"error": "Contraseña incorrecta"}), 401
            usuario_id = user["id"]
            tipo_cuenta = user["tipo_cuenta"]
            empresa_id = None
            if tipo_cuenta == "persona":
                cursor.execute("SELECT nombre, apellido FROM personas WHERE usuario_id=%s LIMIT 1", (usuario_id,))
                perfil = cursor.fetchone()
                nombre_sesion = (f"{perfil['nombre']} {perfil['apellido']}".strip() if perfil else email)
            else:
                cursor.execute("SELECT id, nombre_contacto, razon_social FROM empresas WHERE usuario_id=%s LIMIT 1", (usuario_id,))
                perfil = cursor.fetchone()
                empresa_id = perfil["id"] if perfil else None
                nombre_sesion = ((perfil.get("razon_social") or perfil.get("nombre_contacto")) if perfil else email)
        _set_session(usuario_id, email, tipo_cuenta, nombre_sesion, empresa_id)
        return jsonify({"success": True, "message": "Inicio de sesión exitoso", "redirect": _redirect_for(tipo_cuenta)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()

@auth_bp.route("/api/logout", methods=["POST", "GET"])
def logout():
    session.clear()
    if request.method == "POST":
        return jsonify({"success": True, "redirect": url_for("main.login")})
    return redirect(url_for("main.login"))
