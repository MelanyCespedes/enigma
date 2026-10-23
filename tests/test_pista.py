import pytest

from gui.pistas import PISTAS_GENERICAS as _PISTAS_GENERICAS, elegir_pista, es_orientadora


def test_usa_la_pista_propia_si_orienta_sin_delatar_el_lugar():
    pista = "No se puede consultar sobre el hecho 'limite'."
    assert elegir_pista(pista, "ErrorSemantico") == pista


@pytest.mark.parametrize("pista", [
    "Se esperaba SELLO cerca de la linea 5.",
    "Algo falla en la línea 12.",
    "Se encontro FIN_DE_ARCHIVO antes de tiempo.",
    "El token CASO no corresponde.",
])
def test_si_delata_la_linea_o_usa_nombres_internos_se_cambia_por_una_general(pista):
    elegida = elegir_pista(pista, "ErrorSintactico")
    assert elegida in _PISTAS_GENERICAS["ErrorSintactico"]


@pytest.mark.parametrize("pista", ["", "   ", None])
def test_sin_pista_propia_usa_una_general(pista):
    assert elegir_pista(pista, "ErrorSemantico") in _PISTAS_GENERICAS["ErrorSemantico"]


def test_tipo_de_error_desconocido_tiene_pista_por_defecto():
    assert elegir_pista("", "ErrorRaro")


def test_las_pistas_de_los_errores_reales_no_delatan_el_lugar():
    """Pasa varios programas con error por el compilador y revisa la pista que vería el estudiante."""
    from core.errors import PistaFallidaDeRazonamiento
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
        with pytest.raises(PistaFallidaDeRazonamiento) as info:
            analizar(parsear(tokenizar(codigo, "p.eng"), "p.eng"))
        error = info.value
        elegida = elegir_pista(error.pista, type(error).__name__)
        assert "linea" not in elegida.lower() and "línea" not in elegida.lower(), (codigo, elegida)


@pytest.mark.parametrize("pista,esperado", [
    ("Revisa lo que declaraste.", True),
    ("Se esperaba SELLO.", False),
    ("Falla cerca de la linea 3.", False),
    ("", False),
    (None, False),
])
def test_es_orientadora(pista, esperado):
    assert es_orientadora(pista) is esperado
