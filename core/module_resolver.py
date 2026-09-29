from __future__ import annotations

import os

from core.ast_nodes import Programa
from core.errors import ErrorDeImportacion
from core.lexer import tokenizar
from core.parser import parsear


def resolver_importaciones(programa: Programa, directorio_base: str) -> Programa:
    """Resuelve las importaciones (#expediente <archivo.eng>) de 'programa',
    fusionando las funciones de cada archivo importado dentro de
    'programa.funciones'. Modifica 'programa' en el lugar y lo devuelve.

    Solo se importan funciones (escena/proceso), no variables globales.

    Nota: si dos archivos distintos importan un mismo tercer archivo
    (importacion en 'diamante'), esta implementacion podria reportar un
    falso 'funcion duplicada'. No se resuelve aqui por quedar fuera del
    alcance minimo del proyecto (que solo requiere importaciones simples
    y una prueba de importacion circular).
    """
    _resolver(programa, directorio_base, pila=[programa.archivo_origen])
    return programa


def _resolver(programa: Programa, directorio_base: str, pila: list[str]) -> None:
    for importacion in programa.importaciones:
        ruta = os.path.join(directorio_base, importacion.archivo)

        if not os.path.isfile(ruta):
            raise ErrorDeImportacion(
                tipo="importacion",
                archivo=programa.archivo_origen,
                linea=importacion.linea,
                pista=f"No se encontró el archivo '{importacion.archivo}'.",
                descripcion=f"El archivo '{importacion.archivo}' no existe en '{directorio_base}'.",
                causa_posible="Revisa el nombre del archivo o su ubicación.",
            )

        if importacion.archivo in pila:
            cadena = " -> ".join(pila + [importacion.archivo])
            raise ErrorDeImportacion(
                tipo="importacion circular",
                archivo=programa.archivo_origen,
                linea=importacion.linea,
                pista="Hay una importación circular entre archivos.",
                descripcion=f"La cadena de importaciones {cadena} vuelve a un archivo ya en proceso.",
                causa_posible="Dos o más archivos se importan entre sí formando un ciclo.",
            )

        with open(ruta, encoding="utf-8") as archivo:
            codigo = archivo.read()

        tokens = tokenizar(codigo, importacion.archivo)
        programa_importado = parsear(tokens, importacion.archivo)

        _resolver(programa_importado, directorio_base, pila + [importacion.archivo])
        _fusionar_funciones(programa, programa_importado, importacion)


def _fusionar_funciones(programa: Programa, importado: Programa, importacion) -> None:
    for nombre, funcion in importado.funciones.items():
        if nombre in programa.funciones:
            raise ErrorDeImportacion(
                tipo="importacion",
                archivo=programa.archivo_origen,
                linea=importacion.linea,
                pista=f"La función '{nombre}' ya existe.",
                descripcion=(
                    f"'{nombre}' está declarada tanto en '{programa.archivo_origen}' "
                    f"como en el archivo importado '{importacion.archivo}'."
                ),
                causa_posible="Dos archivos declaran una función con el mismo nombre.",
            )
        programa.funciones[nombre] = funcion