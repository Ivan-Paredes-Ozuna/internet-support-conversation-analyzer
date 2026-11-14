import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.tabla_simbolos import TablaSimbolos


class TablaHash(unittest.TestCase):
    def test_insercion_busqueda_y_duplicado(self):
        tabla = TablaSimbolos("S01", capacidad=1)
        alta = tabla.insertar("TK-204", "ticket", {"turno": 1, "desplazamiento": 3})
        self.assertIsNotNone(alta)
        self.assertIsNone(tabla.insertar("TK-204", "ticket"))
        encontrada = tabla.buscar("TK-204")
        self.assertEqual(encontrada.tipo, "ticket")
        self.assertEqual(len(encontrada.apariciones), 1)

    def test_actualizar_no_crea_otra_entrada(self):
        tabla = TablaSimbolos("S01", capacidad=2)
        tabla.insertar("TK-204", "ticket", {"turno": 1, "desplazamiento": 0})
        tabla.actualizar("TK-204", {"turno": 2, "desplazamiento": 8})
        entradas = [entrada for entrada in tabla.entradas() if entrada.clave == "TK-204"]
        self.assertEqual(len(entradas), 1)
        self.assertEqual([item["turno"] for item in entradas[0].apariciones], [1, 2])

    def test_actualizar_ausente_falla(self):
        tabla = TablaSimbolos("S01", capacidad=3)
        self.assertIsNone(tabla.actualizar("TK-999", {"turno": 1, "desplazamiento": 0}))

    def test_cadenas_distintas_en_la_misma_cubeta(self):
        tabla = TablaSimbolos("S01", capacidad=1)
        tabla.insertar("CLIENTE", "participante")
        tabla.insertar("AGENTE", "participante")
        self.assertEqual(tabla.buscar("CLIENTE").tipo, "participante")
        self.assertEqual(tabla.buscar("AGENTE").tipo, "participante")
        self.assertIsNone(tabla.buscar("SOPORTE"))


if __name__ == "__main__":
    unittest.main()
