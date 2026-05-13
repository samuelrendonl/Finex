from flask import Blueprint, request, session, redirect, url_for
from controller.persona_controller import *

persona_bp = Blueprint("persona", __name__)

@persona_bp.before_request
def require_persona_session():
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    if session.get("usuario_tipo") == "empresa":
        return redirect(url_for("finex.index"))


@persona_bp.route("/")
def dashboard():
    return render_dashboard()

@persona_bp.route("/api/dashboard")
def dashboard_data_route():
    return obtener_dashboard()

@persona_bp.route("/api/movimientos")
def movimientos():
    return obtener_movimientos()

@persona_bp.route("/api/movimientos", methods=["POST"])
def crear():
    return crear_movimiento()

@persona_bp.route("/api/movimientos/<int:id>", methods=["DELETE"])
def eliminar(id):
    return eliminar_movimiento(id)

@persona_bp.route("/api/categorias/<tipo>")
def categorias(tipo):
    return obtener_categorias(tipo)

@persona_bp.route("/api/categorias", methods=["POST"])
def crear_categoria_route():
    return crear_categoria()

@persona_bp.route("/api/facturas/<int:id>", methods=["GET"])
def ver_factura(id):
    return obtener_factura(id)


@persona_bp.route("/api/facturas/<int:id>", methods=["PUT"])
def editar_factura(id):
    return actualizar_movimiento(id)


@persona_bp.route("/api/facturas/<int:id>", methods=["DELETE"])
def eliminar_factura(id):
    return eliminar_movimiento(id)


@persona_bp.route("/api/facturas/<int:id>/estado", methods=["PATCH"])
def cambiar_estado(id):
    data = request.get_json()
    return actualizar_estado(id, data["estado"])

@persona_bp.route("/api/movimientos/<int:id>", methods=["GET"])
def obtener_movimiento(id):
    return obtener_factura(id)


@persona_bp.route("/api/movimientos/<int:id>", methods=["PUT"])
def actualizar_movimiento_route(id):
    return actualizar_movimiento(id)