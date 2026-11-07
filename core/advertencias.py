"""Advertencias del compilador (seccion 12 del enunciado).

Una advertencia senala algo sospechoso pero valido: el programa compila y se ejecuta igual.
Se buscan despues del analisis semantico, recorriendo el AST ya verificado.

Tres advertencias:
  1. Pista declarada y nunca usada.
  2. Codigo despues de 'concluir', que nunca se ejecuta.
  3. Parametro que la funcion nunca usa.

(Una escena sin ningun 'concluir' no es advertencia: es un error semantico, ver semantic.py.)
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Iterator

from core.ast_nodes import Concluir, DeclaracionPista, Identificador, Programa, recorrer
from core.errors import ErrorSintactico
from core.parser import parsear
from core.tokens import TipoToken, Token


PISTA_SIN_USAR = "pista_sin_usar"
CODIGO_INALCANZABLE = "codigo_inalcanzable"
PARAMETRO_SIN_USAR = "parametro_sin_usar"

# Como se nombra cada tipo en el resumen (singular, plural). El orden es el del resumen.
TIPOS = {
    PISTA_SIN_USAR: ("pista declarada que nunca se usa", "pistas declaradas que nunca se usan"),
    PARAMETRO_SIN_USAR: ("parámetro que nunca se usa", "parámetros que nunca se usan"),
    CODIGO_INALCANZABLE: ("bloque de código que nunca se ejecuta", "bloques de código que nunca se ejecutan"),
}


@dataclass(frozen=True)
class Advertencia:
    archivo: str
    linea: int
    descripcion: str
    causa_posible: str
    tipo: str = ""

    def mostrar_completo(self) -> str:
        # Mismo formato que los errores (seccion 12): archivo, linea, descripcion y posible causa.
        return (
            "Advertencia\n"
            f"Archivo: {self.archivo}\n"
            f"Linea: {self.linea}\n"
            f"Descripcion: {self.descripcion}\n"
            f"Posible causa: {self.causa_posible}"
        )

    __str__ = mostrar_completo

    @property
    def firma(self) -> tuple:
        """Identifica la advertencia entre compilaciones (para saber si sigue siendo la misma)."""
        return (self.archivo, self.linea, self.descripcion)


def resumen_por_tipo(advertencias: list[Advertencia]) -> list[str]:
    """Primer aviso: cuantas hay de cada tipo, sin decir donde ni cuales son."""
    lineas = []
    for tipo, (singular, plural) in TIPOS.items():
        cantidad = sum(1 for a in advertencias if a.tipo == tipo)
        if cantidad:
            lineas.append(f"{cantidad} {singular if cantidad == 1 else plural}")
    return lineas


def _listas(obj) -> Iterator[list]:
    """Todas las listas de nodos (cuerpos de bloques, argumentos...) dentro de 'obj'."""
    if isinstance(obj, list):
        yield obj
        for elemento in obj:
            yield from _listas(elemento)
    elif is_dataclass(obj):
        for campo in fields(obj):
            yield from _listas(getattr(obj, campo.name))


def _nombres_usados(cuerpo: list) -> set[str]:
    return {n.nombre for n in recorrer(cuerpo) if isinstance(n, Identificador)}


def _pistas_sin_usar(cuerpo: list, usados: set[str], archivo: str) -> list[Advertencia]:
    resultado = []
    for nodo in recorrer(cuerpo):
        if isinstance(nodo, DeclaracionPista) and nodo.nombre not in usados:
            resultado.append(Advertencia(
                archivo, nodo.linea,
                f"La pista '{nodo.nombre}' se declaró pero nunca se usa.",
                "Quedó sin usar, o falta incluirla en un cálculo o en un 'revelar'.",
                PISTA_SIN_USAR,
            ))
    return resultado


def _codigo_inalcanzable(cuerpo: list, archivo: str) -> list[Advertencia]:
    resultado = []
    for lista in _listas(cuerpo):
        for posicion, sentencia in enumerate(lista[:-1]):
            if isinstance(sentencia, Concluir):
                siguiente = lista[posicion + 1]
                resultado.append(Advertencia(
                    archivo, getattr(siguiente, "linea", sentencia.linea),
                    "Este código está después de 'concluir' y nunca se ejecuta.",
                    "'concluir' termina la escena; lo que sigue en el mismo bloque se ignora.",
                    CODIGO_INALCANZABLE,
                ))
                break
    return resultado


def _advertencias_de_funcion(funcion, archivo: str) -> list[Advertencia]:
    resultado = []
    usados = _nombres_usados(funcion.cuerpo)

    for parametro in funcion.parametros:
        if parametro.nombre not in usados:
            resultado.append(Advertencia(
                archivo, funcion.linea,
                f"El parámetro '{parametro.nombre}' de '{funcion.nombre}' nunca se usa.",
                "Sobra el parámetro, o falta usarlo dentro de la función.",
                PARAMETRO_SIN_USAR,
            ))

    resultado += _pistas_sin_usar(funcion.cuerpo, usados, archivo)
    resultado += _codigo_inalcanzable(funcion.cuerpo, archivo)
    return resultado


MAX_REPARACIONES = 20


def advertencias_tras_error_de_sintaxis(tokens: list[Token], archivo: str, error: ErrorSintactico) -> list[Advertencia]:
    """Advertencias de un codigo al que solo le faltan sellos ('!').

    Con un error de sintaxis el parser se detiene y no hay arbol que revisar. Cuando lo que falta es un
    '!' (el descuido mas comun) se supone que el estudiante iba a ponerlo: se agrega solo para poder seguir
    leyendo y asi avisar tambien de lo demas. El error que se muestra sigue siendo el original.
    Con cualquier otro error de sintaxis no hay forma segura de continuar y devuelve [].
    """
    tokens = list(tokens)  # se trabaja sobre una copia: los tokens originales no cambian
    for _ in range(MAX_REPARACIONES):
        if getattr(error, "esperado", None) != TipoToken.SELLO:
            return []
        tokens.insert(error.posicion, Token(TipoToken.SELLO, "!", None, error.linea, 0))
        try:
            return buscar_advertencias(parsear(tokens, archivo))
        except ErrorSintactico as siguiente:
            error = siguiente
    return []


def buscar_advertencias(programa: Programa) -> list[Advertencia]:
    """Devuelve las advertencias del programa ordenadas por archivo y linea."""
    principal = programa.archivo_origen
    caso = programa.caso_principal
    resultado: list[Advertencia] = []

    # Las pistas globales se pueden usar desde cualquier parte, asi que se mira todo el programa.
    todo = [programa.declaraciones_globales, caso.cuerpo, *(f.cuerpo for f in programa.funciones.values())]
    resultado += _pistas_sin_usar(programa.declaraciones_globales, _nombres_usados(todo), principal)

    resultado += _pistas_sin_usar(caso.cuerpo, _nombres_usados(caso.cuerpo), principal)
    resultado += _codigo_inalcanzable(caso.cuerpo, principal)

    for funcion in programa.funciones.values():
        resultado += _advertencias_de_funcion(funcion, funcion.archivo or principal)

    return sorted(resultado, key=lambda a: (a.archivo != principal, a.archivo, a.linea))
