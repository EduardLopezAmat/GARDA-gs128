function validateCajaForm() {
    const gtin = document.querySelector('input[name="gtin"]').value;
    const fecha = document.querySelector('input[name="fecha"]').value;
    const cantidad = document.querySelector('input[name="cantidad"]').value;

    if (!/^\d{14}$/.test(gtin)) { alert("GTIN debe tener 14 dígitos"); return false; }
    if (!/^\d{2}\/\d{2}\/\d{4}$/.test(fecha)) { alert("Fecha debe ser DD/MM/AAAA"); return false; }
    if (parseInt(cantidad) < 1) { alert("Cantidad mínima es 1"); return false; }
    return true;
}

function validatePalletForm() {
    const sscc = document.querySelector('input[name="sscc"]').value;
    const gtin = document.querySelector('input[name="gtin"]').value;
    const fecha = document.querySelector('input[name="fecha"]').value;
    const cantidad = document.querySelector('input[name="cantidad"]').value;

    if (!/^\d{18}$/.test(sscc)) { alert("SSCC debe tener 18 dígitos"); return false; }
    if (!/^\d{14}$/.test(gtin)) { alert("GTIN debe tener 14 dígitos"); return false; }
    if (!/^\d{2}\/\d{2}\/\d{4}$/.test(fecha)) { alert("Fecha debe ser DD/MM/AAAA"); return false; }
    if (parseInt(cantidad) < 1) { alert("Cantidad mínima es 1"); return false; }
    return true;
}
