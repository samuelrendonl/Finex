"""Rutas de autenticacion: login normal, registro, OAuth y cierre de sesion."""
import os
import secrets
import smtplib
import ssl
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
import json
import urllib.request
import urllib.error
from flask import Blueprint, request, jsonify, session, redirect, url_for, flash
from werkzeug.security import generate_password_hash, check_password_hash
from oauth_config import oauth
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)



PASSWORD_RESET_SESSION_KEY = "password_reset"
PASSWORD_RESET_CODE_TTL_MINUTES = int(os.getenv("PASSWORD_RESET_CODE_TTL_MINUTES", "10"))
PASSWORD_RESET_MAX_ATTEMPTS = int(os.getenv("PASSWORD_RESET_MAX_ATTEMPTS", "5"))

EMAIL_VERIFICATION_SESSION_KEY = "email_verification_codes"
REGISTRATION_VERIFICATION_PURPOSE = "registro"
CONFIG_PASSWORD_VERIFICATION_PURPOSE = "config_password"
EMAIL_VERIFICATION_CODE_TTL_MINUTES = int(os.getenv("EMAIL_VERIFICATION_CODE_TTL_MINUTES", "10"))
EMAIL_VERIFICATION_MAX_ATTEMPTS = int(os.getenv("EMAIL_VERIFICATION_MAX_ATTEMPTS", "5"))


def _now_utc():
    return datetime.now(timezone.utc)


def _smtp_enabled():
   
    if os.getenv("BREVO_API_KEY"):
        return bool(os.getenv("SMTP_FROM"))

    return all([
        os.getenv("SMTP_HOST"),
        os.getenv("SMTP_PORT"),
        os.getenv("SMTP_USER"),
        os.getenv("SMTP_PASSWORD"),
        os.getenv("SMTP_FROM") or os.getenv("SMTP_USER"),
    ])


def _generate_six_digit_code():
    return f"{secrets.randbelow(1000000):06d}"


def _send_verification_email(email, code, subject, action_text, ttl_minutes):
    """Envia un codigo de verificacion usando Brevo API o SMTP configurado en .env."""

    smtp_host = os.getenv("SMTP_HOST")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = (os.getenv("SMTP_PASSWORD") or "").strip()

    if smtp_host and "gmail" in smtp_host.lower():
        smtp_password = smtp_password.replace(" ", "")

    smtp_from = os.getenv("SMTP_FROM") or smtp_user
    smtp_from_name = os.getenv("SMTP_FROM_NAME", "FINEX")
    use_ssl = os.getenv("SMTP_USE_SSL", "false").lower() in ("1", "true", "yes", "si")
    use_tls = os.getenv("SMTP_USE_TLS", "true").lower() in ("1", "true", "yes", "si")

    brevo_api_key = os.getenv("BREVO_API_KEY")

    text_content = (
        f"Hola,\n\n"
        f"Tu codigo para {action_text} en FINEX es: {code}\n\n"
        f"Este codigo vence en {ttl_minutes} minutos. "
        f"Si no solicitaste este codigo, puedes ignorar este correo.\n\n"
        f"FINEX"
    )

    html_content = f"""
        <div style="font-family: Arial, sans-serif; color: #111827; line-height: 1.5;">
            <h2>FINEX</h2>
            <p>Hola,</p>
            <p>Tu código para {action_text} en FINEX es:</p>
            <div style="font-size: 28px; font-weight: bold; letter-spacing: 4px; margin: 20px 0;">
                {code}
            </div>
            <p>Este código vence en {ttl_minutes} minutos.</p>
            <p>Si no solicitaste este código, puedes ignorar este correo.</p>
            <br>
            <p>FINEX</p>
        </div>
    """

    # =========================
    # OPCION 1: BREVO API
    # =========================
    if brevo_api_key:
        if not smtp_from:
            raise RuntimeError("Configura SMTP_FROM en Render para usar Brevo API.")

        payload = {
            "sender": {
                "name": smtp_from_name,
                "email": smtp_from,
            },
            "to": [
                {
                    "email": email,
                }
            ],
            "subject": subject,
            "textContent": text_content,
            "htmlContent": html_content,
        }

        request_data = json.dumps(payload).encode("utf-8")

        req = urllib.request.Request(
            "https://api.brevo.com/v3/smtp/email",
            data=request_data,
            headers={
                "accept": "application/json",
                "api-key": brevo_api_key,
                "content-type": "application/json",
            },
            method="POST",
        )

        try:
            with urllib.request.urlopen(req, timeout=20) as response:
                if response.status not in (200, 201, 202):
                    raise RuntimeError(f"Brevo respondio con estado {response.status}")
            return

        except urllib.error.HTTPError as e:
            error_body = e.read().decode("utf-8", errors="ignore")
            raise RuntimeError(f"Error Brevo API: {e.code} - {error_body}")

        except Exception as e:
            raise RuntimeError(f"Error enviando email por Brevo API: {e}")

    # =========================
    # OPCION 2: SMTP NORMAL
    # =========================
    if not smtp_host or not smtp_port or not smtp_user or not smtp_password or not smtp_from:
        raise RuntimeError(
            "Configura BREVO_API_KEY o configura SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD y SMTP_FROM."
        )

    message = EmailMessage()
    message["Subject"] = subject
    message["From"] = f"{smtp_from_name} <{smtp_from}>"
    message["To"] = email
    message.set_content(text_content)
    message.add_alternative(html_content, subtype="html")

    if use_ssl:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context, timeout=20) as server:
            server.login(smtp_user, smtp_password)
            server.send_message(message)
        return

    with smtplib.SMTP(smtp_host, smtp_port, timeout=20) as server:
        if use_tls:
            server.starttls(context=ssl.create_default_context())
        server.login(smtp_user, smtp_password)
        server.send_message(message)

