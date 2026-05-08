from flask import Blueprint, request, jsonify, session
from db import get_db_connection
from decorators import login_required

user_bp = Blueprint("user", __name__)

@user_bp.route("/api/usuario-info")
@login_required
def usuario_info():
    connection = None
    try:
        connection = get_db_connection()

        with connection.cursor() as cursor:
            # ===== Obtener usuario =====
            cursor.execute("""
                SELECT id, email, tipo_cuenta, activo, fecha_creacion
                FROM usuarios
                WHERE id = %s
                LIMIT 1
            """, (session["usuario_id"],))

            user = cursor.fetchone()

            if not user:
                session.clear()
                return jsonify({"error": "Usuario no encontrado"}), 401

            # ===== SI ES PERSONA =====
            if user["tipo_cuenta"] == "persona":
                cursor.execute("""
                    SELECT nombre, apellido, documento_identidad
                    FROM personas
                    WHERE usuario_id = %s
                    LIMIT 1
                """, (user["id"],))

                persona = cursor.fetchone()

                return jsonify({
                    "id": user["id"],
                    "email": user["email"],
                    "tipo_cuenta": user["tipo_cuenta"],
                    "nombre": persona["nombre"] if persona else "",
                    "apellido": persona["apellido"] if persona else "",
                    "empresa": "",
                    "documento_identidad": persona["documento_identidad"] if persona else ""
                }), 200

            # ===== SI ES EMPRESA =====
            else:
                cursor.execute("""
                    SELECT nombre_contacto, razon_social, nit, telefono, ciudad, direccion
                    FROM empresas
                    WHERE usuario_id = %s
                    LIMIT 1
                """, (user["id"],))

                empresa = cursor.fetchone()

                return jsonify({
                    "id": user["id"],
                    "email": user["email"],
                    "tipo_cuenta": user["tipo_cuenta"],
                    "nombre": (empresa["nombre_contacto"] or empresa["razon_social"]) if empresa else "",
                    "empresa": empresa["razon_social"] if empresa else "",
                    "razon_social": empresa["razon_social"] if empresa else "",
                    "nit": empresa["nit"] if empresa else "",
                    "telefono": empresa["telefono"] if empresa else "",
                    "ciudad": empresa["ciudad"] if empresa else "",
                    "direccion": empresa["direccion"] if empresa else ""
                }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

    finally:
        if connection:
            connection.close()