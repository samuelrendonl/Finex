
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from db import get_db_connection

VALID_STATES = ("emitida", "pagada", "vencida", "anulada")


def _money(value):
    """Convierte valores escritos como 20.000 en Decimal sin decimales."""
    raw = str(value or "0").replace("$", "").replace(".", "").replace(",", "").strip()
    return Decimal(raw or "0").quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def _date_value(value):
    """Normaliza fechas recibidas desde formularios HTML."""
    if not value:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    value = str(value).replace("T", " ")
    if len(value) == 10:
        value += " 00:00:00"
    return value


def _user_filter(usuario_id):
    if not usuario_id:
        raise ValueError("Usuario no autenticado.")
    return int(usuario_id)


def dashboard_data(usuario_id):
    """Retorna totales y datos mensuales; solo cuenta estados pagados."""
    usuario_id = _user_filter(usuario_id)
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT tipo, COALESCE(SUM(valor),0) AS total
                FROM movimientos_persona
                WHERE usuario_id=%s AND estado='pagada'
                GROUP BY tipo
            """, (usuario_id,))
            totals_rows = cursor.fetchall()
            totals = {r["tipo"]: int(_money(r["total"])) for r in totals_rows}

            cursor.execute("""
                SELECT MONTH(fecha) AS mes, tipo, COALESCE(SUM(valor),0) AS total
                FROM movimientos_persona
                WHERE usuario_id=%s AND estado='pagada'
                GROUP BY MONTH(fecha), tipo
            """, (usuario_id,))
            monthly_rows = cursor.fetchall()
    finally:
        connection.close()

    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    maps = {(int(r["mes"]), r["tipo"]): int(_money(r["total"])) for r in monthly_rows if r.get("mes")}
    monthly = []
    for idx, nombre in enumerate(meses, start=1):
        monthly.append({"mes": nombre, "ventas": maps.get((idx, "ingreso"), 0), "compras": maps.get((idx, "egreso"), 0)})
    ingresos = totals.get("ingreso", 0)
    egresos = totals.get("egreso", 0)
    return {
        "saldo": ingresos - egresos,
        "ingresos": ingresos,
        "egresos": egresos,
        "monthly": monthly,
        "totals": {"ventas": ingresos, "compras": egresos},
        "labels": {"ventas": "Ingresos", "compras": "Egresos", "empty": "Registra movimientos"},
    }


def get_categorias(tipo, usuario_id):
    """Lista categorias del usuario por tipo de movimiento."""
    usuario_id = _user_filter(usuario_id)
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


def ensure_categoria(nombre, tipo, usuario_id, cursor):
    """Busca o crea una categoria personal para el usuario."""
    nombre = (nombre or "Sin categoria").strip()
    cursor.execute("""
        SELECT id FROM categorias
        WHERE usuario_id=%s AND tipo=%s AND nombre=%s
        LIMIT 1
    """, (usuario_id, tipo, nombre))
    row = cursor.fetchone()
    if row:
        return row["id"]
    cursor.execute("""
        INSERT INTO categorias (usuario_id, nombre, tipo)
        VALUES (%s,%s,%s)
    """, (usuario_id, nombre, tipo))
    return cursor.lastrowid


def insert_categoria(data, usuario_id):
    """Crea una categoria manual desde el panel personal."""
    usuario_id = _user_filter(usuario_id)
    nombre = (data.get("nombre") or "").strip()
    tipo = (data.get("tipo") or "ingreso").strip().lower()
    if not nombre:
        raise ValueError("El nombre de la categoria es obligatorio.")
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            ensure_categoria(nombre, tipo, usuario_id, cursor)
            connection.commit()
    finally:
        connection.close()


def get_movimientos_filtrados(usuario_id, desde=None, hasta=None, tipo=None):
    """Consulta movimientos personales con filtros opcionales."""
    usuario_id = _user_filter(usuario_id)
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            query = """
                SELECT m.id,
                       LPAD(m.id,4,'0') AS numero_registro,
                       m.tipo,
                       c.nombre AS categoria,
                       m.descripcion,
                       m.valor,
                       m.fecha,
                       m.estado
                FROM movimientos_persona m
                LEFT JOIN categorias c ON c.id = m.categoria_id
                WHERE m.usuario_id=%s
            """
            params = [usuario_id]
            if tipo:
                query += " AND m.tipo=%s"
                params.append(tipo)
            if desde:
                query += " AND DATE(m.fecha) >= %s"
                params.append(desde)
            if hasta:
                query += " AND DATE(m.fecha) <= %s"
                params.append(hasta)
            query += " ORDER BY m.fecha DESC, m.id DESC"
            cursor.execute(query, params)
            return cursor.fetchall()
    finally:
        connection.close()


def get_movimiento_by_id(usuario_id, movimiento_id):
    """Obtiene un movimiento por id validando que pertenezca al usuario."""
    usuario_id = _user_filter(usuario_id)
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT m.id,
                       LPAD(m.id,4,'0') AS numero_registro,
                       m.tipo,
                       c.nombre AS categoria,
                       m.descripcion,
                       m.valor,
                       m.fecha,
                       m.estado
                FROM movimientos_persona m
                LEFT JOIN categorias c ON c.id = m.categoria_id
                WHERE m.usuario_id=%s AND m.id=%s
                LIMIT 1
            """, (usuario_id, movimiento_id))
            return cursor.fetchone()
    finally:
        connection.close()


