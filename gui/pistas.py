"""Pistas para el estudiante: orientan sin revelar donde esta el error (sin tkinter)."""
from __future__ import annotations

import random
import re

# Pistas de respaldo, por tipo de error (se usan si la pista propia del error delata el lugar).
PISTAS_GENERICAS = {
    "ErrorLexico": [
        "Hay un símbolo en tu código que Enigma no reconoce.",
        "Puede que haya un símbolo de más, o que te falte alguno.",
    ],
    "ErrorSintactico": [
        "Puede que te falte un '!' al final de alguna instrucción.",
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
PISTA_POR_DEFECTO = "Hay algo que no cuadra en tu código. Revísalo con calma."

# Una pista no debe delatar donde esta el error ni usar nombres internos del compilador.
_DELATA_LINEA = re.compile(r"l[ií]nea\s+\d+", re.IGNORECASE)
_NOMBRE_INTERNO = re.compile(r"\b[A-Z][A-Z_]{2,}\b")  # SELLO, FIN_DE_ARCHIVO, CASO...


def es_orientadora(pista: str | None) -> bool:
    """True si la pista sirve tal cual: no menciona una linea ni un nombre interno."""
    pista = (pista or "").strip()
    return bool(pista) and not _DELATA_LINEA.search(pista) and not _NOMBRE_INTERNO.search(pista)


def elegir_pista(pista_propia: str | None, tipo_de_error: str) -> str:
    """La pista que se le muestra al estudiante primero: la propia del error si orienta
    sin delatar el lugar; si no, una pista general del tipo de error."""
    if es_orientadora(pista_propia):
        return pista_propia.strip()
    return random.choice(PISTAS_GENERICAS.get(tipo_de_error, [PISTA_POR_DEFECTO]))
