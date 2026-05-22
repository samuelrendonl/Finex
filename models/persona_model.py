"""Consultas del modulo personal de FINEX.

Cada funcion usa el usuario autenticado para mantener los movimientos,
categorias y reportes separados por cuenta personal.
"""
from datetime import datetime, date
from decimal import Decimal, ROUND_HALF_UP
from db import get_db_connection

VALID_STATES = ("completado", "vencido", "anulado")


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



def _cuentas_resumen(cursor, usuario_id):
    """Resumen por cuenta sin crear cuentas por defecto."""
    cursor.execute("""
        SELECT cp.id, cp.nombre, cp.tipo, cp.saldo_inicial, cp.activo, cp.created_at,
               COALESCE(SUM(CASE WHEN m.tipo='ingreso' AND m.estado='completado' THEN m.valor ELSE 0 END),0) AS ingresos,
               COALESCE(SUM(CASE WHEN m.tipo='egreso' AND m.estado='completado' THEN m.valor ELSE 0 END),0) AS egresos,
               cp.saldo_inicial
               + COALESCE(SUM(CASE WHEN m.tipo='ingreso' AND m.estado='completado' THEN m.valor ELSE 0 END),0)
               - COALESCE(SUM(CASE WHEN m.tipo='egreso' AND m.estado='completado' THEN m.valor ELSE 0 END),0) AS saldo_actual
        FROM cuentas_personales cp
        LEFT JOIN movimientos_persona m ON m.cuenta_id=cp.id AND m.usuario_id=cp.usuario_id
        WHERE cp.usuario_id=%s AND cp.activo=1
        GROUP BY cp.id, cp.nombre, cp.tipo, cp.saldo_inicial, cp.activo, cp.created_at
        ORDER BY cp.nombre ASC
    """, (usuario_id,))
    return cursor.fetchall()

