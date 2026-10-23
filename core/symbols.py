from __future__ import annotations
from dataclasses import dataclass
from typing import Optional

from core.errors import ErrorSemantico


@dataclass
class Simbolo:
    nombre: str
    tipo: str 
    es_constante: bool
    linea: int
    ambito: str
    # Si nacio como 'entero(valor: sin_pista)': tipo que tendra al recibir un valor
    tipo_declarado: str = ""


class TablaSimbolos:
    """Pila de ambitos. El ambito global siempre es el de la posicion 0."""

    def __init__(self, archivo: str):
        self.archivo = archivo
        self._ambitos: list[dict[str, Simbolo]] = [{}]
        self._nombres: list[str] = ["global"]


    def entrar_ambito(self, nombre: str) -> None:
        self._ambitos.append({})
        self._nombres.append(nombre)

    def salir_ambito(self) -> None:
        if len(self._ambitos) == 1:
            raise RuntimeError("No se puede salir del ambito global")
        self._ambitos.pop()
        self._nombres.pop()

    @property
    def ambito_actual(self) -> str:
        return self._nombres[-1]


    def declarar(
        self, nombre: str, tipo: str, es_constante: bool, linea: int, tipo_declarado: str = ""
    ) -> Simbolo:
        ambito = self._ambitos[-1]

        if nombre in ambito:
            previo = ambito[nombre]
            raise ErrorSemantico(
                tipo="semantica",
                archivo=self.archivo,
                linea=linea,
                pista=f"La pista '{nombre}' ya tiene dueno en este bloque.",
                descripcion=(
                    f"'{nombre}' ya fue declarada en la linea {previo.linea} "
                    f"dentro del ambito '{self.ambito_actual}'."
                ),
                causa_posible="Se declaro dos veces la misma variable o funcion en el mismo bloque.",
            )

        simbolo = Simbolo(
            nombre=nombre,
            tipo=tipo,
            es_constante=es_constante,
            linea=linea,
            ambito=self.ambito_actual,
            tipo_declarado=tipo_declarado,
        )
        ambito[nombre] = simbolo
        return simbolo

    def buscar(self, nombre: str) -> Optional[Simbolo]:
        """Busca de adentro hacia afuera. Devuelve None si no existe."""
        for ambito in reversed(self._ambitos):
            if nombre in ambito:
                return ambito[nombre]
        return None

    def existe(self, nombre: str) -> bool:
        return self.buscar(nombre) is not None