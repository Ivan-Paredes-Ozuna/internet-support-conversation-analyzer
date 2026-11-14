"""Tabla de símbolos por sesión: hash con encadenamiento separado.

La sesión, cada rol y cada ticket ocupan una entrada. Una mención repetida del
mismo ticket no crea otra clave: se actualiza la lista de apariciones.
"""

from dataclasses import dataclass, field


@dataclass
class Entrada:
    clave: str
    tipo: str
    apariciones: list[dict] = field(default_factory=list)


class TablaSimbolos:
    def __init__(self, sesion: str, capacidad: int = 31, registro: list | None = None):
        if capacidad < 1:
            raise ValueError("la capacidad de la tabla debe ser positiva")
        self.sesion = sesion
        self.capacidad = capacidad
        self.cubetas: list[list[Entrada]] = [[] for _ in range(capacidad)]
        self.registro = registro if registro is not None else []
        self.turno_actual = 0

    def _indice(self, clave: str) -> int:
        acumulado = 0
        for caracter in clave:
            acumulado = (acumulado * 33 + ord(caracter)) % self.capacidad
        return acumulado

    def _localizar(self, clave: str) -> Entrada | None:
        for entrada in self.cubetas[self._indice(clave)]:
            if entrada.clave == clave:
                return entrada
        return None

    def _anotar(self, operacion: str, clave: str, detalle: str) -> None:
        self.registro.append(
            {
                "tipo": "tabla",
                "op": operacion,
                "clave": clave,
                "detalle": detalle,
                "sesion": self.sesion,
                "turno": self.turno_actual,
            }
        )

    def buscar(self, clave: str) -> Entrada | None:
        entrada = self._localizar(clave)
        self._anotar("buscar", clave, "encontrado" if entrada else "ausente")
        return entrada

    def insertar(self, clave: str, tipo: str, aparicion: dict | None = None) -> Entrada | None:
        """Inserta si la clave no existe. Si existe, no duplica y devuelve None."""
        if self._localizar(clave) is not None:
            self._anotar("insertar", clave, "rechazado por duplicado")
            return None
        entrada = Entrada(clave=clave, tipo=tipo)
        if aparicion is not None:
            entrada.apariciones.append(dict(aparicion))
        self.cubetas[self._indice(clave)].append(entrada)
        self._anotar("insertar", clave, f"alta tipo {tipo}")
        return entrada

    def actualizar(self, clave: str, aparicion: dict) -> Entrada | None:
        entrada = self._localizar(clave)
        if entrada is None:
            self._anotar("actualizar", clave, "fallo: no existe")
            return None
        entrada.apariciones.append(dict(aparicion))
        self._anotar("actualizar", clave, "aparición agregada")
        return entrada

    def asegurar(self, clave: str, tipo: str, aparicion: dict | None = None) -> Entrada:
        """Busca y, según exista, inserta o actualiza. Es el uso normal del pipeline."""
        existente = self.buscar(clave)
        if existente is None:
            creada = self.insertar(clave, tipo, aparicion)
            if creada is None:
                raise RuntimeError(f"no se pudo insertar {clave}")
            return creada
        if aparicion is not None:
            actualizada = self.actualizar(clave, aparicion)
            if actualizada is None:
                raise RuntimeError(f"no se pudo actualizar {clave}")
            return actualizada
        return existente

    def entradas(self) -> list[Entrada]:
        return [entrada for cubeta in self.cubetas for entrada in cubeta]