def dashboard_data(usuario_id):
    """Retorna totales, saldos de cuentas, datos mensuales y distribuciones."""
    usuario_id = _user_filter(usuario_id)
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cuentas = _cuentas_resumen(cursor, usuario_id)
            cursor.execute("""
                SELECT tipo, COALESCE(SUM(valor),0) AS total
                FROM movimientos_persona
                WHERE usuario_id=%s AND estado='completado'
                GROUP BY tipo
            """, (usuario_id,))
            totals_rows = cursor.fetchall()
            totals = {r["tipo"]: int(_money(r["total"])) for r in totals_rows}

            cursor.execute("""
                SELECT MONTH(fecha) AS mes, tipo, COALESCE(SUM(valor),0) AS total
                FROM movimientos_persona
                WHERE usuario_id=%s AND estado='completado'
                GROUP BY MONTH(fecha), tipo
            """, (usuario_id,))
            monthly_rows = cursor.fetchall()

            cursor.execute("""
                SELECT m.tipo,
                       COALESCE(c.nombre, 'Sin categoría') AS categoria,
                       COALESCE(SUM(m.valor),0) AS total
                FROM movimientos_persona m
                LEFT JOIN categorias c ON c.id = m.categoria_id
                LEFT JOIN cuentas_personales cp ON cp.id = m.cuenta_id
                WHERE m.usuario_id=%s AND m.estado='completado'
                GROUP BY m.tipo, COALESCE(c.nombre, 'Sin categoría')
                ORDER BY total DESC, categoria ASC
            """, (usuario_id,))
            dist_rows = cursor.fetchall()

            cursor.execute("""
                SELECT tipo, COALESCE(SUM(valor),0) AS total
                FROM movimientos_persona
                WHERE usuario_id=%s AND estado='completado' AND cuenta_id IS NULL
                GROUP BY tipo
            """, (usuario_id,))
            sin_cuenta_rows = cursor.fetchall()
    finally:
        connection.close()

    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    maps = {(int(r["mes"]), r["tipo"]): int(_money(r["total"])) for r in monthly_rows if r.get("mes")}
    monthly = []
    for idx, nombre in enumerate(meses, start=1):
        monthly.append({"mes": nombre, "ventas": maps.get((idx, "ingreso"), 0), "compras": maps.get((idx, "egreso"), 0)})

    ingresos = totals.get("ingreso", 0)
    egresos = totals.get("egreso", 0)
    sin_cuenta = {r["tipo"]: int(_money(r["total"])) for r in sin_cuenta_rows}
    cuentas_json = []
    saldo_cuentas = 0
    for c in cuentas:
        saldo_actual = int(_money(c.get("saldo_actual")))
        saldo_cuentas += saldo_actual
        cuentas_json.append({
            "id": c.get("id"),
            "nombre": c.get("nombre"),
            "tipo": c.get("tipo"),
            "saldo_inicial": int(_money(c.get("saldo_inicial"))),
            "ingresos": int(_money(c.get("ingresos"))),
            "egresos": int(_money(c.get("egresos"))),
            "saldo_actual": saldo_actual,
        })

    dist_ingresos = []
    dist_egresos = []
    for row in dist_rows:
        item = {"categoria": row.get("categoria") or "Sin categoría", "total": int(_money(row.get("total")))}
        if row.get("tipo") == "ingreso":
            dist_ingresos.append(item)
        elif row.get("tipo") == "egreso":
            dist_egresos.append(item)

    saldo = saldo_cuentas + sin_cuenta.get("ingreso", 0) - sin_cuenta.get("egreso", 0)
    return {
        "saldo": saldo,
        "ingresos": ingresos,
        "egresos": egresos,
        "monthly": monthly,
        "totals": {"ventas": ingresos, "compras": egresos},
        "cuentas": cuentas_json,
        "distribution_ingresos": dist_ingresos,
        "distribution_egresos": dist_egresos,
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
                       m.cuenta_id,
                       cp.nombre AS cuenta,
                       c.nombre AS categoria,
                       m.descripcion,
                       m.valor,
                       m.fecha,
                       m.estado
                FROM movimientos_persona m
                LEFT JOIN categorias c ON c.id = m.categoria_id
                LEFT JOIN cuentas_personales cp ON cp.id = m.cuenta_id
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
                       m.cuenta_id,
                       cp.nombre AS cuenta,
                       c.nombre AS categoria,
                       m.descripcion,
                       m.valor,
                       m.fecha,
                       m.estado
                FROM movimientos_persona m
                LEFT JOIN categorias c ON c.id = m.categoria_id
                LEFT JOIN cuentas_personales cp ON cp.id = m.cuenta_id
                WHERE m.usuario_id=%s AND m.id=%s
                LIMIT 1
            """, (usuario_id, movimiento_id))
            return cursor.fetchone()
    finally:
        connection.close()



def _validar_cuenta(cursor, usuario_id, cuenta_id):
    """Valida una cuenta personal; permite vacío para mantener compatibilidad."""
    if cuenta_id in (None, "", "0"):
        return None
    try:
        cuenta_id = int(cuenta_id)
    except Exception:
        raise ValueError("Selecciona una cuenta válida.")
    cursor.execute("""
        SELECT id FROM cuentas_personales
        WHERE id=%s AND usuario_id=%s AND activo=1
        LIMIT 1
    """, (cuenta_id, usuario_id))
    if not cursor.fetchone():
        raise ValueError("La cuenta seleccionada no existe o está inactiva.")
    return cuenta_id

def insert_movimiento(data, usuario_id):
    """Registra un ingreso o egreso personal."""
    usuario_id = _user_filter(usuario_id)
    tipo = (data.get("tipo") or "ingreso").strip().lower()
    categoria = (data.get("categoria") or "Sin categoria").strip()
    descripcion = (data.get("descripcion") or "").strip()
    valor = _money(data.get("monto") or data.get("valor"))
    fecha = _date_value(data.get("fecha"))
    estado = "completado"
    if valor <= 0:
        raise ValueError("El monto debe ser mayor que cero.")

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            categoria_id = ensure_categoria(categoria, tipo, usuario_id, cursor)
            cuenta_id = _validar_cuenta(cursor, usuario_id, data.get("cuenta_id"))
            cursor.execute("""
                INSERT INTO movimientos_persona
                (usuario_id, categoria_id, cuenta_id, tipo, descripcion, valor, fecha, estado)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
            """, (usuario_id, categoria_id, cuenta_id, tipo, descripcion, valor, fecha, estado))
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
    estado = "completado"

    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            categoria_id = ensure_categoria(categoria, tipo, usuario_id, cursor)
            cuenta_id = _validar_cuenta(cursor, usuario_id, data.get("cuenta_id"))
            cursor.execute("""
                UPDATE movimientos_persona
                SET categoria_id=%s, cuenta_id=%s, tipo=%s, descripcion=%s, valor=%s, fecha=%s, estado=%s
                WHERE id=%s AND usuario_id=%s
            """, (categoria_id, cuenta_id, tipo, descripcion, valor, fecha, estado, movimiento_id, usuario_id))
            connection.commit()
    finally:
        connection.close()


def update_estado_movimiento(usuario_id, movimiento_id, estado):
    """Actualiza solamente el estado del movimiento."""
    usuario_id = _user_filter(usuario_id)
    estado = (estado or "completado").strip().lower()
    if estado not in VALID_STATES:
        estado = "completado"
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
    if (nueva or confirmar) and (not nueva or not confirmar):
        raise ValueError("Debes completar y confirmar la nueva contraseña.")
    if nueva and len(nueva) < 6:
        raise ValueError("La contraseña debe tener al menos 6 caracteres.")
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


def get_cuentas_personales(usuario_id):
    """Lista cuentas personales activas con saldo calculado."""
    usuario_id = _user_filter(usuario_id)
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            return _cuentas_resumen(cursor, usuario_id)
    finally:
        connection.close()


def get_cuenta_personal(usuario_id, cuenta_id):
    """Obtiene una cuenta personal activa."""
    usuario_id = _user_filter(usuario_id)
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, nombre, tipo, saldo_inicial
                FROM cuentas_personales
                WHERE id=%s AND usuario_id=%s AND activo=1
                LIMIT 1
            """, (cuenta_id, usuario_id))
            return cursor.fetchone()
    finally:
        connection.close()


