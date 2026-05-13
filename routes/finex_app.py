import json
import os
from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP
from io import BytesIO

from flask import Blueprint, flash, jsonify, make_response, redirect, render_template, request, url_for, session
from db import get_db

finex_bp = Blueprint("finex", __name__)

DEFAULT_EMPRESA_ID = int(os.getenv("EMPRESA_ID", "1"))

def build_initials(name, email=""):
    base = (name or email or "Usuario").strip()
    parts = [p for p in base.replace("@", " ").split() if p]
    if not parts:
        return "US"
    if len(parts) == 1:
        return parts[0][:2].upper()
    return (parts[0][0] + parts[1][0]).upper()


def current_user_display():
    nombre = session.get("usuario_nombre") or "Usuario"
    email = session.get("usuario_email") or ""
    return {"nombre": nombre, "email": email, "iniciales": build_initials(nombre, email)}


def ensure_empresa_profile():
    if "usuario_id" not in session:
        return redirect(url_for("main.login"))
    if session.get("usuario_tipo") == "persona":
        return redirect(url_for("persona.dashboard"))
    if session.get("empresa_id"):
        return None
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, nombre_contacto, razon_social, email_contacto FROM empresas WHERE usuario_id=%s ORDER BY id LIMIT 1", (session.get("usuario_id"),))
            empresa = cur.fetchone()
            if empresa:
                session["empresa_id"] = empresa["id"]
                session["usuario_nombre"] = empresa.get("razon_social") or empresa.get("nombre_contacto") or session.get("usuario_email")
                return None
            nombre = session.get("usuario_nombre") or "Administrador"
            email = session.get("usuario_email") or ""
            cur.execute("""
                INSERT INTO empresas (usuario_id, nombre_contacto, razon_social, nombre_empresa, nit, email_contacto)
                VALUES (%s,%s,%s,%s,%s,%s)
            """, (session.get("usuario_id"), nombre, "FINEX", "FINEX", "Sin configurar", email))
            session["empresa_id"] = cur.lastrowid
        conn.commit()
    return None


@finex_bp.before_request
def require_empresa_session():
    return ensure_empresa_profile()

def current_empresa_id():
    try:
        return int(session.get("empresa_id") or DEFAULT_EMPRESA_ID)
    except Exception:
        return DEFAULT_EMPRESA_ID

