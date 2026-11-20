import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analizador import analizar_texto
from src.parser import TABLA
from src.salida import sesion_a_dict


def _una(texto: str):
    resultado = analizar_texto(texto)
    return resultado.sesiones[0]


class TablaPredictiva(unittest.TestCase):
    def test_la_tabla_elige_la_produccion_por_el_primer_token(self):
        self.assertEqual(TABLA[("Clausula", "NO")][0], "NO")
        self.assertEqual(TABLA[("Clausula", "AHORA")][0], "AHORA")
        self.assertEqual(TABLA[("Clausula", "ART")][0], "ART")
        self.assertNotIn(("Clausula", "PALABRA"), TABLA)
        self.assertNotIn(("RestoNo", "EOF"), TABLA)


class Recuperacion(unittest.TestCase):
    def _turno(self, texto: str):
        sesion = _una(f"SESION S30\n1 CLIENTE: {texto}\nFIN\n")
        return sesion, sesion.turnos[0]

    def test_produccion_cortada_no_emite_la_regla_y_sigue_despues_de_pero(self):
        sesion, turno = self._turno("Ahora lento, pero funciona bien.")
        datos = sesion_a_dict(sesion)
        self.assertEqual(datos["analisis"], "completo")
        self.assertEqual(datos["estado"], "RESUELTO")
        self.assertEqual([item["regla"] for item in datos["evidencias"]], ["R3"])
        self.assertEqual(turno.no_interpretados, ["Ahora lento"])
        self.assertEqual(turno.errores_sintacticos[0]["tipo"], "ERROR_SINTACTICO")
        self.assertIn("FUNCIONA", turno.errores_sintacticos[0]["mensaje"])
        self.assertIn("lento", turno.errores_sintacticos[0]["mensaje"])

    def test_falta_el_adjetivo_y_no_se_inventa_r1(self):
        sesion, turno = self._turno("El servicio está.")
        datos = sesion_a_dict(sesion)
        self.assertEqual(datos["evidencias"], [])
        self.assertEqual(datos["estado"], "NO_CONFIRMADO")
        self.assertTrue(turno.errores_sintacticos)
        self.assertEqual(turno.no_interpretados, ["El servicio está"])

    def test_fragmento_fuera_de_first_no_es_error_sintactico(self):
        sesion, turno = self._turno("lent.")
        self.assertEqual(sesion.analisis, "completo")
        self.assertEqual(turno.errores_sintacticos, [])
        self.assertEqual(turno.no_interpretados, ["lent"])

    def test_se_corta_incompleto_no_consume_el_todos(self):
        _sesion, turno = self._turno("Se corta todos.")
        self.assertEqual(turno.errores_sintacticos, [])
        self.assertEqual(turno.clausulas[0].regla, "R5")
        self.assertEqual(turno.no_interpretados, ["todos"])


if __name__ == "__main__":
    unittest.main()
