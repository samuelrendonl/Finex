from flask import Blueprint, Response, render_template, request, session
import pdfkit

from models.persona_model import get_movimientos_filtrados

reportes_bp = Blueprint("reportes", __name__)


@reportes_bp.route("/reportes/movimientos/pdf")
def pdf_movimientos():
    
    desde = request.args.get("desde")
    hasta = request.args.get("hasta")

    movimientos = get_movimientos_filtrados(desde, hasta)

    usuario = {
        "nombre": session.get("usuario_nombre"),
        "correo": session.get("usuario_email")
    }

    ingresos = sum(float(m["valor"]) for m in movimientos if m["tipo"] == "ingreso")
    egresos = sum(float(m["valor"]) for m in movimientos if m["tipo"] == "egreso")
    saldo = ingresos - egresos

    html = render_template(
        "pdf_movimientos.html",
        movimientos=movimientos,
        usuario=usuario,
        desde=desde,
        hasta=hasta,
        ingresos=ingresos,
        egresos=egresos,
        saldo=saldo
    )

    config = pdfkit.configuration(
        wkhtmltopdf=r"C:\Program Files\wkhtmltopdf\bin\wkhtmltopdf.exe"
    )

    pdf = pdfkit.from_string(html, False, configuration=config)

    return Response(
        pdf,
        mimetype="application/pdf",
        headers={"Content-Disposition": "attachment; filename=finex.pdf"}
    )
    

