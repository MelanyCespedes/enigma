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
