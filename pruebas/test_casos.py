import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analizador import analizar_archivo, analizar_texto
from src.salida import sesion_a_dict

RAIZ = Path(__file__).resolve().parents[1]


def caso(nombre: str):
    for ruta in (RAIZ / "casos").rglob(nombre):
        return analizar_archivo(ruta)
    raise AssertionError(f"no está {nombre}")


def primera(nombre: str) -> dict:
    return sesion_a_dict(caso(nombre).sesiones[0])


class CasosGuia(unittest.TestCase):
    def test_01_mixta_resuelto(self):
        sesion = primera("caso01.txt")
        self.assertEqual(sesion["analisis"], "completo")
        self.assertEqual(sesion["estado"], "RESUELTO")
        self.assertEqual(sesion["resumen_por_aspecto"]["SERVICIO"], "MIXTA")
        self.assertEqual(sesion["resumen_por_aspecto"]["ATENCION"], "SIN_EVIDENCIA")
        self.assertEqual(sesion["resumen_por_aspecto"]["CLARIDAD"], "SIN_EVIDENCIA")
        self.assertEqual(sesion["errores"], [])

    def test_02_atencion_y_servicio(self):
        sesion = primera("caso02.txt")
        self.assertEqual(sesion["estado"], "NO_RESUELTO")
        self.assertEqual(sesion["resumen_por_aspecto"]["ATENCION"], "POSITIVA")
        self.assertEqual(sesion["resumen_por_aspecto"]["SERVICIO"], "NEGATIVA")
        self.assertEqual(sesion["resumen_por_aspecto"]["CLARIDAD"], "SIN_EVIDENCIA")

    def test_03_temporal(self):
        sesion = primera("caso03.txt")
        self.assertEqual(sesion["estado"], "TEMPORAL")
        self.assertEqual(sesion["resumen_por_aspecto"]["SERVICIO"], "MIXTA")

    def test_04_claridad_y_atencion(self):
        sesion = primera("caso04.txt")
        self.assertEqual(sesion["estado"], "NO_CONFIRMADO")
        self.assertEqual(sesion["resumen_por_aspecto"]["CLARIDAD"], "NEGATIVA")
        self.assertEqual(sesion["resumen_por_aspecto"]["ATENCION"], "POSITIVA")
        self.assertEqual(sesion["resumen_por_aspecto"]["SERVICIO"], "SIN_EVIDENCIA")

    def test_05_correccion_y_ticket(self):
        sesion = primera("caso05.txt")
        self.assertEqual(sesion["resumen_por_aspecto"]["SERVICIO"], "NEGATIVA")
        self.assertEqual(sesion["estado"], "NO_RESUELTO")
        self.assertEqual(sesion["correcciones"][0]["original"], "lentto")
        self.assertEqual(sesion["correcciones"][0]["corregido"], "lento")
        self.assertEqual(sesion["entidades"]["tickets"][0]["id"], "TK-204")
        self.assertEqual(sesion["entidades"]["tickets"][0]["apariciones"][0]["turno"], 2)

    def test_06_pendiente_sin_evidencia(self):
        sesion = primera("caso06.txt")
        self.assertEqual(sesion["estado"], "PENDIENTE")
        self.assertTrue(all(valor == "SIN_EVIDENCIA" for valor in sesion["resumen_por_aspecto"].values()))
        self.assertEqual(sesion["entidades"]["tickets"][0]["id"], "TK-205")
        reglas = {evidencia["regla"] for evidencia in sesion["evidencias"]}
        self.assertEqual(reglas, {"R13", "R14"})

    def test_07_rol_invalido_y_sigue(self):
        resultado = caso("caso07.txt")
        self.assertEqual([sesion.id for sesion in resultado.sesiones], ["S07", "S07B"])
        primera_sesion = sesion_a_dict(resultado.sesiones[0])
        segunda = sesion_a_dict(resultado.sesiones[1])
        self.assertEqual(primera_sesion["analisis"], "parcial")
        self.assertEqual(primera_sesion["errores"][0]["tipo"], "ROL_INVALIDO")
        self.assertEqual([turno["turno"] for turno in primera_sesion["valoraciones_por_turno"]], [1, 3])
        self.assertEqual(segunda["analisis"], "completo")
        self.assertEqual(segunda["estado"], "RESUELTO")

    def test_08_empate_sin_evidencia(self):
        sesion = primera("caso08.txt")
        self.assertEqual(sesion["analisis"], "completo")
        self.assertEqual(sesion["correcciones"], [])
        self.assertEqual(sesion["abstenciones"][0]["original"], "lent")
        self.assertEqual(sesion["abstenciones"][0]["candidatos"], ["lenta", "lento"])
        self.assertEqual(sesion["estado"], "NO_CONFIRMADO")
        self.assertTrue(all(valor == "SIN_EVIDENCIA" for valor in sesion["resumen_por_aspecto"].values()))
        self.assertEqual(sesion["valoraciones_por_turno"][0]["no_interpretados"], ["lent"])


