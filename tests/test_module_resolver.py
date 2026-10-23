import contextlib
import io

import pytest

from core.errors import ErrorDeEjecucion, ErrorDeImportacion, ErrorSemantico
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

# ---------- archivo correcto en los errores y subcarpetas ----------

def _cargar_proyecto(tmp_path, principal):
    ruta = tmp_path / principal
    programa = _leer_y_parsear(ruta, ruta.name)
    resolver_importaciones(programa, str(ruta.parent))
    return programa


def test_error_semantico_en_funcion_importada_reporta_el_archivo_importado(tmp_path):
    (tmp_path / "utilidades.eng").write_text(
        "proceso Saludar() inicio\n"
        "    revelar(variable_inexistente)!\n"
        "fin!\n\n"
        "caso U abierto\ncaso U cerrado!\n",
        encoding="utf-8",
    )
    (tmp_path / "principal.eng").write_text(
        "#expediente <utilidades.eng>\n\n"
        "caso Principal abierto\n"
        "    resolver Saludar()!\n"
        "caso Principal cerrado!\n",
        encoding="utf-8",
    )
    programa = _cargar_proyecto(tmp_path, "principal.eng")

    with pytest.raises(ErrorSemantico) as info:
        analizar(programa)

    assert info.value.archivo == "utilidades.eng"
    assert info.value.linea == 2


def test_error_de_ejecucion_en_funcion_importada_reporta_el_archivo_importado(tmp_path):
    (tmp_path / "utilidades.eng").write_text(
        "proceso Dividir() inicio\n"
        "    revelar(repartir(entero(valor: 1), entero(valor: 0)))!\n"
        "fin!\n\n"
        "caso U abierto\ncaso U cerrado!\n",
        encoding="utf-8",
    )
    (tmp_path / "principal.eng").write_text(
        "#expediente <utilidades.eng>\n\n"
        "caso Principal abierto\n"
        "    resolver Dividir()!\n"
        "caso Principal cerrado!\n",
        encoding="utf-8",
    )
    programa = _cargar_proyecto(tmp_path, "principal.eng")
    analizar(programa)

    with pytest.raises(ErrorDeEjecucion) as info:
        ejecutar(programa)

    assert info.value.archivo == "utilidades.eng"


def test_importar_desde_subcarpeta_busca_junto_al_archivo_que_importa(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "pistas.eng").write_text(
        "proceso Saludar() inicio\n    revelar('Hola desde src')!\nfin!\n\n"
        "caso P abierto\ncaso P cerrado!\n",
        encoding="utf-8",
    )
    (src / "principal.eng").write_text(
        "#expediente <pistas.eng>\n\n"
        "caso Principal abierto\n    resolver Saludar()!\ncaso Principal cerrado!\n",
        encoding="utf-8",
    )
    programa = _cargar_proyecto(tmp_path, "src/principal.eng")
    analizar(programa)

    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        ejecutar(programa)
    assert "Hola desde src" in salida.getvalue()


def test_importar_con_ruta_relativa_a_otra_carpeta(tmp_path):
    (tmp_path / "lib").mkdir()
    (tmp_path / "src").mkdir()
    (tmp_path / "lib" / "util.eng").write_text(
        "proceso Saludar() inicio\n    revelar('Hola desde lib')!\nfin!\n\n"
        "caso L abierto\ncaso L cerrado!\n",
        encoding="utf-8",
    )
    (tmp_path / "src" / "principal.eng").write_text(
        "#expediente <../lib/util.eng>\n\n"
        "caso Principal abierto\n    resolver Saludar()!\ncaso Principal cerrado!\n",
        encoding="utf-8",
    )
    programa = _cargar_proyecto(tmp_path, "src/principal.eng")
    assert "Saludar" in programa.funciones


def test_importacion_anidada_resuelve_cada_nivel_desde_su_carpeta(tmp_path):
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "a" / "b" / "hoja.eng").write_text(
        "proceso Hoja() inicio\n    revelar('hoja')!\nfin!\n\ncaso H abierto\ncaso H cerrado!\n",
        encoding="utf-8",
    )
    (tmp_path / "a" / "medio.eng").write_text(
        "#expediente <b/hoja.eng>\n\ncaso M abierto\ncaso M cerrado!\n",
        encoding="utf-8",
    )
    (tmp_path / "principal.eng").write_text(
        "#expediente <a/medio.eng>\n\ncaso P abierto\n    resolver Hoja()!\ncaso P cerrado!\n",
        encoding="utf-8",
    )
    programa = _cargar_proyecto(tmp_path, "principal.eng")
    assert "Hoja" in programa.funciones


def test_circular_entre_carpetas_se_detecta(tmp_path):
    (tmp_path / "x").mkdir()
    (tmp_path / "x" / "a.eng").write_text(
        "#expediente <../b.eng>\n\ncaso A abierto\ncaso A cerrado!\n", encoding="utf-8")
    (tmp_path / "b.eng").write_text(
        "#expediente <x/a.eng>\n\ncaso B abierto\ncaso B cerrado!\n", encoding="utf-8")
    (tmp_path / "principal.eng").write_text(
        "#expediente <x/a.eng>\n\ncaso P abierto\ncaso P cerrado!\n", encoding="utf-8")

    with pytest.raises(ErrorDeImportacion):
        _cargar_proyecto(tmp_path, "principal.eng")


def test_mismo_nombre_en_carpetas_distintas_no_es_circular(tmp_path):
    (tmp_path / "uno").mkdir()
    (tmp_path / "uno" / "datos.eng").write_text(
        "proceso A() inicio\n    revelar('a')!\nfin!\n\ncaso U abierto\ncaso U cerrado!\n",
        encoding="utf-8")
    (tmp_path / "datos.eng").write_text(
        "#expediente <uno/datos.eng>\n\ncaso D abierto\ncaso D cerrado!\n", encoding="utf-8")
    (tmp_path / "principal.eng").write_text(
        "#expediente <datos.eng>\n\ncaso P abierto\ncaso P cerrado!\n", encoding="utf-8")

    programa = _cargar_proyecto(tmp_path, "principal.eng")
    assert "A" in programa.funciones


def test_importacion_en_diamante_no_cuenta_como_funcion_duplicada(tmp_path):
    (tmp_path / "base.eng").write_text(
        "proceso Base() inicio\n    revelar('base')!\nfin!\n\ncaso B abierto\ncaso B cerrado!\n",
        encoding="utf-8")
    (tmp_path / "izq.eng").write_text(
        "#expediente <base.eng>\n\ncaso I abierto\ncaso I cerrado!\n", encoding="utf-8")
    (tmp_path / "der.eng").write_text(
        "#expediente <base.eng>\n\ncaso D abierto\ncaso D cerrado!\n", encoding="utf-8")
    (tmp_path / "principal.eng").write_text(
        "#expediente <izq.eng>\n#expediente <der.eng>\n\n"
        "caso P abierto\n    resolver Base()!\ncaso P cerrado!\n", encoding="utf-8")

    programa = _cargar_proyecto(tmp_path, "principal.eng")
    analizar(programa)
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        ejecutar(programa)
    assert "base" in salida.getvalue()
