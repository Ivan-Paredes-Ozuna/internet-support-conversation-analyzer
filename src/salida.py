"""Vista de consola y JSON de un lote."""

import json

from src.analizador import Resultado, SesionAnalizada


def sesion_a_dict(sesion: SesionAnalizada) -> dict:
    participantes = sorted(
        entrada.clave for entrada in sesion.tabla.entradas() if entrada.tipo == "participante"
    )
    tickets = [
        {"id": entrada.clave, "apariciones": [dict(aparicion) for aparicion in entrada.apariciones]}
        for entrada in sesion.tabla.entradas()
        if entrada.tipo == "ticket"
    ]
    tickets.sort(key=lambda ticket: ticket["id"])

    valoraciones = []
    evidencias = []
    correcciones = []
    abstenciones = []
    for turno in sesion.turnos:
        aspectos = []
        for clausula in turno.clausulas:
            if clausula.regla == "R15":
                continue
            evidencias.append(
                {
                    "turno": turno.numero,
                    "texto": clausula.fragmento,
                    "regla": clausula.regla,
                    "actor": clausula.actor,
                    "aspecto": clausula.aspecto,
                    "valoracion": clausula.valoracion,
                    "efecto": clausula.efecto,
                    "negado": clausula.negado,
                }
            )
            if clausula.aspecto and clausula.valoracion:
                aspectos.append(
                    {
                        "aspecto": clausula.aspecto,
                        "valoracion": clausula.valoracion,
                        "regla": clausula.regla,
                        "fragmento": clausula.fragmento,
                        "actor": clausula.actor,
                    }
                )
        valoraciones.append(
            {
                "turno": turno.numero,
                "rol": turno.rol,
                "texto": turno.texto,
                "aspectos": aspectos,
                "no_interpretados": list(turno.no_interpretados),
            }
        )
        correcciones.extend(turno.correcciones)
        abstenciones.extend(turno.abstenciones)

    return {
        "id": sesion.id,
        "analisis": sesion.analisis,
        "valoraciones_por_turno": valoraciones,
        "resumen_por_aspecto": sesion.resumen,
        "estado": sesion.estado,
        "entidades": {"participantes": participantes, "tickets": tickets},
        "correcciones": correcciones,
        "abstenciones": abstenciones,
        "errores": sesion.errores,
        "evidencias": evidencias,
    }


def resultado_a_dict(resultado: Resultado) -> dict:
    return {"sesiones": [sesion_a_dict(sesion) for sesion in resultado.sesiones]}


def a_json(resultado: Resultado) -> str:
    return json.dumps(resultado_a_dict(resultado), ensure_ascii=False, indent=2) + "\n"


def a_consola(resultado: Resultado) -> str:
    bloques = []
    for sesion in resultado.sesiones:
        datos = sesion_a_dict(sesion)
        lineas = [
            f"Sesión {datos['id']} — {datos['analisis']} — estado {datos['estado']}",
        ]
        for aspecto, valor in datos["resumen_por_aspecto"].items():
            lineas.append(f"  {aspecto}: {valor}")
        if datos["entidades"]["tickets"]:
            ids = ", ".join(ticket["id"] for ticket in datos["entidades"]["tickets"])
            lineas.append(f"  Tickets: {ids}")
        for correccion in datos["correcciones"]:
            lineas.append(
                f"  Corrección t{correccion['turno']}: {correccion['original']} → {correccion['corregido']}"
            )
        for abstencion in datos["abstenciones"]:
            candidatos = ", ".join(abstencion["candidatos"])
            lineas.append(
                f"  Empate t{abstencion['turno']}: {abstencion['original']} ({candidatos})"
            )
        for error in datos["errores"]:
            lineas.append(f"  Error línea {error['linea']}: {error['tipo']} — {error['texto']}")
        for turno in sesion.turnos:
            lineas.append(f"  Turno {turno.numero} {turno.rol}: {turno.texto}")
            for clausula in turno.clausulas:
                if clausula.regla == "R15":
                    continue
                negado = " negado" if clausula.negado else ""
                if clausula.aspecto and clausula.valoracion:
                    lineas.append(
                        f"    {clausula.aspecto} {clausula.valoracion} ({clausula.regla}{negado}) «{clausula.fragmento}»"
                    )
                elif clausula.efecto:
                    lineas.append(f"    {clausula.efecto} ({clausula.regla}) «{clausula.fragmento}»")
            for suelto in turno.no_interpretados:
                lineas.append(f"    NO_INTERPRETADO «{suelto}»")
        bloques.append("\n".join(lineas))
    if resultado.errores_fuera:
        avisos = ["Fuera de sesión:"]
        for error in resultado.errores_fuera:
            avisos.append(f"  línea {error['linea']}: {error['tipo']} — {error['texto']}")
        bloques.append("\n".join(avisos))
    if not bloques:
        return "Sin sesiones.\n"
    return "\n\n".join(bloques) + "\n"
