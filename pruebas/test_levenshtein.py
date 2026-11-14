import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.levenshtein import distancia


class DistanciaLevenshtein(unittest.TestCase):
    def test_identicas(self):
        self.assertEqual(distancia("lento", "lento"), 0)

    def test_insercion(self):
        self.assertEqual(distancia("lento", "lentto"), 1)
        self.assertEqual(distancia("lent", "lento"), 1)
        self.assertEqual(distancia("lent", "lenta"), 1)

    def test_sustitucion_y_mas(self):
        self.assertEqual(distancia("lentto", "lenta"), 2)
        self.assertEqual(distancia("kitten", "sitting"), 3)

    def test_vacio(self):
        self.assertEqual(distancia("", "no"), 2)
        self.assertEqual(distancia("tk", ""), 2)


if __name__ == "__main__":
    unittest.main()
