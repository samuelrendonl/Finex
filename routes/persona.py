
from flask import Blueprint, request
from decorators import login_required
from controller.persona_controller import *

persona_bp = Blueprint("persona", __name__)

@persona_bp.route("/")
@login_required
def dashboard():
    return render_dashboard()

@persona_bp.route("/api/dashboard")
@login_required
def dashboard_data_route():
    return obtener_dashboard()

@persona_bp.route("/api/movimientos")
@login_required
def movimientos():
    return obtener_movimientos()

@persona_bp.route("/api/movimientos", methods=["POST"])
@login_required
def crear():
    return crear_movimiento()

@persona_bp.route("/api/movimientos/<int:id>", methods=["GET"])
@login_required
def obtener_movimiento(id):
    return obtener_factura(id)

@persona_bp.route("/api/movimientos/<int:id>", methods=["PUT"])
@login_required
def actualizar_movimiento_route(id):
    return actualizar_movimiento(id)

@persona_bp.route("/api/movimientos/<int:id>", methods=["DELETE"])
@login_required
def eliminar(id):
    return eliminar_movimiento(id)

@persona_bp.route("/api/movimientos/<int:id>/pdf")
@login_required
def pdf_movimiento(id):
    return descargar_pdf_movimiento(id)

@persona_bp.route("/api/movimientos/<int:id>/excel")
@login_required
def excel_movimiento(id):
    return descargar_excel_movimiento(id)

@persona_bp.route("/api/categorias/<tipo>")
@login_required
def categorias(tipo):
    return obtener_categorias(tipo)

@persona_bp.route("/api/categorias", methods=["POST"])
@login_required
def crear_categoria_route():
    return crear_categoria()

@persona_bp.route("/api/facturas/<int:id>", methods=["GET"])
@login_required
def ver_factura(id):
    return obtener_factura(id)

@persona_bp.route("/api/facturas/<int:id>", methods=["PUT"])
@login_required
def editar_factura(id):
    return actualizar_movimiento(id)

@persona_bp.route("/api/facturas/<int:id>", methods=["DELETE"])
@login_required
def eliminar_factura(id):
    return eliminar_movimiento(id)

@persona_bp.route("/api/facturas/<int:id>/estado", methods=["PATCH"])
@login_required
def cambiar_estado(id):
    data = request.get_json() or {}
    return actualizar_estado(id, data.get("estado"))


@persona_bp.route("/configuracion", methods=["POST"])
@login_required
def configuracion_personal():
    return actualizar_configuracion_personal()
