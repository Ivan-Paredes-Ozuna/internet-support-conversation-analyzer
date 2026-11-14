"""Genera el PDF del informe técnico. No forma parte del analizador.

Requiere fpdf2 solo para este script:
    python3 -m pip install fpdf2
    python3 herramientas/generar_informe_pdf.py
"""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))

from fpdf import FPDF
from fpdf.fonts import FontFace

from src.analizador import analizar_archivo
from src.salida import sesion_a_dict

ARIAL = "/System/Library/Fonts/Supplemental/Arial.ttf"
ARIAL_B = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
ARIAL_I = "/System/Library/Fonts/Supplemental/Arial Italic.ttf"
COURIER = "/System/Library/Fonts/Supplemental/Courier New.ttf"
SALIDA = RAIZ / "entrega" / "Informe_tecnico_TP1.pdf"

CASOS = [
    ("01", "casos/guia/caso01.txt", "Servicio lento y luego «ahora funciona bien».", "SERVICIO MIXTA; RESUELTO."),
    ("02", "casos/guia/caso02.txt", "«Muy bien, pero sigo sin internet».", "ATENCION POSITIVA; SERVICIO NEGATIVA; NO_RESUELTO."),
    ("03", "casos/guia/caso03.txt", "«Funciona, pero se corta todos los días».", "SERVICIO MIXTA; TEMPORAL."),
    ("04", "casos/guia/caso04.txt", "«No entendí» y «el agente fue amable».", "CLARIDAD NEGATIVA; ATENCION POSITIVA; NO_CONFIRMADO."),
    ("05", "casos/guia/caso05.txt", "«lentto» y mención de TK-204.", "Corrige a lento; conserva TK-204; SERVICIO NEGATIVA; NO_RESUELTO."),
    ("06", "casos/guia/caso06.txt", "El agente revisará mañana; el cliente dice gracias.", "PENDIENTE; aspectos SIN_EVIDENCIA."),
    ("07", "casos/guia/caso07.txt", "Rol SOPORTE entre dos turnos válidos, y otra sesión.", "Rechaza el turno; la primera sesión queda parcial; la segunda sigue."),
    ("08", "casos/guia/caso08.txt", "«lent» con los lemas lenta y lento.", "Empate a distancia 1; no corrige; SIN_EVIDENCIA."),
    ("09", "casos/propios/caso09.txt", "Negación y contraste: no funciona, pero la atención fue muy buena.", "SERVICIO NEGATIVA; ATENCION POSITIVA; NO_RESUELTO."),
    ("10", "casos/propios/caso10.txt", "Corrección única de «conxion».", "Corrige a conexion; SERVICIO NEGATIVA; NO_RESUELTO."),
    ("11", "casos/propios/caso11.txt", "El turno 3 llega sin el turno 2.", "Rechaza ese turno y no usa «funciona bien»; sesión parcial."),
    ("12", "casos/propios/caso12.txt", "Regresión: el sinónimo conexión / lenta, luego funciona bien.", "Igual que el 01: SERVICIO MIXTA; RESUELTO."),
]


def _obtenido(ruta: Path) -> str:
    resultado = analizar_archivo(ruta)
    frases = []
    for sesion in resultado.sesiones:
        datos = sesion_a_dict(sesion)
        resumen = datos["resumen_por_aspecto"]
        presentes = [f"{aspecto} {valor}" for aspecto, valor in resumen.items() if valor != "SIN_EVIDENCIA"]
        if not presentes:
            presentes = ["aspectos SIN_EVIDENCIA"]
        frase = f"{sesion.id}: {', '.join(presentes)}; {datos['estado']}"
        if datos["analisis"] == "parcial":
            tipos = ", ".join(error["tipo"] for error in datos["errores"])
            frase += f"; parcial ({tipos})"
        if datos["correcciones"]:
            correccion = datos["correcciones"][0]
            frase += f"; {correccion['original']} → {correccion['corregido']}"
        if datos["abstenciones"]:
            frase += "; empate, sin corrección"
        if datos["entidades"]["tickets"]:
            frase += "; " + ", ".join(ticket["id"] for ticket in datos["entidades"]["tickets"])
        frases.append(frase)
    return " ".join(frases)


