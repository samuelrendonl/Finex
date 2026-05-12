from db import get_db_connection

# =====================================
# OBTENER MOVIMIENTOS
# =====================================

def get_movimientos():

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    m.id,
                    m.tipo,
                    c.nombre AS categoria,
                    m.descripcion,
                    m.valor,
                    m.fecha,
                    m.estado
                FROM movimientos_persona m
                LEFT JOIN categorias c
                ON c.id = m.categoria_id
                ORDER BY m.id DESC
            """)

            return cursor.fetchall()

    finally:
        connection.close()

# =====================================
# OBTENER CATEGORIAS
# =====================================

def get_categorias():

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    id,
                    nombre
                FROM categorias
                ORDER BY nombre ASC
            """)

            return cursor.fetchall()

    finally:
        connection.close()

# =====================================
# DASHBOARD
# =====================================

def dashboard_data():

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            # INGRESOS

            cursor.execute("""
                SELECT
                COALESCE(SUM(valor),0)
                AS total
                FROM movimientos_persona
                WHERE tipo='ingreso'
            """)

            ingresos = float(
                cursor.fetchone()["total"]
            )

            # EGRESOS

            cursor.execute("""
                SELECT
                COALESCE(SUM(valor),0)
                AS total
                FROM movimientos_persona
                WHERE tipo='egreso'
            """)

            egresos = float(
                cursor.fetchone()["total"]
            )

            saldo = ingresos - egresos

            return {
                "saldo": saldo,
                "ingresos": ingresos,
                "egresos": egresos,
                "ahorros": saldo * 0.20
            }

    finally:
        connection.close()

# =====================================
# CREAR MOVIMIENTO
# =====================================

def insert_movimiento(data):

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            tipo = data["tipo"].strip().lower()

            categoria = data["categoria"]

            descripcion = data["descripcion"]

            valor = data["monto"]

            fecha = data["fecha"]

            estado = data["estado"]

            # =====================================
            # BUSCAR CATEGORIA
            # =====================================

            cursor.execute("""
                SELECT id
                FROM categorias
                WHERE nombre=%s
                LIMIT 1
            """, (categoria,))

            categoria_db = cursor.fetchone()

            # =====================================
            # SI EXISTE
            # =====================================

            if categoria_db:

                categoria_id = categoria_db["id"]

            # =====================================
            # SI NO EXISTE
            # =====================================

            else:

                cursor.execute("""
                    INSERT INTO categorias (
                        usuario_id,
                        nombre,
                        tipo
                    )
                    VALUES (%s,%s,%s)
                """, (
                    1,
                    categoria,
                    tipo
                ))

                categoria_id = cursor.lastrowid

            # =====================================
            # INSERTAR MOVIMIENTO
            # =====================================

            cursor.execute("""
                INSERT INTO movimientos_persona (
                    usuario_id,
                    categoria_id,
                    tipo,
                    descripcion,
                    valor,
                    fecha,
                    estado
                )
                VALUES (%s,%s,%s,%s,%s,%s,%s)
            """, (
                1,
                categoria_id,
                tipo,
                descripcion,
                valor,
                fecha,
                estado
            ))

            connection.commit()

    finally:
        connection.close()

# =====================================
# ELIMINAR
# =====================================

def delete_movimiento(id):

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute("""
                DELETE FROM movimientos_persona
                WHERE id=%s
            """, (id,))

            connection.commit()

    finally:
        connection.close()

# =====================================
# OBTENER CATEGORIAS
# =====================================

def get_categorias(tipo):

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    id,
                    nombre,
                    tipo
                FROM categorias
                WHERE tipo = %s
                ORDER BY nombre ASC
            """, (tipo,))

            return cursor.fetchall()

    finally:
        connection.close()

# =====================================
# CREAR CATEGORIA
# =====================================

def insert_categoria(data):

    connection = get_db_connection()

    try:

        with connection.cursor() as cursor:

            nombre = data["nombre"]
            tipo = data["tipo"]

            cursor.execute("""
                INSERT INTO categorias (
                    usuario_id,
                    nombre,
                    tipo
                )
                VALUES (%s,%s,%s)
            """, (
                1,
                nombre,
                tipo
            ))

            connection.commit()

    finally:
        connection.close()


def get_movimientos_filtrados(desde=None, hasta=None):

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:

            query = """
                SELECT
                    m.id,
                    m.tipo,
                    c.nombre AS categoria,
                    m.descripcion,
                    m.valor,
                    m.fecha,
                    m.estado
                FROM movimientos_persona m
                LEFT JOIN categorias c ON c.id = m.categoria_id
                WHERE 1=1
            """

            params = []

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

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                SELECT
                    m.id,
                    m.tipo,
                    c.nombre AS categoria,
                    m.descripcion,
                    m.valor,
                    m.fecha,
                    m.estado
                FROM movimientos_persona m
                LEFT JOIN categorias c ON c.id = m.categoria_id
                WHERE m.id = %s
            """, (id,))

            return cursor.fetchone()

    finally:
        connection.close()

def update_movimiento(id, data):

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                UPDATE movimientos_persona
                SET descripcion=%s,
                    valor=%s,
                    fecha=%s,
                    estado=%s
                WHERE id=%s
            """, (
                data["descripcion"],
                data["valor"],
                data["fecha"],
                data["estado"],
                id
            ))

            connection.commit()

    finally:
        connection.close()


def update_estado_movimiento(id, estado):

    connection = get_db_connection()

    try:
        with connection.cursor() as cursor:

            cursor.execute("""
                UPDATE movimientos_persona
                SET estado=%s
                WHERE id=%s
            """, (estado, id))

            connection.commit()

    finally:
        connection.close()