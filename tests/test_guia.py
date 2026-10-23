"""La Guia del detective no puede mentir: todo ejemplo debe ser codigo valido."""
import builtins
import contextlib
import io
import re

import pytest

from core.interpreter import ejecutar
from core.lexer import tokenizar
from core.parser import parsear
from core.semantic import analizar
from gui import guia_contenido as guia
from gui.guia_contenido import Codigo, Ficha, Termino


def _envolver(fragmento: str) -> str:
    """Convierte un fragmento en un archivo completo para poder parsearlo."""
    if re.search(r"^\s*caso\s", fragmento, re.M):
        return fragmento
    if re.search(r"^\s*(escena|proceso|#expediente)\b", fragmento, re.M):
        return fragmento + "\ncaso T abierto\ncaso T cerrado!\n"
    return "caso T abierto\n" + fragmento + "\ncaso T cerrado!\n"


def _parsear(codigo: str):
    return parsear(tokenizar(codigo, "guia.eng"), "guia.eng")


def _bloques(tipo):
    return [(s.id, b) for s in guia.SECCIONES for b in s.bloques if isinstance(b, tipo)]


def test_las_diez_secciones_estan_y_cubren_lo_que_pide_el_pdf():
    ids = {s.id for s in guia.SECCIONES}
    # PDF seccion 10: palabras reservadas, sintaxis, estructuras de control, funciones,
    # operaciones, semantica, tipos de datos, importaciones y ejemplos.
    assert {"palabras", "sintaxis", "control", "funciones", "operaciones",
            "semantica", "tipos", "importaciones", "ejemplos"} <= ids
    assert len(ids) == len(guia.SECCIONES), "ids de seccion repetidos"
    assert all(s.bloques for s in guia.SECCIONES)


def test_la_guia_documenta_todas_las_palabras_reservadas():
    from core.tokens import PALABRAS_RESERVADAS

    documentadas = set()
    for _, termino in _bloques(Termino):
        for parte in re.split(r"\s*/\s*|\s+", termino.nombre):
            documentadas.add(parte)
    faltan = sorted(set(PALABRAS_RESERVADAS) - documentadas)
    assert faltan == [], f"palabras reservadas sin documentar en la guia: {faltan}"


@pytest.mark.parametrize("seccion,codigo", [
    (s, c) for s, c in _bloques(Codigo) if c.ejecutable
], ids=lambda v: v.titulo if isinstance(v, Codigo) else v)
def test_los_programas_completos_compilan_y_se_ejecutan(seccion, codigo, monkeypatch):
    entradas = list(codigo.entradas)
    monkeypatch.setattr(builtins, "input", lambda *a: entradas.pop(0))

    programa = _parsear(codigo.texto)
    analizar(programa)
    with contextlib.redirect_stdout(io.StringIO()):
        ejecutar(programa)


@pytest.mark.parametrize("seccion,codigo", [
    (s, c) for s, c in _bloques(Codigo) if not c.plantilla
], ids=lambda v: v.titulo if isinstance(v, Codigo) else v)
def test_todo_el_codigo_de_la_guia_es_sintacticamente_valido(seccion, codigo):
    _parsear(_envolver(codigo.texto))


@pytest.mark.parametrize("seccion,termino", [
    (s, t) for s, t in _bloques(Termino) if t.ejemplo
], ids=lambda v: v.nombre if isinstance(v, Termino) else v)
def test_los_ejemplos_de_las_palabras_reservadas_son_validos(seccion, termino):
    _parsear(_envolver(termino.ejemplo))


@pytest.mark.parametrize("seccion,ficha", _bloques(Ficha), ids=lambda v: v.nombre if isinstance(v, Ficha) else v)
def test_las_fichas_de_tipos_tienen_ejemplo_valido_y_los_cuatro_datos(seccion, ficha):
    assert ficha.declaracion and ficha.uso and ficha.operaciones and ficha.restricciones
    _parsear(_envolver(ficha.declaracion))


def test_el_ejemplo_de_importacion_funciona_con_dos_archivos(tmp_path):
    from core.module_resolver import resolver_importaciones

    codigos = {c.titulo: c.texto for _, c in _bloques(Codigo) if c.titulo.endswith(".eng")}
    assert set(codigos) == {"pistas.eng", "caso-042.eng"}
    for nombre, texto in codigos.items():
        (tmp_path / nombre).write_text(texto, encoding="utf-8")

    programa = _parsear(codigos["caso-042.eng"])
    programa.archivo_origen = "caso-042.eng"
    resolver_importaciones(programa, str(tmp_path))
    analizar(programa)

    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        ejecutar(programa)
    assert "culpable" in salida.getvalue()
