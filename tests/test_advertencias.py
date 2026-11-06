"""Advertencias del compilador: el programa es valido, pero algo es sospechoso."""
from core.advertencias import buscar_advertencias
from core.semantic import analizar
from tests.helpers import parsear_codigo


def _advertencias(codigo: str):
    programa = parsear_codigo(codigo)
    analizar(programa)  # las advertencias solo existen en programas que compilan
    return buscar_advertencias(programa)


def test_programa_limpio_no_tiene_advertencias():
    codigo = """
    escena Doble(n: entero)::entero inicio
        concluir intensificar(n, 2)!
    fin!
    caso Limpio abierto
        pista x = entero(valor: 4)!
        revelar(resolver Doble(x))!
    caso Limpio cerrado!
    """
    assert _advertencias(codigo) == []


def test_pista_declarada_y_nunca_usada():
    codigo = """
    caso Prueba abierto
        pista usada = entero(valor: 1)!
        pista olvidada = entero(valor: 2)!
        revelar(usada)!
    caso Prueba cerrado!
    """
    resultado = _advertencias(codigo)
    assert len(resultado) == 1
    assert "olvidada" in resultado[0].descripcion
    assert resultado[0].linea == 4
    assert resultado[0].archivo == "prueba.eng"


def test_pista_dentro_de_un_bloque_sin_usar():
    codigo = """
    caso Prueba abierto
        evaluar si (culpable == culpable) inicio
            pista suelta = entero(valor: 1)!
        fin!
    caso Prueba cerrado!
    """
    resultado = _advertencias(codigo)
    assert [a.linea for a in resultado] == [4]


def test_asignar_no_cuenta_como_usar():
    codigo = """
    caso Prueba abierto
        pista x = entero(valor: 1)!
        x = 5!
    caso Prueba cerrado!
    """
    assert len(_advertencias(codigo)) == 1


def test_pista_global_usada_solo_dentro_de_una_funcion_no_avisa():
    codigo = """
    pista base = entero(valor: 10)!
    escena Suma(n: entero)::entero inicio
        concluir conectar(n, base)!
    fin!
    caso Prueba abierto
        revelar(resolver Suma(1))!
    caso Prueba cerrado!
    """
    assert _advertencias(codigo) == []


def test_codigo_despues_de_concluir_nunca_se_ejecuta():
    codigo = """
    escena Uno()::entero inicio
        concluir 1!
        revelar('nunca')!
    fin!
    caso Prueba abierto
        revelar(resolver Uno())!
    caso Prueba cerrado!
    """
    resultado = _advertencias(codigo)
    assert len(resultado) == 1
    assert "nunca se ejecuta" in resultado[0].descripcion
    assert resultado[0].linea == 4


def test_concluir_dentro_de_un_if_no_hace_inalcanzable_lo_de_afuera():
    codigo = """
    escena Signo(n: entero)::entero inicio
        evaluar si (n < 0) inicio
            concluir 0!
        fin!
        concluir n!
    fin!
    caso Prueba abierto
        revelar(resolver Signo(3))!
    caso Prueba cerrado!
    """
    assert _advertencias(codigo) == []


def test_escena_sin_concluir():
    codigo = """
    escena Vacia()::entero inicio
        revelar('hola')!
    fin!
    caso Prueba abierto
        pista r = entero(valor: 0)!
        revelar(r)!
    caso Prueba cerrado!
    """
    resultado = _advertencias(codigo)
    assert len(resultado) == 1
    assert "no tiene 'concluir'" in resultado[0].descripcion
    assert resultado[0].linea == 2


def test_proceso_sin_concluir_es_normal():
    codigo = """
    proceso Hablar() inicio
        revelar('hola')!
    fin!
    caso Prueba abierto
        resolver Hablar()!
    caso Prueba cerrado!
    """
    assert _advertencias(codigo) == []


def test_parametro_que_nunca_se_usa():
    codigo = """
    escena Primero(a: entero, b: entero)::entero inicio
        concluir a!
    fin!
    caso Prueba abierto
        revelar(resolver Primero(1, 2))!
    caso Prueba cerrado!
    """
    resultado = _advertencias(codigo)
    assert len(resultado) == 1
    assert "'b'" in resultado[0].descripcion
    assert resultado[0].linea == 2


def test_formato_igual_al_de_los_errores():
    codigo = """
    caso Prueba abierto
        pista olvidada = entero(valor: 2)!
    caso Prueba cerrado!
    """
    texto = _advertencias(codigo)[0].mostrar_completo()
    lineas = texto.splitlines()
    assert lineas[0] == "Advertencia"
    assert lineas[1] == "Archivo: prueba.eng"
    assert lineas[2] == "Linea: 3"
    assert lineas[3].startswith("Descripcion: ")
    assert lineas[4].startswith("Posible causa: ")
