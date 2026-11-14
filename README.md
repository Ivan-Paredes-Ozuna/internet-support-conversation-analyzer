# Analizador de sesiones de soporte

Procesador determinista del TP 1 de Diseño de Compiladores (FPUNA, 2026/2). Lee sesiones de soporte de internet, las analiza con léxico, gramática y reglas semánticas, y escribe un JSON, un resumen de consola y, si se pide, la traza de una sesión.

En ejecución no se consulta ningún modelo. Hace falta Python 3.11 o posterior y no hay dependencias aparte de la biblioteca estándar. Los comandos se corren desde la raíz del repositorio.

## Ejecutar

Un archivo o todo el directorio de casos:

```bash
python -m src.main casos/guia/caso01.txt
python -m src.main casos/ --json ejemplos/salida.json --traza S01 --guardar-traza ejemplos/traza_s01.txt
python -m src.main ejemplos/lote.txt
```

`--json` escribe el lote. `--traza S01` imprime el camino de esa sesión. `--diccionario` cambia el vocabulario.

Pruebas:

```bash
python -m unittest discover -s pruebas -t .
```

## Formato de entrada

```
SESION S01
1 CLIENTE: El servicio está lento.
2 AGENTE: Reinicie el router.
3 CLIENTE: Ahora funciona bien.
FIN
```

Cada turno lleva número consecutivo desde 1, rol `CLIENTE` o `AGENTE`, dos puntos y texto. Un rol inválido o un número fuera de orden se rechaza y el análisis sigue en la línea siguiente: la sesión queda `parcial` y el resto de sesiones se conserva. Una palabra fuera de la gramática queda `NO_INTERPRETADO` y no inventa una valoración.

## Dónde está cada parte

- Léxico, normalización y posiciones: [src/lexer.py](src/lexer.py), [src/normalizacion.py](src/normalizacion.py)
- AFD del ticket `TK-[0-9]{3,6}`: [src/afd_ticket.py](src/afd_ticket.py)
- Corrección por Levenshtein: [src/levenshtein.py](src/levenshtein.py), vocabulario en [diccionario/vocabulario.txt](diccionario/vocabulario.txt)
- Tabla de símbolos (hash con encadenamiento): [src/tabla_simbolos.py](src/tabla_simbolos.py)
- Gramática y parser LL(1): [src/parser.py](src/parser.py)
- Reglas, resumen y estado: [src/semantica.py](src/semantica.py)
- Recuperación de turnos: [src/analizador.py](src/analizador.py)
- JSON, consola y traza: [src/salida.py](src/salida.py), [src/traza.py](src/traza.py)

El informe de las decisiones está en [INFORME.md](INFORME.md). La declaración de IA, en [DECLARACION_IA.md](DECLARACION_IA.md).

## Casos

Ocho de la guía en [casos/guia](casos/guia) y cuatro propios en [casos/propios](casos/propios). El 12 es el de regresión: «la conexión está lenta» y después «ahora funciona bien» debe seguir en `SERVICIO MIXTA` y `RESUELTO`. [ejemplos/lote.txt](ejemplos/lote.txt) junta los doce en un solo archivo. [ejemplos/salida.json](ejemplos/salida.json) es el JSON de `casos/`, con los números de línea de cada archivo.
