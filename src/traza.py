"""Traza de una sesión: texto, tokens, estructura, tabla, acción y resultado."""


def _mostrar(valor) -> str:
    if valor is None:
        return "—"
    return str(valor)


def formatear(eventos: list[dict]) -> str:
    lineas = []
    for evento in eventos:
        tipo = evento["tipo"]
        if tipo == "texto":
            lineas.append(
                f"--- Turno {evento['turno']} {evento['rol']} ---\nTexto original: {evento['texto']}"
            )
        elif tipo == "tokens":
            piezas = "\n".join(f"  {pieza}" for pieza in evento["piezas"]) or "  (sin tokens)"
            lineas.append(f"Tokens:\n{piezas}")
        elif tipo == "estructura":
            if evento["clausulas"]:
                cuerpo = "\n".join(f"  {clausula}" for clausula in evento["clausulas"])
            else:
                cuerpo = "  (ninguna)"
            lineas.append(f"Estructura reconocida:\n{cuerpo}")
        elif tipo == "tabla":
            turno = evento.get("turno") or 0
            prefijo = f"t{turno} " if turno else ""
            lineas.append(f"Tabla: {prefijo}{evento['op']} {evento['clave']} — {evento['detalle']}")
        elif tipo == "semantica":
            lineas.append(
                "Acción semántica: "
                f"{evento['regla']} actor={evento['actor']} aspecto={_mostrar(evento['aspecto'])} "
                f"valoracion={_mostrar(evento['valoracion'])} efecto={_mostrar(evento['efecto'])} "
                f"negado={evento['negado']} «{evento['fragmento']}»"
            )
        elif tipo == "error_sintactico":
            lineas.append(f"Error sintáctico t{evento['turno']}: {evento['mensaje']}")
        elif tipo == "rechazo":
            lineas.append(f"Rechazo línea {evento['linea']} ({evento['motivo']}): {evento['texto']}")
        elif tipo == "resultado":
            resumen = ", ".join(f"{aspecto} {valor}" for aspecto, valor in evento["resumen"].items())
            lineas.append(
                f"Resultado: análisis {evento['analisis']}; estado {evento['estado']}; {resumen}"
            )
    return "\n".join(lineas) + ("\n" if lineas else "")
