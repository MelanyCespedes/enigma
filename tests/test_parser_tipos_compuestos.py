import pytest

from core.errors import ErrorSintactico
from core.ast_nodes import Literal, Identificador, ListaLiteral, TableroLiteral, AccesoIndice
from tests.helpers import parsear_codigo as _parsear


def test_pistas_literal_con_enteros():
    codigo = "caso Prueba abierto pista archivos = pistas entero[2, 4, 6]! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert declaracion.valor == ListaLiteral(
        tipo_elemento="entero",
        elementos=[
            Literal(tipo="entero", valor=2),
            Literal(tipo="entero", valor=4),
            Literal(tipo="entero", valor=6),
        ],
    )


def test_tablero_literal_con_dimensiones():
    codigo = "caso Prueba abierto pista celda = tablero entero[4][4]! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert declaracion.valor == TableroLiteral(
        tipo_elemento="entero",
        filas=Literal(tipo="entero", valor=4),
        columnas=Literal(tipo="entero", valor=4),
    )


def test_acceso_indice_simple():
    codigo = "caso Prueba abierto pista x = archivos[0]! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert declaracion.valor == AccesoIndice(
        base=Identificador(nombre="archivos"),
        indices=[Literal(tipo="entero", valor=0)],
    )


def test_acceso_indice_doble_para_tablero():
    codigo = "caso Prueba abierto pista x = celda[1][2]! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert declaracion.valor == AccesoIndice(
        base=Identificador(nombre="celda"),
        indices=[Literal(tipo="entero", valor=1), Literal(tipo="entero", valor=2)],
    )


def test_identificador_sin_corchetes_no_se_afecta():
    codigo = "caso Prueba abierto pista x = archivos! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert declaracion.valor == Identificador(nombre="archivos")


def test_error_pistas_sin_tipo_valido():
    codigo = "caso Prueba abierto pista archivos = pistas NoEsUnTipo[1, 2]! caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_tablero_sin_segunda_dimension():
    codigo = "caso Prueba abierto pista celda = tablero entero[4]! caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_acceso_indice_sin_cerrar():
    codigo = "caso Prueba abierto pista x = archivos[0! caso Prueba cerrado!"
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_asignacion_indexada_simple():
    codigo = "caso Prueba abierto archivos[0] = 99! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (asignacion,) = programa.caso_principal.cuerpo
    assert asignacion.nombre == "archivos"
    assert asignacion.indices == [Literal(tipo="entero", valor=0)]
    assert asignacion.valor == Literal(tipo="entero", valor=99)


def test_asignacion_indexada_doble_para_tablero():
    codigo = "caso Prueba abierto celda[1][2] = 5! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (asignacion,) = programa.caso_principal.cuerpo
    assert asignacion.indices == [Literal(tipo="entero", valor=1), Literal(tipo="entero", valor=2)]


def test_asignacion_simple_no_lleva_indices():
    codigo = "caso Prueba abierto edad = 20! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (asignacion,) = programa.caso_principal.cuerpo
    assert asignacion.indices is None
