import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.afd_ticket import acepta, transicion


class AfdTicket(unittest.TestCase):
    def test_acepta_entre_tres_y_seis_digitos(self):
        self.assertTrue(acepta("TK-204"))
        self.assertTrue(acepta("tk-204"))
        self.assertTrue(acepta("TK-123456"))
        self.assertTrue(acepta("TK-000"))

    def test_rechaza_longitud_y_forma(self):
        self.assertFalse(acepta("TK-20"))
        self.assertFalse(acepta("TK-1234567"))
        self.assertFalse(acepta("TK204"))
        self.assertFalse(acepta("TX-204"))
        self.assertFalse(acepta(""))
        self.assertFalse(acepta("TK-20A"))

    def test_digito_de_mas_cae_en_muerto(self):
        estado = "q0"
        for caracter in "TK-1234567":
            estado = transicion(estado, caracter)
        self.assertEqual(estado, "qM")


if __name__ == "__main__":
    unittest.main()
