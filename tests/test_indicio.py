import pytest

from gui.indicios import INDICIOS_GENERICOS as _INDICIOS_GENERICOS, elegir_indicio, es_orientadora


def test_usa_el_indicio_propio_si_orienta_sin_delatar_el_lugar():
    indicio = "No se puede consultar sobre el hecho 'limite'."
    assert elegir_indicio(indicio, "ErrorSemantico") == indicio


@pytest.mark.parametrize("indicio", [
    "Se esperaba SELLO cerca de la linea 5.",
    "Algo falla en la línea 12.",
    "Se encontro FIN_DE_ARCHIVO antes de tiempo.",
    "El token CASO no corresponde.",
])
def test_si_delata_la_linea_o_usa_nombres_internos_se_cambia_por_uno_general(indicio):
    elegido = elegir_indicio(indicio, "ErrorSintactico")
    assert elegido in _INDICIOS_GENERICOS["ErrorSintactico"]


@pytest.mark.parametrize("indicio", ["", "   ", None])
def test_sin_indicio_propio_usa_uno_general(indicio):
    assert elegir_indicio(indicio, "ErrorSemantico") in _INDICIOS_GENERICOS["ErrorSemantico"]


def test_tipo_de_error_desconocido_tiene_indicio_por_defecto():
    assert elegir_indicio("", "ErrorRaro")


def test_los_indicios_de_los_errores_reales_no_delatan_el_lugar():
    """Pasa varios programas con error por el compilador y revisa el indicio que vería el estudiante."""
    from core.errors import IndicioFallidoDeRazonamiento
    from core.lexer import tokenizar
    from core.parser import parsear
    from core.semantic import analizar

    programas = [
        "caso A abierto\n pista x = entero(valor: 1)\ncaso A cerrado!\n",             # falta !
        "caso A abierto\n revelar(y)!\ncaso A cerrado!\n",                             # variable inexistente
        "caso A abierto\n pista x = entero(valor: 1.5)!\ncaso A cerrado!\n",           # tipo
        "caso A abierto\n pista x = entero(valor: 1)!\ncaso B cerrado!\n",             # nombre de caso
        "caso A abierto\n { sin cerrar\ncaso A cerrado!\n",                            # comentario
        "caso A abierto\n evaluar si (1 == 1) inicio\n revelar(1)!\ncaso A cerrado!\n",  # falta fin
    ]
    for codigo in programas:
        with pytest.raises(IndicioFallidoDeRazonamiento) as info:
            analizar(parsear(tokenizar(codigo, "p.eng"), "p.eng"))
        error = info.value
        elegido = elegir_indicio(error.indicio, type(error).__name__)
        assert "linea" not in elegido.lower() and "línea" not in elegido.lower(), (codigo, elegido)


@pytest.mark.parametrize("indicio,esperado", [
    ("Revisa lo que declaraste.", True),
    ("Se esperaba SELLO.", False),
    ("Falla cerca de la linea 3.", False),
    ("", False),
    (None, False),
])
def test_es_orientadora(indicio, esperado):
    assert es_orientadora(indicio) is esperado


# ---------- indicios propios cuando falta un simbolo (parser_base) ----------


def _indicio_visto(codigo: str) -> str:
    from core.errors import ErrorSintactico
    from core.lexer import tokenizar
    from core.parser import parsear

    with pytest.raises(ErrorSintactico) as info:
        parsear(tokenizar(codigo, "p.eng"), "p.eng")
    return elegir_indicio(info.value.indicio, "ErrorSintactico")


def test_falta_el_sello_da_un_indicio_propio_y_no_uno_al_azar():
    codigo = "caso A abierto\n pista x = entero(valor: 1)\ncaso A cerrado!\n"
    assert _indicio_visto(codigo) == "Parece que falta algo al final de alguna instrucción."


def test_cada_error_de_simbolo_faltante_tiene_su_indicio_relacionado():
    sin_parentesis = "caso A abierto\n revelar('hola'!\ncaso A cerrado!\n"
    sin_fin = "caso A abierto\n evaluar si (1 == 1) inicio\n revelar(1)!\ncaso A cerrado!\n"
    sin_corchete = "caso A abierto\n pista x = pistas entero[1, 2!\ncaso A cerrado!\n"
    esperado = "Parece que algo no quedó bien abierto o cerrado."
    assert _indicio_visto(sin_parentesis) == _indicio_visto(sin_fin) == _indicio_visto(sin_corchete) == esperado


def test_los_indicios_de_simbolo_faltante_no_nombran_simbolos_ni_lineas():
    from core.parser_base import INDICIOS_POR_TOKEN_FALTANTE, INDICIO_FALTA_ALGO

    for indicio in [*INDICIOS_POR_TOKEN_FALTANTE.values(), INDICIO_FALTA_ALGO]:
        assert es_orientadora(indicio), indicio
        assert "!" not in indicio and not any(c.isdigit() for c in indicio), indicio


# ---------- ningun indicio revela nombres ni valores del programa ----------


def test_ningun_indicio_del_compilador_incluye_nombres_ni_valores():
    """Recorre core/ y comprueba que ningun 'indicio=' sea un f-string: un f-string interpola nombres,
    tipos, operadores o cantidades del programa, y eso es parte de la explicacion completa, no del indicio."""
    import ast
    import glob
    import os

    raiz = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    interpolados = []
    revisados = 0
    for ruta in glob.glob(os.path.join(raiz, "core", "*.py")):
        arbol = ast.parse(open(ruta, encoding="utf-8").read())
        for nodo in ast.walk(arbol):
            if isinstance(nodo, ast.Call):
                for kw in nodo.keywords:
                    if kw.arg == "indicio":
                        revisados += 1
                        if isinstance(kw.value, ast.JoinedStr):
                            interpolados.append(f"{os.path.basename(ruta)}:{nodo.lineno}")
    assert revisados > 50  # el recorrido encontro los indicios (hay mas de 50 en core/)
    assert not interpolados, f"indicios con nombres o valores del programa: {interpolados}"


def test_una_constante_en_mayusculas_no_hace_que_se_pierda_el_indicio():
    """Antes, un nombre como MAX se tomaba por un nombre interno y el indicio se cambiaba por una frase al azar."""
    from core.ast_nodes import Asignacion, CasoPrincipal, DeclaracionPista, Literal, Programa
    from core.errors import ErrorSemantico
    from core.semantic import analizar

    programa = Programa(
        importaciones=[],
        declaraciones_globales=[DeclaracionPista("MAX", Literal("entero", 3), True, 1)],
        funciones={},
        caso_principal=CasoPrincipal("P", [Asignacion("MAX", Literal("entero", 4), 3)], 1),
        archivo_origen="p.eng",
    )
    with pytest.raises(ErrorSemantico) as info:
        analizar(programa)
    elegidos = {elegir_indicio(info.value.indicio, "ErrorSemantico") for _ in range(30)}
    assert elegidos == {"Parece que intentas cambiar algo que debía quedar fijo."}
