"""Diccionario de vocabulario, separado de la tabla de símbolos."""

from pathlib import Path

from src.levenshtein import distancia

RAIZ = Path(__file__).resolve().parents[1]
RUTA_DEFECTO = RAIZ / "diccionario" / "vocabulario.txt"


class Diccionario:
    def __init__(self, cerrada: dict[str, str], correccion: dict[str, str]):
        self.cerrada = cerrada
        self.correccion = correccion
        self.exactos = {**correccion, **cerrada}
        self.lemas = sorted(correccion)

    def candidatos_a_uno(self, normalizada: str) -> list[str]:
        """Lemas de contenido a distancia 1. Ignora pares cuya longitud ya los descarta."""
        encontrados = []
        for lema in self.lemas:
            if abs(len(lema) - len(normalizada)) > 1:
                continue
            if distancia(normalizada, lema) == 1:
                encontrados.append(lema)
        return sorted(encontrados)


def cargar(ruta: Path | None = None) -> Diccionario:
    archivo = Path(ruta) if ruta else RUTA_DEFECTO
    cerrada: dict[str, str] = {}
    correccion: dict[str, str] = {}
    seccion = None
    for numero, linea in enumerate(archivo.read_text(encoding="utf-8").splitlines(), start=1):
        limpia = linea.split("#", 1)[0].strip()
        if not limpia:
            continue
        if limpia.startswith("[") and limpia.endswith("]"):
            seccion = limpia[1:-1].strip().lower()
            if seccion not in {"cerrada", "correccion"}:
                raise ValueError(f"{archivo}:{numero}: sección desconocida {limpia}")
            continue
        if seccion is None:
            raise ValueError(f"{archivo}:{numero}: falta la sección [correccion] o [cerrada]")
        partes = limpia.split()
        if len(partes) != 2:
            raise ValueError(f"{archivo}:{numero}: se espera «lema CATEGORIA»")
        lema, categoria = partes
        destino = cerrada if seccion == "cerrada" else correccion
        if lema in destino or lema in cerrada or lema in correccion:
            raise ValueError(f"{archivo}:{numero}: lema duplicado {lema}")
        destino[lema] = categoria
    return Diccionario(cerrada, correccion)
