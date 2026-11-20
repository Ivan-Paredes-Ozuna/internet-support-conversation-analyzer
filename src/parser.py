"""Analizador sintáctico predictivo (ASP): pila, tabla LL(1) y un token de anticipación.

La cima de la pila decide el paso. Un terminal que coincide se consume. Un no
terminal se reemplaza por la producción que indica la tabla. Una acción
dispara la regla semántica de esa producción.

Un token fuera del FIRST de Clausula no es un error: es la producción
Fragmento (R15). Si la producción elegida no se puede terminar, el modo pánico
anota el error, descarta el tramo hasta «pero» o el fin del turno y sigue con
la cláusula siguiente. No emite la regla a medias.

CompServ, CompClar y RecurrenciaOpt miran uno o dos tokens más, como ya fija
la gramática: no consumen un artículo ni un «todos» que no cierra la construcción.
"""

from src.lexer import Token
from src.semantica import (
    r1_servicio_negativo,
    r2_ahora_funciona,
    r3_funciona,
    r4_no_funciona,
    r5_se_corta,
    r6_se_corta_recurrente,
    r7_sigue_negativo,
    r8_sigo_sin,
    r9_atencion_positiva,
    r10_agente_amable,
    r11_no_entendi,
    r12_solicitud,
    r13_compromiso,
    r14_cortesia,
    r15_no_interpretado,
    r16_atencion_nominal,
    r17_servicio_bien,
    r18_mencion_neutra,
)
from src.tabla_simbolos import TablaSimbolos

_FIN = frozenset({"PERO", "EOF"})

_REGLAS = {
    "R1": r1_servicio_negativo,
    "R2": r2_ahora_funciona,
    "R3": r3_funciona,
    "R4": r4_no_funciona,
    "R5": r5_se_corta,
    "R6": r6_se_corta_recurrente,
    "R7": r7_sigue_negativo,
    "R8": r8_sigo_sin,
    "R9": r9_atencion_positiva,
    "R10": r10_agente_amable,
    "R11": r11_no_entendi,
    "R12": r12_solicitud,
    "R13": r13_compromiso,
    "R14": r14_cortesia,
    "R16": r16_atencion_nominal,
    "R17": r17_servicio_bien,
}

# Qué anunciar cuando el no terminal no tiene producción para el lookahead.
_ESPERADO = {
    "RestoNo": "FUNCIONA o V_CLARIDAD",
    "RestoPers": "ADJ_NEG o SIN",
    "Resto": "PERO o fin de turno",
    "Polaridad": "ADJ_NEG o BIEN",
    "MuyAdj": "MUY, ADJ_ATENCION o BIEN",
    "AdjAt": "ADJ_ATENCION o BIEN",
    "Nominal": "SUST_SERVICIO, SUST_ATENCION, AGENTE_SUST o SUST_CLARIDAD",
    "Predicado": "COPULA, ADJ_NEG, BIEN o SE",
    "ObjetoSol": "ART o SUST_SERVICIO",
    "Corte": "CORTA",
    "Atencion": "ME o V_ATENCION",
    "Clausula": "una cláusula",
    "Enunciado": "una cláusula",
}


class Accion:
    """Símbolo de pila: al desapilarlo se ejecuta la regla de la producción."""

    def __init__(self, nombre: str, aspecto: str | None = None):
        self.nombre = nombre
        self.aspecto = aspecto

    def __repr__(self) -> str:
        return f"@{self.nombre}"


def _a(nombre: str, aspecto: str | None = None) -> Accion:
    return Accion(nombre, aspecto)


