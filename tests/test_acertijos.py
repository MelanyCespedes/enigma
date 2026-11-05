import contextlib
import io
from pathlib import Path

from core.interpreter import ejecutar
from core.lexer import tokenizar
from core.parser import parsear
from core.semantic import analizar


RAIZ = Path(__file__).resolve().parents[1]


def ejecutar_acertijo(ruta_relativa: str) -> str:
    ruta = RAIZ / ruta_relativa
    codigo = ruta.read_text(encoding="utf-8")
    programa = parsear(tokenizar(codigo, str(ruta)), str(ruta))
    analizar(programa)

    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        ejecutar(programa)
    return salida.getvalue()


def test_acertijo_caja_fuerte():
    salida = ejecutar_acertijo(
        "ejemplos/acertijo_caja_fuerte/caja_fuerte.eng"
    )

    assert "Codigo calculado: 64" in salida
    assert "La caja se abre" in salida


def test_acertijo_sospechosos():
    salida = ejecutar_acertijo(
        "ejemplos/acertijo_sospechosos/galeria_sospechosos.eng"
    )

    assert "El sospechoso A queda descartado." in salida
    assert "El sospechoso B es el culpable" in salida