def _send_password_reset_email(email, code):
    _send_verification_email(
        email,
        code,
        "Codigo de recuperacion FINEX",
        "recuperar tu contraseña",
        PASSWORD_RESET_CODE_TTL_MINUTES,
    )


def _store_password_reset_code(email, code):
    session[PASSWORD_RESET_SESSION_KEY] = {
        "email": email,
        "code_hash": generate_password_hash(code),
        "expires_at": (_now_utc() + timedelta(minutes=PASSWORD_RESET_CODE_TTL_MINUTES)).isoformat(),
        "attempts": 0,
    }
    session.modified = True


def _get_password_reset_data():
    data = session.get(PASSWORD_RESET_SESSION_KEY) or {}
    if not data:
        return None

    try:
        expires_at = datetime.fromisoformat(data.get("expires_at", ""))
    except ValueError:
        session.pop(PASSWORD_RESET_SESSION_KEY, None)
        session.modified = True
        return None

    if expires_at < _now_utc():
        session.pop(PASSWORD_RESET_SESSION_KEY, None)
        session.modified = True
        return None

    return data


def _clear_password_reset_data():
    session.pop(PASSWORD_RESET_SESSION_KEY, None)
    session.modified = True


def _store_email_verification_code(purpose, email, code, usuario_id=None):
    codes = session.get(EMAIL_VERIFICATION_SESSION_KEY) or {}
    codes[purpose] = {
        "email": email,
        "usuario_id": str(usuario_id) if usuario_id is not None else None,
        "code_hash": generate_password_hash(code),
        "expires_at": (_now_utc() + timedelta(minutes=EMAIL_VERIFICATION_CODE_TTL_MINUTES)).isoformat(),
        "attempts": 0,
    }
    session[EMAIL_VERIFICATION_SESSION_KEY] = codes
    session.modified = True


def _get_email_verification_data(purpose):
    codes = session.get(EMAIL_VERIFICATION_SESSION_KEY) or {}
    data = codes.get(purpose)
    if not data:
        return None

    try:
        expires_at = datetime.fromisoformat(data.get("expires_at", ""))
    except ValueError:
        _clear_email_verification_code(purpose)
        return None

    if expires_at < _now_utc():
        _clear_email_verification_code(purpose)
        return None

    return data


def _save_email_verification_data(purpose, data):
    codes = session.get(EMAIL_VERIFICATION_SESSION_KEY) or {}
    codes[purpose] = data
    session[EMAIL_VERIFICATION_SESSION_KEY] = codes
    session.modified = True


def _clear_email_verification_code(purpose):
    codes = session.get(EMAIL_VERIFICATION_SESSION_KEY) or {}
    if purpose in codes:
        codes.pop(purpose, None)
        session[EMAIL_VERIFICATION_SESSION_KEY] = codes
        session.modified = True


def _verify_email_verification_code(purpose, codigo, email=None, usuario_id=None, missing_message=None):
    codigo = (codigo or "").strip()
    if not codigo:
        return False, "Ingresa el codigo de verificacion enviado a tu correo."

    if not codigo.isdigit() or len(codigo) != 6:
        return False, "El codigo de verificacion debe tener 6 digitos."

    data = _get_email_verification_data(purpose)
    if not data:
        return False, missing_message or "Solicita un codigo de verificacion antes de continuar."

    if email and data.get("email") != email:
        return False, "El codigo no corresponde al correo indicado. Solicita un nuevo codigo."

    if usuario_id is not None and data.get("usuario_id") != str(usuario_id):
        return False, "El codigo no corresponde a esta sesion. Solicita un nuevo codigo."

    attempts = int(data.get("attempts", 0))
    if attempts >= EMAIL_VERIFICATION_MAX_ATTEMPTS:
        _clear_email_verification_code(purpose)
        return False, "Demasiados intentos fallidos. Solicita un nuevo codigo."

    if not check_password_hash(data.get("code_hash", ""), codigo):
        data["attempts"] = attempts + 1
        _save_email_verification_data(purpose, data)
        return False, "Codigo de verificacion incorrecto."

    _clear_email_verification_code(purpose)
    return True, None