# Tabla LL(1). La clave es (no terminal, lookahead). El valor es la producción,
# de izquierda a derecha. La cadena vacía no se guarda: la decide _predecir.
TABLA: dict[tuple[str, str], tuple] = {
    ("Clausula", "NO"): ("NO", "RestoNo"),
    ("Clausula", "AHORA"): ("AHORA", "FUNCIONA", "BienOpt", _a("R2")),
    ("Clausula", "SE"): ("SE", "Corte"),
    ("Clausula", "V_PERS"): ("V_PERS", "RestoPers"),
    ("Clausula", "ME"): ("Atencion",),
    ("Clausula", "V_ATENCION"): ("Atencion",),
    ("Clausula", "ART"): ("ART", "Nominal"),
    ("Clausula", "SUST_SERVICIO"): ("SUST_SERVICIO", "Predicado"),
    ("Clausula", "V_SOLICITUD"): ("V_SOLICITUD", "ObjetoSol", _a("R12")),
    ("Clausula", "V_COMPROMISO"): ("V_COMPROMISO", "TicketOpt", _a("R13")),
    ("Clausula", "MANANA"): ("MANANA", "V_COMPROMISO", "TicketOpt", _a("R13")),
    ("Clausula", "FUNCIONA"): ("FUNCIONA", "BienOpt", _a("R3")),
    ("Clausula", "CORTESIA"): ("CORTESIA", _a("R14")),
    ("Resto", "PERO"): ("PERO", "Clausula", _a("sobrante"), "Resto"),
    ("RestoNo", "FUNCIONA"): ("FUNCIONA", "CompServ", _a("R4")),
    ("RestoNo", "V_CLARIDAD"): ("V_CLARIDAD", "CompClar", _a("R11")),
    ("RestoPers", "ADJ_NEG"): ("ADJ_NEG", _a("R7")),
    ("RestoPers", "SIN"): ("SIN", "SUST_SERVICIO", _a("R8")),
    ("Atencion", "ME"): ("ME", "V_ATENCION", "MuyAdj", _a("R9")),
    ("Atencion", "V_ATENCION"): ("V_ATENCION", "MuyAdj", _a("R9")),
    ("MuyAdj", "MUY"): ("MUY", "AdjAt"),
    ("MuyAdj", "ADJ_ATENCION"): ("ADJ_ATENCION",),
    ("MuyAdj", "BIEN"): ("BIEN",),
    ("AdjAt", "ADJ_ATENCION"): ("ADJ_ATENCION",),
    ("AdjAt", "BIEN"): ("BIEN",),
    ("Nominal", "SUST_SERVICIO"): ("SUST_SERVICIO", "Predicado"),
    ("Nominal", "SUST_ATENCION"): ("SUST_ATENCION", "COPULA", "MuyAdj", _a("R16")),
    ("Nominal", "AGENTE_SUST"): ("AGENTE_SUST", "COPULA", "MuyAdj", _a("R10")),
    ("Predicado", "COPULA"): ("COPULA", "MuyOpt", "Polaridad"),
    ("Predicado", "ADJ_NEG"): ("ADJ_NEG", _a("R1")),
    ("Predicado", "BIEN"): ("BIEN", _a("R17")),
    ("Predicado", "SE"): ("SE", "Corte"),
    ("Polaridad", "ADJ_NEG"): ("ADJ_NEG", _a("R1")),
    ("Polaridad", "BIEN"): ("BIEN", _a("R17")),
    ("ObjetoSol", "ART"): ("ART", "SUST_SERVICIO"),
    ("ObjetoSol", "SUST_SERVICIO"): ("SUST_SERVICIO",),
    ("Corte", "CORTA"): ("CORTA", "RecurrenciaOpt"),
}

TERMINALES = frozenset(
    {
        "ART",
        "SUST_SERVICIO",
        "ADJ_NEG",
        "FUNCIONA",
        "CORTA",
        "BIEN",
        "ADJ_ATENCION",
        "V_ATENCION",
        "V_CLARIDAD",
        "SUST_CLARIDAD",
        "SUST_ATENCION",
        "V_SOLICITUD",
        "V_COMPROMISO",
        "V_PERS",
        "AGENTE_SUST",
        "ME",
        "SE",
        "SIN",
        "COPULA",
        "PERO",
        "MUY",
        "NO",
        "AHORA",
        "MANANA",
        "TODOS",
        "DIAS",
        "CORTESIA",
        "TICKET",
        "EOF",
    }
)


