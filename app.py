from flask import Flask, render_template, request, redirect, url_for, send_file, session
from utils import (
    validate_gtin, validate_sscc, validate_date, generate_pdf, generate_zpl
)
from translations import translations
import io

app = Flask(__name__)
app.secret_key = "supersecretkey"

# -----------------------
# Diccionario para mapear claves de form_data a translations
# -----------------------
KEY_MAP = {
    "GTIN": "gtin",
    "Lote": "lote",
    "Fecha caducidad": "fecha",
    "Cantidad": "cantidad",
    "Cantidad de cajas": "cantidad_cajas",
    "Peso neto KG": "peso",
    "Descripción": "descripcion",
    "SSCC": "sscc",
    "Nº PEDIDO GARDA": "pedido_garda"
}

# -----------------------
# Rutas principales
# -----------------------

@app.route("/", methods=["GET", "POST"])
def index():
    """
    Pantalla principal: selección de tipo de unidad (caja/pallet)
    """
    if request.method == "POST":
        session['tipo_unidad'] = request.form['tipo_unidad']
        return redirect(url_for("form_unidad"))
    
    lang = session.get('lang', 'ES')
    return render_template("index.html", translations=translations, lang=lang)


@app.route("/set_lang/<lang>")
def set_lang(lang):
    """
    Cambiar idioma de la aplicación
    """
    session['lang'] = lang
    return redirect(request.referrer or url_for('index'))


@app.route("/form", methods=["GET", "POST"])
def form_unidad():
    """
    Formulario de caja o pallet sin Nº de pedido
    """
    tipo = session.get('tipo_unidad', 'caja')
    lang = session.get('lang', 'ES')

    if request.method == "POST":
        form_data = []

        if tipo == "caja":
            item = {
                "GTIN": request.form["gtin"],
                "Lote": request.form["lote"],
                "Fecha caducidad": request.form["fecha"],
                "Cantidad": request.form["cantidad"],
                "Peso neto KG": f"{request.form.get('peso','')} KG" if request.form.get('peso') else "",
                "Descripción": request.form.get("descripcion", "")
            }
        else:
            item = {
                "SSCC": request.form["sscc"],
                "GTIN": request.form["gtin"],
                "Lote": request.form["lote"],
                "Fecha caducidad": request.form["fecha"],
                "Cantidad de cajas": request.form["cantidad"],
                "Peso neto KG": f"{request.form.get('peso','')} KG" if request.form.get('peso') else "",
                "Descripción": request.form.get("descripcion", "")
            }

        form_data.append(item)
        session['form_data'] = form_data

        # Ya no guardamos en DB ni historial
        return redirect(url_for("preview"))

    if tipo == "caja":
        return render_template("form_caja.html", translations=translations, lang=lang)
    else:
        return render_template("form_pallet.html", translations=translations, lang=lang)


@app.route("/preview")
def preview():
    """
    Vista previa de etiquetas antes de descargar
    """
    form_data = session.get('form_data', [])
    lang = session.get('lang', 'ES')
    tipo = session.get('tipo_unidad', 'caja')
    return render_template(
        "preview.html",
        form_data=form_data,
        translations=translations,
        lang=lang,
        tipo=tipo,
        KEY_MAP=KEY_MAP
    )


@app.route("/download/<file_type>")
def download(file_type):
    """
    Descargar etiquetas en PDF o ZPL
    """
    form_data = session.get('form_data', [])
    if file_type == "pdf":
        pdf = generate_pdf(form_data)
        return send_file(io.BytesIO(pdf), mimetype='application/pdf', as_attachment=True, download_name="etiquetas.pdf")
    elif file_type == "zpl":
        zpl = generate_zpl(form_data)
        return send_file(io.BytesIO(zpl.encode()), mimetype='text/plain', as_attachment=True, download_name="etiquetas.zpl")
    return redirect(url_for("preview"))


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
