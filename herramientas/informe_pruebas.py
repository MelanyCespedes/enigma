"""Corre los 20 programas de prueba y genera la tabla del enunciado (seccion 18).

Uso:
    python herramientas/informe_pruebas.py

Escribe docs/Pruebas_Programas.md con objetivo, entrada, resultado esperado, resultado obtenido
y estado de cada prueba. Termina con codigo 1 si alguna prueba no da lo esperado.
"""
from __future__ import annotations

import os
import re
import sys

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, RAIZ)

from tests.programas_prueba.casos import CASOS, Caso  # noqa: E402
from tests.programas_prueba.ejecutor import Resultado, correr  # noqa: E402

SALIDA = os.path.join(RAIZ, "docs", "Pruebas_Programas.md")


def _celda(texto: str) -> str:
    return texto.replace("|", "\\|").replace("\n", "<br>")


def _describir_entrada(caso: Caso) -> str:
    texto = f"`tests/programas_prueba/{caso.principal}`"
    if caso.entradas:
        texto += " · se escribe: " + ", ".join(f"`{e}`" for e in caso.entradas)
    return texto


def _describir_esperado(caso: Caso) -> str:
    if caso.es_valido:
        return "Compila y se ejecuta. Imprime:<br>" + "<br>".join(f"`{l}`" for l in caso.salida)
    return f"`{caso.error}` en `{caso.archivo}`, línea {caso.linea}: «{caso.fragmento}»"


def _sin_ruta_local(texto: str) -> str:
    """Deja las rutas relativas al proyecto: el informe no debe mostrar carpetas del equipo de quien lo genera."""
    return re.sub(r"[A-Za-z]:[\\/][^']*?tests[\\/]programas_prueba[\\/]", lambda _: "tests/programas_prueba/", texto)


def _describir_obtenido(resultado: Resultado) -> str:
    if resultado.exito:
        return "Compila y se ejecuta. Imprime:<br>" + "<br>".join(f"`{l}`" for l in resultado.salida)
    return (f"`{resultado.error}` ({resultado.etapa}) en `{resultado.archivo}`, línea {resultado.linea}: "
            f"{_sin_ruta_local(resultado.descripcion)}")


def _coincide(caso: Caso, resultado: Resultado) -> bool:
    if caso.es_valido:
        return resultado.exito and tuple(resultado.salida) == caso.salida
    return (not resultado.exito and resultado.error == caso.error and resultado.archivo == caso.archivo
            and resultado.linea == caso.linea and caso.fragmento in resultado.descripcion)


def main() -> int:
    filas, aprobadas = [], 0
    for caso in CASOS:
        resultado = correr(caso.principal, caso.entradas)
        ok = _coincide(caso, resultado)
        aprobadas += ok
        filas.append(
            f"| {caso.id} | {_celda(caso.categoria)} | {_celda(caso.objetivo)} | {_celda(_describir_entrada(caso))} "
            f"| {_celda(_describir_esperado(caso))} | {_celda(_describir_obtenido(resultado))} "
            f"| {'Aprobado' if ok else 'FALLIDO'} |"
        )

    lineas = [
        "# Programas de prueba (sección 18 del enunciado)",
        "",
        "Generado con `python herramientas/informe_pruebas.py`. No editar a mano.",
        "",
        f"**Resultado: {aprobadas} de {len(CASOS)} pruebas aprobadas.**",
        "",
        "Cinco programas válidos, cinco errores sintácticos, cinco errores semánticos, tres pruebas de "
        "importación, una importación circular y una prueba completa.",
        "",
        "| # | Tipo | Objetivo | Entrada | Resultado esperado | Resultado obtenido | Estado |",
        "|---|---|---|---|---|---|---|",
        *filas,
        "",
        "## Notas",
        "",
        "- El resultado esperado se dedujo de las reglas del lenguaje antes de ejecutar cada programa.",
        "- Hoy toda biblioteca importada necesita su propio bloque `caso` (por eso las bibliotecas de las "
        "pruebas I2, I3, C1 y P1 incluyen uno). Es una limitación conocida, no un requisito del lenguaje.",
        "- `valor` es palabra reservada y no puede usarse como nombre de parámetro.",
        "- `no(...)` solo puede aparecer al inicio de una condición; `a y no(b)` no es válido.",
        "",
    ]
    with open(SALIDA, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lineas))

    print(f"{aprobadas} de {len(CASOS)} pruebas aprobadas. Informe: {os.path.relpath(SALIDA, RAIZ)}")
    return 0 if aprobadas == len(CASOS) else 1


if __name__ == "__main__":
    sys.exit(main())