class Parser:
    def __init__(self, tokens: list[Token], tabla: TablaSimbolos, turno: int, actor: str):
        self.tokens = list(tokens)
        self.tokens.append(
            Token(
                tipo="EOF",
                lexema="",
                normalizado="",
                sesion=tabla.sesion,
                turno=turno,
                desplazamiento=-1,
            )
        )
        self.tabla = tabla
        self.turno = turno
        self.actor = actor
        self.i = 0
        self.pila: list = []
        self.clausulas: list = []
        self.errores: list[dict] = []
        self.no_interpretados: list[str] = []
        self.inicio_clausula = 0
        self.clausula_abierta = False

    def parsear(self):
        self.clausulas = []
        self.errores = []
        self.no_interpretados = []
        self.i = 0
        self.clausula_abierta = False
        if self._mirar().tipo == "EOF":
            return []
        self.pila = ["EOF", "Enunciado"]
        for _ in range(10000):
            if not self.pila:
                break
            cima = self.pila[-1]
            if isinstance(cima, Accion):
                self.pila.pop()
                self._ejecutar(cima)
                continue
            if cima == "EOF":
                if self._mirar().tipo == "EOF":
                    self.pila.pop()
                else:
                    self._panico("fin de turno")
                continue
            if cima in TERMINALES:
                if self._mirar().tipo == cima:
                    self._consumir()
                    self.pila.pop()
                else:
                    self._panico(cima)
                continue
            if cima == "Clausula":
                self.inicio_clausula = self.i
                self.clausula_abierta = True
            produccion = self._predecir(cima, self._mirar().tipo)
            if produccion is None:
                self._panico(_ESPERADO.get(cima, cima))
                continue
            self.pila.pop()
            if cima == "Clausula" and not produccion:
                self.clausula_abierta = False
            for simbolo in reversed(produccion):
                self.pila.append(simbolo)
        return self.clausulas

    def _predecir(self, nt: str, tipo: str):
        if nt == "Enunciado":
            return ("Clausula", Accion("sobrante"), "Resto")
        if nt == "BienOpt":
            return ("BIEN",) if tipo == "BIEN" else ()
        if nt == "MuyOpt":
            return ("MUY",) if tipo == "MUY" else ()
        if nt == "TicketOpt":
            return ("TICKET",) if tipo == "TICKET" else ()
        if nt == "CompServ":
            if tipo == "ART" and self._en(1, "SUST_SERVICIO"):
                return ("ART", "SUST_SERVICIO")
            return ()
        if nt == "CompClar":
            if tipo == "ART" and self._en(1, "SUST_CLARIDAD"):
                return ("ART", "SUST_CLARIDAD")
            return ()
        if nt == "RecurrenciaOpt":
            if tipo == "TODOS" and self._en(1, "ART") and self._en(2, "DIAS"):
                return ("TODOS", "ART", "DIAS", Accion("R6"))
            return (Accion("R5"),)
        if nt == "Clausula":
            if tipo in _FIN:
                return ()
            if (nt, tipo) in TABLA:
                return TABLA[(nt, tipo)]
            return (Accion("fragmento"),)
        if nt == "Nominal" and tipo == "SUST_CLARIDAD":
            if self._en_fin(1):
                return ("SUST_CLARIDAD", Accion("R18", "CLARIDAD"))
            return None
        if nt == "Predicado" and tipo in {"PERO", "EOF", "TICKET"}:
            return (Accion("R18", "SERVICIO"),)
        if nt == "Resto" and tipo == "EOF":
            return ()
        return TABLA.get((nt, tipo))

    def _ejecutar(self, accion: Accion) -> None:
        if accion.nombre == "fragmento":
            self._fragmento()
            return
        if accion.nombre == "sobrante":
            self._sobrante()
            return
        if accion.nombre == "R18":
            self.clausulas.append(r18_mencion_neutra(self.actor, self._texto(self.inicio_clausula), accion.aspecto))
        else:
            self.clausulas.append(_REGLAS[accion.nombre](self.actor, self._texto(self.inicio_clausula)))
        self.clausula_abierta = False

    def _fragmento(self) -> None:
        palabras = []
        while self._mirar().tipo not in _FIN:
            token = self._consumir()
            if token.tipo != "TICKET":
                palabras.append(token.lexema)
        if palabras:
            texto = " ".join(palabras)
            self.no_interpretados.append(texto)
            self.clausulas.append(r15_no_interpretado(self.actor, texto))
        self.clausula_abierta = False

    def _sobrante(self) -> None:
        palabras = []
        while self._mirar().tipo not in _FIN:
            token = self._consumir()
            if token.tipo != "TICKET":
                palabras.append(token.lexema)
        if palabras:
            self.no_interpretados.append(" ".join(palabras))

    def _panico(self, esperado: str) -> None:
        """Descarta el tramo hasta «pero» o el fin y vacía la cláusula a medias."""
        self._registrar(esperado)
        desde = self.inicio_clausula if self.clausula_abierta else self.i
        avanzo_entrada = False
        while self._mirar().tipo not in _FIN:
            self._consumir()
            avanzo_entrada = True
        self._volcar(desde)
        fondo = len(self.pila)
        while self.pila and not self._ancla(self.pila[-1]):
            self.pila.pop()
        if not avanzo_entrada and len(self.pila) == fondo and self.pila:
            self.pila.pop()
        self.clausula_abierta = False

    def _registrar(self, esperado: str) -> None:
        token = self._mirar()
        if token.tipo == "EOF":
            llegado = "el fin del turno"
            cita = ""
        else:
            llegado = token.tipo
            cita = f" «{token.lexema}»"
        self.errores.append(
            {
                "turno": self.turno,
                "tipo": "ERROR_SINTACTICO",
                "esperado": esperado,
                "encontrado": token.tipo,
                "texto": token.lexema,
                "mensaje": f"se esperaba {esperado} y llegó {llegado}{cita}",
            }
        )

    def _volcar(self, desde: int) -> None:
        palabras = [
            token.lexema
            for token in self.tokens[desde : self.i]
            if token.tipo not in {"TICKET", "EOF"} and token.lexema
        ]
        if palabras:
            self.no_interpretados.append(" ".join(palabras))

    def _ancla(self, cima) -> bool:
        if cima in {"EOF", "Resto"}:
            return True
        return isinstance(cima, Accion) and cima.nombre == "sobrante"

    def _mirar(self) -> Token:
        return self.tokens[self.i]

    def _en(self, salto: int, tipo: str) -> bool:
        indice = self.i + salto
        if indice >= len(self.tokens):
            return False
        return self.tokens[indice].tipo == tipo

    def _en_fin(self, salto: int) -> bool:
        indice = self.i + salto
        if indice >= len(self.tokens):
            return True
        return self.tokens[indice].tipo in _FIN

    def _consumir(self) -> Token:
        token = self.tokens[self.i]
        self.i += 1
        if token.tipo == "TICKET":
            self.tabla.asegurar(
                token.normalizado,
                "ticket",
                {"turno": self.turno, "desplazamiento": token.desplazamiento},
            )
        return token

    def _texto(self, desde: int) -> str:
        return " ".join(token.lexema for token in self.tokens[desde : self.i] if token.tipo != "EOF")
