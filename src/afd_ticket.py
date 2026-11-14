"""AFD de la categoría TICKET.

Expresión regular: TK-[0-9]{3,6}

El autómata se construye directo desde la expresión (el prefijo es fijo y los
dígitos repiten entre tres y seis veces). Acepta solo si toda la cadena termina
en un estado de aceptación. La letra se compara en mayúsculas.
"""

ESTADOS_ACEPTACION = frozenset({"q3", "q4", "q5", "q6"})

# (estado, símbolo) -> estado. «d» representa cualquier dígito.
TRANSICIONES = {
    ("q0", "T"): "qT",
    ("qT", "K"): "qK",
    ("qK", "-"): "qH",
    ("qH", "d"): "q1",
    ("q1", "d"): "q2",
    ("q2", "d"): "q3",
    ("q3", "d"): "q4",
    ("q4", "d"): "q5",
    ("q5", "d"): "q6",
}


def _simbolo(caracter: str) -> str:
    if caracter.isdigit():
        return "d"
    return caracter


def transicion(estado: str, caracter: str) -> str:
    return TRANSICIONES.get((estado, _simbolo(caracter)), "qM")


def acepta(cadena: str) -> bool:
    """True si la cadena completa es un ticket TK- con 3 a 6 dígitos."""
    estado = "q0"
    if not cadena:
        return False
    for caracter in cadena.upper():
        estado = transicion(estado, caracter)
        if estado == "qM":
            return False
    return estado in ESTADOS_ACEPTACION
