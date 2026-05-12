from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from io import BytesIO
from datetime import datetime
import os
from flask import request
def generar_pdf_movimientos(movimientos, usuario, desde=None, hasta=None):
    pass