def insert_cuenta_personal(usuario_id, data):
    """Crea una cuenta personal."""
    usuario_id = _user_filter(usuario_id)
    nombre = (data.get("nombre") or "").strip()
    tipo = (data.get("tipo") or "efectivo").strip().lower()
    saldo = _money(data.get("saldo_inicial"))
    if not nombre:
        raise ValueError("El nombre de la cuenta es obligatorio.")
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                INSERT INTO cuentas_personales (usuario_id, nombre, tipo, saldo_inicial)
                VALUES (%s,%s,%s,%s)
            """, (usuario_id, nombre, tipo, saldo))
            cuenta_id = cursor.lastrowid
            connection.commit()
            return cuenta_id
    finally:
        connection.close()


def update_cuenta_personal(usuario_id, cuenta_id, data):
    """Actualiza una cuenta personal."""
    usuario_id = _user_filter(usuario_id)
    nombre = (data.get("nombre") or "").strip()
    tipo = (data.get("tipo") or "efectivo").strip().lower()
    saldo = _money(data.get("saldo_inicial"))
    if not nombre:
        raise ValueError("El nombre de la cuenta es obligatorio.")
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("""
                UPDATE cuentas_personales
                SET nombre=%s, tipo=%s, saldo_inicial=%s
                WHERE id=%s AND usuario_id=%s AND activo=1
            """, (nombre, tipo, saldo, cuenta_id, usuario_id))
            connection.commit()
    finally:
        connection.close()


def delete_cuenta_personal(usuario_id, cuenta_id):
    """Desactiva una cuenta para conservar historial."""
    usuario_id = _user_filter(usuario_id)
    connection = get_db_connection()
    try:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE cuentas_personales SET activo=0 WHERE id=%s AND usuario_id=%s", (cuenta_id, usuario_id))
            connection.commit()
    finally:
        connection.close()
