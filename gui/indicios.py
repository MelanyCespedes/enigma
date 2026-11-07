"""Indicios para el estudiante: orientan sin revelar donde esta el error (sin tkinter)."""
from __future__ import annotations

import random
import re

# Indicios de respaldo, por tipo de error (se usan si el indicio propio del error delata el lugar).
INDICIOS_GENERICOS = {
    "ErrorLexico": [
        "Hay un símbolo en tu código que Enigma no reconoce.",
        "Puede que haya un símbolo de más, o que te falte alguno.",
    ],
    "ErrorSintactico": [
        "Puede que te falte algo al final de alguna instrucción.",
        "Revisa que cada bloque que abriste también lo hayas cerrado.",
        "Algo en el orden de tu código no es el que Enigma espera.",
    ],
    "ErrorSemantico": [
        "Quizás olvidaste declarar algo en tu código.",
        "Puede que estés mezclando tipos de datos que no combinan.",
        "Revisa si intentaste cambiar algo que debía quedar fijo.",
        "Puede que una de tus funciones no reciba lo que esperaba.",
    ],
    "ErrorDeImportacion": [
        "Puede que un archivo que esperabas usar no esté donde lo buscaste.",
        "Revisa los nombres de los archivos que estás importando.",
    ],
    "ErrorDeEjecucion": [
        "Algo durante la ejecución no salió como lo planeaste.",
        "Revisa los valores que le estás dando a tus operaciones.",
    ],
}
INDICIO_POR_DEFECTO = "Hay algo que no cuadra en tu código. Revísalo con calma."

# Un indicio no debe delatar donde esta el error ni usar nombres internos del compilador.
_DELATA_LINEA = re.compile(r"l[ií]nea\s+\d+", re.IGNORECASE)
_NOMBRE_INTERNO = re.compile(r"\b[A-Z][A-Z_]{2,}\b")  # SELLO, FIN_DE_ARCHIVO, CASO...


def es_orientadora(indicio: str | None) -> bool:
    """True si el indicio sirve tal cual: no menciona una linea ni un nombre interno."""
    indicio = (indicio or "").strip()
    return bool(indicio) and not _DELATA_LINEA.search(indicio) and not _NOMBRE_INTERNO.search(indicio)


def elegir_indicio(indicio_propio: str | None, tipo_de_error: str) -> str:
    """El indicio que se le muestra al estudiante primero: el propio del error si orienta
    sin delatar el lugar; si no, uno general del tipo de error."""
    if es_orientadora(indicio_propio):
        return indicio_propio.strip()
    return random.choice(INDICIOS_GENERICOS.get(tipo_de_error, [INDICIO_POR_DEFECTO]))
