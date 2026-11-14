"""Punto de entrada: un archivo o un directorio de sesiones."""

import argparse
import sys
from pathlib import Path

from src.analizador import analizar_archivo, analizar_rutas
from src.diccionario import cargar
from src.salida import a_consola, a_json
from src.traza import formatear


def _rutas(entrada: Path) -> list[Path]:
    if entrada.is_file():
        return [entrada]
    if entrada.is_dir():
        return sorted(entrada.rglob("*.txt"), key=lambda ruta: (ruta.name, str(ruta)))
    raise SystemExit(f"No existe la entrada: {entrada}")


def main(argumentos: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Analiza sesiones de soporte de internet y emite JSON, consola y traza."
    )
    parser.add_argument("entrada", type=Path, help="Archivo .txt o directorio con casos")
    parser.add_argument("--json", dest="json_path", type=Path, help="Dónde escribir el JSON del lote")
    parser.add_argument("--traza", help="Id de sesión a trazar, por ejemplo S01")
    parser.add_argument("--guardar-traza", type=Path, help="Archivo donde guardar la traza")
    parser.add_argument("--diccionario", type=Path, help="Vocabulario alternativo")
    opciones = parser.parse_args(argumentos)

    diccionario = cargar(opciones.diccionario) if opciones.diccionario else cargar()
    rutas = _rutas(opciones.entrada)
    if not rutas:
        raise SystemExit(f"No hay archivos .txt en {opciones.entrada}")
    if len(rutas) == 1 and opciones.entrada.is_file():
        resultado = analizar_archivo(rutas[0], diccionario)
    else:
        resultado = analizar_rutas(rutas, diccionario)

    sys.stdout.write(a_consola(resultado))
    if opciones.json_path:
        opciones.json_path.parent.mkdir(parents=True, exist_ok=True)
        opciones.json_path.write_text(a_json(resultado), encoding="utf-8")

    if opciones.traza:
        sesion = next((item for item in resultado.sesiones if item.id == opciones.traza), None)
        if sesion is None:
            raise SystemExit(f"No está la sesión {opciones.traza}")
        texto = f"=== Traza {sesion.id} ===\n" + formatear(sesion.eventos)
        sys.stdout.write("\n" + texto)
        if opciones.guardar_traza:
            opciones.guardar_traza.parent.mkdir(parents=True, exist_ok=True)
            opciones.guardar_traza.write_text(texto, encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