def fetch_all(sql, params=None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()


def fetch_one(sql, params=None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchone()


def execute(sql, params=None):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            conn.commit()
            return cur.lastrowid


def money(value):
    try:
        if value is None or value == "":
            return Decimal("0")
        cleaned = str(value).strip().replace("$", "").replace(" ", "")
        # Inputs use Colombian thousands dots and no decimals.
        cleaned = cleaned.replace(".", "").replace(",", "")
        if cleaned == "":
            return Decimal("0")
        return Decimal(cleaned)
    except Exception:
        return Decimal("0")


def whole(value):
    return money(value).quantize(Decimal("1"), rounding=ROUND_HALF_UP)


def form_money(name, default="0"):
    return whole(request.form.get(name, default))


def format_dt(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y %I:%M %p").replace("AM", "a. m.").replace("PM", "p. m.")
    try:
        return datetime.fromisoformat(str(value)).strftime("%d/%m/%Y %I:%M %p").replace("AM", "a. m.").replace("PM", "p. m.")
    except Exception:
        return str(value)


def format_date(value):
    if not value:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%d/%m/%Y")
    if isinstance(value, date):
        return value.strftime("%d/%m/%Y")
    try:
        return datetime.fromisoformat(str(value)).strftime("%d/%m/%Y")
    except Exception:
        return str(value)


def html_datetime(value):
    if not value:
        return datetime.now().strftime("%Y-%m-%dT%H:%M")
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%dT%H:%M")
    try:
        return datetime.fromisoformat(str(value)).strftime("%Y-%m-%dT%H:%M")
    except Exception:
        return datetime.now().strftime("%Y-%m-%dT%H:%M")


def html_date(value):
    if not value:
        return date.today().isoformat()
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    try:
        return datetime.fromisoformat(str(value)).date().isoformat()
    except Exception:
        return str(value)


@finex_bp.app_template_filter("cop")
def cop(value):
    value = whole(value)
    return "$ {:,}".format(int(value)).replace(",", ".")


@finex_bp.app_template_filter("num")
def num(value):
    value = whole(value)
    return "{:,}".format(int(value)).replace(",", ".")


@finex_bp.app_template_filter("dt")
def dt_filter(value):
    return format_dt(value)


@finex_bp.app_template_filter("d")
def d_filter(value):
    return format_date(value)


@finex_bp.app_template_filter("html_dt")
def html_dt_filter(value):
    return html_datetime(value)


@finex_bp.app_template_filter("html_d")
def html_d_filter(value):
    return html_date(value)


@finex_bp.context_processor
def inject_empresa():
    empresa = None
    try:
        empresa = fetch_one("SELECT * FROM empresas WHERE id=%s", (current_empresa_id(),))
    except Exception:
        empresa = None
    return {
        "empresa": empresa or {"nombre_empresa": "FINEX", "nit": "Sin configurar"},
        "usuario_actual": current_user_display(),
        "today": date.today().isoformat(),
        "now_local": datetime.now().strftime("%Y-%m-%dT%H:%M"),
    }


def next_invoice_number(prefix, table):
    ym = datetime.now().strftime("%Y%m")
    row = fetch_one(
        f"SELECT COUNT(*) AS total FROM {table} WHERE empresa_id=%s AND numero LIKE %s",
        (current_empresa_id(), f"{prefix}-{ym}-%"),
    )
    return f"{prefix}-{ym}-{int(row['total']) + 1:03d}"


def next_code(table, start):
    row = fetch_one(f"SELECT MAX(CAST(codigo AS UNSIGNED)) AS max_code FROM {table} WHERE empresa_id=%s", (current_empresa_id(),))
    max_code = int(row["max_code"] or 0)
    if max_code < start:
        max_code = start - 1
    return f"{max_code + 1:04d}"


def parse_sale_lines():
    item_ids = request.form.getlist("item_id[]")
    item_searches = request.form.getlist("item_search[]")
    cantidades = request.form.getlist("cantidad[]")
    precios = request.form.getlist("precio_unitario[]")
    impuestos = request.form.getlist("impuesto_porcentaje[]")
    descripciones = request.form.getlist("descripcion[]")
    notas = request.form.getlist("nota[]")
    lines = []
    max_rows = max(len(item_ids), len(item_searches))
    for idx in range(max_rows):
        raw_item_id = item_ids[idx] if idx < len(item_ids) else ""
        item = None
        if raw_item_id:
            try:
                item_id = int(raw_item_id)
                item = fetch_one("SELECT * FROM items_venta WHERE id=%s AND empresa_id=%s AND activo=1", (item_id, current_empresa_id()))
            except ValueError:
                item = None
        if not item:
            item = resolve_item_from_text(item_searches[idx] if idx < len(item_searches) else "")
        if not item:
            continue
        qty = whole(cantidades[idx] if idx < len(cantidades) else "0")
        if qty <= 0:
            continue
        item_id = int(item["id"])
        price = whole(precios[idx] if idx < len(precios) else item["precio_unitario"])
        tax_pct = whole(impuestos[idx] if idx < len(impuestos) else item["impuesto_porcentaje"])
        descripcion = (descripciones[idx] if idx < len(descripciones) else "").strip() or item.get("descripcion") or item.get("nombre") or "Producto/Servicio"
        nota = (notas[idx] if idx < len(notas) else "").strip() or None
        subtotal = qty * price
        tax = (subtotal * tax_pct / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        total = subtotal + tax
        lines.append({
            "item_id": item_id,
            "descripcion": descripcion,
            "nota": nota,
            "cantidad": qty,
            "precio_unitario": price,
            "impuesto_porcentaje": tax_pct,
            "subtotal": subtotal,
            "impuesto": tax,
            "total": total,
        })
    return lines


def parse_purchase_lines():
    item_ids = request.form.getlist("item_id[]")
    item_searches = request.form.getlist("item_search[]")
    cantidades = request.form.getlist("cantidad[]")
    precios = request.form.getlist("precio_unitario[]")
    impuestos = request.form.getlist("impuesto_porcentaje[]")
    descripciones = request.form.getlist("descripcion[]")
    notas = request.form.getlist("nota[]")
    lines = []
    max_rows = max(len(item_ids), len(item_searches))
    for idx in range(max_rows):
        raw_item_id = item_ids[idx] if idx < len(item_ids) else ""
        item = None
        if raw_item_id:
            try:
                item_id = int(raw_item_id)
                item = fetch_one("SELECT * FROM items_venta WHERE id=%s AND empresa_id=%s AND activo=1", (item_id, current_empresa_id()))
            except ValueError:
                item = None
        if not item:
            item = resolve_item_from_text(item_searches[idx] if idx < len(item_searches) else "")
        if not item:
            continue
        qty = whole(cantidades[idx] if idx < len(cantidades) else "0")
        if qty <= 0:
            continue
        item_id = int(item["id"])
        price = whole(precios[idx] if idx < len(precios) else item["precio_unitario"])
        tax_pct = whole(impuestos[idx] if idx < len(impuestos) else item["impuesto_porcentaje"])
        descripcion = (descripciones[idx] if idx < len(descripciones) else "").strip() or item.get("descripcion") or item.get("nombre") or "Producto/Servicio"
        nota = (notas[idx] if idx < len(notas) else "").strip() or None
        subtotal = qty * price
        tax = (subtotal * tax_pct / Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        total = subtotal + tax
        lines.append({
            "item_id": item_id,
            "descripcion": descripcion,
            "nota": nota,
            "cantidad": qty,
            "valor_unitario": price,
            "precio_unitario": price,
            "impuesto_porcentaje": tax_pct,
            "subtotal": subtotal,
            "impuesto": tax,
            "total": total,
            "categoria": "Compra",
        })
    return lines

def sale_totals(lines):
    subtotal = sum((l["subtotal"] for l in lines), Decimal("0"))
    impuestos = sum((l["impuesto"] for l in lines), Decimal("0"))
    total = sum((l["total"] for l in lines), Decimal("0"))
    return subtotal, impuestos, total


def list_clients():
    return fetch_all("SELECT * FROM clientes WHERE empresa_id=%s ORDER BY nombre", (current_empresa_id(),))


def list_providers():
    return fetch_all("SELECT * FROM proveedores WHERE empresa_id=%s ORDER BY nombre", (current_empresa_id(),))


def list_sale_items():
    return fetch_all("SELECT * FROM items_venta WHERE empresa_id=%s AND activo=1 ORDER BY nombre", (current_empresa_id(),))


def serialize_items(items):
    data = []
    for item in items:
        data.append({
            "id": int(item["id"]),
            "codigo": item.get("codigo") or "",
            "nombre": item.get("nombre") or "",
            "descripcion": item.get("descripcion") or "",
            "tipo": item.get("tipo") or "servicio",
            "precio_unitario": int(whole(item.get("precio_unitario"))),
            "impuesto_porcentaje": int(whole(item.get("impuesto_porcentaje"))),
            "cantidad": int(whole(item.get("cantidad"))),
            "label": f"{item.get('codigo') or ''} - {item.get('nombre') or ''}".strip(" -"),
        })
    return data


def resolve_item_from_text(text):
    raw = (text or "").strip()
    if not raw:
        return None
    lowered = raw.lower()
    return fetch_one(
        """
        SELECT * FROM items_venta
        WHERE empresa_id=%s AND activo=1
          AND (LOWER(codigo)=%s OR LOWER(nombre)=%s OR LOWER(CONCAT(codigo, ' - ', nombre))=%s)
        LIMIT 1
        """,
        (current_empresa_id(), lowered, lowered, lowered),
    )


def inventory_factor(kind, state):
    if state == "anulada":
        return Decimal("0")
    return Decimal("-1") if kind == "venta" else Decimal("1")


def inventory_line_map(lines):
    totals = {}
    for line in lines or []:
        item_id = line.get("item_id")
        if not item_id:
            continue
        totals[int(item_id)] = totals.get(int(item_id), Decimal("0")) + whole(line.get("cantidad"))
    return totals


def fetch_invoice_stock_lines(cur, table, invoice_id):
    cur.execute(f"SELECT item_id, cantidad FROM {table} WHERE factura_id=%s", (invoice_id,))
    return cur.fetchall()


def fetch_invoice_state(cur, table, invoice_id):
    cur.execute(f"SELECT estado FROM {table} WHERE id=%s AND empresa_id=%s", (invoice_id, current_empresa_id()))
    row = cur.fetchone()
    return row["estado"] if row else None


def adjust_inventory(cur, kind, old_lines=None, old_state=None, new_lines=None, new_state=None):
    old_factor = inventory_factor(kind, old_state) if old_state else Decimal("0")
    new_factor = inventory_factor(kind, new_state) if new_state else Decimal("0")
    old_map = inventory_line_map(old_lines)
    new_map = inventory_line_map(new_lines)
    item_ids = set(old_map) | set(new_map)
    for item_id in item_ids:
        delta = (new_map.get(item_id, Decimal("0")) * new_factor) - (old_map.get(item_id, Decimal("0")) * old_factor)
        if delta == 0:
            continue
        cur.execute("SELECT nombre, tipo, cantidad FROM items_venta WHERE id=%s AND empresa_id=%s", (item_id, current_empresa_id()))
        item = cur.fetchone()
        if not item or item.get("tipo") != "producto":
            continue
        nueva_cantidad = whole(item.get("cantidad")) + delta
        if nueva_cantidad < 0:
            raise ValueError(f"No hay existencias suficientes para {item.get('nombre')}. Disponible: {int(whole(item.get('cantidad')))}")
        cur.execute("UPDATE items_venta SET cantidad=%s WHERE id=%s AND empresa_id=%s", (nueva_cantidad, item_id, current_empresa_id()))


def invoice_sale(invoice_id):
    invoice = fetch_one(
        """
        SELECT f.*, c.nombre AS cliente_nombre, c.email AS cliente_email, c.telefono AS cliente_telefono, c.direccion AS cliente_direccion
        FROM facturas_venta f
        LEFT JOIN clientes c ON c.id=f.cliente_id
        WHERE f.id=%s AND f.empresa_id=%s
        """,
        (invoice_id, current_empresa_id()),
    )
    if invoice:
        invoice["lineas"] = fetch_all(
            """
            SELECT l.*, i.codigo, i.nombre AS item_nombre
            FROM factura_venta_items l
            LEFT JOIN items_venta i ON i.id=l.item_id
            WHERE l.factura_id=%s
            ORDER BY l.id
            """,
            (invoice_id,),
        )
    return invoice


def invoice_purchase(invoice_id):
    invoice = fetch_one(
        """
        SELECT f.*, p.nombre AS proveedor_nombre, p.email AS proveedor_email, p.telefono AS proveedor_telefono, p.direccion AS proveedor_direccion
        FROM facturas_compra f
        LEFT JOIN proveedores p ON p.id=f.proveedor_id
        WHERE f.id=%s AND f.empresa_id=%s
        """,
        (invoice_id, current_empresa_id()),
    )
    if invoice:
        invoice["lineas"] = fetch_all(
            """
            SELECT l.*, i.codigo, i.nombre AS item_nombre
            FROM factura_compra_items l
            LEFT JOIN items_venta i ON i.id=l.item_id
            WHERE l.factura_id=%s
            ORDER BY l.id
            """,
            (invoice_id,),
        )
    return invoice


def invoices_sale():
    facturas = fetch_all(
        """
        SELECT f.*, c.nombre AS cliente_nombre, c.email AS cliente_email, c.telefono AS cliente_telefono, c.direccion AS cliente_direccion
        FROM facturas_venta f
        LEFT JOIN clientes c ON c.id=f.cliente_id
        WHERE f.empresa_id=%s
        ORDER BY f.fecha_emision DESC, f.id DESC
        """,
        (current_empresa_id(),),
    )
    for f in facturas:
        f["lineas"] = fetch_all(
            """
            SELECT l.*, i.codigo, i.nombre AS item_nombre
            FROM factura_venta_items l
            LEFT JOIN items_venta i ON i.id=l.item_id
            WHERE l.factura_id=%s
            ORDER BY l.id
            """,
            (f["id"],),
        )
    return facturas


def invoices_purchase():
    facturas = fetch_all(
        """
        SELECT f.*, p.nombre AS proveedor_nombre, p.email AS proveedor_email, p.telefono AS proveedor_telefono, p.direccion AS proveedor_direccion
        FROM facturas_compra f
        LEFT JOIN proveedores p ON p.id=f.proveedor_id
        WHERE f.empresa_id=%s
        ORDER BY f.fecha_emision DESC, f.id DESC
        """,
        (current_empresa_id(),),
    )
    for f in facturas:
        f["lineas"] = fetch_all(
            """
            SELECT l.*, i.codigo, i.nombre AS item_nombre
            FROM factura_compra_items l
            LEFT JOIN items_venta i ON i.id=l.item_id
            WHERE l.factura_id=%s
            ORDER BY l.id
            """,
            (f["id"],),
        )
    return facturas


def dashboard_data():
    ventas = fetch_all(
        """
        SELECT MONTH(fecha_emision) mes, COALESCE(SUM(total),0) total, COUNT(*) cantidad
        FROM facturas_venta
        WHERE empresa_id=%s AND estado = 'pagada'
        GROUP BY MONTH(fecha_emision)
        """,
        (current_empresa_id(),),
    )
    compras = fetch_all(
        """
        SELECT MONTH(fecha_emision) mes, COALESCE(SUM(total),0) total, COUNT(*) cantidad
        FROM facturas_compra
        WHERE empresa_id=%s AND estado = 'pagada'
        GROUP BY MONTH(fecha_emision)
        """,
        (current_empresa_id(),),
    )
    meses = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
    ventas_map = {int(r["mes"]): int(whole(r["total"])) for r in ventas}
    compras_map = {int(r["mes"]): int(whole(r["total"])) for r in compras}
    monthly = []
    for idx, nombre in enumerate(meses, start=1):
        monthly.append({"mes": nombre, "ventas": ventas_map.get(idx, 0), "compras": compras_map.get(idx, 0)})
    total_ventas = sum(x["ventas"] for x in monthly)
    total_compras = sum(x["compras"] for x in monthly)
    return {"monthly": monthly, "totals": {"ventas": total_ventas, "compras": total_compras}}


@finex_bp.route("/dashboard-empresa")
@finex_bp.route("/app")
def index():
    stats = {
        "ventas": fetch_one("SELECT COALESCE(SUM(total),0) total, COUNT(*) cantidad FROM facturas_venta WHERE empresa_id=%s AND estado = 'pagada'", (current_empresa_id(),)),
        "compras": fetch_one("SELECT COALESCE(SUM(total),0) total, COUNT(*) cantidad FROM facturas_compra WHERE empresa_id=%s AND estado = 'pagada'", (current_empresa_id(),)),
        "movimientos": fetch_one("SELECT COUNT(*) cantidad FROM movimientos_contables WHERE empresa_id=%s AND estado = 'pagada'", (current_empresa_id(),)),
    }
    data = dashboard_data()
    return render_template("finex.html", page="index", active="inicio", stats=stats, dashboard_json=json.dumps(data))


@finex_bp.route("/facturacion-venta", methods=["GET", "POST"])
def facturacion_venta():
    if request.method == "POST":
        invoice_id = request.form.get("invoice_id", type=int)
        cliente_id = request.form.get("cliente_id", type=int)
        fecha_emision = request.form.get("fecha_emision") or datetime.now().strftime("%Y-%m-%dT%H:%M")
        fecha_vencimiento = request.form.get("fecha_vencimiento") or date.today().isoformat()
        estado = request.form.get("estado") or "emitida"
        lines = parse_sale_lines()

        if not cliente_id:
            flash("Selecciona un cliente.", "error")
            return redirect(url_for("finex.facturacion_venta"))
        if not lines:
            flash("Agrega al menos un producto o servicio a la factura.", "error")
            return redirect(url_for("finex.facturacion_venta"))

        subtotal, impuestos, total = sale_totals(lines)
        with get_db() as conn:
            try:
                with conn.cursor() as cur:
                    old_lines = []
                    old_state = None
                    if invoice_id:
                        old_state = fetch_invoice_state(cur, "facturas_venta", invoice_id)
                        old_lines = fetch_invoice_stock_lines(cur, "factura_venta_items", invoice_id)
                        cur.execute(
                            """
                            UPDATE facturas_venta
                            SET cliente_id=%s, fecha_emision=%s, fecha_vencimiento=%s,
                                subtotal=%s, impuestos=%s, total=%s, estado=%s
                            WHERE id=%s AND empresa_id=%s
                            """,
                            (cliente_id, fecha_emision.replace("T", " "), fecha_vencimiento, subtotal, impuestos, total, estado, invoice_id, current_empresa_id()),
                        )
                        cur.execute("DELETE FROM factura_venta_items WHERE factura_id=%s", (invoice_id,))
                    else:
                        codigo = next_code("facturas_venta", 1)
                        numero = next_invoice_number("FVE", "facturas_venta")
                        cur.execute(
                            """
                            INSERT INTO facturas_venta
                            (empresa_id, cliente_id, codigo, numero, fecha_emision, fecha_vencimiento, subtotal, impuestos, total, estado)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (current_empresa_id(), cliente_id, codigo, numero, fecha_emision.replace("T", " "), fecha_vencimiento, subtotal, impuestos, total, estado),
                        )
                        invoice_id = cur.lastrowid
                    for line in lines:
                        cur.execute(
                            """
                            INSERT INTO factura_venta_items
                            (factura_id, item_id, descripcion, nota, cantidad, precio_unitario, impuesto_porcentaje, subtotal, impuesto, total)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (invoice_id, line["item_id"], line["descripcion"], line.get("nota"), line["cantidad"], line["precio_unitario"], line["impuesto_porcentaje"], line["subtotal"], line["impuesto"], line["total"]),
                        )
                    adjust_inventory(cur, "venta", old_lines, old_state, lines, estado)
                conn.commit()
                flash("Factura de venta guardada. El movimiento y el PDF quedaron actualizados.", "success")
            except Exception as exc:
                conn.rollback()
                flash(f"No se pudo guardar la factura: {exc}", "error")
        return redirect(url_for("finex.facturacion_venta"))

    items = list_sale_items()
    return render_template(
        "finex.html",
        page="venta",
        active="venta",
        facturas=invoices_sale(),
        clientes=list_clients(),
        items=items,
        items_json=json.dumps(serialize_items(items)),
    )


@finex_bp.post("/facturacion-venta/<int:invoice_id>/eliminar")
def eliminar_venta(invoice_id):
    with get_db() as conn:
        try:
            with conn.cursor() as cur:
                old_state = fetch_invoice_state(cur, "facturas_venta", invoice_id)
                old_lines = fetch_invoice_stock_lines(cur, "factura_venta_items", invoice_id)
                adjust_inventory(cur, "venta", old_lines, old_state, [], None)
                cur.execute("DELETE FROM factura_venta_items WHERE factura_id=%s", (invoice_id,))
                cur.execute("DELETE FROM facturas_venta WHERE id=%s AND empresa_id=%s", (invoice_id, current_empresa_id()))
            conn.commit()
            flash("Factura de venta eliminada. Su movimiento tambien fue eliminado.", "success")
        except Exception as exc:
            conn.rollback()
            flash(f"No se pudo eliminar la factura: {exc}", "error")
    return redirect(url_for("finex.facturacion_venta"))


@finex_bp.route("/facturas-compra", methods=["GET", "POST"])
def facturas_compra():
    if request.method == "POST":
        invoice_id = request.form.get("invoice_id", type=int)
        proveedor_id = request.form.get("proveedor_id", type=int)
        numero_proveedor = request.form.get("numero_proveedor") or None
        fecha_emision = request.form.get("fecha_emision") or datetime.now().strftime("%Y-%m-%dT%H:%M")
        fecha_vencimiento = request.form.get("fecha_vencimiento") or date.today().isoformat()
        descripcion = request.form.get("descripcion") or "Compra"
        estado = request.form.get("estado") or "recibida"
        observaciones = request.form.get("observaciones") or None
        lines = parse_purchase_lines()

        if not proveedor_id:
            flash("Selecciona un proveedor.", "error")
            return redirect(url_for("finex.facturas_compra"))
        if not lines:
            flash("Agrega al menos un producto o servicio a la factura de compra.", "error")
            return redirect(url_for("finex.facturas_compra"))

        subtotal, impuestos, total = sale_totals(lines)
        with get_db() as conn:
            try:
                with conn.cursor() as cur:
                    old_lines = []
                    old_state = None
                    if invoice_id:
                        old_state = fetch_invoice_state(cur, "facturas_compra", invoice_id)
                        old_lines = fetch_invoice_stock_lines(cur, "factura_compra_items", invoice_id)
                        cur.execute(
                            """
                            UPDATE facturas_compra
                            SET proveedor_id=%s, numero_proveedor=%s, fecha_emision=%s, fecha_vencimiento=%s,
                                descripcion=%s, subtotal=%s, impuestos=%s, total=%s, estado=%s, observaciones=%s
                            WHERE id=%s AND empresa_id=%s
                            """,
                            (proveedor_id, numero_proveedor, fecha_emision.replace("T", " "), fecha_vencimiento, descripcion, subtotal, impuestos, total, estado, observaciones, invoice_id, current_empresa_id()),
                        )
                        cur.execute("DELETE FROM factura_compra_items WHERE factura_id=%s", (invoice_id,))
                    else:
                        codigo = next_code("facturas_compra", 1001)
                        numero = next_invoice_number("FCO", "facturas_compra")
                        cur.execute(
                            """
                            INSERT INTO facturas_compra
                            (empresa_id, proveedor_id, codigo, numero, numero_proveedor, fecha_emision, fecha_vencimiento, descripcion, subtotal, impuestos, total, estado, observaciones)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                            """,
                            (current_empresa_id(), proveedor_id, codigo, numero, numero_proveedor, fecha_emision.replace("T", " "), fecha_vencimiento, descripcion, subtotal, impuestos, total, estado, observaciones),
                        )
                        invoice_id = cur.lastrowid
                    for line in lines:
                        cur.execute(
                            """
                            INSERT INTO factura_compra_items
                            (factura_id, item_id, descripcion, nota, cantidad, valor_unitario, impuesto_porcentaje, subtotal, impuesto, total, categoria)
                            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,'Compra')
                            """,
                            (invoice_id, line["item_id"], line["descripcion"], line.get("nota"), line["cantidad"], line["valor_unitario"], line["impuesto_porcentaje"], line["subtotal"], line["impuesto"], line["total"]),
                        )
                    adjust_inventory(cur, "compra", old_lines, old_state, lines, estado)
                conn.commit()
                flash("Factura de compra guardada. El movimiento y el PDF quedaron actualizados.", "success")
            except Exception as exc:
                conn.rollback()
                flash(f"No se pudo guardar la factura: {exc}", "error")
        return redirect(url_for("finex.facturas_compra"))

    items = list_sale_items()
    return render_template(
        "finex.html",
        page="compra",
        active="compra",
        facturas=invoices_purchase(),
        proveedores=list_providers(),
        items=items,
        items_json=json.dumps(serialize_items(items)),
    )

@finex_bp.post("/facturas-compra/<int:invoice_id>/eliminar")
def eliminar_compra(invoice_id):
    with get_db() as conn:
        try:
            with conn.cursor() as cur:
                old_state = fetch_invoice_state(cur, "facturas_compra", invoice_id)
                old_lines = fetch_invoice_stock_lines(cur, "factura_compra_items", invoice_id)
                adjust_inventory(cur, "compra", old_lines, old_state, [], None)
                cur.execute("DELETE FROM factura_compra_items WHERE factura_id=%s", (invoice_id,))
                cur.execute("DELETE FROM facturas_compra WHERE id=%s AND empresa_id=%s", (invoice_id, current_empresa_id()))
            conn.commit()
            flash("Factura de compra eliminada. Su movimiento tambien fue eliminado.", "success")
        except Exception as exc:
            conn.rollback()
            flash(f"No se pudo eliminar la factura: {exc}", "error")
    return redirect(url_for("finex.facturas_compra"))


@finex_bp.route("/movimientos")
def movimientos():
    movimientos = fetch_all(
        """
        SELECT * FROM movimientos_contables
        WHERE empresa_id=%s
        ORDER BY fecha DESC, id DESC
        """,
        (current_empresa_id(),),
    )
    return render_template("finex.html", page="movimientos", active="movimientos", movimientos=movimientos)


@finex_bp.route("/movimientos/<int:movimiento_id>/pdf")
def movimiento_pdf(movimiento_id):
    mov = fetch_one("SELECT * FROM movimientos_contables WHERE id=%s AND empresa_id=%s", (movimiento_id, current_empresa_id()))
    if not mov:
        flash("Movimiento no encontrado.", "error")
        return redirect(url_for("finex.movimientos"))
    if mov["origen"] == "factura_venta":
        return redirect(url_for("finex.pdf_venta", invoice_id=mov["origen_id"]))
    return redirect(url_for("finex.pdf_compra", invoice_id=mov["origen_id"]))


def render_invoice_pdf(kind, invoice):
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    from reportlab.pdfgen import canvas

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter
    y = height - 0.75 * inch
    title = "Factura de venta" if kind == "venta" else "Factura de compra"
    p.setFont("Helvetica-Bold", 18)
    p.drawString(0.75 * inch, y, "FINEX")
    p.setFont("Helvetica-Bold", 13)
    p.drawRightString(width - 0.75 * inch, y, title.upper())
    y -= 0.35 * inch
    p.setFont("Helvetica", 10)
    p.drawString(0.75 * inch, y, f"Numero: {invoice['numero']}   ID: {invoice['codigo']}")
    y -= 0.25 * inch
    p.drawString(0.75 * inch, y, f"Emision: {format_dt(invoice['fecha_emision'])}")
    y -= 0.25 * inch
    p.drawString(0.75 * inch, y, f"Vencimiento: {format_date(invoice['fecha_vencimiento'])}")
    y -= 0.25 * inch
    p.drawString(0.75 * inch, y, f"Estado: {invoice['estado']}")
    y -= 0.35 * inch
    if kind == "venta":
        p.drawString(0.75 * inch, y, f"Cliente: {invoice.get('cliente_nombre') or ''}")
        y -= 0.22 * inch
        p.drawString(0.75 * inch, y, f"Email: {invoice.get('cliente_email') or ''}   Telefono: {invoice.get('cliente_telefono') or ''}")
        y -= 0.22 * inch
        p.drawString(0.75 * inch, y, f"Direccion: {invoice.get('cliente_direccion') or ''}")
    else:
        p.drawString(0.75 * inch, y, f"Proveedor: {invoice.get('proveedor_nombre') or ''}")
        y -= 0.22 * inch
        p.drawString(0.75 * inch, y, f"No. proveedor: {invoice.get('numero_proveedor') or ''}")
        y -= 0.22 * inch
        p.drawString(0.75 * inch, y, f"Email: {invoice.get('proveedor_email') or ''}   Telefono: {invoice.get('proveedor_telefono') or ''}")
        y -= 0.22 * inch
        p.drawString(0.75 * inch, y, f"Direccion: {invoice.get('proveedor_direccion') or ''}")
    y -= 0.45 * inch
    p.setFont("Helvetica-Bold", 10)
    if kind == "venta":
        p.drawString(0.75 * inch, y, "Producto/Servicio")
        p.drawString(3.15 * inch, y, "Cant.")
        p.drawString(3.75 * inch, y, "Precio")
        p.drawString(4.8 * inch, y, "Imp.")
        p.drawRightString(width - 0.75 * inch, y, "Total")
        y -= 0.12 * inch
        p.line(0.75 * inch, y, width - 0.75 * inch, y)
        y -= 0.25 * inch
        p.setFont("Helvetica", 9)
        for line in invoice.get("lineas", []):
            p.drawString(0.75 * inch, y, str(line.get("descripcion") or "")[:42])
            p.drawString(3.15 * inch, y, str(int(whole(line.get("cantidad")))))
            p.drawString(3.75 * inch, y, cop(line.get("precio_unitario")))
            p.drawString(4.8 * inch, y, f"{int(whole(line.get('impuesto_porcentaje')))}%")
            p.drawRightString(width - 0.75 * inch, y, cop(line.get("total")))
            y -= 0.24 * inch
    else:
        p.drawString(0.75 * inch, y, "Producto/Servicio")
        p.drawString(3.15 * inch, y, "Cant.")
        p.drawString(3.75 * inch, y, "Precio")
        p.drawString(4.8 * inch, y, "Imp.")
        p.drawRightString(width - 0.75 * inch, y, "Total")
        y -= 0.12 * inch
        p.line(0.75 * inch, y, width - 0.75 * inch, y)
        y -= 0.25 * inch
        p.setFont("Helvetica", 9)
        for line in invoice.get("lineas", []):
            p.drawString(0.75 * inch, y, str(line.get("descripcion") or "")[:42])
            p.drawString(3.15 * inch, y, str(int(whole(line.get("cantidad")))))
            p.drawString(3.75 * inch, y, cop(line.get("valor_unitario")))
            p.drawString(4.8 * inch, y, f"{int(whole(line.get('impuesto_porcentaje')))}%")
            p.drawRightString(width - 0.75 * inch, y, cop(line.get("total")))
            y -= 0.24 * inch
    y -= 0.35 * inch
    p.line(4.5 * inch, y, width - 0.75 * inch, y)
    y -= 0.25 * inch
    p.setFont("Helvetica-Bold", 12)
    p.drawRightString(width - 0.75 * inch, y, f"TOTAL: {cop(invoice.get('total'))}")
    p.showPage()
    p.save()
    buffer.seek(0)
    response = make_response(buffer.read())
    response.headers["Content-Type"] = "application/pdf"
    response.headers["Content-Disposition"] = f"inline; filename={invoice['numero']}.pdf"
    return response


@finex_bp.route("/facturacion-venta/<int:invoice_id>/pdf")
def pdf_venta(invoice_id):
    invoice = invoice_sale(invoice_id)
    if not invoice:
        flash("Factura no encontrada.", "error")
        return redirect(url_for("finex.facturacion_venta"))
    return render_invoice_pdf("venta", invoice)


@finex_bp.route("/facturas-compra/<int:invoice_id>/pdf")
def pdf_compra(invoice_id):
    invoice = invoice_purchase(invoice_id)
    if not invoice:
        flash("Factura no encontrada.", "error")
        return redirect(url_for("finex.facturas_compra"))
    return render_invoice_pdf("compra", invoice)


@finex_bp.route("/clientes", methods=["GET", "POST"])
def clientes():
    if request.method == "POST":
        cliente_id = request.form.get("cliente_id", type=int)
        params = (current_empresa_id(), request.form.get("nombre"), request.form.get("documento"), request.form.get("email"), request.form.get("telefono"), request.form.get("direccion"))
        if cliente_id:
            execute(
                "UPDATE clientes SET nombre=%s, documento=%s, email=%s, telefono=%s, direccion=%s WHERE id=%s AND empresa_id=%s",
                (request.form.get("nombre"), request.form.get("documento"), request.form.get("email"), request.form.get("telefono"), request.form.get("direccion"), cliente_id, current_empresa_id()),
            )
            flash("Cliente actualizado.", "success")
        else:
            execute(
                "INSERT INTO clientes (empresa_id, tipo, nombre, documento, email, telefono, direccion) VALUES (%s,'empresa',%s,%s,%s,%s,%s)",
                params,
            )
            flash("Cliente guardado.", "success")
        return redirect(url_for("finex.clientes"))
    return render_template("finex.html", page="clientes", active="clientes", clientes=list_clients())


@finex_bp.post("/clientes/<int:cliente_id>/eliminar")
def eliminar_cliente(cliente_id):
    try:
        execute("DELETE FROM clientes WHERE id=%s AND empresa_id=%s", (cliente_id, current_empresa_id()))
        flash("Cliente eliminado.", "success")
    except Exception as exc:
        flash(f"No se pudo eliminar el cliente. Revisa si tiene facturas asociadas. {exc}", "error")
    return redirect(url_for("finex.clientes"))


@finex_bp.route("/proveedores", methods=["GET", "POST"])
def proveedores():
    if request.method == "POST":
        proveedor_id = request.form.get("proveedor_id", type=int)
        if proveedor_id:
            execute(
                "UPDATE proveedores SET nombre=%s, numero_proveedor=%s, email=%s, telefono=%s, direccion=%s WHERE id=%s AND empresa_id=%s",
                (request.form.get("nombre"), request.form.get("numero_proveedor"), request.form.get("email"), request.form.get("telefono"), request.form.get("direccion"), proveedor_id, current_empresa_id()),
            )
            flash("Proveedor actualizado.", "success")
        else:
            execute(
                "INSERT INTO proveedores (empresa_id, tipo, nombre, numero_proveedor, email, telefono, direccion) VALUES (%s,'empresa',%s,%s,%s,%s,%s)",
                (current_empresa_id(), request.form.get("nombre"), request.form.get("numero_proveedor"), request.form.get("email"), request.form.get("telefono"), request.form.get("direccion")),
            )
            flash("Proveedor guardado.", "success")
        return redirect(url_for("finex.proveedores"))
    return render_template("finex.html", page="proveedores", active="proveedores", proveedores=list_providers())


@finex_bp.post("/proveedores/<int:proveedor_id>/eliminar")
def eliminar_proveedor(proveedor_id):
    try:
        execute("DELETE FROM proveedores WHERE id=%s AND empresa_id=%s", (proveedor_id, current_empresa_id()))
        flash("Proveedor eliminado.", "success")
    except Exception as exc:
        flash(f"No se pudo eliminar el proveedor. Revisa si tiene facturas asociadas. {exc}", "error")
    return redirect(url_for("finex.proveedores"))


@finex_bp.post("/items/rapido")
def crear_item_rapido():
    codigo = (request.form.get("codigo") or "").strip()
    values = (
        request.form.get("nombre"),
        request.form.get("descripcion"),
        request.form.get("tipo") or "servicio",
        form_money("precio_unitario"),
        form_money("cantidad"),
        form_money("impuesto_porcentaje"),
    )
    if not codigo:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "error": "El codigo del producto o servicio es obligatorio."}), 400
        flash("El codigo del producto o servicio es obligatorio.", "error")
        return redirect(request.referrer or url_for("finex.items"))
    if not values[0]:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "error": "El nombre del producto o servicio es obligatorio."}), 400
        flash("El nombre del producto o servicio es obligatorio.", "error")
        return redirect(request.referrer or url_for("finex.items"))
    try:
        item_id = execute(
            """
            INSERT INTO items_venta
            (empresa_id, codigo, nombre, descripcion, tipo, precio_unitario, cantidad, impuesto_porcentaje, activo)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1)
            """,
            (current_empresa_id(), codigo, *values),
        )
        item = fetch_one("SELECT * FROM items_venta WHERE id=%s AND empresa_id=%s", (item_id, current_empresa_id()))
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": True, "item": serialize_items([item])[0]})
        flash("Producto/servicio agregado.", "success")
    except Exception as exc:
        if request.headers.get("X-Requested-With") == "XMLHttpRequest":
            return jsonify({"ok": False, "error": str(exc)}), 400
        flash(f"No se pudo guardar el item: {exc}", "error")
    return redirect(request.referrer or url_for("finex.items"))


@finex_bp.route("/items", methods=["GET", "POST"])
def items():
    if request.method == "POST":
        item_id = request.form.get("item_id", type=int)
        codigo = (request.form.get("codigo") or "").strip()
        values = (
            request.form.get("nombre"),
            request.form.get("descripcion"),
            request.form.get("tipo") or "servicio",
            form_money("precio_unitario"),
            form_money("cantidad"),
            form_money("impuesto_porcentaje"),
        )
        if not codigo:
            flash("El codigo del item es obligatorio.", "error")
            return redirect(url_for("finex.items"))
        try:
            if item_id:
                execute(
                    """
                    UPDATE items_venta
                    SET codigo=%s, nombre=%s, descripcion=%s, tipo=%s, precio_unitario=%s, cantidad=%s, impuesto_porcentaje=%s
                    WHERE id=%s AND empresa_id=%s
                    """,
                    (codigo, *values, item_id, current_empresa_id()),
                )
                flash("Item actualizado.", "success")
            else:
                execute(
                    """
                    INSERT INTO items_venta
                    (empresa_id, codigo, nombre, descripcion, tipo, precio_unitario, cantidad, impuesto_porcentaje, activo)
                    VALUES (%s,%s,%s,%s,%s,%s,%s,%s,1)
                    """,
                    (current_empresa_id(), codigo, *values),
                )
                flash("Item guardado.", "success")
        except Exception as exc:
            flash(f"No se pudo guardar el item. Revisa que el codigo no este repetido. {exc}", "error")
        return redirect(url_for("finex.items"))
    return render_template("finex.html", page="items", active="items", items=list_sale_items())


@finex_bp.post("/items/<int:item_id>/eliminar")
def eliminar_item(item_id):
    execute("DELETE FROM items_venta WHERE id=%s AND empresa_id=%s", (item_id, current_empresa_id()))
    flash("Item eliminado.", "success")
    return redirect(url_for("finex.items"))


@finex_bp.route("/configuracion")
def configuracion():
    return render_template("finex.html", page="configuracion", active="configuracion")


@finex_bp.app_errorhandler(500)
def handle_500(error):
    return render_template("finex.html", page="error", active="", error=error), 500

