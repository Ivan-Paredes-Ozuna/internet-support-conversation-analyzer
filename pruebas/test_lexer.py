import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.diccionario import cargar
from src.lexer import tokenizar


class Lexer(unittest.TestCase):
    def setUp(self):
        self.diccionario = cargar()

    def test_posicion_correccion_y_ticket(self):
        texto = "El internet está lentto TK-204."
        tokens = tokenizar(texto, self.diccionario, "S05", 1)
        por_lexema = {token.lexema: token for token in tokens}
        self.assertEqual(por_lexema["El"].tipo, "ART")
        self.assertEqual(por_lexema["El"].desplazamiento, 0)
        self.assertEqual(por_lexema["El"].sesion, "S05")
        self.assertEqual(por_lexema["El"].turno, 1)
        lento = por_lexema["lentto"]
        self.assertEqual(lento.tipo, "ADJ_NEG")
        self.assertEqual(lento.normalizado, "lento")
        self.assertEqual(lento.correccion["distancia"], 1)
        self.assertEqual(lento.desplazamiento, texto.index("lentto"))
        ticket = por_lexema["TK-204"]
        self.assertEqual(ticket.tipo, "TICKET")
        self.assertEqual(ticket.normalizado, "TK-204")
        self.assertIsNone(ticket.correccion)
        self.assertEqual(ticket.desplazamiento, texto.index("TK-204"))

    def test_no_numeros_ni_ticket_corto_se_corrigen(self):
        tokens = tokenizar("no 123 TK-20", self.diccionario, "S", 1)
        tipos = [(token.lexema, token.tipo, token.correccion) for token in tokens]
        self.assertEqual(tipos[0], ("no", "NO", None))
        self.assertEqual(tipos[1], ("123", "NUMERO", None))
        self.assertEqual(tokens[2].tipo, "PALABRA")
        self.assertIsNone(tokens[2].correccion)

    def test_empate_no_elige_lema(self):
        tokens = tokenizar("lent", self.diccionario, "S08", 1)
        self.assertEqual(tokens[0].tipo, "PALABRA")
        self.assertEqual(tokens[0].abstencion, ["lenta", "lento"])
        self.assertIsNone(tokens[0].correccion)

    def test_palabras_del_agente_no_se_reescriben(self):
        tokens = tokenizar("Quedó registrado el ticket", self.diccionario, "S05", 2)
        self.assertTrue(all(token.correccion is None for token in tokens))
        self.assertEqual([token.tipo for token in tokens], ["PALABRA", "PALABRA", "ART", "PALABRA"])


if __name__ == "__main__":
    unittest.main()
