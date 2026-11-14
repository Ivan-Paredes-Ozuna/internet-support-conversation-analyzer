"""Parser LL(1) por descenso recursivo, con un token de anticipación.

La gramática está factorizada para que cada alternativa de Clausula arranque
con un conjunto FIRST disjunto. Lo que no entra en una producción se rebobina
y, si ninguna alternativa reconoce el tramo, se emite R15 (NO_INTERPRETADO)
hasta el próximo «pero» o el fin del turno. Un ticket suelto igual se anota
en la tabla de símbolos.
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

_FIN_DE_CLAUSULA = frozenset({"PERO", "EOF"})
_ADJETIVO_ATENCION = frozenset({"ADJ_ATENCION", "BIEN"})


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
        self.no_interpretados: list[str] = []

    def parsear(self):
        clausulas = []
        if self._mirar().tipo == "EOF":
            return clausulas
        reconocida = self._clausula()
        if reconocida is not None:
            clausulas.append(reconocida)
        self._sobrantes()
        while self._mirar().tipo == "PERO":
            self._avanzar()
            reconocida = self._clausula()
            if reconocida is not None:
                clausulas.append(reconocida)
            self._sobrantes()
        return clausulas

    def _mirar(self) -> Token:
        return self.tokens[self.i]

    def _en(self, salto: int, tipo: str) -> bool:
        indice = self.i + salto
        if indice >= len(self.tokens):
            return False
        return self.tokens[indice].tipo == tipo

    def _avanzar(self) -> Token:
        token = self.tokens[self.i]
        self.i += 1
        return token

    def _texto(self, desde: int) -> str:
        return " ".join(token.lexema for token in self.tokens[desde : self.i] if token.tipo != "EOF")

    def _registrar_ticket(self, token: Token) -> None:
        aparicion = {"turno": self.turno, "desplazamiento": token.desplazamiento}
        self.tabla.asegurar(token.normalizado, "ticket", aparicion)

    def _clausula(self):
        inicio = self.i
        for alternativa in (
            self._desde_no,
            self._desde_ahora,
            self._desde_se,
            self._desde_persiste,
            self._desde_atencion,
            self._desde_nominal,
            self._desde_servicio,
            self._desde_solicitud,
            self._desde_compromiso,
            self._desde_manana,
            self._desde_funciona,
            self._desde_cortesia,
        ):
            self.i = inicio
            atributos = alternativa(inicio)
            if atributos is not None:
                return atributos
        self.i = inicio
        return self._fragmento()

    def _desde_no(self, inicio: int):
        if self._mirar().tipo != "NO":
            return None
        self._avanzar()
        if self._mirar().tipo == "FUNCIONA":
            self._avanzar()
            self._complemento("SUST_SERVICIO")
            return r4_no_funciona(self.actor, self._texto(inicio))
        if self._mirar().tipo == "V_CLARIDAD":
            self._avanzar()
            self._complemento("SUST_CLARIDAD")
            return r11_no_entendi(self.actor, self._texto(inicio))
        return None

    def _complemento(self, sustantivo: str) -> None:
        """Objeto opcional «artículo + sustantivo». Si el artículo no introduce ese sustantivo, no se consume."""
        if self._mirar().tipo != "ART":
            return
        if not self._en(1, sustantivo):
            return
        self._avanzar()
        self._avanzar()

    def _desde_ahora(self, inicio: int):
        if self._mirar().tipo != "AHORA":
            return None
        self._avanzar()
        if self._mirar().tipo != "FUNCIONA":
            return None
        self._avanzar()
        self._bien_opcional()
        return r2_ahora_funciona(self.actor, self._texto(inicio))

    def _desde_funciona(self, inicio: int):
        if self._mirar().tipo != "FUNCIONA":
            return None
        self._avanzar()
        self._bien_opcional()
        return r3_funciona(self.actor, self._texto(inicio))

    def _bien_opcional(self) -> None:
        if self._mirar().tipo == "BIEN":
            self._avanzar()

    def _desde_se(self, inicio: int):
        if self._mirar().tipo != "SE":
            return None
        self._avanzar()
        return self._corte(inicio)

    def _corte(self, inicio: int):
        if self._mirar().tipo != "CORTA":
            return None
        self._avanzar()
        if self._recurrencia():
            return r6_se_corta_recurrente(self.actor, self._texto(inicio))
        return r5_se_corta(self.actor, self._texto(inicio))

    def _recurrencia(self) -> bool:
        if self._mirar().tipo == "TODOS" and self._en(1, "ART") and self._en(2, "DIAS"):
            self._avanzar()
            self._avanzar()
            self._avanzar()
            return True
        return False

    def _desde_persiste(self, inicio: int):
        if self._mirar().tipo != "V_PERS":
            return None
        self._avanzar()
        if self._mirar().tipo == "ADJ_NEG":
            self._avanzar()
            return r7_sigue_negativo(self.actor, self._texto(inicio))
        if self._mirar().tipo == "SIN" and self._en(1, "SUST_SERVICIO"):
            self._avanzar()
            self._avanzar()
            return r8_sigo_sin(self.actor, self._texto(inicio))
        return None

    def _desde_atencion(self, inicio: int):
        if self._mirar().tipo == "ME":
            self._avanzar()
        if self._mirar().tipo != "V_ATENCION":
            return None
        self._avanzar()
        if not self._muy_y_adjetivo(_ADJETIVO_ATENCION):
            return None
        return r9_atencion_positiva(self.actor, self._texto(inicio))

    def _muy_y_adjetivo(self, tipos: frozenset[str]) -> bool:
        if self._mirar().tipo == "MUY":
            self._avanzar()
        if self._mirar().tipo not in tipos:
            return False
        self._avanzar()
        return True

    def _desde_nominal(self, inicio: int):
        if self._mirar().tipo != "ART":
            return None
        self._avanzar()
        tipo = self._mirar().tipo
        if tipo == "SUST_SERVICIO":
            self._avanzar()
            return self._predicado_servicio(inicio)
        if tipo in {"SUST_ATENCION", "AGENTE_SUST"}:
            self._avanzar()
            if self._mirar().tipo != "COPULA":
                return None
            self._avanzar()
            if not self._muy_y_adjetivo(_ADJETIVO_ATENCION):
                return None
            if tipo == "AGENTE_SUST":
                return r10_agente_amable(self.actor, self._texto(inicio))
            return r16_atencion_nominal(self.actor, self._texto(inicio))
        if tipo == "SUST_CLARIDAD":
            self._avanzar()
            if self._mirar().tipo not in _FIN_DE_CLAUSULA:
                return None
            return r18_mencion_neutra(self.actor, self._texto(inicio), "CLARIDAD")
        return None

    def _desde_servicio(self, inicio: int):
        if self._mirar().tipo != "SUST_SERVICIO":
            return None
        self._avanzar()
        return self._predicado_servicio(inicio)

    def _predicado_servicio(self, inicio: int):
        tipo = self._mirar().tipo
        if tipo in _FIN_DE_CLAUSULA or tipo == "TICKET":
            return r18_mencion_neutra(self.actor, self._texto(inicio), "SERVICIO")
        if tipo == "COPULA":
            self._avanzar()
            if self._mirar().tipo == "MUY":
                self._avanzar()
            if self._mirar().tipo == "ADJ_NEG":
                self._avanzar()
                return r1_servicio_negativo(self.actor, self._texto(inicio))
            if self._mirar().tipo == "BIEN":
                self._avanzar()
                return r17_servicio_bien(self.actor, self._texto(inicio))
            return None
        if tipo == "ADJ_NEG":
            self._avanzar()
            return r1_servicio_negativo(self.actor, self._texto(inicio))
        if tipo == "BIEN":
            self._avanzar()
            return r17_servicio_bien(self.actor, self._texto(inicio))
        if tipo == "SE":
            self._avanzar()
            return self._corte(inicio)
        return None

    def _desde_solicitud(self, inicio: int):
        if self._mirar().tipo != "V_SOLICITUD":
            return None
        self._avanzar()
        if self._mirar().tipo == "ART":
            self._avanzar()
        if self._mirar().tipo != "SUST_SERVICIO":
            return None
        self._avanzar()
        return r12_solicitud(self.actor, self._texto(inicio))

    def _desde_compromiso(self, inicio: int):
        if self._mirar().tipo != "V_COMPROMISO":
            return None
        self._avanzar()
        self._ticket_opcional()
        return r13_compromiso(self.actor, self._texto(inicio))

    def _desde_manana(self, inicio: int):
        if self._mirar().tipo != "MANANA":
            return None
        self._avanzar()
        if self._mirar().tipo != "V_COMPROMISO":
            return None
        self._avanzar()
        self._ticket_opcional()
        return r13_compromiso(self.actor, self._texto(inicio))

    def _ticket_opcional(self) -> None:
        if self._mirar().tipo == "TICKET":
            self._registrar_ticket(self._avanzar())

    def _desde_cortesia(self, inicio: int):
        if self._mirar().tipo != "CORTESIA":
            return None
        self._avanzar()
        return r14_cortesia(self.actor, self._texto(inicio))

    def _fragmento(self):
        if self._mirar().tipo in _FIN_DE_CLAUSULA:
            return None
        palabras = []
        while self._mirar().tipo not in _FIN_DE_CLAUSULA:
            token = self._avanzar()
            if token.tipo == "TICKET":
                self._registrar_ticket(token)
            else:
                palabras.append(token.lexema)
        if not palabras:
            return None
        texto = " ".join(palabras)
        self.no_interpretados.append(texto)
        return r15_no_interpretado(self.actor, texto)

    def _sobrantes(self) -> None:
        palabras = []
        while self._mirar().tipo not in _FIN_DE_CLAUSULA:
            token = self._avanzar()
            if token.tipo == "TICKET":
                self._registrar_ticket(token)
            else:
                palabras.append(token.lexema)
        if palabras:
            self.no_interpretados.append(" ".join(palabras))
