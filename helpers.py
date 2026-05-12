from datetime import date, timedelta
from decimal import Decimal, ROUND_HALF_UP
from flask import jsonify, request


def get_empresa_id() -> int:
    raw = request.headers.get("X-Empresa-Id") or request.args.get("empresa_id") or 1
    try:
        return int(raw)
    except (TypeError, ValueError):
        return 1


def money(value) -> Decimal:
    if value is None or value == "":
        value = 0
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def to_float(value):
    if value is None:
        return 0.0
    if isinstance(value, Decimal):
        return float(value)
    return value


def jsonify_ok(data=None, status=200):
    payload = {"ok": True}
    if data is not None:
        payload.update(data)
    return jsonify(payload), status


def jsonify_error(message, status=400):
    return jsonify({"ok": False, "error": message}), status


def current_month_bounds():
    today = date.today()
    first = today.replace(day=1)
    if first.month == 12:
        next_first = first.replace(year=first.year + 1, month=1)
    else:
        next_first = first.replace(month=first.month + 1)
    last = next_first - timedelta(days=1)
    return first, last


def previous_month_bounds(first_day):
    prev_last = first_day - timedelta(days=1)
    prev_first = prev_last.replace(day=1)
    return prev_first, prev_last


def pct_change(current, previous):
    current = money(current)
    previous = money(previous)
    if previous == 0:
        return 100 if current > 0 else 0
    return float(((current - previous) / previous * 100).quantize(Decimal("0.01")))


def next_invoice_number(cursor, empresa_id, table_name, prefix):
    year_month = date.today().strftime("%Y%m")
    pattern = f"{prefix}-{year_month}-%"
    cursor.execute(
        f"SELECT numero FROM {table_name} WHERE empresa_id=%s AND numero LIKE %s ORDER BY id DESC LIMIT 1",
        (empresa_id, pattern),
    )
    row = cursor.fetchone()
    if not row:
        return f"{prefix}-{year_month}-001"
    last = str(row["numero"]).split("-")[-1]
    try:
        seq = int(last) + 1
    except ValueError:
        seq = 1
    return f"{prefix}-{year_month}-{seq:03d}"


def fetch_invoice_items(cursor, factura_id, tipo="venta"):
    table = "factura_venta_items" if tipo == "venta" else "factura_compra_items"
    cursor.execute(f"SELECT * FROM {table} WHERE factura_id=%s ORDER BY id", (factura_id,))
    return cursor.fetchall()
