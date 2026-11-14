"""Acciones semánticas y el criterio de resumen y estado.

Cada acción corresponde a una producción. La negación no se hereda a través de
«pero»: el parser llama a la acción de la cláusula negada con negado=True y a
la siguiente cláusula con negado=False.
"""

from dataclasses import dataclass

ASPECTOS = ("SERVICIO", "ATENCION", "CLARIDAD")
EFECTOS_FALLA = frozenset({"FALLA", "CORTE", "RECURRENCIA"})


@dataclass
class Atributos:
    regla: str
    actor: str
    fragmento: str
    aspecto: str | None = None
    valoracion: str | None = None
    efecto: str | None = None
    negado: bool = False


def _base(regla: str, actor: str, fragmento: str, **extra) -> Atributos:
    return Atributos(regla=regla, actor=actor, fragmento=fragmento, **extra)


def r1_servicio_negativo(actor: str, fragmento: str) -> Atributos:
    return _base("R1", actor, fragmento, aspecto="SERVICIO", valoracion="NEGATIVA", efecto="FALLA")


def r2_ahora_funciona(actor: str, fragmento: str) -> Atributos:
    return _base("R2", actor, fragmento, aspecto="SERVICIO", valoracion="POSITIVA", efecto="RECUPERACION")


def r3_funciona(actor: str, fragmento: str) -> Atributos:
    return _base("R3", actor, fragmento, aspecto="SERVICIO", valoracion="POSITIVA", efecto="RECUPERACION")


def r4_no_funciona(actor: str, fragmento: str) -> Atributos:
    return _base(
        "R4",
        actor,
        fragmento,
        aspecto="SERVICIO",
        valoracion="NEGATIVA",
        efecto="FALLA",
        negado=True,
    )


def r5_se_corta(actor: str, fragmento: str) -> Atributos:
    return _base("R5", actor, fragmento, aspecto="SERVICIO", valoracion="NEGATIVA", efecto="CORTE")


def r6_se_corta_recurrente(actor: str, fragmento: str) -> Atributos:
    return _base(
        "R6",
        actor,
        fragmento,
        aspecto="SERVICIO",
        valoracion="NEGATIVA",
        efecto="RECURRENCIA",
    )


def r7_sigue_negativo(actor: str, fragmento: str) -> Atributos:
    return _base("R7", actor, fragmento, aspecto="SERVICIO", valoracion="NEGATIVA", efecto="FALLA")


def r8_sigo_sin(actor: str, fragmento: str) -> Atributos:
    return _base("R8", actor, fragmento, aspecto="SERVICIO", valoracion="NEGATIVA", efecto="FALLA")


def r9_atencion_positiva(actor: str, fragmento: str) -> Atributos:
    return _base("R9", actor, fragmento, aspecto="ATENCION", valoracion="POSITIVA")


def r10_agente_amable(actor: str, fragmento: str) -> Atributos:
    return _base("R10", actor, fragmento, aspecto="ATENCION", valoracion="POSITIVA")


def r11_no_entendi(actor: str, fragmento: str) -> Atributos:
    return _base(
        "R11",
        actor,
        fragmento,
        aspecto="CLARIDAD",
        valoracion="NEGATIVA",
        negado=True,
    )


def r12_solicitud(actor: str, fragmento: str) -> Atributos:
    return _base("R12", actor, fragmento, efecto="SOLICITUD")


def r13_compromiso(actor: str, fragmento: str) -> Atributos:
    return _base("R13", actor, fragmento, efecto="COMPROMISO")


def r14_cortesia(actor: str, fragmento: str) -> Atributos:
    return _base("R14", actor, fragmento, efecto="CORTESIA")


def r15_no_interpretado(actor: str, fragmento: str) -> Atributos:
    return _base("R15", actor, fragmento)


def r16_atencion_nominal(actor: str, fragmento: str) -> Atributos:
    return _base("R16", actor, fragmento, aspecto="ATENCION", valoracion="POSITIVA")


def r17_servicio_bien(actor: str, fragmento: str) -> Atributos:
    return _base("R17", actor, fragmento, aspecto="SERVICIO", valoracion="POSITIVA", efecto="RECUPERACION")


def r18_mencion_neutra(actor: str, fragmento: str, aspecto: str) -> Atributos:
    return _base("R18", actor, fragmento, aspecto=aspecto, valoracion="NEUTRA")


def resumir(turnos) -> dict[str, str]:
    """Resumen por aspecto usando solo evidencia del cliente. No promedia ni cancela."""
    acumulado = {aspecto: set() for aspecto in ASPECTOS}
    for turno in turnos:
        if turno.rol != "CLIENTE":
            continue
        for clausula in turno.clausulas:
            if clausula.aspecto in acumulado and clausula.valoracion in {"POSITIVA", "NEGATIVA", "NEUTRA"}:
                acumulado[clausula.aspecto].add(clausula.valoracion)
    resumen = {}
    for aspecto, valores in acumulado.items():
        polares = valores & {"POSITIVA", "NEGATIVA"}
        if polares == {"POSITIVA", "NEGATIVA"}:
            resumen[aspecto] = "MIXTA"
        elif polares == {"POSITIVA"}:
            resumen[aspecto] = "POSITIVA"
        elif polares == {"NEGATIVA"}:
            resumen[aspecto] = "NEGATIVA"
        elif "NEUTRA" in valores:
            resumen[aspecto] = "NEUTRA"
        else:
            resumen[aspecto] = "SIN_EVIDENCIA"
    return resumen


def _veredicto(clausulas) -> str | None:
    efectos = [clausula.efecto for clausula in clausulas]
    hay_recuperacion = "RECUPERACION" in efectos
    hay_falla = any(efecto in EFECTOS_FALLA for efecto in efectos)
    if hay_recuperacion and hay_falla:
        return "MIXTO"
    if hay_recuperacion:
        return "POS"
    if hay_falla:
        return "NEG"
    return None


def inferir_estado(turnos) -> str:
    """La última declaración del cliente sobre el funcionamiento manda.

    Un compromiso del agente solo produce PENDIENTE cuando el cliente no dijo
    nada sobre el funcionamiento. Recuperación y falla en el mismo enunciado
    (unidas por «pero») son TEMPORAL, no RESUELTO.
    """
    ultimo = None
    hay_compromiso = False
    for turno in turnos:
        for clausula in turno.clausulas:
            if clausula.efecto == "COMPROMISO":
                hay_compromiso = True
        if turno.rol != "CLIENTE":
            continue
        veredicto = _veredicto(turno.clausulas)
        if veredicto is not None:
            ultimo = veredicto
    if ultimo == "POS":
        return "RESUELTO"
    if ultimo == "NEG":
        return "NO_RESUELTO"
    if ultimo == "MIXTO":
        return "TEMPORAL"
    if hay_compromiso:
        return "PENDIENTE"
    return "NO_CONFIRMADO"
