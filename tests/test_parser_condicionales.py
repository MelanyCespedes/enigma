import pytest

from core.errors import ErrorSintactico
from core.ast_nodes import (
    Literal,
    Identificador,
    OperacionRelacional,
    EvaluarSi,
    Suceso,
)
from tests.helpers import parsear_codigo as _parsear


def test_evaluar_si_simple():
    codigo = (
        "caso Prueba abierto "
        "evaluar si (pista1 > pista2) inicio revelar('mayor')! fin! "
        "caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    (evaluar_si,) = programa.caso_principal.cuerpo
    assert isinstance(evaluar_si, EvaluarSi)
    assert evaluar_si.rama_si.condicion == OperacionRelacional(
        operador=">",
        izquierda=Identificador(nombre="pista1"),
        derecha=Identificador(nombre="pista2"),
    )
    assert len(evaluar_si.rama_si.cuerpo) == 1
    assert evaluar_si.ramas_sino_evaluar == []
    assert evaluar_si.cuerpo_sino is None


def test_evaluar_si_con_sino_evaluar_y_sino():
    codigo = (
        "caso Prueba abierto "
        "evaluar si (pista1 < pista2) inicio revelar('menor')! fin! "
        "sino evaluar (pista1 == pista2) inicio revelar('igual')! fin! "
        "sino inicio revelar('mayor')! fin! "
        "caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    (evaluar_si,) = programa.caso_principal.cuerpo
    assert len(evaluar_si.ramas_sino_evaluar) == 1
    assert evaluar_si.ramas_sino_evaluar[0].condicion == OperacionRelacional(
        operador="==",
        izquierda=Identificador(nombre="pista1"),
        derecha=Identificador(nombre="pista2"),
    )
    assert evaluar_si.cuerpo_sino is not None
    assert len(evaluar_si.cuerpo_sino) == 1


def test_evaluar_si_con_multiples_sino_evaluar():
    codigo = (
        "caso Prueba abierto "
        "evaluar si (a == 1) inicio revelar('uno')! fin! "
        "sino evaluar (a == 2) inicio revelar('dos')! fin! "
        "sino evaluar (a == 3) inicio revelar('tres')! fin! "
        "caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    (evaluar_si,) = programa.caso_principal.cuerpo
    assert len(evaluar_si.ramas_sino_evaluar) == 2
    assert evaluar_si.cuerpo_sino is None


def test_suceso_con_varios_casos():
    codigo = (
        "caso Prueba abierto "
        "suceso (edad) inicio "
        "1 (edad < 18): revelar('El sospechoso es:', sospechoso1)! "
        "2 (edad > 18): revelar('El sospechoso es:', sospechoso2)! "
        "3 (edad == 18): revelar('El sospechoso es:', sospechoso3)! "
        "fin! "
        "caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    (suceso,) = programa.caso_principal.cuerpo
    assert isinstance(suceso, Suceso)
    assert suceso.variable == Identificador(nombre="edad")
    assert len(suceso.casos) == 3
    assert suceso.casos[0].numero == 1
    assert suceso.casos[0].condicion == OperacionRelacional(
        operador="<",
        izquierda=Identificador(nombre="edad"),
        derecha=Literal(tipo="entero", valor=18),
    )
    assert len(suceso.casos[0].cuerpo) == 1


def test_error_evaluar_si_sin_fin():
    codigo = "caso Prueba abierto evaluar si (a == 1) inicio revelar('x')! caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_sino_sin_evaluar_ni_inicio():
    codigo = (
        "caso Prueba abierto "
        "evaluar si (a == 1) inicio revelar('x')! fin! "
        "sino consultar(x)! "
        "caso Prueba cerrado!"
    )
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)
