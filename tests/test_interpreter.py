import pytest

from core.ast_nodes import (
    Asignacion,
    CasoPrincipal,
    Concluir,
    DeclaracionPista,
    EvaluarSi,
    Escena,
    Identificador,
    Literal,
    OperacionAritmetica,
    OperacionLogica,
    OperacionRelacional,
    Parametro,
    Proceso,
    Programa,
    RamaCondicional,
    Rastrear,
    Resolver,
    Revelar,
    SeguirMientras,
)
from core.errors import ErrorDeEjecucion
from core.interpreter import ejecutar


# ---------- Ayudas para construir el AST a mano ----------

def entero(valor: int) -> Literal:
    return Literal(tipo="entero", valor=valor)


def decimal(valor: float) -> Literal:
    return Literal(tipo="decimal", valor=valor)


def booleano(valor: bool) -> Literal:
    return Literal(tipo="declaracion", valor=valor)


def programa(cuerpo: list, globales: list | None = None, funciones: dict | None = None) -> Programa:
    return Programa(
        importaciones=[],
        declaraciones_globales=globales or [],
        funciones=funciones or {},
        caso_principal=CasoPrincipal(nombre="Principal", cuerpo=cuerpo, linea=1),
        archivo_origen="principal.eng",
    )


# ---------- Aritmética y salida ----------

def test_revelar_imprime_resultado(capsys):
    # pista x = entero(15)
    # x = conectar(x, 5)
    # revelar('Resultado:', x)
    cuerpo = [
        DeclaracionPista(nombre="x", valor=entero(15), es_constante=False, linea=1),
        Asignacion(
            nombre="x",
            valor=OperacionAritmetica("conectar", [Identificador("x"), entero(5)], linea=2),
            linea=2,
        ),
        Revelar(argumentos=[Literal("expresion", "Resultado:"), Identificador("x")], linea=3),
    ]
    ejecutar(programa(cuerpo))

    salida = capsys.readouterr().out
    assert "Resultado:" in salida
    assert "20" in salida


def test_repartir_da_decimal():
    # pista r = decimal(0.0)
    # r = repartir(7, 2)
    # revelar(r)
    cuerpo = [
        DeclaracionPista(nombre="r", valor=decimal(0.0), es_constante=False, linea=1),
        Asignacion(
            nombre="r",
            valor=OperacionAritmetica("repartir", [entero(7), entero(2)], linea=2),
            linea=2,
        ),
        Revelar(argumentos=[Identificador("r")], linea=3),
    ]
    import io, contextlib
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        ejecutar(programa(cuerpo))

    assert "3.5" in salida.getvalue()


def test_repartir_entre_cero_lanza_error():
    cuerpo = [
        Asignacion(
            nombre="x",
            valor=OperacionAritmetica("repartir", [entero(7), entero(0)], linea=4),
            linea=4,
        )
    ]
    # 'x' no se declaró antes, pero eso lo detecta el semántico, no el intérprete;
    # aquí forzamos el error de división antes de llegar a asignar()
    with pytest.raises(ErrorDeEjecucion) as info:
        ejecutar(programa(cuerpo))

    assert info.value.linea == 4


# ---------- Condicionales ----------

def test_evaluar_si_ejecuta_rama_correcta(capsys):
    # pista edad = entero(20)
    # evaluar si (edad >= 18) inicio
    #     revelar('mayor')
    # fin
    # sino inicio
    #     revelar('menor')
    # fin
    condicion = OperacionRelacional(">=", Identificador("edad"), entero(18))
    bloque = EvaluarSi(
        rama_si=RamaCondicional(condicion, [Revelar([Literal("expresion", "mayor")], linea=3)]),
        ramas_sino_evaluar=[],
        cuerpo_sino=[Revelar([Literal("expresion", "menor")], linea=5)],
        linea=2,
    )
    cuerpo = [
        DeclaracionPista(nombre="edad", valor=entero(20), es_constante=False, linea=1),
        bloque,
    ]
    ejecutar(programa(cuerpo))

    assert "mayor" in capsys.readouterr().out


def test_operacion_logica_y():
    # (culpable y NoCulpable) debe dar False
    expr = OperacionLogica("y", booleano(True), booleano(False))
    condicion = EvaluarSi(
        rama_si=RamaCondicional(expr, [Revelar([Literal("expresion", "SI")], linea=2)]),
        ramas_sino_evaluar=[],
        cuerpo_sino=[Revelar([Literal("expresion", "NO")], linea=4)],
        linea=1,
    )
    import io, contextlib
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        ejecutar(programa([condicion]))

    assert "NO" in salida.getvalue()
    assert "SI" not in salida.getvalue()


# ---------- Ciclos ----------

