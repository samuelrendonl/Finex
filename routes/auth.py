from flask import Blueprint, request, jsonify, session, redirect, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from oauth_config import oauth
from db import get_db_connection

auth_bp = Blueprint("auth", __name__)

# =====================================
# LOGIN GOOGLE
# =====================================

@auth_bp.route('/login/google')
def login_google():

    google = oauth.create_client('google')

    redirect_uri = url_for(
        'auth.callback_google',
        _external=True
    )

    return google.authorize_redirect(
        redirect_uri
    )

# =====================================
# CALLBACK GOOGLE
# =====================================

@auth_bp.route('/login/google/callback')
def callback_google():

    google = oauth.create_client('google')

    try:

        google.authorize_access_token()

        user = google.get(
            'https://openidconnect.googleapis.com/v1/userinfo'
        ).json()

        email = user['email']
        nombre = user['name']
        google_id = user['sub']
        foto = user['picture']

        connection = get_db_connection()

        with connection.cursor() as cursor:

            # =====================================
            # VALIDAR SI EL USUARIO YA EXISTE
            # =====================================

            cursor.execute("""
                SELECT
                    id,
                    tipo_cuenta
                FROM usuarios
                WHERE email = %s
                LIMIT 1
            """, (email,))

            usuario = cursor.fetchone()

            # =====================================
            # EXISTE
            # =====================================

            if usuario:

                usuario_id = usuario["id"]
                tipo_cuenta = usuario["tipo_cuenta"]

            # =====================================
            # NO EXISTE
            # =====================================

            else:

                cursor.execute("""
                    INSERT INTO usuarios (
                        email,
                        google_id,
                        foto,
                        tipo_cuenta,
                        activo,
                        fecha_creacion
                    )
                    VALUES (%s,%s,%s,%s,%s,NOW())
                """, (
                    email,
                    google_id,
                    foto,
                    "persona",
                    1
                ))

                usuario_id = cursor.lastrowid
                tipo_cuenta = "persona"

                # =====================================
                # CREAR PERFIL PERSONA
                # =====================================

                cursor.execute("""
                    INSERT INTO personas (
                        usuario_id,
                        nombre,
                        apellido
                    )
                    VALUES (%s,%s,%s)
                """, (
                    usuario_id,
                    nombre,
                    ""
                ))

                connection.commit()

        # =====================================
        # SESION
        # =====================================

        session.permanent = True
        session["usuario_id"] = usuario_id
        session["usuario_nombre"] = nombre
        session["usuario_email"] = email
        session["usuario_tipo"] = tipo_cuenta

        # =====================================
        # REDIRECCION
        # =====================================

        if tipo_cuenta == "persona":

            return redirect(
                url_for("persona.dashboard")
            )

        return redirect(
            url_for("main.dashboard_empresa")
        )

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

# =====================================
# REGISTRO
# =====================================

