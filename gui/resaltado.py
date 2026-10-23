"""Calculo del resaltado de sintaxis, sin depender de Tkinter.

Se usa un escaner con expresiones regulares (en vez del lexer) a proposito:
mientras el usuario escribe, el codigo casi siempre esta incompleto
(comentarios o cadenas sin cerrar), y el lexer lanzaria un error y dejaria el
editor sin colores. Este escaner nunca falla y, ademas, conserva los
comentarios y las posiciones exactas, que el lexer descarta.
"""
from __future__ import annotations

import re

from core.tokens import PALABRAS_RESERVADAS, TipoToken

PALABRA_CLAVE = "palabra_clave"
TIPO = "tipo"
TEXTO = "texto"
VARIABLE = "variable"
NUMERO = "numero"
COMENTARIO = "comentario"

ETIQUETAS = (PALABRA_CLAVE, TIPO, TEXTO, VARIABLE, NUMERO, COMENTARIO)

_TIPOS_DE_DATO = {
    TipoToken.ENTERO,
    TipoToken.DECIMAL,
    TipoToken.EXPRESION,
    TipoToken.DECLARACION,
    TipoToken.PISTAS,
    TipoToken.TABLERO,
}

_PATRON = re.compile(
    r"""
    (?P<comentario>\{[^}]*(?:\}|\Z))
  | (?P<texto>'[^']*(?:'|\Z))
  | (?P<importacion>\#[ \t]*expediente)(?P<espacio>[ \t]*)(?P<ruta><[^>\n]*>?)?
  | (?P<numero>\d+(?:\.\d+)?)
  | (?P<palabra>[^\W\d]\w*)
    """,
    re.VERBOSE,
)


def calcular_resaltado(codigo: str) -> list[tuple[str, int, int]]:
    """Devuelve una lista de (etiqueta, inicio, fin) con posiciones de
    caracter (fin exclusivo) dentro de 'codigo'."""
    resultado: list[tuple[str, int, int]] = []

    for m in _PATRON.finditer(codigo):
        if m.group("comentario") is not None:
            resultado.append((COMENTARIO, m.start(), m.end()))
        elif m.group("texto") is not None:
            resultado.append((TEXTO, m.start(), m.end()))
        elif m.group("importacion") is not None:
            resultado.append((PALABRA_CLAVE, m.start("importacion"), m.end("importacion")))
            if m.group("ruta") is not None:
                resultado.append((TEXTO, m.start("ruta"), m.end("ruta")))
        elif m.group("numero") is not None:
            resultado.append((NUMERO, m.start(), m.end()))
        else:
            tipo_token = PALABRAS_RESERVADAS.get(m.group("palabra"))
            if tipo_token is None:
                etiqueta = VARIABLE
            elif tipo_token in _TIPOS_DE_DATO:
                etiqueta = TIPO
            else:
                etiqueta = PALABRA_CLAVE
            resultado.append((etiqueta, m.start(), m.end()))

    return resultado
