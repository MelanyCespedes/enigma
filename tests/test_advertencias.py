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


# ---------- resumen de la primera vez (sin decir donde) ----------


def test_cada_advertencia_tiene_su_tipo():
    codigo = """
    escena Vacia(a: entero)::entero inicio
        concluir 1!
    fin!
    escena Primero(uno: entero, dos: entero)::entero inicio
        concluir uno!
        revelar('nunca')!
    fin!
    caso Prueba abierto
        pista olvidada = entero(valor: 2)!
        revelar(resolver Primero(1, 2))!
    caso Prueba cerrado!
    """
    tipos = sorted(a.tipo for a in _advertencias(codigo))
    assert tipos == sorted([
        "parametro_sin_usar", "parametro_sin_usar", "codigo_inalcanzable", "pista_sin_usar",
    ])


def test_resumen_cuenta_por_tipo_y_no_dice_donde():
    from core.advertencias import resumen_por_tipo

    codigo = """
    escena Vacia(a: entero, b: entero)::entero inicio
        concluir 1!
    fin!
    caso Prueba abierto
        pista olvidada = entero(valor: 2)!
        revelar(resolver Vacia(1, 2))!
    caso Prueba cerrado!
    """
    resumen = resumen_por_tipo(_advertencias(codigo))
    assert resumen == [
        "1 pista declarada que nunca se usa",
        "2 parámetros que nunca se usan",
    ]
    texto = " ".join(resumen)
    assert "olvidada" not in texto and "Vacia" not in texto  # no revela nombres ni lineas


def test_resumen_sin_advertencias_esta_vacio():
    from core.advertencias import resumen_por_tipo

    assert resumen_por_tipo([]) == []


def test_firma_distingue_una_advertencia_de_otra():
    codigo = """
    caso Prueba abierto
        pista uno = entero(valor: 1)!
        pista dos = entero(valor: 2)!
    caso Prueba cerrado!
    """
    a, b = _advertencias(codigo)
    assert a.firma != b.firma
    assert a.firma == a.firma


# ---------- advertencias aunque falte un '!' ----------


def _tras_error(codigo: str):
    import pytest

    from core.advertencias import advertencias_tras_error_de_sintaxis
    from core.errors import ErrorSintactico
    from core.lexer import tokenizar
    from core.parser import parsear

    tokens = tokenizar(codigo, "prueba.eng")
    with pytest.raises(ErrorSintactico) as info:
        parsear(tokens, "prueba.eng")
    copia = list(tokens)
    resultado = advertencias_tras_error_de_sintaxis(tokens, "prueba.eng", info.value)
    assert tokens == copia  # no modifica los tokens originales
    return resultado


def test_falta_un_sello_pero_aun_se_avisa_de_lo_demas():
    # el ejemplo de la guia, al que le falta el '!' del segundo 'fin'
    codigo = """
    escena Vacia(a: entero)::entero inicio
        concluir 1!
    fin!
    escena Primero(uno: entero, dos: entero)::entero inicio
        concluir uno!
        revelar('nunca')!
    fin
    caso Advertencias abierto
        pista usada = entero(valor: 1)!
        pista olvidada = entero(valor: 2)!
        revelar(usada)!
        revelar(resolver Primero(1, 2))!
    caso Advertencias cerrado!
    """
    tipos = sorted(a.tipo for a in _tras_error(codigo))
    assert tipos == sorted([
        "parametro_sin_usar", "parametro_sin_usar", "codigo_inalcanzable", "pista_sin_usar",
    ])


def test_faltan_varios_sellos():
    codigo = """
    caso Prueba abierto
        pista olvidada = entero(valor: 2)
        pista usada = entero(valor: 1)
        revelar(usada)
    caso Prueba cerrado!
    """
    resultado = _tras_error(codigo)
    assert len(resultado) == 1 and "olvidada" in resultado[0].descripcion


def test_si_falta_otra_cosa_no_se_inventan_advertencias():
    codigo = """
    caso Prueba abierto
        pista olvidada = entero(valor: 2)!
        revelar('hola'!
    caso Prueba cerrado!
    """
    assert _tras_error(codigo) == []