class CasosPropios(unittest.TestCase):
    def test_09_negacion_y_contraste(self):
        sesion = primera("caso09.txt")
        self.assertEqual(sesion["estado"], "NO_RESUELTO")
        self.assertEqual(sesion["resumen_por_aspecto"]["SERVICIO"], "NEGATIVA")
        self.assertEqual(sesion["resumen_por_aspecto"]["ATENCION"], "POSITIVA")
        negada = sesion["evidencias"][0]
        self.assertEqual(negada["regla"], "R4")
        self.assertTrue(negada["negado"])

    def test_10_correccion_unica(self):
        sesion = primera("caso10.txt")
        self.assertEqual(sesion["correcciones"][0]["original"], "conxion")
        self.assertEqual(sesion["correcciones"][0]["corregido"], "conexion")
        self.assertEqual(sesion["resumen_por_aspecto"]["SERVICIO"], "NEGATIVA")
        self.assertEqual(sesion["estado"], "NO_RESUELTO")

    def test_11_orden_inconsistente_no_aplica_el_turno(self):
        resultado = caso("caso11.txt")
        self.assertEqual([sesion.id for sesion in resultado.sesiones], ["S11", "S11B"])
        rota = sesion_a_dict(resultado.sesiones[0])
        siguiente = sesion_a_dict(resultado.sesiones[1])
        self.assertEqual(rota["analisis"], "parcial")
        self.assertEqual(rota["errores"][0]["tipo"], "ORDEN_INCONSISTENTE")
        self.assertEqual(rota["estado"], "NO_RESUELTO")
        self.assertEqual(len(rota["valoraciones_por_turno"]), 1)
        self.assertEqual(siguiente["analisis"], "completo")
        self.assertEqual(siguiente["estado"], "NO_CONFIRMADO")


class Construcciones(unittest.TestCase):
    def _una(self, texto: str) -> dict:
        resultado = analizar_texto(texto)
        self.assertEqual(len(resultado.sesiones), 1)
        return sesion_a_dict(resultado.sesiones[0])

    def test_sigue_lento_y_funciona_bien(self):
        sesion = self._una("SESION S20\n1 CLIENTE: Sigue lento.\n2 CLIENTE: Funciona bien.\nFIN\n")
        self.assertEqual(sesion["resumen_por_aspecto"]["SERVICIO"], "MIXTA")
        self.assertEqual(sesion["estado"], "RESUELTO")
        self.assertEqual([item["regla"] for item in sesion["evidencias"]], ["R7", "R3"])

    def test_se_corta_sin_recuperacion_no_es_temporal(self):
        sesion = self._una("SESION S21\n1 CLIENTE: Se corta todos los días.\nFIN\n")
        self.assertEqual(sesion["estado"], "NO_RESUELTO")
        self.assertEqual(sesion["resumen_por_aspecto"]["SERVICIO"], "NEGATIVA")
        self.assertEqual(sesion["evidencias"][0]["regla"], "R6")

    def test_la_promesa_del_agente_no_pisa_al_cliente(self):
        negativo = self._una(
            "SESION S22\n1 CLIENTE: El servicio está lento.\n2 AGENTE: Mañana revisaremos TK-300.\nFIN\n"
        )
        self.assertEqual(negativo["estado"], "NO_RESUELTO")
        resuelto = self._una(
            "SESION S23\n1 AGENTE: Mañana revisaremos TK-301.\n2 CLIENTE: Ahora funciona bien.\nFIN\n"
        )
        self.assertEqual(resuelto["estado"], "RESUELTO")

    def test_el_mismo_ticket_es_una_sola_entrada(self):
        sesion = self._una(
            "SESION S24\n1 CLIENTE: El internet está lento TK-204.\n2 AGENTE: Mañana revisaremos TK-204.\nFIN\n"
        )
        self.assertEqual(len(sesion["entidades"]["tickets"]), 1)
        apariciones = sesion["entidades"]["tickets"][0]["apariciones"]
        self.assertEqual([item["turno"] for item in apariciones], [1, 2])

    def test_linea_en_blanco_y_fin_ausente_dejan_la_sesion_parcial(self):
        resultado = analizar_texto("SESION S25\n1 CLIENTE: Funciona bien.\n\n2 CLIENTE: Sigue lento.\n")
        sesion = sesion_a_dict(resultado.sesiones[0])
        self.assertEqual(sesion["analisis"], "parcial")
        tipos = {error["tipo"] for error in sesion["errores"]}
        self.assertEqual(tipos, {"LINEA_EN_BLANCO", "FIN_AUSENTE"})
        self.assertEqual(sesion["estado"], "NO_RESUELTO")


if __name__ == "__main__":
    unittest.main()
