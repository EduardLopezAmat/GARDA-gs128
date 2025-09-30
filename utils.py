import sqlite3
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.graphics.barcode import code128
import io

# -----------------------
# Inicializar Base de Datos
# -----------------------
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    # Tabla etiquetas
    c.execute('''
        CREATE TABLE IF NOT EXISTS etiquetas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            contenido TEXT NOT NULL,
            fecha TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# -----------------------
# Guardar y obtener etiquetas
# -----------------------
def save_etiquetas(form_data, tipo):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    fecha = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    for item in form_data:
        contenido = str(item)
        c.execute(
            "INSERT INTO etiquetas (tipo, contenido, fecha) VALUES (?, ?, ?)",
            (tipo, contenido, fecha)
        )
    conn.commit()
    conn.close()

def get_etiquetas(filtro=""):
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    if filtro:
        c.execute(
            "SELECT tipo, contenido, fecha FROM etiquetas WHERE contenido LIKE ? ORDER BY id DESC",
            (f"%{filtro}%",)
        )
    else:
        c.execute(
            "SELECT tipo, contenido, fecha FROM etiquetas ORDER BY id DESC"
        )
    rows = c.fetchall()
    conn.close()
    etiquetas = [{"tipo": r[0], "contenido": r[1], "fecha": r[2]} for r in rows]
    return etiquetas

# -----------------------
# Validaciones
# -----------------------
def validate_gtin(gtin):
    return gtin.isdigit() and len(gtin) == 14

def validate_sscc(sscc):
    return sscc.isdigit() and len(sscc) == 18

def validate_date(date_str):
    try:
        date_obj = datetime.strptime(date_str, "%d/%m/%Y")
        return date_obj >= datetime.today()
    except:
        return False

# -----------------------
# Generación AIS para códigos de barras
# -----------------------
def generate_ais(item, tipo):
    ais = ""
    if tipo == "caja":
        ais += f"(01){item['GTIN']}"
        ais += f"(10){item['Lote']}"
        ais += f"(17){datetime.strptime(item['Fecha caducidad'], '%d/%m/%Y').strftime('%y%m%d')}"
        ais += f"(37){item['Cantidad']}"
    elif tipo == "pallet":
        ais += f"(00){item['SSCC']}"
        ais += f"(01){item['GTIN']}"
        ais += f"(10){item['Lote']}"
        ais += f"(17){datetime.strptime(item['Fecha caducidad'], '%d/%m/%Y').strftime('%y%m%d')}"
        ais += f"(37){item['Cantidad de cajas']}"
    return ais

# -----------------------
# Generar PDF con código de barras
# -----------------------
def generate_pdf(form_data):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    y_start = height - 50
    column_b_x = width / 2

    for item in form_data:
        tipo = "caja" if "GTIN" in item and "SSCC" not in item else "pallet"
        y_b = y_start

        c.setFont("Helvetica", 12)

        if tipo == "pallet":
            # Primer código solo SSCC
            ais_sscc = f"(00){item['SSCC']}"
            barcode1 = code128.Code128(ais_sscc, barHeight=50, barWidth=1.0)
            x_center1 = column_b_x - barcode1.width / 2
            barcode1.drawOn(c, x_center1, y_b - 50)
            y_b -= 55
            c.drawCentredString(column_b_x, y_b - 5, ais_sscc)
            y_b -= 26

            # Segundo código sin repetir (00)
            ais_full = generate_ais(item, tipo)
            ais_gtin = ais_full.replace(ais_sscc, "")  # 🔥 eliminamos el (00) duplicado

            barcode2 = code128.Code128(ais_gtin, barHeight=50, barWidth=1.0)
            x_center2 = column_b_x - barcode2.width / 2
            barcode2.drawOn(c, x_center2, y_b - 50)
            y_b -= 55
            c.drawCentredString(column_b_x, y_b - 5, ais_gtin)
            y_b -= 26

            # Info adicional
            for key in ["Cantidad de cajas", "Descripción", "Fecha caducidad", "GTIN", "Lote", "Peso neto KG"]:
                val = item.get(key, "")
                if val:
                    c.drawCentredString(column_b_x, y_b - 1, f"{key}: {val}")
                    y_b -= 18

        else:  # Caja
            ais = generate_ais(item, tipo)
            barcode = code128.Code128(ais, barHeight=50, barWidth=1.0)
            x_center = column_b_x - barcode.width / 2
            barcode.drawOn(c, x_center, y_b - 50)
            y_b -= 55
            c.drawCentredString(column_b_x, y_b - 5, ais)
            y_b -= 26

            for key in ["Cantidad", "Descripción", "Fecha caducidad", "GTIN", "Lote", "Peso neto KG"]:
                val = item.get(key, "")
                if val:
                    c.drawCentredString(column_b_x, y_b - 1, f"{key}: {val}")
                    y_b -= 18

        y_start = y_b - 30
        if y_start < 100:
            c.showPage()
            y_start = height - 50
            c.setFont("Helvetica-Bold", 14)

    c.showPage()
    c.save()
    pdf = buffer.getvalue()
    buffer.close()
    return pdf

# -----------------------
# Generar ZPL con plantilla fija
# -----------------------
def generate_zpl(form_data):
    zpl_full = ""
    max_width = 800  # ancho máximo de la etiqueta en pixels

    for item in form_data:
        tipo = "caja" if "GTIN" in item and "SSCC" not in item else "pallet"
        gtin = item.get("GTIN", "")
        lote = item.get("Lote", "")
        fecha = item.get("Fecha caducidad", "")
        cantidad = item.get("Cantidad", "") if tipo == "caja" else item.get("Cantidad de cajas", "")
        sscc = item.get("SSCC", "") if tipo == "pallet" else ""
        descripcion = item.get("Descripción", "")
        peso = item.get("Peso neto KG", "")

        ais = generate_ais(item, tipo)

        estimated_width = len(ais) * 11 * 2
        bar_width = int(max_width / estimated_width * 2)
        if bar_width < 1:
            bar_width = 1

        y_pos = 50
        contenido_zpl = ""

        if tipo == "pallet" and sscc:
            # Texto SSCC
            contenido_zpl += f"^FO50,{y_pos}^A0N,35,35^FDSSCC: {sscc}^FS\n"
            y_pos += 40
            # Código SSCC
            contenido_zpl += f"^FO50,{y_pos}^BY{bar_width},2,120^BCN,120,Y,N,N^FD{sscc}^FS\n"
            y_pos += 160  # 🔥 aumentamos margen (antes 120, ahora +40 extra)

        # Datos adicionales
        contenido_zpl += f"^FO50,{y_pos}^A0N,35,35^FDGTIN: {gtin}^FS\n"
        y_pos += 40
        contenido_zpl += f"^FO50,{y_pos}^A0N,35,35^FDLote: {lote}^FS\n"
        y_pos += 40
        contenido_zpl += f"^FO50,{y_pos}^A0N,35,35^FDFecha caducidad: {fecha}^FS\n"
        y_pos += 40
        contenido_zpl += f"^FO50,{y_pos}^A0N,35,35^FDCantidad: {cantidad}^FS\n"
        y_pos += 40
        if descripcion:
            contenido_zpl += f"^FO50,{y_pos}^A0N,35,35^FDDescripción: {descripcion}^FS\n"
            y_pos += 40
        if peso:
            contenido_zpl += f"^FO50,{y_pos}^A0N,35,35^FDPeso neto: {peso}^FS\n"
            y_pos += 40

        # Segundo código de barras
        contenido_zpl += f"^FO50,{y_pos}^BY{bar_width},2,120^BCN,120,Y,N,N^FD{ais}^FS\n"

        zpl_item = f"^XA\n^PW{max_width}\n^LL609\n^LH20,20\n^CI28\n^MNG\n^MMT\n^FT0,0^A0N,0,0\n"
        zpl_item += contenido_zpl
        zpl_item += "^XZ\n"
        zpl_full += zpl_item

    return zpl_full