def verify_config_password_code(codigo):
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        raise ValueError("Usuario no autenticado.")

    ok, error = _verify_email_verification_code(
        CONFIG_PASSWORD_VERIFICATION_PURPOSE,
        codigo,
        usuario_id=usuario_id,
        missing_message="Solicita el codigo enviado a tu correo antes de cambiar la contraseña.",
    )
    if not ok:
        raise ValueError(error)
    return True



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
            cursor.execute("SELECT id, tipo_cuenta, contraseña FROM usuarios WHERE email=%s LIMIT 1", (email,))
            usuario = cursor.fetchone()
            password_configurada = False
            if usuario:
                usuario_id = usuario["id"]
                tipo_cuenta = usuario["tipo_cuenta"]
                password_configurada = bool(usuario.get("contraseña"))
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
        if provider == "google" and tipo_cuenta == "persona" and not password_configurada:
            flash("Cuenta creada con Google. Configura una contraseña desde esta seccion si tambien quieres iniciar con correo y contraseña.", "success")
            return redirect(url_for("persona.dashboard", section="configuracion"))
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


@auth_bp.route("/api/solicitar-codigo-registro", methods=["POST"])
def solicitar_codigo_registro():
    connection = None
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()

        if not email:
            return jsonify({"error": "El correo electronico es obligatorio"}), 400

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE email=%s LIMIT 1", (email,))
            if cursor.fetchone():
                return jsonify({"error": "Ese correo ya esta registrado."}), 400

        if not _smtp_enabled():
            return jsonify({
                "error": "No se pudo enviar el codigo porque el correo SMTP no esta configurado en el servidor. Revisa SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD y SMTP_FROM en .env."
            }), 500

        code = _generate_six_digit_code()
        _send_verification_email(
            email,
            code,
            "Codigo de verificacion FINEX",
            "verificar tu correo antes de crear la cuenta",
            EMAIL_VERIFICATION_CODE_TTL_MINUTES,
        )
        _store_email_verification_code(REGISTRATION_VERIFICATION_PURPOSE, email, code)

        return jsonify({
            "success": True,
            "message": "Enviamos un codigo de verificacion a tu correo. Ingresalo para completar el registro.",
            "expires_in_minutes": EMAIL_VERIFICATION_CODE_TTL_MINUTES,
        })
    except Exception as e:
        _clear_email_verification_code(REGISTRATION_VERIFICATION_PURPOSE)
        return jsonify({"error": f"No se pudo enviar el codigo: {e}"}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route("/api/registro", methods=["POST"])
def registro():
    connection = None
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        contraseña = data.get("contraseña") or ""
        codigo_verificacion = (data.get("codigo_verificacion") or data.get("codigo") or "").strip()
        tipo_cuenta = data.get("tipo_cuenta") or "empresa"
        if not email or not contraseña:
            return jsonify({"error": "Email y contraseña son obligatorios"}), 400

        if len(contraseña) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE email=%s", (email,))
            if cursor.fetchone():
                return jsonify({"error": "Email ya existe"}), 400

            ok, error = _verify_email_verification_code(
                REGISTRATION_VERIFICATION_PURPOSE,
                codigo_verificacion,
                email=email,
                missing_message="Solicita el codigo enviado a tu correo antes de completar el registro.",
            )
            if not ok:
                return jsonify({"error": error}), 400

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
        # No iniciar sesión automáticamente después del registro.
        # El usuario debe ir al login e ingresar con sus credenciales.
        return jsonify({
            "success": True,
            "message": "Registro exitoso. Ahora inicia sesión con tus credenciales.",
            "redirect": url_for("main.login"),
        })
    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route("/api/solicitar-codigo-configuracion", methods=["POST"])
def solicitar_codigo_configuracion():
    connection = None
    try:
        usuario_id = session.get("usuario_id")
        if not usuario_id:
            return jsonify({"error": "Debes iniciar sesion para solicitar el codigo."}), 401

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT email FROM usuarios WHERE id=%s LIMIT 1", (usuario_id,))
            user = cursor.fetchone()

        if not user:
            return jsonify({"error": "No se encontro la cuenta activa."}), 404

        email = (user.get("email") or session.get("usuario_email") or "").strip().lower()
        if not email:
            return jsonify({"error": "La cuenta no tiene un correo registrado."}), 400

        if not _smtp_enabled():
            return jsonify({
                "error": "No se pudo enviar el codigo porque el correo SMTP no esta configurado en el servidor. Revisa SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD y SMTP_FROM en .env."
            }), 500

        code = _generate_six_digit_code()
        _send_verification_email(
            email,
            code,
            "Codigo para cambiar contraseña FINEX",
            "cambiar la contraseña de tu cuenta",
            EMAIL_VERIFICATION_CODE_TTL_MINUTES,
        )
        _store_email_verification_code(CONFIG_PASSWORD_VERIFICATION_PURPOSE, email, code, usuario_id=usuario_id)

        return jsonify({
            "success": True,
            "message": "Enviamos un codigo de verificacion al correo registrado en tu cuenta.",
            "expires_in_minutes": EMAIL_VERIFICATION_CODE_TTL_MINUTES,
        })
    except Exception as e:
        _clear_email_verification_code(CONFIG_PASSWORD_VERIFICATION_PURPOSE)
        return jsonify({"error": f"No se pudo enviar el codigo: {e}"}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route("/api/solicitar-codigo-recuperacion", methods=["POST"])
def solicitar_codigo_recuperacion():
    connection = None
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()

        if not email:
            return jsonify({"error": "El correo electronico es obligatorio"}), 400

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, contraseña FROM usuarios WHERE email=%s LIMIT 1", (email,))
            user = cursor.fetchone()

        if not user:
            _clear_password_reset_data()
            return jsonify({
                "success": True,
                "message": "Si el correo existe, enviaremos un codigo de confirmacion.",
            })

        if not user.get("contraseña"):
            _clear_password_reset_data()
            return jsonify({"error": "Esta cuenta usa Google o Microsoft. Recupera el acceso desde ese proveedor."}), 400

        if not _smtp_enabled():
            return jsonify({
                "error": "No se pudo enviar el codigo porque el correo SMTP no esta configurado en el servidor. Revisa SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD y SMTP_FROM en .env."
            }), 500

        code = _generate_six_digit_code()
        _send_password_reset_email(email, code)
        _store_password_reset_code(email, code)

        return jsonify({
            "success": True,
            "message": "Enviamos un codigo de confirmacion a tu correo. Revisa tu bandeja de entrada.",
            "expires_in_minutes": PASSWORD_RESET_CODE_TTL_MINUTES,
        })
    except Exception as e:
        _clear_password_reset_data()
        return jsonify({"error": f"No se pudo enviar el codigo: {e}"}), 500
    finally:
        if connection:
            connection.close()


@auth_bp.route("/api/recuperar-contrasena", methods=["POST"])
def recuperar_contrasena():
    connection = None
    try:
        data = request.get_json() or {}
        email = (data.get("email") or "").strip().lower()
        codigo = (data.get("codigo") or "").strip()
        nueva_contraseña = data.get("nueva_contraseña") or data.get("contraseña") or ""

        if not email or not codigo or not nueva_contraseña:
            return jsonify({"error": "Correo, codigo y nueva contraseña son obligatorios"}), 400

        if len(nueva_contraseña) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

        reset_data = _get_password_reset_data()
        if not reset_data or reset_data.get("email") != email:
            return jsonify({"error": "Solicita un codigo de confirmacion antes de cambiar la contraseña."}), 400

        attempts = int(reset_data.get("attempts", 0))
        if attempts >= PASSWORD_RESET_MAX_ATTEMPTS:
            _clear_password_reset_data()
            return jsonify({"error": "Demasiados intentos fallidos. Solicita un nuevo codigo."}), 400

        if not check_password_hash(reset_data.get("code_hash", ""), codigo):
            reset_data["attempts"] = attempts + 1
            session[PASSWORD_RESET_SESSION_KEY] = reset_data
            session.modified = True
            return jsonify({"error": "Codigo de confirmacion incorrecto."}), 400

        connection = get_db_connection()
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, contraseña FROM usuarios WHERE email=%s LIMIT 1", (email,))
            user = cursor.fetchone()

            if not user:
                _clear_password_reset_data()
                return jsonify({"error": "No existe una cuenta registrada con ese correo"}), 404

            if not user.get("contraseña"):
                _clear_password_reset_data()
                return jsonify({"error": "Esta cuenta usa Google o Microsoft. Recupera el acceso desde ese proveedor."}), 400

            cursor.execute(
                "UPDATE usuarios SET contraseña=%s WHERE id=%s",
                (generate_password_hash(nueva_contraseña), user["id"]),
            )
            connection.commit()

        session.clear()
        return jsonify({
            "success": True,
            "message": "Contraseña actualizada. Ya puedes iniciar sesión.",
            "redirect": url_for("main.login"),
        })
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
