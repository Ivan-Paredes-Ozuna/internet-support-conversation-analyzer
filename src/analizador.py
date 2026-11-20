"""Separa sesiones, recupera turnos inválidos y dispara el resto del pipeline."""

import re
from dataclasses import dataclass, field
from pathlib import Path

from src.diccionario import Diccionario, cargar
from src.lexer import tokenizar
from src.parser import Parser
from src.semantica import inferir_estado, resumir
from src.tabla_simbolos import TablaSimbolos

_RE_SESION = re.compile(r"^SESION\s+(S\d+[A-Za-z0-9]*)\s*$")
_RE_FIN = re.compile(r"^FIN\s*$")
_RE_TURNO = re.compile(r"^(\d+)\s+(\S+)\s*:\s*(.*)$")
_ROLES = frozenset({"CLIENTE", "AGENTE"})


@dataclass
class TurnoAnalizado:
    numero: int
    rol: str
    texto: str
    clausulas: list
    no_interpretados: list[str]
    correcciones: list[dict]
    abstenciones: list[dict]
    tokens: list
    errores_sintacticos: list


@dataclass
class SesionAnalizada:
    id: str
    analisis: str
    turnos: list[TurnoAnalizado]
    errores: list[dict]
    resumen: dict
    estado: str
    tabla: TablaSimbolos
    eventos: list = field(default_factory=list)


@dataclass
class Resultado:
    sesiones: list[SesionAnalizada]
    errores_fuera: list[dict] = field(default_factory=list)


def analizar_texto(texto: str, diccionario: Diccionario | None = None) -> Resultado:
    vocabulario = diccionario if diccionario is not None else cargar()
    return _analizar_lineas(texto.splitlines(), vocabulario)


def analizar_archivo(ruta: Path, diccionario: Diccionario | None = None) -> Resultado:
    texto = Path(ruta).read_text(encoding="utf-8-sig")
    return analizar_texto(texto, diccionario)


def analizar_rutas(rutas: list[Path], diccionario: Diccionario | None = None) -> Resultado:
    vocabulario = diccionario if diccionario is not None else cargar()
    sesiones: list[SesionAnalizada] = []
    errores_fuera: list[dict] = []
    for ruta in rutas:
        resultado = analizar_archivo(ruta, vocabulario)
        sesiones.extend(resultado.sesiones)
        for error in resultado.errores_fuera:
            error = dict(error)
            error["archivo"] = str(ruta)
            errores_fuera.append(error)
    return Resultado(sesiones=sesiones, errores_fuera=errores_fuera)


def _analizar_lineas(lineas: list[str], diccionario: Diccionario) -> Resultado:
    sesiones: list[SesionAnalizada] = []
    errores_fuera: list[dict] = []
    actual: dict | None = None

    def cerrar(fin_ausente: bool) -> None:
        nonlocal actual
        if actual is None:
            return
        if fin_ausente:
            actual["errores"].append(
                {
                    "linea": actual["linea_inicio"],
                    "tipo": "FIN_AUSENTE",
                    "texto": f"SESION {actual['id']}",
                }
            )
        sesiones.append(_cerrar_sesion(actual))
        actual = None

    for numero_linea, cruda in enumerate(lineas, start=1):
        linea = cruda.strip()
        if actual is None:
            if not linea:
                continue
            sesion = _RE_SESION.fullmatch(linea)
            if sesion:
                actual = _nueva_sesion(sesion.group(1), numero_linea)
                continue
            if _RE_FIN.fullmatch(linea):
                errores_fuera.append({"linea": numero_linea, "tipo": "FIN_SIN_SESION", "texto": linea})
                continue
            errores_fuera.append({"linea": numero_linea, "tipo": "LINEA_FUERA_DE_SESION", "texto": linea})
            continue

        if not linea:
            actual["errores"].append({"linea": numero_linea, "tipo": "LINEA_EN_BLANCO", "texto": ""})
            continue
        if _RE_FIN.fullmatch(linea):
            cerrar(fin_ausente=False)
            continue
        if _RE_SESION.fullmatch(linea):
            cerrar(fin_ausente=True)
            abierta = _RE_SESION.fullmatch(linea)
            actual = _nueva_sesion(abierta.group(1), numero_linea)
            continue

        turno = _RE_TURNO.fullmatch(linea)
        if not turno:
            actual["errores"].append({"linea": numero_linea, "tipo": "LINEA_INVALIDA", "texto": linea})
            actual["eventos"].append(
                {"tipo": "rechazo", "linea": numero_linea, "motivo": "LINEA_INVALIDA", "texto": linea}
            )
            continue

        numero = int(turno.group(1))
        rol = turno.group(2)
        texto = turno.group(3).strip()
        if numero != actual["esperado"]:
            actual["errores"].append({"linea": numero_linea, "tipo": "ORDEN_INCONSISTENTE", "texto": linea})
            actual["eventos"].append(
                {
                    "tipo": "rechazo",
                    "linea": numero_linea,
                    "motivo": "ORDEN_INCONSISTENTE",
                    "texto": linea,
                }
            )
            actual["esperado"] = numero + 1
            continue
        if rol not in _ROLES:
            actual["errores"].append({"linea": numero_linea, "tipo": "ROL_INVALIDO", "texto": linea})
            actual["eventos"].append(
                {"tipo": "rechazo", "linea": numero_linea, "motivo": "ROL_INVALIDO", "texto": linea}
            )
            actual["esperado"] = numero + 1
            continue
        if not texto:
            actual["errores"].append({"linea": numero_linea, "tipo": "TEXTO_VACIO", "texto": linea})
            actual["eventos"].append(
                {"tipo": "rechazo", "linea": numero_linea, "motivo": "TEXTO_VACIO", "texto": linea}
            )
            actual["esperado"] = numero + 1
            continue

        actual["turnos"].append(_analizar_turno(actual, numero, rol, texto, diccionario))
        actual["esperado"] = numero + 1

    cerrar(fin_ausente=actual is not None)
    return Resultado(sesiones=sesiones, errores_fuera=errores_fuera)


