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
    assert "y" in info.value.indicio


def test_reasignar_hecho_lanza_error():
    globales = [DeclaracionPista(nombre="MAX", valor=entero(3), es_constante=True, linea=1)]
    cuerpo = [Asignacion(nombre="MAX", valor=entero(4), linea=3)]

    with pytest.raises(ErrorSemantico) as info:
        analizar(programa(cuerpo, globales=globales))

    assert "hecho" in info.value.indicio


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


def test_escena_sin_concluir_lanza_error():
    escena = Escena(
        nombre="Vacia", parametros=[], tipo_retorno="entero",
        cuerpo=[Revelar(argumentos=[expresion("hola")], linea=3)], linea=2,
    )

    with pytest.raises(ErrorSemantico) as info:
        analizar(programa([], funciones={"Vacia": escena}))

    assert info.value.linea == 2
    assert "Vacia" in info.value.indicio and "concluir" in info.value.indicio


def test_escena_con_concluir_dentro_de_un_condicional_es_valida():
    _analizar_codigo(
        "escena Signo(n: entero)::entero inicio\n"
        "    evaluar si (n < 0) inicio\n        concluir 0!\n    fin!\n"
        "    concluir n!\nfin!\n"
        "caso Prueba abierto\n    revelar(resolver Signo(3))!\ncaso Prueba cerrado!"
    )


def test_proceso_sin_concluir_es_valido():
    _analizar_codigo(
        "proceso Hablar() inicio\n    revelar('hola')!\nfin!\n"
        "caso Prueba abierto\n    resolver Hablar()!\ncaso Prueba cerrado!"
    )

# ---------- pistas declaradas con sin_pista ----------

def _analizar_codigo(codigo):
    from core.lexer import tokenizar
    from core.parser import parsear
    programa = parsear(tokenizar(codigo, "p.eng"), "p.eng")
    analizar(programa)


def test_sin_pista_se_puede_reasignar_a_su_tipo_declarado():
    _analizar_codigo(
        "caso P abierto\n"
        "    pista x = entero(valor: sin_pista)!\n"
        "    x = entero(valor: 3)!\n"
        "    revelar(conectar(x, 1))!\n"
        "caso P cerrado!\n"
    )


def test_sin_pista_rechaza_un_tipo_distinto_al_declarado():
    with pytest.raises(ErrorSemantico):
        _analizar_codigo(
            "caso P abierto\n"
            "    pista x = entero(valor: sin_pista)!\n"
            "    x = expresion(valor: 'hola')!\n"
            "caso P cerrado!\n"
        )


def test_sin_pista_no_se_puede_operar_antes_de_reasignar():
    with pytest.raises(ErrorSemantico):
        _analizar_codigo(
            "caso P abierto\n"
            "    pista x = entero(valor: sin_pista)!\n"
            "    revelar(conectar(x, 1))!\n"
            "caso P cerrado!\n"
        )


def test_consultar_da_valor_a_una_pista_sin_pista():
    _analizar_codigo(
        "caso P abierto\n"
        "    pista x = entero(valor: sin_pista)!\n"
        "    consultar(x)!\n"
        "    revelar(conectar(x, 1))!\n"
        "caso P cerrado!\n"
    )


# ---------- restricciones de los tipos (seccion 5.5 del diseño) ----------

@pytest.mark.parametrize("declaracion", [
    "entero(valor: 1.5)",
    "entero(valor: 'a')",
    "expresion(valor: 3)",
    "declaracion(valor: 1)",
    "decimal(valor: 'x')",
])
def test_el_valor_de_un_literal_debe_corresponder_a_su_tipo(declaracion):
    with pytest.raises(ErrorSemantico):
        _analizar_codigo(f"caso P abierto\n    pista x = {declaracion}!\ncaso P cerrado!\n")


@pytest.mark.parametrize("declaracion", [
    "entero(valor: 3)", "decimal(valor: 3)", "decimal(valor: 3.5)",
    "expresion(valor: 'a')", "declaracion(valor: culpable)",
])
def test_literales_validos_siguen_aceptandose(declaracion):
    _analizar_codigo(f"caso P abierto\n    pista x = {declaracion}!\ncaso P cerrado!\n")


def test_una_lista_no_puede_mezclar_tipos():
    with pytest.raises(ErrorSemantico):
        _analizar_codigo("caso P abierto\n    pista l = pistas entero[1, 'a', 3]!\ncaso P cerrado!\n")


def test_una_lista_de_un_solo_tipo_es_valida():
    _analizar_codigo("caso P abierto\n    pista l = pistas entero[1, 2, 3]!\ncaso P cerrado!\n")


@pytest.mark.parametrize("operador", [">", "<", ">=", "<="])
def test_el_texto_no_se_puede_ordenar(operador):
    with pytest.raises(ErrorSemantico):
        _analizar_codigo(
            "caso P abierto\n"
            "    pista a = expresion(valor: 'a')!\n"
            f"    evaluar si (a {operador} 'b') inicio\n        revelar(1)!\n    fin!\n"
            "caso P cerrado!\n"
        )


def test_el_texto_si_se_puede_comparar_por_igualdad():
    _analizar_codigo(
        "caso P abierto\n"
        "    pista a = expresion(valor: 'a')!\n"
        "    evaluar si (a == 'b') inicio\n        revelar(1)!\n    fin!\n"
        "    evaluar si (a <> 'b') inicio\n        revelar(2)!\n    fin!\n"
        "caso P cerrado!\n"
    )