def test_rastrear_suma_del_1_al_5(capsys):
    # pista total = entero(0)
    # rastrear i desde 1 hasta 5 inicio
    #     total = conectar(total, i)
    # fin
    # revelar(total)
    cuerpo = [
        DeclaracionPista(nombre="total", valor=entero(0), es_constante=False, linea=1),
        Rastrear(
            variable="i",
            desde=entero(1),
            hasta=entero(5),
            cuerpo=[
                Asignacion(
                    nombre="total",
                    valor=OperacionAritmetica("conectar", [Identificador("total"), Identificador("i")], linea=3),
                    linea=3,
                )
            ],
            linea=2,
        ),
        Revelar(argumentos=[Identificador("total")], linea=5),
    ]
    ejecutar(programa(cuerpo))

    assert "15" in capsys.readouterr().out  # 1+2+3+4+5


def test_seguir_mientras_se_detiene():
    # pista contador = entero(0)
    # seguir mientras (contador <= 3) inicio
    #     contador = conectar(contador, 1)
    # fin
    cuerpo = [
        DeclaracionPista(nombre="contador", valor=entero(0), es_constante=False, linea=1),
        SeguirMientras(
            condicion=OperacionRelacional("<=", Identificador("contador"), entero(3)),
            cuerpo=[
                Asignacion(
                    nombre="contador",
                    valor=OperacionAritmetica("conectar", [Identificador("contador"), entero(1)], linea=3),
                    linea=3,
                )
            ],
            linea=2,
        ),
    ]
    ejecutar(programa(cuerpo))  # si no termina en un tiempo razonable, el ciclo está mal


# ---------- Funciones ----------

def test_escena_retorna_valor_con_concluir():
    # escena Doble(entero: n)::entero inicio
    #     concluir conectar(n, n)
    # fin
    # pista resultado = entero(0)
    # resultado = resolver Doble(4)
    escena = Escena(
        nombre="Doble",
        parametros=[Parametro(nombre="n", tipo="entero")],
        tipo_retorno="entero",
        cuerpo=[Concluir(valor=OperacionAritmetica("conectar", [Identificador("n"), Identificador("n")], linea=2), linea=2)],
        linea=1,
    )
    cuerpo = [
        DeclaracionPista(nombre="resultado", valor=entero(0), es_constante=False, linea=1),
        Asignacion(nombre="resultado", valor=Resolver("Doble", [entero(4)], linea=2), linea=2),
        Revelar(argumentos=[Identificador("resultado")], linea=3),
    ]

    import io, contextlib
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        ejecutar(programa(cuerpo, funciones={"Doble": escena}))

    assert "8" in salida.getvalue()


def test_concluir_dentro_de_rastrear_corta_el_ciclo():
    # escena PrimerParTraQuince(entero: inicio)::entero inicio
    #     rastrear i desde inicio hasta 100 inicio
    #         evaluar si (i > 15) inicio
    #             concluir i
    #         fin
    #     fin
    #     concluir 0
    # fin
    escena = Escena(
        nombre="PrimeroMayor",
        parametros=[Parametro(nombre="ini", tipo="entero")],
        tipo_retorno="entero",
        cuerpo=[
            Rastrear(
                variable="i",
                desde=Identificador("ini"),
                hasta=entero(100),
                cuerpo=[
                    EvaluarSi(
                        rama_si=RamaCondicional(
                            OperacionRelacional(">", Identificador("i"), entero(15)),
                            [Concluir(valor=Identificador("i"), linea=4)],
                        ),
                        ramas_sino_evaluar=[],
                        cuerpo_sino=None,
                        linea=3,
                    )
                ],
                linea=2,
            ),
            Concluir(valor=entero(0), linea=7),
        ],
        linea=1,
    )
    cuerpo = [
        DeclaracionPista(nombre="r", valor=entero(0), es_constante=False, linea=1),
        Asignacion(nombre="r", valor=Resolver("PrimeroMayor", [entero(1)], linea=2), linea=2),
        Revelar(argumentos=[Identificador("r")], linea=3),
    ]

    import io, contextlib
    salida = io.StringIO()
    with contextlib.redirect_stdout(salida):
        ejecutar(programa(cuerpo, funciones={"PrimeroMayor": escena}))

    assert "16" in salida.getvalue()  # el ciclo se corta apenas i > 15


def test_proceso_no_devuelve_valor(capsys):
    # proceso Saludar(expresion: nombre) inicio
    #     revelar('Hola', nombre)
    # fin
    # resolver Saludar('Ana')
    proceso = Proceso(
        nombre="Saludar",
        parametros=[Parametro(nombre="nombre", tipo="expresion")],
        cuerpo=[Revelar([Literal("expresion", "Hola"), Identificador("nombre")], linea=2)],
        linea=1,
    )
    cuerpo = [Resolver("Saludar", [Literal("expresion", "Ana")], linea=1)]

    ejecutar(programa(cuerpo, funciones={"Saludar": proceso}))

    assert "Ana" in capsys.readouterr().out