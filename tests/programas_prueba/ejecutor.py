"""Corre un programa .eng de punta a punta (como lo hace el IDE) y describe el resultado.

Lo usan `tests/test_programas_prueba.py` y `herramientas/informe_pruebas.py`.
"""
from __future__ import annotations

import builtins
import contextlib
import io
import os
from dataclasses import dataclass

from core.errors import IndicioFallidoDeRazonamiento
from core.interpreter import ejecutar
from core.lexer import tokenizar
from core.module_resolver import resolver_importaciones
from core.parser import parsear
from core.semantic import analizar

CARPETA = os.path.dirname(os.path.abspath(__file__))


@dataclass
class Resultado:
    exito: bool
    salida: list[str]              # lineas que imprimio el programa
    etapa: str = ""                # compilacion | ejecucion (solo si hubo error)
    error: str = ""                # nombre de la clase del error
    archivo: str = ""
    linea: int = 0
    descripcion: str = ""


def correr(ruta_relativa: str, entradas: tuple[str, ...] = ()) -> Resultado:
    """Compila y ejecuta `ruta_relativa` (respecto a tests/programas_prueba)."""
    ruta = os.path.join(CARPETA, *ruta_relativa.split("/"))
    nombre = os.path.basename(ruta)
    pendientes = list(entradas)
    etapa = "compilacion"
    salida = io.StringIO()
    entrada_original = builtins.input

    def leer(_mensaje: str = "") -> str:
        return pendientes.pop(0) if pendientes else ""

    try:
        with open(ruta, encoding="utf-8") as f:
            codigo = f.read()
        programa = parsear(tokenizar(codigo, nombre), nombre)
        resolver_importaciones(programa, os.path.dirname(ruta))
        analizar(programa)
        etapa = "ejecucion"
        builtins.input = leer
        with contextlib.redirect_stdout(salida):
            ejecutar(programa)
    except IndicioFallidoDeRazonamiento as error:
        return Resultado(
            False, salida.getvalue().splitlines(), etapa, type(error).__name__,
            error.archivo, error.linea, error.descripcion,
        )
    finally:
        builtins.input = entrada_original
    return Resultado(True, salida.getvalue().splitlines())