def insert_movimiento(data, usuario_id):
    """Registra un ingreso o egreso personal."""
    usuario_id = _user_filter(usuario_id)
    tipo = (data.get("tipo") or "ingreso").strip().lower()
    categoria = (data.get("categoria") or "Sin categoria").strip()
    descripcion = (data.get("descripcion") or "").strip()
    valor = _money(data.get("monto") or data.get("valor"))
    fecha = _date_value(data.get("fecha"))
    estado = (data.get("estado") or "emitida").strip().lower()
    if estado not in VALID_STATES:
        estado = "emitida"
    if valor <= 0:
        raise ValueError("El monto debe ser mayor que cero.")

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            categoria_id = ensure_categoria(categoria, tipo, usuario_id, cursor)
            cursor.execute("""
                INSERT INTO movimientos_persona
                (usuario_id, categoria_id, tipo, descripcion, valor, fecha, estado)
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (usuario_id, categoria_id, tipo, descripcion, valor, fecha, estado))
            movimiento_id = cursor.lastrowid
            connection.commit()
            return movimiento_id
    finally:
        connection.close()


def update_movimiento(usuario_id, movimiento_id, data):
    """Actualiza categoria, monto, descripcion, fecha y estado."""
    usuario_id = _user_filter(usuario_id)
    tipo = (data.get("tipo") or "ingreso").strip().lower()
    categoria = (data.get("categoria") or "Sin categoria").strip()
    valor = _money(data.get("monto") or data.get("valor"))
    descripcion = (data.get("descripcion") or "").strip()
    fecha = _date_value(data.get("fecha"))
    estado = (data.get("estado") or "emitida").strip().lower()
    if estado not in VALID_STATES:
        estado = "emitida"

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            categoria_id = ensure_categoria(categoria, tipo, usuario_id, cursor)
            cursor.execute("""
                UPDATE movimientos_persona
                SET categoria_id=%s, tipo=%s, descripcion=%s, valor=%s, fecha=%s, estado=%s
                WHERE id=%s AND usuario_id=%s
            """, (categoria_id, tipo, descripcion, valor, fecha, estado, movimiento_id, usuario_id))
            connection.commit()
    finally:
        connection.close()


def update_estado_movimiento(usuario_id, movimiento_id, estado):
    """Actualiza solamente el estado del movimiento."""
    usuario_id = _user_filter(usuario_id)
    estado = (estado or "emitida").strip().lower()
    if estado not in VALID_STATES:
        estado = "emitida"
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE movimientos_persona
                SET estado=%s
                WHERE id=%s AND usuario_id=%s
            """, (estado, movimiento_id, usuario_id))
            connection.commit()
    finally:
        connection.close()


def delete_movimiento(usuario_id, movimiento_id):
    """Elimina un movimiento del usuario actual."""
    usuario_id = _user_filter(usuario_id)
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("DELETE FROM movimientos_persona WHERE id=%s AND usuario_id=%s", (movimiento_id, usuario_id))
            connection.commit()
    finally:
        connection.close()


def get_persona_profile(usuario_id):
    """Obtiene los datos de registro de la cuenta personal."""
    usuario_id = _user_filter(usuario_id)
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT u.email,
                       p.nombre,
                       p.apellido,
                       p.documento_identidad,
                       p.telefono,
                       p.direccion
                FROM usuarios u
                LEFT JOIN personas p ON p.usuario_id = u.id
                WHERE u.id=%s
                LIMIT 1
            """, (usuario_id,))
            return cursor.fetchone() or {}
    finally:
        connection.close()


def update_persona_profile(usuario_id, data):
    """Actualiza nombre, correo y datos basicos de la cuenta personal."""
    usuario_id = _user_filter(usuario_id)
    nombre = (data.get("nombre") or "").strip()
    apellido = (data.get("apellido") or "").strip()
    email = (data.get("email") or "").strip().lower()
    documento = (data.get("documento_identidad") or "").strip()
    telefono = (data.get("telefono") or "").strip()
    direccion = (data.get("direccion") or "").strip()
    nueva = (data.get("nueva_contrasena") or "").strip()
    confirmar = (data.get("confirmar_contrasena") or "").strip()

    if not nombre or not apellido or not email or not documento or not telefono:
        raise ValueError("Nombre, apellido, correo, documento y telefono son obligatorios.")
    if nueva and nueva != confirmar:
        raise ValueError("Las contraseñas no coinciden.")

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT id FROM usuarios WHERE email=%s AND id<>%s LIMIT 1", (email, usuario_id))
            if cursor.fetchone():
                raise ValueError("Ese correo ya está registrado en otra cuenta.")

            if nueva:
                from werkzeug.security import generate_password_hash
                cursor.execute("UPDATE usuarios SET email=%s, contraseña=%s WHERE id=%s", (email, generate_password_hash(nueva), usuario_id))
            else:
                cursor.execute("UPDATE usuarios SET email=%s WHERE id=%s", (email, usuario_id))

            cursor.execute("SELECT id FROM personas WHERE usuario_id=%s LIMIT 1", (usuario_id,))
            perfil = cursor.fetchone()
            if perfil:
                cursor.execute("""
                    UPDATE personas
                    SET nombre=%s, apellido=%s, documento_identidad=%s, telefono=%s, direccion=%s
                    WHERE usuario_id=%s
                """, (nombre, apellido, documento, telefono, direccion, usuario_id))
            else:
                cursor.execute("""
                    INSERT INTO personas (usuario_id, nombre, apellido, documento_identidad, telefono, direccion)
                    VALUES (%s,%s,%s,%s,%s,%s)
                """, (usuario_id, nombre, apellido, documento, telefono, direccion))
            connection.commit()
    finally:
        connection.close()

    return {"nombre": f"{nombre} {apellido}".strip(), "email": email}