class Informe(FPDF):
    def __init__(self):
        super().__init__(format="A4", unit="mm")
        self.add_font("Arial", "", ARIAL)
        self.add_font("Arial", "B", ARIAL_B)
        self.add_font("Arial", "I", ARIAL_I)
        self.add_font("Mono", "", COURIER)
        self.set_margins(18, 16, 18)
        self.set_auto_page_break(auto=True, margin=18)
        self.set_title("Informe técnico — TP 1 — Análisis de conversaciones de soporte")
        self.set_author("Diseño de Compiladores, FPUNA, 2026/2")

    def header(self):
        if self.page_no() == 1:
            return
        self.set_font("Arial", "", 8)
        self.set_text_color(90, 90, 90)
        self.cell(0, 6, "FPUNA  ·  Diseño de Compiladores  ·  TP 1  ·  2026/2", align="L", new_x="LMARGIN", new_y="NEXT")
        self.ln(2)
        self.set_text_color(0, 0, 0)

    def footer(self):
        self.set_y(-14)
        self.set_font("Arial", "", 8)
        self.set_text_color(90, 90, 90)
        self.cell(0, 8, str(self.page_no()), align="C", new_x="LMARGIN", new_y="NEXT")
        self.set_text_color(0, 0, 0)

    def titulo(self, texto: str) -> None:
        self.ln(2)
        self.set_font("Arial", "B", 13)
        self.multi_cell(0, 7, texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def subtitulo(self, texto: str) -> None:
        self.ln(1)
        self.set_font("Arial", "B", 11)
        self.multi_cell(0, 6, texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(0.5)

    def parrafo(self, texto: str) -> None:
        self.set_font("Arial", "", 10.5)
        self.multi_cell(0, 5.2, texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(1.4)

    def item(self, texto: str) -> None:
        self.set_font("Arial", "", 10.5)
        self.multi_cell(0, 5.2, "•  " + texto, new_x="LMARGIN", new_y="NEXT")
        self.ln(0.4)

    def mono(self, texto: str) -> None:
        self.set_font("Mono", "", 8)
        for linea in texto.splitlines():
            self.multi_cell(0, 3.8, linea if linea else " ", new_x="LMARGIN", new_y="NEXT")
        self.ln(1.5)
        self.set_font("Arial", "", 10.5)


def construir() -> Informe:
    pdf = Informe()
    pdf.add_page()
    pdf.set_font("Arial", "", 10)
    pdf.set_text_color(80, 80, 80)
    pdf.cell(0, 5, "Facultad Politécnica — Universidad Nacional de Asunción", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.cell(0, 5, "Diseño de Compiladores  ·  Segundo período 2026", align="L", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(4)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", "B", 18)
    pdf.multi_cell(0, 8, "Trabajo práctico 1", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("Arial", "B", 14)
    pdf.multi_cell(0, 7, "Análisis de conversaciones de soporte de Internet", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 6, "Informe técnico, casos con resultado obtenido, traza y declaración de herramientas.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)
    pdf.multi_cell(0, 6, "Entrega y defensa: jueves 19/11/2026.", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(2)
    pdf.set_font("Arial", "I", 10)
    pdf.multi_cell(
        0,
        5,
        "La sección 8 del enunciado pide un informe breve, los casos con resultado esperado y obtenido, "
        "un JSON de ejemplo, la evidencia de una traza, el README y la declaración de bibliotecas e IA. "
        "No pide un PDF distinto por cada ítem. Este documento reúne la parte escrita. "
        "El código, el diccionario y el comando de ejecución están en el repositorio.",
        new_x="LMARGIN",
        new_y="NEXT",
    )
    pdf.ln(2)

    pdf.titulo("1. Objetivo")
    pdf.parrafo(
        "El programa es un procesador determinista de texto. Lee una o varias sesiones de soporte, "
        "identifica valoraciones de SERVICIO, ATENCION y CLARIDAD, infiere el estado conversacional "
        "y conserva la evidencia de cada decisión. El dominio queda en falta de conexión, lentitud, "
        "cortes, reinicio del router y seguimiento de tickets. No interpreta español libre, ironía ni audio."
    )
    pdf.parrafo(
        "Al ejecutarse no consulta un modelo. Las etiquetas salen del léxico, de la gramática y de las "
        "reglas semánticas. El diccionario de vocabulario y la tabla de símbolos son estructuras distintas."
    )

    pdf.titulo("2. Léxico y normalización")
    pdf.parrafo(
        "Para clasificar, cada pieza pasa a minúsculas y pierde las tildes: «está» queda «esta». "
        "El lexema original se conserva. Cada token lleva sesión, turno y desplazamiento dentro del texto del turno."
    )
    pdf.parrafo("El orden de clasificación es fijo:")
    pdf.item("Ticket TK- y de tres a seis dígitos, reconocido por un autómata finito determinista.")
    pdf.item("Número, o la palabra «no». Esas piezas no se corrigen.")
    pdf.item("Coincidencia exacta con el vocabulario.")
    pdf.item("Si no hay coincidencia, distancia de Levenshtein contra los lemas de contenido.")
    pdf.parrafo(
        "Los lemas de contenido cubren el dominio: servicio, internet, conexión, router, lento, lenta, "
        "funciona, corta, atendiste, amable, entendí, explicación, reinicie, revisaremos, y sus formas "
        "cerradas (artículos, «pero», «muy», «sin», «ahora», «gracias»). «lenta» y «lento» conviven a propósito, "
        "para que «lent» empate y no se corrija."
    )

    pdf.subtitulo("Expresión regular y AFD del ticket")
    pdf.parrafo("Categoría mostrada con el procedimiento de la materia: una expresión regular y su autómata.")
    pdf.mono("TK-[0-9]{3,6}")
    pdf.parrafo(
        "El prefijo TK- es una cadena fija y los dígitos forman un lazo acotado. Menos de tres dígitos "
        "no acepta. Un séptimo dígito, o cualquier otro símbolo, cae al estado muerto. Aceptan q3, q4, q5 y q6, "
        "y solo si se consumió toda la cadena. La comparación es en mayúsculas: tk-204 es el ticket TK-204."
    )
    pdf.mono(
        "q0 -T-> qT -K-> qK --> qH -d-> q1 -d-> q2 -d-> q3* -d-> q4* -d-> q5* -d-> q6*\n"
        "* = aceptación (3 a 6 dígitos).  d = un dígito.  Otro símbolo -> qM."
    )

    pdf.titulo("3. Corrección ortográfica")
    pdf.parrafo(
        "La distancia de Levenshtein usa costo 1 para inserción, borrado y sustitución. "
        "Hay reemplazo automático solo cuando existe un único lema de contenido a distancia 1: "
        "«lentto» pasa a «lento», porque «lenta» queda a distancia 2. Si hay dos candidatos, como "
        "«lent» frente a «lenta» y «lento», se conserva el original y se anota el empate. "
        "No se modifican «no», los números ni los tickets."
    )

    pdf.titulo("4. Tabla de símbolos")
    pdf.parrafo(
        "Es una tabla hash con encadenamiento separado. La función es el polinomio "
        "h = h · 33 + código del carácter, módulo la capacidad de la tabla. Cada entrada guarda la clave, "
        "el tipo (sesión, participante o ticket) y las apariciones, con turno y desplazamiento."
    )
    pdf.item("buscar recorre la cubeta y compara la clave.")
    pdf.item("insertar rechaza la clave si ya existe.")
    pdf.item("actualizar agrega una aparición a la entrada que ya está.")
    pdf.parrafo(
        "El pipeline busca y, según el resultado, inserta o actualiza. Dos menciones de TK-204 quedan "
        "en una sola entrada. El ámbito es la sesión. El vocabulario no se mezcla con esta tabla."
    )

    pdf.titulo("5. Gramática y parser")
    pdf.parrafo(
        "Un enunciado es una cláusula, o dos unidas por «pero». Las construcciones se componen: "
        "«muy bien», «sin internet» y «todos los días» no son frases guardadas enteras. "
        "El parser es de descenso recursivo, con un token de anticipación."
    )
    pdf.mono(
        "Enunciado  -> Clausula Resto\n"
        "Resto      -> PERO Clausula Resto | ε\n"
        "Clausula   -> NO RestoNo | AHORA FUNCIONA BienOpt | SE Corte\n"
        "            | V_PERS RestoPers | Atencion | ART Nominal\n"
        "            | SUST_SERVICIO Predicado | V_SOLICITUD Objeto\n"
        "            | V_COMPROMISO TicketOpt | MANANA V_COMPROMISO TicketOpt\n"
        "            | FUNCIONA BienOpt | CORTESIA | Fragmento\n"
        "BienOpt    -> BIEN | ε\n"
        "Corte      -> CORTA (TODOS ART DIAS | ε)\n"
        "RestoPers  -> ADJ_NEG | SIN SUST_SERVICIO\n"
        "RestoNo    -> FUNCIONA objeto? | V_CLARIDAD objeto?"
    )
    pdf.parrafo(
        "La elección de Clausula es LL(1): el primer token alcanza, porque los conjuntos FIRST no se pisan. "
        "«no» abre la negación; «ahora», la recuperación; «se», el corte; «sigue» o «sigo», la persistencia; "
        "«me» o «atendiste», la atención; un artículo, el sintagma nominal; «reinicie», la solicitud; "
        "«revisaremos» o «mañana», el compromiso; «funciona», el funcionamiento; «gracias», la cortesía. "
        "Cualquier otro inicio es un fragmento."
    )
    pdf.parrafo(
        "FOLLOW de una cláusula es {pero, fin de turno}. «bien» y el ticket son opcionales: se consumen "
        "solo si el lookahead es ese token; si no, se reduce la producción vacía. «todos los días» se consume "
        "solo cuando están los tres tokens. El objeto de «no funciona» o «no entendí» se consume solo si "
        "vienen el artículo y el sustantivo esperado. Si la alternativa elegida no se puede terminar, "
        "se rebobina ese intento y el tramo queda como NO_INTERPRETADO, sin inventar una valoración."
    )

    pdf.titulo("6. Semántica, resumen y estado")
    pdf.parrafo(
        "Cada producción que cierra una cláusula dispara una acción. El actor es el rol del turno. "
        "La negación vale solo para esa cláusula: «pero» abre otra, con la negación en falso. "
        "«muy» intensifica y no cambia la polaridad. Una solicitud («reinicie el router») y la cortesía "
        "(«gracias») no son valoraciones. Un compromiso («mañana revisaremos») tampoco es una confirmación del cliente."
    )
    pdf.parrafo(
        "El resumen usa solo evidencia del cliente. Si un aspecto tiene valoración positiva y negativa, "
        "queda MIXTA: no se promedia ni se borra una de las dos. Sin evidencia interpretable, SIN_EVIDENCIA. "
        "La opinión del agente se guarda con su autor y no entra al resumen."
    )
    pdf.parrafo("El estado se decide por la última declaración del cliente sobre el funcionamiento:")
    pdf.item("solo recuperación: RESUELTO.")
    pdf.item("solo falla, corte o recurrencia: NO_RESUELTO.")
    pdf.item("recuperación y falla en el mismo enunciado: TEMPORAL. «Ahora funciona, pero se corta todos los días» no es RESUELTO.")
    pdf.item("si el cliente no habló del funcionamiento y hay un compromiso: PENDIENTE.")
    pdf.item("si no hay nada de eso: NO_CONFIRMADO.")
    pdf.parrafo(
        "Una promesa del agente no pisa lo que el cliente dijo. La sesión queda parcial solo si se rechazó "
        "la forma de un turno (rol inválido, número fuera de orden, línea en blanco o fin ausente). "
        "Un fragmento no interpretado no vuelve parcial a la sesión."
    )

    pdf.titulo("7. Casos: resultado esperado y obtenido")
    pdf.parrafo(
        "Los ocho primeros son los de la guía. Los cuatro últimos son del grupo: negación con contraste, "
        "corrección única, recuperación de un número fuera de orden, y regresión con el sinónimo «conexión». "
        "La columna obtenida la produce el programa sobre el archivo del caso."
    )

    pdf.set_font("Arial", "", 8.5)
    encabezado = FontFace(family="Arial", emphasis="BOLD", size_pt=8, fill_color=(32, 32, 32), color=(255, 255, 255))
    with pdf.table(
        col_widths=(8, 28, 32, 32),
        line_height=4.2,
        text_align="LEFT",
        headings_style=encabezado,
        padding=1.2,
        repeat_headings=1,
    ) as tabla:
        cabecera = tabla.row()
        cabecera.cell("Caso")
        cabecera.cell("Situación")
        cabecera.cell("Esperado")
        cabecera.cell("Obtenido")
        for numero, ruta, situacion, esperado in CASOS:
            fila = tabla.row()
            fila.cell(numero)
            fila.cell(situacion)
            fila.cell(esperado)
            fila.cell(_obtenido(RAIZ / ruta))
    pdf.ln(3)
    pdf.parrafo(
        "El caso 12 vuelve a pasar por las mismas reglas que el 01, con «conexión» y «lenta». "
        "Si se modifica una de esas reglas, la prueba de regresión tiene que seguir en MIXTA y RESUELTO. "
        "El JSON del lote está en ejemplos/salida.json y los archivos, en casos/."
    )

    pdf.titulo("8. Traza de la sesión S01")
    pdf.parrafo(
        "Orden pedido por el enunciado: texto original, tokens con posición, estructura reconocida, "
        "consulta e inserción en la tabla de símbolos, acción semántica y resultado. "
        "En el turno 3, CLIENTE ya existe: la tabla lo busca y lo actualiza, no lo duplica."
    )
    traza = (RAIZ / "ejemplos" / "traza_s01.txt").read_text(encoding="utf-8").strip()
    pdf.mono(traza)

    pdf.titulo("9. Cómo ejecutarlo")
    pdf.mono(
        "python3 -m src.main casos/ --json ejemplos/salida.json --traza S01\n"
        "python3 -m unittest discover -s pruebas -t ."
    )
    pdf.parrafo(
        "Hace falta Python 3.11 o posterior. El analizador no instala bibliotecas: usa solo la biblioteca estándar."
    )

    pdf.titulo("10. Bibliotecas e IA")
    pdf.parrafo(
        "Bibliotecas del analizador: ninguna fuera de la biblioteca estándar de Python "
        "(argparse, json, re, unicodedata, unittest, dataclasses y pathlib). "
        "fpdf2 se usó únicamente para componer este PDF; el programa que analiza las sesiones no la importa."
    )
    pdf.parrafo(
        "El código se generó con Cursor (modelo Grok) a partir del enunciado. La cátedra permite usar IA "
        "también para generar código. En ejecución el analizador no llama a un modelo ni reemplaza el parser "
        "por una consulta que devuelva las etiquetas."
    )
    return pdf


def main() -> None:
    SALIDA.parent.mkdir(parents=True, exist_ok=True)
    construir().output(SALIDA)
    print(SALIDA)


if __name__ == "__main__":
    main()
