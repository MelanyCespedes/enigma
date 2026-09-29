import contextlib
import io

import pytest

from core.errors import ErrorDeImportacion
from core.interpreter import ejecutar
from core.lexer import tokenizar
from core.module_resolver import resolver_importaciones
from core.parser import parsear
from core.semantic import analizar


def _leer_y_parsear(ruta, nombre_archivo):
    codigo = ruta.read_text(encoding="utf-8")
    tokens = tokenizar(codigo, nombre_archivo)
    return parsear(tokens, nombre_archivo)


def test_importar_archivo_existente_fusiona_funciones(tmp_path):
    (tmp_path / "utilidades.eng").write_text(
        "proceso Saludar(nombre: expresion) inicio\n"
        "    revelar('Hola', nombre)!\n"
        "fin!\n\n"
        "caso Utilidades abierto\n"
        "caso Utilidades cerrado!\n",
        encoding="utf-8",
    )
    (tmp_path / "principal.eng").write_text(
        "#expediente <utilidades.eng>\n\n"
        "caso Principal abierto\n"
        "    resolver Saludar('Ana')!\n"
        "caso Principal cerrado!\n",
        encoding="utf-8",
    )

    programa = _leer_y_parsear(tmp_path / "principal.eng", "principal.eng")
    resolver_importaciones(programa, str(tmp_path))

    assert "Saludar" in programa.funciones

    analizar(programa)

    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        ejecutar(programa)
    assert "Hola" in salida.getvalue() and "Ana" in salida.getvalue()


def test_importar_archivo_inexistente_lanza_error(tmp_path):
    (tmp_path / "principal.eng").write_text(
        "#expediente <no_existe.eng>\n\n"
        "caso Principal abierto\n"
        "caso Principal cerrado!\n",
        encoding="utf-8",
    )

    programa = _leer_y_parsear(tmp_path / "principal.eng", "principal.eng")

    with pytest.raises(ErrorDeImportacion):
        resolver_importaciones(programa, str(tmp_path))


def test_importar_funcion_duplicada_lanza_error(tmp_path):
    (tmp_path / "utilidades.eng").write_text(
        "proceso Saludar(nombre: expresion) inicio\n"
        "    revelar('Hola', nombre)!\n"
        "fin!\n\n"
        "caso Utilidades abierto\n"
        "caso Utilidades cerrado!\n",
        encoding="utf-8",
    )
    (tmp_path / "principal.eng").write_text(
        "#expediente <utilidades.eng>\n\n"
        "proceso Saludar(nombre: expresion) inicio\n"
        "    revelar('Otra vez', nombre)!\n"
        "fin!\n\n"
        "caso Principal abierto\n"
        "caso Principal cerrado!\n",
        encoding="utf-8",
    )

    programa = _leer_y_parsear(tmp_path / "principal.eng", "principal.eng")

    with pytest.raises(ErrorDeImportacion):
        resolver_importaciones(programa, str(tmp_path))


def test_importacion_circular_lanza_error(tmp_path):
    (tmp_path / "a.eng").write_text(
        "#expediente <b.eng>\n\n"
        "caso CasoA abierto\n"
        "caso CasoA cerrado!\n",
        encoding="utf-8",
    )
    (tmp_path / "b.eng").write_text(
        "#expediente <a.eng>\n\n"
        "caso CasoB abierto\n"
        "caso CasoB cerrado!\n",
        encoding="utf-8",
    )

    programa = _leer_y_parsear(tmp_path / "a.eng", "a.eng")

    with pytest.raises(ErrorDeImportacion):
        resolver_importaciones(programa, str(tmp_path))