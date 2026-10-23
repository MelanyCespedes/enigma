from gui.resaltado import (
    COMENTARIO,
    NUMERO,
    PALABRA_CLAVE,
    TEXTO,
    TIPO,
    VARIABLE,
    calcular_resaltado,
)


def _fragmentos(codigo):
    return [(etiqueta, codigo[i:f]) for etiqueta, i, f in calcular_resaltado(codigo)]


def test_declaracion_simple():
    assert _fragmentos("pista x = entero(valor: 15)!") == [
        (PALABRA_CLAVE, "pista"),
        (VARIABLE, "x"),
        (TIPO, "entero"),
        (PALABRA_CLAVE, "valor"),
        (NUMERO, "15"),
    ]


def test_cadena_de_texto():
    assert _fragmentos("revelar('hola mundo')!") == [
        (PALABRA_CLAVE, "revelar"),
        (TEXTO, "'hola mundo'"),
    ]


def test_numero_decimal():
    assert _fragmentos("3.14") == [(NUMERO, "3.14")]


def test_comentario_de_varias_lineas():
    assert _fragmentos("{ uno\ndos } pista") == [
        (COMENTARIO, "{ uno\ndos }"),
        (PALABRA_CLAVE, "pista"),
    ]


def test_palabras_reservadas_dentro_de_comentario_o_texto_no_se_resaltan():
    assert _fragmentos("{ pista caso }") == [(COMENTARIO, "{ pista caso }")]
    assert _fragmentos("'pista { caso'") == [(TEXTO, "'pista { caso'")]


def test_comentario_sin_cerrar_llega_hasta_el_final_sin_fallar():
    assert _fragmentos("pista { sin cierre\n x") == [
        (PALABRA_CLAVE, "pista"),
        (COMENTARIO, "{ sin cierre\n x"),
    ]


def test_cadena_sin_cerrar_llega_hasta_el_final_sin_fallar():
    assert _fragmentos("revelar('abierta") == [
        (PALABRA_CLAVE, "revelar"),
        (TEXTO, "'abierta"),
    ]


def test_importacion():
    assert _fragmentos("#expediente <pistas.eng>") == [
        (PALABRA_CLAVE, "#expediente"),
        (TEXTO, "<pistas.eng>"),
    ]


def test_menor_que_normal_no_es_ruta():
    assert _fragmentos("a < b") == [(VARIABLE, "a"), (VARIABLE, "b")]


def test_literales_especiales_son_palabras_clave():
    assert _fragmentos("culpable NoCulpable sin_pista") == [
        (PALABRA_CLAVE, "culpable"),
        (PALABRA_CLAVE, "NoCulpable"),
        (PALABRA_CLAVE, "sin_pista"),
    ]


def test_texto_vacio():
    assert calcular_resaltado("") == []
