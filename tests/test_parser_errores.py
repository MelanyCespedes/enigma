import pytest

from core.errors import ErrorSintactico
from tests.helpers import parsear_codigo as _parsear


def test_error_1_sentencia_sin_sello_final():
    """Falta el '!' que termina una sentencia ejecutable."""
    codigo = "caso Prueba abierto pista x = entero(valor: 15) caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_2_caso_principal_sin_abierto():
    """Falta la palabra 'abierto' al declarar el caso principal."""
    codigo = "caso Prueba pista x = entero(valor: 15)! caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_3_nombre_de_cierre_no_coincide():
    """El nombre del caso al cerrar no coincide con el de la apertura."""
    codigo = "caso Prueba abierto caso Otro cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_4_parentesis_sin_cerrar():
    """Una llamada (revelar) se queda sin cerrar el parentesis."""
    codigo = "caso Prueba abierto revelar('hola'! caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_5_bloque_de_control_sin_fin():
    """Un bloque evaluar-si nunca cierra con 'fin'."""
    codigo = "caso Prueba abierto evaluar si (a == 1) inicio revelar('x')! caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


# cobertura adicional sobre el formato del error


def test_error_falta_sello_al_cerrar_caso():
    codigo = "caso Prueba abierto caso Prueba cerrado"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_incluye_archivo_y_linea():
    codigo = "caso Prueba abierto\npista x = entero(valor: 15)\ncaso Prueba cerrado!"
    with pytest.raises(ErrorSintactico) as info:
        _parsear(codigo)
    assert info.value.archivo == "prueba.eng"
    assert info.value.linea == 2  # el '!' falta al final de la linea 2, no en la linea del token siguiente
