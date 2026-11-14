"""Normalización para clasificar, sin perder el lexema original."""

import unicodedata


def normalizar(texto: str) -> str:
    """Minúsculas y sin marcas diacríticas: «está» queda «esta»."""
    minusculas = texto.lower()
    descompuesto = unicodedata.normalize("NFKD", minusculas)
    return "".join(caracter for caracter in descompuesto if not unicodedata.combining(caracter))
