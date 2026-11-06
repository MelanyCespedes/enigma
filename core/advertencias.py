"""Advertencias del compilador (seccion 12 del enunciado).

Una advertencia senala algo sospechoso pero valido: el programa compila y se ejecuta igual.
Se buscan despues del analisis semantico, recorriendo el AST ya verificado.

Cuatro advertencias:
  1. Pista declarada y nunca usada.
  2. Codigo despues de 'concluir', que nunca se ejecuta.
  3. Escena que no tiene ningun 'concluir'.
  4. Parametro que la funcion nunca usa.
"""
from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from typing import Iterator

from core.ast_nodes import Concluir, DeclaracionPista, Escena, Identificador, Programa


@dataclass(frozen=True)
class Advertencia:
    archivo: str
    linea: int
    descripcion: str
    causa_posible: str

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


def _nodos(obj) -> Iterator[object]:
    """Todos los nodos del AST que cuelgan de 'obj' (incluido el propio), a cualquier profundidad."""
    if isinstance(obj, list):
        for elemento in obj:
            yield from _nodos(elemento)
    elif is_dataclass(obj):
        yield obj
        for campo in fields(obj):
            yield from _nodos(getattr(obj, campo.name))


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
    return {n.nombre for n in _nodos(cuerpo) if isinstance(n, Identificador)}


def _pistas_sin_usar(cuerpo: list, usados: set[str], archivo: str) -> list[Advertencia]:
    resultado = []
    for nodo in _nodos(cuerpo):
        if isinstance(nodo, DeclaracionPista) and nodo.nombre not in usados:
            resultado.append(Advertencia(
                archivo, nodo.linea,
                f"La pista '{nodo.nombre}' se declaró pero nunca se usa.",
                "Quedó sin usar, o falta incluirla en un cálculo o en un 'revelar'.",
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
            ))

    if isinstance(funcion, Escena) and not any(isinstance(n, Concluir) for n in _nodos(funcion.cuerpo)):
        resultado.append(Advertencia(
            archivo, funcion.linea,
            f"La escena '{funcion.nombre}' promete devolver '{funcion.tipo_retorno}' pero no tiene 'concluir'.",
            "Falta 'concluir' para entregar el valor; si no devuelve nada, debería ser un proceso.",
        ))

    resultado += _pistas_sin_usar(funcion.cuerpo, usados, archivo)
    resultado += _codigo_inalcanzable(funcion.cuerpo, archivo)
    return resultado


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
