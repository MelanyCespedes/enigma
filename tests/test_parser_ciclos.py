import pytest

from core.errors import ErrorSintactico
from core.ast_nodes import Literal, Identificador, OperacionRelacional, Rastrear, SeguirMientras
from tests.helpers import parsear_codigo as _parsear


def test_rastrear_desde_hasta():
    codigo = (
        "caso Prueba abierto "
        "rastrear pasos desde 1 hasta 10 inicio revelar(pasos)! fin! "
        "caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    (rastrear,) = programa.caso_principal.cuerpo
    assert isinstance(rastrear, Rastrear)
    assert rastrear.variable == "pasos"
    assert rastrear.desde == Literal(tipo="entero", valor=1)
    assert rastrear.hasta == Literal(tipo="entero", valor=10)
    assert len(rastrear.cuerpo) == 1


def test_seguir_mientras():
    codigo = (
        "caso Prueba abierto "
        "seguir mientras (pista1 > pista2) inicio revelar('sigue')! fin! "
        "caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    (seguir,) = programa.caso_principal.cuerpo
    assert isinstance(seguir, SeguirMientras)
    assert seguir.condicion == OperacionRelacional(
        operador=">",
        izquierda=Identificador(nombre="pista1"),
        derecha=Identificador(nombre="pista2"),
    )
    assert len(seguir.cuerpo) == 1


def test_rastrear_anidado_en_seguir_mientras():
    codigo = (
        "caso Prueba abierto "
        "seguir mientras (activo == culpable) inicio "
        "rastrear i desde 0 hasta 5 inicio revelar(i)! fin! "
        "fin! "
        "caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    (seguir,) = programa.caso_principal.cuerpo
    (rastrear,) = seguir.cuerpo
    assert isinstance(rastrear, Rastrear)
    assert rastrear.variable == "i"


def test_error_rastrear_sin_hasta():
    codigo = "caso Prueba abierto rastrear i desde 0 inicio revelar(i)! fin! caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_seguir_mientras_sin_parentesis():
    codigo = "caso Prueba abierto seguir mientras activo inicio fin! caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)
