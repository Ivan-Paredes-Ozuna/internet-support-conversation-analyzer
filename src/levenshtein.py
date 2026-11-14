"""Distancia de edición de Levenshtein, con costos de inserción, borrado y sustitución en 1."""


def distancia(origen: str, destino: str) -> int:
    if origen == destino:
        return 0
    if not origen:
        return len(destino)
    if not destino:
        return len(origen)

    fila_anterior = list(range(len(destino) + 1))
    for indice_origen, caracter_origen in enumerate(origen, start=1):
        fila = [indice_origen]
        for indice_destino, caracter_destino in enumerate(destino, start=1):
            insercion = fila[indice_destino - 1] + 1
            borrado = fila_anterior[indice_destino] + 1
            sustitucion = fila_anterior[indice_destino - 1] + (caracter_origen != caracter_destino)
            fila.append(min(insercion, borrado, sustitucion))
        fila_anterior = fila
    return fila_anterior[-1]