def _nueva_sesion(identificador: str, linea_inicio: int) -> dict:
    eventos: list = []
    tabla = TablaSimbolos(identificador, registro=eventos)
    tabla.turno_actual = 0
    tabla.asegurar(identificador, "sesion")
    return {
        "id": identificador,
        "linea_inicio": linea_inicio,
        "esperado": 1,
        "turnos": [],
        "errores": [],
        "tabla": tabla,
        "eventos": eventos,
    }


def _analizar_turno(actual: dict, numero: int, rol: str, texto: str, diccionario: Diccionario) -> TurnoAnalizado:
    tabla: TablaSimbolos = actual["tabla"]
    eventos: list = actual["eventos"]
    ops: list = []
    tabla.registro = ops
    tabla.turno_actual = numero

    tokens = tokenizar(texto, diccionario, actual["id"], numero)
    tabla.asegurar(rol, "participante", {"turno": numero, "desplazamiento": 0})
    parser = Parser(tokens, tabla, numero, rol)
    clausulas = parser.parsear()

    correcciones = []
    abstenciones = []
    for token in tokens:
        if token.correccion:
            correcciones.append(
                {
                    "turno": numero,
                    "original": token.lexema,
                    "corregido": token.correccion["corregido"],
                    "distancia": token.correccion["distancia"],
                }
            )
        if token.abstencion:
            abstenciones.append(
                {
                    "turno": numero,
                    "original": token.lexema,
                    "candidatos": list(token.abstencion),
                }
            )

    eventos.append({"tipo": "texto", "sesion": actual["id"], "turno": numero, "rol": rol, "texto": texto})
    eventos.append(
        {
            "tipo": "tokens",
            "sesion": actual["id"],
            "turno": numero,
            "piezas": [_describir_token(token) for token in tokens],
        }
    )
    eventos.append(
        {
            "tipo": "estructura",
            "sesion": actual["id"],
            "turno": numero,
            "clausulas": [_describir_clausula(clausula) for clausula in clausulas],
            "no_interpretados": list(parser.no_interpretados),
        }
    )
    for error in parser.errores:
        eventos.append(
            {
                "tipo": "error_sintactico",
                "sesion": actual["id"],
                "turno": numero,
                "mensaje": error["mensaje"],
            }
        )
    eventos.extend(ops)
    for clausula in clausulas:
        eventos.append(
            {
                "tipo": "semantica",
                "sesion": actual["id"],
                "turno": numero,
                "regla": clausula.regla,
                "actor": clausula.actor,
                "aspecto": clausula.aspecto,
                "valoracion": clausula.valoracion,
                "efecto": clausula.efecto,
                "negado": clausula.negado,
                "fragmento": clausula.fragmento,
            }
        )

    return TurnoAnalizado(
        numero=numero,
        rol=rol,
        texto=texto,
        clausulas=clausulas,
        no_interpretados=list(parser.no_interpretados),
        correcciones=correcciones,
        abstenciones=abstenciones,
        tokens=tokens,
        errores_sintacticos=list(parser.errores),
    )


def _cerrar_sesion(actual: dict) -> SesionAnalizada:
    resumen = resumir(actual["turnos"])
    estado = inferir_estado(actual["turnos"])
    analisis = "parcial" if actual["errores"] else "completo"
    actual["eventos"].append(
        {
            "tipo": "resultado",
            "sesion": actual["id"],
            "analisis": analisis,
            "estado": estado,
            "resumen": resumen,
        }
    )
    return SesionAnalizada(
        id=actual["id"],
        analisis=analisis,
        turnos=actual["turnos"],
        errores=actual["errores"],
        resumen=resumen,
        estado=estado,
        tabla=actual["tabla"],
        eventos=actual["eventos"],
    )


def _describir_token(token) -> str:
    nota = ""
    if token.correccion:
        nota = f" corrección→{token.correccion['corregido']}"
    elif token.abstencion:
        nota = " empate→" + ",".join(token.abstencion)
    return (
        f"{token.tipo} '{token.lexema}'→{token.normalizado} "
        f"@{token.sesion}/t{token.turno}/d{token.desplazamiento}{nota}"
    )


def _mostrar(valor) -> str:
    if valor is None:
        return "—"
    return str(valor)


def _describir_clausula(clausula) -> str:
    return (
        f"{clausula.regla} aspecto={_mostrar(clausula.aspecto)} valoracion={_mostrar(clausula.valoracion)} "
        f"efecto={_mostrar(clausula.efecto)} negado={clausula.negado} «{clausula.fragmento}»"
    )
