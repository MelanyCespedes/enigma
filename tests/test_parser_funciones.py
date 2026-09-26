import pytest

from core.errors import ErrorSintactico
from core.ast_nodes import Escena, Proceso, Parametro, Resolver, Concluir, Literal, Identificador
from tests.helpers import parsear_codigo as _parsear


def test_escena_con_parametros_y_retorno():
    codigo = (
        "escena BuscarEnLista(lista: pistas, objetivo: entero)::expresion inicio "
        "concluir expresion(valor: 'listo')! "
        "fin! "
        "caso Prueba abierto caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    assert "BuscarEnLista" in programa.funciones
    funcion = programa.funciones["BuscarEnLista"]
    assert isinstance(funcion, Escena)
    assert funcion.tipo_retorno == "expresion"
    assert funcion.parametros == [
        Parametro(nombre="lista", tipo="pistas"),
        Parametro(nombre="objetivo", tipo="entero"),
    ]
    (concluir,) = funcion.cuerpo
    assert isinstance(concluir, Concluir)
    assert concluir.valor == Literal(tipo="expresion", valor="listo")


def test_proceso_sin_parametros_y_sin_retorno():
    codigo = (
        "proceso ModificarLista(lista: pistas) inicio "
        "revelar('modificado')! "
        "fin! "
        "caso Prueba abierto caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    funcion = programa.funciones["ModificarLista"]
    assert isinstance(funcion, Proceso)
    assert funcion.parametros == [Parametro(nombre="lista", tipo="pistas")]


def test_funcion_sin_parametros():
    codigo = (
        "proceso Saludar() inicio revelar('hola')! fin! "
        "caso Prueba abierto caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    assert programa.funciones["Saludar"].parametros == []


def test_resolver_como_sentencia():
    codigo = (
        "caso Prueba abierto "
        "resolver BuscarEnLista(lista, 5)! "
        "caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    (resolver,) = programa.caso_principal.cuerpo
    assert isinstance(resolver, Resolver)
    assert resolver.nombre == "BuscarEnLista"
    assert resolver.argumentos == [Identificador(nombre="lista"), Literal(tipo="entero", valor=5)]


def test_resolver_sin_argumentos():
    codigo = "caso Prueba abierto resolver Saludar()! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (resolver,) = programa.caso_principal.cuerpo
    assert resolver.argumentos == []


def test_error_funcion_duplicada():
    codigo = (
        "proceso Saludar() inicio fin! "
        "proceso Saludar() inicio fin! "
        "caso Prueba abierto caso Prueba cerrado!"
    )
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_escena_sin_tipo_retorno():
    codigo = (
        "escena Buscar() inicio concluir culpable! fin! "
        "caso Prueba abierto caso Prueba cerrado!"
    )
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)


def test_error_parametro_con_tipo_invalido():
    codigo = (
        "proceso Modificar(lista: NoEsUnTipo) inicio fin! "
        "caso Prueba abierto caso Prueba cerrado!"
    )
    with pytest.raises(ErrorSintactico):
        _parsear(codigo)
