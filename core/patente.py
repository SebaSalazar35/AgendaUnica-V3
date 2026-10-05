import re

# Patente nueva: ABCD12   patente vieja: AB1234
nueva = re.compile(r"^[A-Z]{4}\d{2}$")
vieja = re.compile(r"^[A-Z]{2}\d{4}$")


def normalizar_patente(texto):
    # Paso todo a mayuscula y saco espacios o guiones
    limpia = (texto or "").upper().strip()
    resultado = ""
    for c in limpia:
        if c.isalnum():
            resultado = resultado + c
    return resultado


def patente_valida(texto):
    patente = normalizar_patente(texto)
    if nueva.match(patente):
        return True
    if vieja.match(patente):
        return True
    return False
