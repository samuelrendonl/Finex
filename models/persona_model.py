from flask import session
from db import get_db_connection


def current_user_id():
    return int(session.get("usuario_id") or 0)


def get_movimientos():
    return get_movimientos_filtrados()


def dashboard_data():
    usuario_id = current_user_id()
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COALESCE(SUM(valor),0) AS total
                FROM movimientos_persona
                WHERE usuario_id=%s AND tipo='ingreso'
            """, (usuario_id,))
            ingresos = float(cursor.fetchone()["total"] or 0)

            cursor.execute("""
                SELECT COALESCE(SUM(valor),0) AS total
                FROM movimientos_persona
                WHERE usuario_id=%s AND tipo='egreso'
            """, (usuario_id,))
            egresos = float(cursor.fetchone()["total"] or 0)

            cursor.execute("""
                SELECT MONTH(fecha) AS mes, tipo, COALESCE(SUM(valor),0) AS total
                FROM movimientos_persona
                WHERE usuario_id=%s
                GROUP BY MONTH(fecha), tipo
            """, (usuario_id,))
            rows = cursor.fetchall()

            monthly = []
            for idx, nombre in enumerate(meses, start=1):
                monthly.append({"mes": nombre, "ingresos": 0, "egresos": 0})
            for row in rows:
                mes = int(row["mes"] or 0)
                if 1 <= mes <= 12:
                    key = "ingresos" if row["tipo"] == "ingreso" else "egresos"
                    monthly[mes - 1][key] = float(row["total"] or 0)

            saldo = ingresos - egresos
            return {
                "saldo": saldo,
                "ingresos": ingresos,
                "egresos": egresos,
                "ahorros": max(saldo * 0.20, 0),
                "monthly": monthly,
                "totals": {"ingresos": ingresos, "egresos": egresos},
            }
    finally:
        connection.close()


def insert_movimiento(data):
    usuario_id = current_user_id()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            tipo = (data.get("tipo") or "").strip().lower()
            categoria = data.get("categoria") or "Sin categoria"
            descripcion = data.get("descripcion") or ""
            valor = data.get("monto") or data.get("valor") or 0
            fecha = data.get("fecha") or None
            estado = data.get("estado") or "Pendiente"

            cursor.execute("""
                SELECT id FROM categorias
                WHERE usuario_id=%s AND nombre=%s AND tipo=%s
                LIMIT 1
            """, (usuario_id, categoria, tipo))
            categoria_db = cursor.fetchone()
            if categoria_db:
                categoria_id = categoria_db["id"]
            else:
                cursor.execute("""
                    INSERT INTO categorias (usuario_id, nombre, tipo)
                    VALUES (%s,%s,%s)
                """, (usuario_id, categoria, tipo))
                categoria_id = cursor.lastrowid

            cursor.execute("""
                INSERT INTO movimientos_persona
                (usuario_id, categoria_id, tipo, descripcion, valor, fecha, estado)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (usuario_id, categoria_id, tipo, descripcion, valor, fecha, estado))
            connection.commit()
    finally:
        connection.close()


def delete_movimiento(id):
    usuario_id = current_user_id()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM movimientos_persona WHERE id=%s AND usuario_id=%s", (id, usuario_id))
            connection.commit()
    finally:
        connection.close()


def get_categorias(tipo):
    usuario_id = current_user_id()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, nombre, tipo
                FROM categorias
                WHERE usuario_id=%s AND tipo=%s
                ORDER BY nombre ASC
            """, (usuario_id, tipo))
            return cursor.fetchall()
    finally:
        connection.close()


def insert_categoria(data):
    usuario_id = current_user_id()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            nombre = data.get("nombre")
            tipo = data.get("tipo")
            cursor.execute("""
                INSERT INTO categorias (usuario_id, nombre, tipo)
                VALUES (%s,%s,%s)
            """, (usuario_id, nombre, tipo))
            connection.commit()
    finally:
        connection.close()


def get_movimientos_filtrados(desde=None, hasta=None):
    usuario_id = current_user_id()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT m.id, m.tipo, c.nombre AS categoria, m.descripcion, m.valor, m.fecha, m.estado
                FROM movimientos_persona m
                LEFT JOIN categorias c ON c.id = m.categoria_id
                WHERE m.usuario_id=%s
            """
            params = [usuario_id]
            if desde:
                query += " AND m.fecha >= %s"
                params.append(desde)
            if hasta:
                query += " AND m.fecha <= %s"
                params.append(hasta)
            query += " ORDER BY m.id DESC"
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        connection.close()


def get_movimiento_by_id(id):
    usuario_id = current_user_id()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT m.id, m.tipo, c.nombre AS categoria, m.descripcion, m.valor, m.fecha, m.estado
                FROM movimientos_persona m
                LEFT JOIN categorias c ON c.id = m.categoria_id
                WHERE m.id=%s AND m.usuario_id=%s
            """, (id, usuario_id))
            return cursor.fetchone()
    finally:
        connection.close()


def update_movimiento(id, data):
    usuario_id = current_user_id()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE movimientos_persona
                SET descripcion=%s, valor=%s, fecha=%s, estado=%s
                WHERE id=%s AND usuario_id=%s
            """, (data.get("descripcion"), data.get("valor"), data.get("fecha"), data.get("estado"), id, usuario_id))
            connection.commit()
    finally:
        connection.close()


def update_estado_movimiento(id, estado):
    usuario_id = current_user_id()
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE movimientos_persona SET estado=%s WHERE id=%s AND usuario_id=%s", (estado, id, usuario_id))
            connection.commit()
    finally:
        connection.close()
