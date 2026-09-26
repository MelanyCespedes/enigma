import pytest

from core.errors import ErrorSintactico
from core.ast_nodes import (
    Literal,
    Identificador,
    OperacionAritmetica,
    OperacionLogica,
    OperacionRelacional,
)
from tests.helpers import parsear_codigo as _parsear


def test_conectar_suma_con_varios_argumentos():
    codigo = "caso Prueba abierto pista total = conectar(pista1, pista2, pista3)! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert declaracion.valor == OperacionAritmetica(
        operador="conectar",
        operandos=[
            Identificador(nombre="pista1"),
            Identificador(nombre="pista2"),
            Identificador(nombre="pista3"),
        ],
        linea=declaracion.valor.linea,
    )


def test_descartar_intensificar_repartir_dos_argumentos():
    codigo = (
        "caso Prueba abierto "
        "pista r = descartar(pista1, pista2)! "
        "pista m = intensificar(pista1, pista2)! "
        "pista d = repartir(pista1, pista2)! "
        "caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    resta, mult, div = programa.caso_principal.cuerpo
    assert resta.valor.operador == "descartar"
    assert mult.valor.operador == "intensificar"
    assert div.valor.operador == "repartir"
    assert resta.valor.operandos == [Identificador(nombre="pista1"), Identificador(nombre="pista2")]


def test_operador_relacional_igual_igual():
    codigo = "caso Prueba abierto pista resultado = edad == 20! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert declaracion.valor == OperacionRelacional(
        operador="==",
        izquierda=Identificador(nombre="edad"),
        derecha=Literal(tipo="entero", valor=20),
    )


def test_operadores_relacionales_todos():
    casos = [
        ("a <> b", "<>"),
        ("a > b", ">"),
        ("a < b", "<"),
        ("a >= b", ">="),
        ("a <= b", "<="),
    ]
    for expresion, operador_esperado in casos:
        codigo = f"caso Prueba abierto pista r = {expresion}! caso Prueba cerrado!"
        programa = _parsear(codigo)
        (declaracion,) = programa.caso_principal.cuerpo
        assert declaracion.valor.operador == operador_esperado


def test_operador_logico_y_o():
    codigo = "caso Prueba abierto pista r = (pista1 == arma) y (pista1 == libro)! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert isinstance(declaracion.valor, OperacionLogica)
    assert declaracion.valor.operador == "y"


def test_operador_logico_no():
    codigo = "caso Prueba abierto pista r = no (pista1 == arma)! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert declaracion.valor == OperacionLogica(
        operador="no",
        izquierda=OperacionRelacional(
            operador="==",
            izquierda=Identificador(nombre="pista1"),
            derecha=Identificador(nombre="arma"),
        ),
        derecha=None,
    )


def test_precedencia_logica_evalua_izquierda_a_derecha():
    codigo = "caso Prueba abierto pista r = a y b o c! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    # (a y b) o c
    assert declaracion.valor.operador == "o"
    assert declaracion.valor.izquierda.operador == "y"


def test_error_descartar_con_un_solo_argumento():
    codigo = "caso Prueba abierto pista r = descartar(pista1)! caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)
