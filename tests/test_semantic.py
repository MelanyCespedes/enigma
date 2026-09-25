import pytest

from core.ast_nodes import (
    Asignacion,
    CasoPrincipal,
    Concluir,
    DeclaracionPista,
    Escena,
    Identificador,
    Literal,
    OperacionAritmetica,
    Parametro,
    Programa,
    Resolver,
    Revelar,
)
from core.errors import ErrorSemantico
from core.semantic import analizar


def entero(valor: int) -> Literal:
    return Literal(tipo="entero", valor=valor)


def decimal(valor: float) -> Literal:
    return Literal(tipo="decimal", valor=valor)


def expresion(valor: str) -> Literal:
    return Literal(tipo="expresion", valor=valor)


def programa(cuerpo: list, globales: list | None = None, funciones: dict | None = None) -> Programa:
    return Programa(
        importaciones=[],
        declaraciones_globales=globales or [],
        funciones=funciones or {},
        caso_principal=CasoPrincipal(nombre="Principal", cuerpo=cuerpo, linea=1),
        archivo_origen="principal.eng",
    )


def test_programa_valido_no_lanza_errores():
    cuerpo = [
        DeclaracionPista(nombre="x", valor=entero(15), es_constante=False, linea=2),
        Asignacion(
            nombre="x",
            valor=OperacionAritmetica("conectar", [Identificador("x"), entero(2)], linea=3),
            linea=3,
        ),
        Revelar(argumentos=[Identificador("x")], linea=4),
    ]
    analizar(programa(cuerpo))


def test_variable_no_declarada_lanza_error():
    cuerpo = [Revelar(argumentos=[Identificador("y")], linea=5)]

    with pytest.raises(ErrorSemantico) as info:
        analizar(programa(cuerpo))

    assert info.value.linea == 5
    assert "y" in info.value.pista


def test_reasignar_hecho_lanza_error():
    globales = [DeclaracionPista(nombre="MAX", valor=entero(3), es_constante=True, linea=1)]
    cuerpo = [Asignacion(nombre="MAX", valor=entero(4), linea=3)]

    with pytest.raises(ErrorSemantico) as info:
        analizar(programa(cuerpo, globales=globales))

    assert "hecho" in info.value.pista


def test_asignar_expresion_a_entero_lanza_error():
    cuerpo = [
        DeclaracionPista(nombre="x", valor=entero(1), es_constante=False, linea=1),
        Asignacion(nombre="x", valor=expresion("hola"), linea=2),
    ]

    with pytest.raises(ErrorSemantico):
        analizar(programa(cuerpo))


def test_resultado_decimal_no_cabe_en_entero():
    cuerpo = [
        DeclaracionPista(nombre="x", valor=entero(1), es_constante=False, linea=1),
        Asignacion(
            nombre="x",
            valor=OperacionAritmetica("conectar", [entero(2), decimal(2.5)], linea=2),
            linea=2,
        ),
    ]

    with pytest.raises(ErrorSemantico):
        analizar(programa(cuerpo))


def test_repartir_siempre_devuelve_decimal():
    cuerpo = [
        DeclaracionPista(nombre="r", valor=decimal(0.0), es_constante=False, linea=1),
        Asignacion(
            nombre="r",
            valor=OperacionAritmetica("repartir", [entero(7), entero(2)], linea=2),
            linea=2,
        ),
    ]
    analizar(programa(cuerpo))  # no debe lanzar excepción


def test_llamada_con_argumentos_de_mas_lanza_error():
    escena = Escena(
        nombre="Doble",
        parametros=[Parametro(nombre="n", tipo="entero")],
        tipo_retorno="entero",
        cuerpo=[Concluir(valor=Identificador("n"), linea=2)],
        linea=1,
    )
    cuerpo = [Resolver(nombre="Doble", argumentos=[entero(1), entero(2)], linea=5)]

    with pytest.raises(ErrorSemantico) as info:
        analizar(programa(cuerpo, funciones={"Doble": escena}))

    assert info.value.linea == 5


def test_concluir_fuera_de_escena_lanza_error():
    cuerpo = [Concluir(valor=entero(1), linea=3)]

    with pytest.raises(ErrorSemantico):
        analizar(programa(cuerpo))