@auth_bp.route(
    "/api/registro",
    methods=["POST"]
)
def registro():

    connection = None

    try:

        data = request.get_json()

        email = data.get("email")
        contraseña = data.get("contraseña")
        tipo_cuenta = data.get("tipo_cuenta")

        connection = get_db_connection()

        with connection.cursor() as cursor:

            # =====================================
            # VALIDAR EMAIL
            # =====================================

            cursor.execute("""
                SELECT id
                FROM usuarios
                WHERE email = %s
            """, (email,))

            if cursor.fetchone():

                return jsonify({
                    "error": "Email ya existe"
                }), 400

            # =====================================
            # CREAR USUARIO
            # =====================================

            password_hash = generate_password_hash(
                contraseña
            )

            cursor.execute("""
                INSERT INTO usuarios (
                    email,
                    contraseña,
                    tipo_cuenta,
                    activo,
                    fecha_creacion
                )
                VALUES (%s,%s,%s,%s,NOW())
            """, (
                email,
                password_hash,
                tipo_cuenta,
                1
            ))

            usuario_id = cursor.lastrowid

            # =====================================
            # PERSONA
            # =====================================

            if tipo_cuenta == "persona":

                nombre = data.get("nombre")
                apellido = data.get("apellido")
                documento_identidad = data.get(
                    "documento_identidad"
                )

                cursor.execute("""
                    INSERT INTO personas (
                        usuario_id,
                        nombre,
                        apellido,
                        documento_identidad
                    )
                    VALUES (%s,%s,%s,%s)
                """, (
                    usuario_id,
                    nombre,
                    apellido,
                    documento_identidad
                ))

                nombre_sesion = nombre

            # =====================================
            # EMPRESA
            # =====================================

            else:

                nombre_contacto = data.get(
                    "nombre"
                )

                razon_social = data.get(
                    "razon_social"
                )

                nit = data.get("nit")
                telefono = data.get("telefono")
                ciudad = data.get("ciudad")
                direccion = data.get("direccion")

                cursor.execute("""
                    INSERT INTO empresas (
                        usuario_id,
                        nombre_contacto,
                        razon_social,
                        nit,
                        telefono,
                        ciudad,
                        direccion
                    )
                    VALUES (%s,%s,%s,%s,%s,%s,%s)
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

        # =====================================
        # SESION
        # =====================================

        session.permanent = True
        session["usuario_id"] = usuario_id
        session["usuario_email"] = email
        session["usuario_tipo"] = tipo_cuenta
        session["usuario_nombre"] = nombre_sesion

        # =====================================
        # REDIRECCION
        # =====================================

        if tipo_cuenta == "persona":

            redirect_url = url_for(
                "persona.dashboard"
            )

        else:

            redirect_url = url_for(
                "main.dashboard_empresa"
            )

        return jsonify({
            "success": True,
            "redirect": redirect_url
        })

    except Exception as e:

        if connection:
            connection.rollback()

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if connection:
            connection.close()

# =====================================
# LOGIN
# =====================================

@auth_bp.route(
    "/api/login",
    methods=["POST"]
)
def login():

    connection = None

    try:

        data = request.get_json()

        email = data.get("email")
        contraseña = data.get("contraseña")

        connection = get_db_connection()

        with connection.cursor() as cursor:

            # =====================================
            # USUARIO
            # =====================================

            cursor.execute("""
                SELECT
                    id,
                    email,
                    contraseña,
                    tipo_cuenta,
                    activo
                FROM usuarios
                WHERE email = %s
                LIMIT 1
            """, (email,))

            user = cursor.fetchone()

            if not user:

                return jsonify({
                    "error": "Usuario no existe"
                }), 401

            if not check_password_hash(
                user["contraseña"],
                contraseña
            ):

                return jsonify({
                    "error": "Contraseña incorrecta"
                }), 401

            usuario_id = user["id"]
            tipo_cuenta = user["tipo_cuenta"]

            # =====================================
            # DATOS PERSONA
            # =====================================

            if tipo_cuenta == "persona":

                cursor.execute("""
                    SELECT
                        nombre,
                        apellido
                    FROM personas
                    WHERE usuario_id = %s
                    LIMIT 1
                """, (usuario_id,))

                perfil = cursor.fetchone()

                if perfil:

                    nombre_sesion = (
                        f"{perfil['nombre']} "
                        f"{perfil['apellido']}"
                    ).strip()

                else:

                    nombre_sesion = email

            # =====================================
            # DATOS EMPRESA
            # =====================================

            else:

                cursor.execute("""
                    SELECT
                        nombre_contacto,
                        razon_social
                    FROM empresas
                    WHERE usuario_id = %s
                    LIMIT 1
                """, (usuario_id,))

                perfil = cursor.fetchone()

                if perfil:

                    nombre_sesion = (
                        perfil["nombre_contacto"]
                        or perfil["razon_social"]
                    )

                else:

                    nombre_sesion = email

        # =====================================
        # SESION
        # =====================================

        session.permanent = True
        session["usuario_id"] = usuario_id
        session["usuario_email"] = email
        session["usuario_tipo"] = tipo_cuenta
        session["usuario_nombre"] = nombre_sesion

        # =====================================
        # REDIRECCION
        # =====================================

        if tipo_cuenta == "persona":

            redirect_url = url_for(
                "persona.dashboard"
            )

        else:

            redirect_url = url_for(
                "main.dashboard_empresa"
            )

        return jsonify({
            "success": True,
            "redirect": redirect_url
        })

    except Exception as e:

        return jsonify({
            "error": str(e)
        }), 500

    finally:

        if connection:
            connection.close()

# =====================================
# LOGOUT
# =====================================

@auth_bp.route(
    "/api/logout",
    methods=["POST", "GET"]
)
def logout():

    session.clear()

    return jsonify({
        "success": True,
        "redirect": url_for("main.index")
    })