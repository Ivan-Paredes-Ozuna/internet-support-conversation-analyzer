"""Analizador léxico del texto de un turno.

Prioridad: ticket (AFD), número, «no», coincidencia exacta del diccionario y,
si no hay coincidencia, Levenshtein contra los lemas de contenido.
"""

import re
from dataclasses import dataclass

from src.afd_ticket import acepta
from src.diccionario import Diccionario
from src.normalizacion import normalizar

_PATRON_PIEZA = re.compile(r"[0-9]+|[A-Za-zÁÉÍÓÚÜüáéíóúñÑ]+(?:-[A-Za-z0-9]+)*")


@dataclass
class Token:
    tipo: str
    lexema: str
    normalizado: str
    sesion: str
    turno: int
    desplazamiento: int
    correccion: dict | None = None
    abstencion: list[str] | None = None


def tokenizar(texto: str, diccionario: Diccionario, sesion: str, turno: int) -> list[Token]:
    tokens = []
    for coincidencia in _PATRON_PIEZA.finditer(texto):
        lexema = coincidencia.group(0)
        tokens.append(
            _clasificar(
                lexema,
                coincidencia.start(),
                diccionario,
                sesion,
                turno,
            )
        )
    return tokens


def _clasificar(
    lexema: str,
    desplazamiento: int,
    diccionario: Diccionario,
    sesion: str,
    turno: int,
) -> Token:
    forma = normalizar(lexema)
    base = dict(
        lexema=lexema,
        sesion=sesion,
        turno=turno,
        desplazamiento=desplazamiento,
    )

    if acepta(lexema):
        return Token(tipo="TICKET", normalizado=lexema.upper(), **base)

    if forma.isdigit() or forma == "no":
        tipo = "NUMERO" if forma.isdigit() else diccionario.exactos.get(forma, "NO")
        return Token(tipo=tipo, normalizado=forma, **base)

    if forma in diccionario.exactos:
        return Token(tipo=diccionario.exactos[forma], normalizado=forma, **base)

    candidatos = diccionario.candidatos_a_uno(forma)
    if len(candidatos) == 1:
        lema = candidatos[0]
        return Token(
            tipo=diccionario.correccion[lema],
            normalizado=lema,
            correccion={"original": forma, "corregido": lema, "distancia": 1},
            **base,
        )
    if len(candidatos) > 1:
        return Token(tipo="PALABRA", normalizado=forma, abstencion=candidatos, **base)
    return Token(tipo="PALABRA", normalizado=forma, **base)
