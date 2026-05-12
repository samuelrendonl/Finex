from flask import render_template, session, jsonify, request
from models.persona_model import *

def render_dashboard():
    return render_template(
        "dashboard.html",
        nombre=session.get("usuario_nombre"),
        correo=session.get("usuario_email")
    )

def obtener_dashboard():
    return jsonify(dashboard_data())

def obtener_dashboard():
    return jsonify(dashboard_data())

def obtener_movimientos():
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    return jsonify(get_movimientos_filtrados(desde, hasta))

def crear_movimiento():
    data = request.get_json()
    insert_movimiento(data)
    return jsonify({"success": True})

def eliminar_movimiento(id):
    delete_movimiento(id)
    return jsonify({"success": True})

def obtener_categorias(tipo):
    return jsonify(get_categorias(tipo))

def crear_categoria():
    data = request.get_json()
    insert_categoria(data)
    return jsonify({"success": True})

def obtener_factura(id):
    return jsonify(get_movimiento_by_id(id))


def actualizar_movimiento(id):
    data = request.get_json()
    update_movimiento(id, data)
    return jsonify({"success": True})


def actualizar_estado(id, estado):
    update_estado_movimiento(id, estado)
    return jsonify({"success": True})