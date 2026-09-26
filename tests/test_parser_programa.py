from core.ast_nodes import (
    DeclaracionPista,
    Asignacion,
    Revelar,
    Consultar,
    Literal,
    Identificador,
)
from tests.helpers import parsear_codigo as _parsear


def test_caso_principal_vacio():
    programa = _parsear("caso Prueba abierto caso Prueba cerrado!")
    assert programa.caso_principal.nombre == "Prueba"
    assert programa.caso_principal.cuerpo == []
    assert programa.importaciones == []
    assert programa.declaraciones_globales == []


def test_declaracion_pista_simple():
    codigo = "caso Prueba abierto pista sospechoso1 = entero(valor: 15)! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert isinstance(declaracion, DeclaracionPista)
    assert declaracion.nombre == "sospechoso1"
    assert declaracion.es_constante is False
    assert declaracion.valor == Literal(tipo="entero", valor=15)


def test_declaracion_hecho_es_constante():
    codigo = "caso Prueba abierto hecho sospechoso2 = entero(valor: 10)! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert declaracion.es_constante is True


def test_declaracion_decimal_expresion_declaracion():
    codigo = (
        "caso Prueba abierto "
        "pista p1 = decimal(valor: 15.5)! "
        "pista p2 = expresion(valor: 'Estaba en el baño.')! "
        "pista p3 = declaracion(valor: culpable)! "
        "pista p4 = declaracion(valor: NoCulpable)! "
        "caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    p1, p2, p3, p4 = programa.caso_principal.cuerpo
    assert p1.valor == Literal(tipo="decimal", valor=15.5)
    assert p2.valor == Literal(tipo="expresion", valor="Estaba en el baño.")
    assert p3.valor == Literal(tipo="declaracion", valor=True)
    assert p4.valor == Literal(tipo="declaracion", valor=False)


def test_declaracion_valor_sin_pista():
    codigo = "caso Prueba abierto pista p5 = entero(valor: sin_pista)! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (declaracion,) = programa.caso_principal.cuerpo
    assert declaracion.valor == Literal(tipo="sin_pista", valor=None)


def test_asignacion():
    codigo = "caso Prueba abierto edad = 20! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (asignacion,) = programa.caso_principal.cuerpo
    assert isinstance(asignacion, Asignacion)
    assert asignacion.nombre == "edad"
    assert asignacion.valor == Literal(tipo="entero", valor=20)


def test_revelar_con_cadena_y_variable():
    codigo = "caso Prueba abierto revelar('El sospechoso es:', sospechoso1)! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (revelar,) = programa.caso_principal.cuerpo
    assert isinstance(revelar, Revelar)
    assert revelar.argumentos == [
        Literal(tipo="expresion", valor="El sospechoso es:"),
        Identificador(nombre="sospechoso1"),
    ]


def test_consultar():
    codigo = "caso Prueba abierto consultar(valorPremisa)! caso Prueba cerrado!"
    programa = _parsear(codigo)
    (consultar,) = programa.caso_principal.cuerpo
    assert isinstance(consultar, Consultar)
    assert consultar.variable == "valorPremisa"


def test_declaracion_global_fuera_de_caso():
    codigo = (
        "pista global1 = entero(valor: 1)! "
        "caso Prueba abierto caso Prueba cerrado!"
    )
    programa = _parsear(codigo)
    assert len(programa.declaraciones_globales) == 1
    assert programa.declaraciones_globales[0].nombre == "global1"


def test_importacion_se_registra_en_programa():
    codigo = "#expediente <investigacion.eng>\ncaso Prueba abierto caso Prueba cerrado!"
    programa = _parsear(codigo)
    assert len(programa.importaciones) == 1
    assert programa.importaciones[0].archivo == "investigacion.eng"
