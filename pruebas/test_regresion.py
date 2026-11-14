import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.analizador import analizar_archivo
from src.salida import sesion_a_dict

RAIZ = Path(__file__).resolve().parents[1]


class RegresionSinonimo(unittest.TestCase):
    """Caso 12: el sinónimo «conexion» debe seguir el mismo criterio que el caso 01.

    Si se toca R1 o R2, esta prueba tiene que seguir en MIXTA / RESUELTO.
    """

    def test_conexion_lenta_luego_funciona(self):
        resultado = analizar_archivo(RAIZ / "casos" / "propios" / "caso12.txt")
        sesion = sesion_a_dict(resultado.sesiones[0])
        self.assertEqual(sesion["id"], "S12")
        self.assertEqual(sesion["analisis"], "completo")
        self.assertEqual(sesion["estado"], "RESUELTO")
        self.assertEqual(sesion["resumen_por_aspecto"]["SERVICIO"], "MIXTA")
        self.assertEqual(sesion["correcciones"], [])
        reglas = [evidencia["regla"] for evidencia in sesion["evidencias"]]
        self.assertEqual(reglas, ["R1", "R12", "R2"])


if __name__ == "__main__":
    unittest.main()
