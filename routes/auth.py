from flask import Blueprint, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from oauth_config import oauth
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)




# ===== LOGIN GOOGLE =====
@auth_bp.route('/login/google')
def login_google():

    google = oauth.create_client('google')

    redirect_uri = url_for('auth.callback_google', _external=True)

    return google.authorize_redirect(redirect_uri)


@auth_bp.route('/login/google/callback')
def callback_google():

    google = oauth.create_client('google')

    try:
        token = google.authorize_access_token()

        user = google.get(
            'https://openidconnect.googleapis.com/v1/userinfo'
        ).json()

        email = user['email']
        nombre = user['name']
        google_id = user['sub']
        foto = user['picture']

        db = get_db_connection()
        cursor = db.cursor()

        cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
        usuario = cursor.fetchone()

        if usuario:
            user_id = usuario["id"]
        else:
            cursor.execute("""
                INSERT INTO usuarios (nombre, email, google_id, foto)
                VALUES (%s, %s, %s, %s)
            """, (nombre, email, google_id, foto))
            db.commit()
            user_id = cursor.lastrowid

        session["usuario_id"] = user_id
        session["usuario_nombre"] = nombre

        return redirect(url_for("main.dashboard"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ===== REGISTRO =====
@auth_bp.route("/api/registro", methods=["POST"])
def registro():
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400

        email = data.get("email")
        contraseña = data.get("contraseña")
        tipo_cuenta = data.get("tipo_cuenta")

        if not email or not contraseña or not tipo_cuenta:
            return jsonify({"error": "Email, contraseña y tipo de cuenta son requeridos"}), 400

        if tipo_cuenta not in ["persona", "empresa"]:
            return jsonify({"error": "Tipo de cuenta inválido"}), 400

        if len(contraseña) < 6:
            return jsonify({"error": "La contraseña debe tener al menos 6 caracteres"}), 400

        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({"error": "Email ya existe"}), 400

            password_hash = generate_password_hash(contraseña)

            cursor.execute("""
                INSERT INTO usuarios 
                (email, `contraseña`, tipo_cuenta, activo, fecha_creacion)
                VALUES (%s, %s, %s, %s, NOW())
            """, (email, password_hash, tipo_cuenta, 1))

            usuario_id = cursor.lastrowid

            if tipo_cuenta == "persona":
                nombre = data.get("nombre")
                apellido = data.get("apellido")
                documento_identidad = data.get("documento_identidad")

                if not nombre or not apellido:
                    connection.rollback()
                    return jsonify({"error": "Nombre y apellido son requeridos"}), 400

                cursor.execute("""
                    INSERT INTO personas
                    (usuario_id, nombre, apellido, documento_identidad)
                    VALUES (%s, %s, %s, %s)
                """, (usuario_id, nombre, apellido, documento_identidad))

                nombre_sesion = nombre

            else:
                nombre_contacto = data.get("nombre")
                razon_social = data.get("razon_social")
                nit = data.get("nit")
                telefono = data.get("telefono")
                ciudad = data.get("ciudad")
                direccion = data.get("direccion")

                if not razon_social or not nit:
                    connection.rollback()
                    return jsonify({"error": "Razón social y NIT son requeridos"}), 400

                if not nombre_contacto:
                    nombre_contacto = razon_social

                cursor.execute("""
                    INSERT INTO empresas
                    (usuario_id, nombre_contacto, razon_social, nit, telefono, ciudad, direccion)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (
                    usuario_id,
                    nombre_contacto,
                    razon_social,
                    nit,
                    telefono,
                    ciudad,
                    direccion
                ))

                nombre_sesion = nombre_contacto

            connection.commit()

        session.permanent = True
        session["usuario_id"] = usuario_id
        session["usuario_email"] = email
        session["usuario_tipo"] = tipo_cuenta
        session["usuario_nombre"] = nombre_sesion

        return jsonify({
            "success": True,
            "message": "Registro exitoso",
            "redirect": url_for("main.dashboard")
        }), 201

    except Exception as e:
        if connection:
            connection.rollback()
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()


# ===== LOGIN =====
@auth_bp.route("/api/login", methods=["POST"])
def login():
    connection = None

    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No se recibieron datos"}), 400

        email = data.get("email")
        contraseña = data.get("contraseña")

        if not email or not contraseña:
            return jsonify({"error": "Email y contraseña son requeridos"}), 400

        connection = get_db_connection()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, email, `contraseña`, tipo_cuenta, activo
                FROM usuarios
                WHERE email = %s
                LIMIT 1
            """, (email,))

            user = cursor.fetchone()

            if not user:
                return jsonify({"error": "Usuario no existe"}), 401

            if user["activo"] != 1:
                return jsonify({"error": "Usuario inactivo"}), 401

            if not check_password_hash(user["contraseña"], contraseña):
                return jsonify({"error": "Contraseña incorrecta"}), 401

            usuario_id = user["id"]
            tipo_cuenta = user["tipo_cuenta"]

            if tipo_cuenta == "persona":
                cursor.execute("""
                    SELECT nombre FROM personas WHERE usuario_id = %s LIMIT 1
                """, (usuario_id,))
                perfil = cursor.fetchone()
                nombre_sesion = perfil["nombre"] if perfil else email

            else:
                cursor.execute("""
                    SELECT nombre_contacto, razon_social FROM empresas WHERE usuario_id = %s LIMIT 1
                """, (usuario_id,))
                perfil = cursor.fetchone()
                if perfil:
                    nombre_sesion = perfil["nombre_contacto"] or perfil["razon_social"]
                else:
                    nombre_sesion = email

        session.permanent = True
        session["usuario_id"] = usuario_id
        session["usuario_email"] = email
        session["usuario_tipo"] = tipo_cuenta
        session["usuario_nombre"] = nombre_sesion

        return jsonify({
            "success": True,
            "message": "Inicio de sesión exitoso",
            "redirect": url_for("main.dashboard")
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()


# ===== LOGOUT =====
@auth_bp.route("/api/logout", methods=["POST", "GET"])
def logout():
    session.clear()

    return jsonify({
        "success": True,
        "message": "Sesión cerrada",
        "redirect": url_for("main.index")
    }), 200