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

    'directorio_base' es la carpeta del archivo principal. Cada importacion se
    busca relativa a la carpeta del archivo que la escribe (como #include en C),
    asi que un archivo en 'src/' que importa <pistas.eng> usa 'src/pistas.eng',
    y se permiten rutas como <../lib/util.eng> o <sub/otro.eng>.

    Solo se importan funciones (escena/proceso), no variables globales.
    Un mismo archivo importado por varios caminos (importacion en 'diamante')
    se lee una sola vez y no cuenta como funcion duplicada.
    """
    base = os.path.abspath(directorio_base)
    principal = os.path.join(base, programa.archivo_origen)
    _resolver(
        programa,
        directorio=os.path.dirname(principal),
        base=base,
        pila_rutas=[_clave(principal)],
        pila_nombres=[programa.archivo_origen],
        cache={},
    )
    return programa


def _clave(ruta: str) -> str:
    return os.path.normcase(os.path.abspath(ruta))


def _nombre_para_mostrar(ruta: str, base: str) -> str:
    """Ruta relativa a la carpeta del archivo principal, con '/' siempre."""
    return os.path.relpath(ruta, base).replace(os.sep, "/")


def _resolver(
    programa: Programa,
    directorio: str,
    base: str,
    pila_rutas: list[str],
    pila_nombres: list[str],
    cache: dict[str, Programa],
) -> None:
    for importacion in programa.importaciones:
        ruta = os.path.normpath(os.path.join(directorio, importacion.archivo))
        nombre = _nombre_para_mostrar(ruta, base)

        if not os.path.isfile(ruta):
            raise ErrorDeImportacion(
                tipo="importación",
                archivo=programa.archivo_origen,
                linea=importacion.linea,
                indicio="Parece que un archivo que importas no está donde se esperaba.",
                descripcion=f"El archivo '{importacion.archivo}' no existe en '{directorio}'.",
                causa_posible="Revisa el nombre del archivo o su ubicación (se busca junto al archivo que lo importa).",
            )

        if _clave(ruta) in pila_rutas:
            cadena = " -> ".join(pila_nombres + [nombre])
            raise ErrorDeImportacion(
                tipo="importación circular",
                archivo=programa.archivo_origen,
                linea=importacion.linea,
                indicio="Hay una importación circular entre archivos.",
                descripcion=f"La cadena de importaciones {cadena} vuelve a un archivo ya en proceso.",
                causa_posible="Dos o más archivos se importan entre sí formando un ciclo.",
            )

        programa_importado = cache.get(_clave(ruta))
        if programa_importado is None:
            with open(ruta, encoding="utf-8") as archivo:
                codigo = archivo.read()

            tokens = tokenizar(codigo, nombre)
            programa_importado = parsear(tokens, nombre)
            cache[_clave(ruta)] = programa_importado

            _resolver(
                programa_importado,
                directorio=os.path.dirname(ruta),
                base=base,
                pila_rutas=pila_rutas + [_clave(ruta)],
                pila_nombres=pila_nombres + [nombre],
                cache=cache,
            )

        _fusionar_funciones(programa, programa_importado, importacion)


def _fusionar_funciones(programa: Programa, importado: Programa, importacion) -> None:
    for nombre, funcion in importado.funciones.items():
        existente = programa.funciones.get(nombre)
        if existente is funcion:
            continue  # la misma funcion llegada por otro camino (diamante)
        if existente is not None:
            raise ErrorDeImportacion(
                tipo="importación",
                archivo=programa.archivo_origen,
                linea=importacion.linea,
                indicio="Parece que dos archivos definen una función con el mismo nombre.",
                descripcion=(
                    f"'{nombre}' está declarada tanto en '{existente.archivo or programa.archivo_origen}' "
                    f"como en el archivo importado '{funcion.archivo or importacion.archivo}'."
                ),
                causa_posible="Dos archivos declaran una función con el mismo nombre.",
            )
        programa.funciones[nombre] = funcion
