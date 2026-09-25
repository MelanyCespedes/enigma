import pytest

from core.lexer import tokenizar
from core.tokens import TipoToken
from core.errors import ErrorLexico


def test_solo_sello():
    tokens = tokenizar("!", "prueba.eng")
    assert tokens[0].tipo == TipoToken.SELLO
    assert tokens[1].tipo == TipoToken.FIN_DE_ARCHIVO


def test_declaracion_simple():
    codigo = "pista sospechoso1 = entero(valor: 15)!"
    tokens = tokenizar(codigo, "prueba.eng")
    tipos = [t.tipo for t in tokens]
    assert TipoToken.PISTA in tipos
    assert TipoToken.IDENTIFICADOR in tipos
    assert TipoToken.ENTERO in tipos
    assert TipoToken.IGUAL in tipos
    assert TipoToken.PARENTESIS_IZQ in tipos
    assert TipoToken.DOS_PUNTOS in tipos
    assert TipoToken.PARENTESIS_DER in tipos
    assert TipoToken.SELLO in tipos
    assert tipos[-1] == TipoToken.FIN_DE_ARCHIVO


def test_identificador_no_reservado():
    tokens = tokenizar("sospechoso1", "prueba.eng")
    assert tokens[0].tipo == TipoToken.IDENTIFICADOR
    assert tokens[0].lexema == "sospechoso1"


def test_palabras_reservadas_especiales():
    tokens = tokenizar("culpable NoCulpable sin_pista", "prueba.eng")
    tipos = [t.tipo for t in tokens]
    assert tipos[0] == TipoToken.CULPABLE
    assert tipos[1] == TipoToken.NO_CULPABLE
    assert tipos[2] == TipoToken.SIN_PISTA


def test_numero_entero():
    tokens = tokenizar("15", "prueba.eng")
    assert tokens[0].tipo == TipoToken.NUMERO_ENTERO
    assert tokens[0].valor == 15


def test_numero_decimal():
    tokens = tokenizar("3.14", "prueba.eng")
    assert tokens[0].tipo == TipoToken.NUMERO_DECIMAL
    assert tokens[0].valor == 3.14


def test_cadena_texto():
    tokens = tokenizar("'hola mundo'", "prueba.eng")
    assert tokens[0].tipo == TipoToken.CADENA_TEXTO
    assert tokens[0].valor == "hola mundo"


def test_cadena_sin_cerrar_lanza_error_lexico():
    with pytest.raises(ErrorLexico):
        tokenizar("'hola mundo", "prueba.eng")


def test_operador_igual_igual():
    tokens = tokenizar("edad == 20", "prueba.eng")
    tipos = [t.tipo for t in tokens]
    assert TipoToken.IGUAL_IGUAL in tipos
    assert TipoToken.IGUAL not in tipos


def test_operador_asignacion_no_se_confunde_con_igual_igual():
    tokens = tokenizar("edad = 20", "prueba.eng")
    tipos = [t.tipo for t in tokens]
    assert TipoToken.IGUAL in tipos
    assert TipoToken.IGUAL_IGUAL not in tipos


def test_operador_diferente_no_se_confunde_con_sello():
    codigo = "edad <> 20"
    tokens = tokenizar(codigo, "prueba.eng")
    tipos = [t.tipo for t in tokens]
    assert TipoToken.DIFERENTE in tipos
    assert TipoToken.SELLO not in tipos


def test_operadores_relacionales_mayor_menor():
    tokens = tokenizar("a > b >= c < d <= e", "prueba.eng")
    tipos = [t.tipo for t in tokens]
    assert tipos.count(TipoToken.MAYOR) == 1
    assert tipos.count(TipoToken.MAYOR_IGUAL) == 1
    assert tipos.count(TipoToken.MENOR) == 1
    assert tipos.count(TipoToken.MENOR_IGUAL) == 1


def test_simbolos_un_caracter():
    tokens = tokenizar(",:()[]", "prueba.eng")
    tipos = [t.tipo for t in tokens]
    assert tipos == [
        TipoToken.COMA,
        TipoToken.DOS_PUNTOS,
        TipoToken.PARENTESIS_IZQ,
        TipoToken.PARENTESIS_DER,
        TipoToken.CORCHETE_IZQ,
        TipoToken.CORCHETE_DER,
        TipoToken.FIN_DE_ARCHIVO,
    ]


def test_importacion_ruta_archivo_como_un_solo_token():
    codigo = "#expediente <investigacion.eng>"
    tokens = tokenizar(codigo, "prueba.eng")
    tipos = [t.tipo for t in tokens]
    lexemas = [t.lexema for t in tokens]
    assert tipos[0] == TipoToken.NUMERAL
    assert tipos[1] == TipoToken.EXPEDIENTE
    assert tipos[2] == TipoToken.RUTA_ARCHIVO
    assert "investigacion.eng" in lexemas


def test_importacion_sin_expediente_lanza_error_lexico():
    with pytest.raises(ErrorLexico):
        tokenizar("#otracosa <investigacion.eng>", "prueba.eng")


def test_importacion_sin_ruta_de_cierre_lanza_error_lexico():
    with pytest.raises(ErrorLexico):
        tokenizar("#expediente <investigacion.eng", "prueba.eng")


def test_saltos_de_linea_cuentan_numero_de_linea():
    codigo = "pista x = 1!\npista y = 2!"
    tokens = tokenizar(codigo, "prueba.eng")
    segundo_pista = [t for t in tokens if t.tipo == TipoToken.PISTA][1]
    assert segundo_pista.linea == 2


def test_caracter_invalido_lanza_error_lexico():
    codigo = "pista x = entero(valor: 15) @"
    with pytest.raises(ErrorLexico) as info:
        tokenizar(codigo, "prueba.eng")
    assert info.value.archivo == "prueba.eng"
