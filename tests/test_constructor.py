import pytest

from gui import constructor_codigo as cc


def _por_defecto(id_bloque, **cambios):
    valores = cc.valores_iniciales(cc.POR_ID[id_bloque])
    valores.update(cambios)
    return valores


def test_hay_un_bloque_por_cada_tema_basico():
    ids = {b.id for b in cc.BLOQUES}
    assert {"declarar", "revelar", "consultar", "condicional", "rastrear",
            "mientras", "escena", "proceso", "importar", "caso"} <= ids


@pytest.mark.parametrize("bloque", cc.BLOQUES, ids=lambda b: b.id)
def test_el_codigo_por_defecto_de_cada_bloque_es_valido(bloque):
    codigo = cc.generar(bloque.id, cc.valores_iniciales(bloque))
    assert cc.validar(codigo) is None, codigo


@pytest.mark.parametrize("tipo,valor,esperado", [
    ("entero", "15", "entero(valor: 15)"),
    ("decimal", "1.5", "decimal(valor: 1.5)"),
    ("expresion", "Alex", "expresion(valor: 'Alex')"),
    ("expresion", "'ya con comillas'", "expresion(valor: 'ya con comillas')"),
    ("declaracion", "culpable", "declaracion(valor: culpable)"),
    ("declaracion", "NoCulpable", "declaracion(valor: NoCulpable)"),
    ("declaracion", "no", "declaracion(valor: NoCulpable)"),
    ("entero", "", "entero(valor: sin_pista)"),
    ("entero", "sin_pista", "entero(valor: sin_pista)"),
])
def test_literal(tipo, valor, esperado):
    assert cc.literal(tipo, valor) == esperado


def test_declarar_pista_y_hecho():
    assert cc.generar("declarar", _por_defecto("declarar")) == "pista sospechoso = entero(valor: 15)!"
    assert cc.generar("declarar", _por_defecto("declarar", constante=True)).startswith("hecho ")


def test_un_valor_que_no_corresponde_al_tipo_se_rechaza():
    codigo = cc.generar("declarar", _por_defecto("declarar", tipo="entero", valor="1.5"))
    assert cc.validar(codigo) is not None


def test_revelar_con_y_sin_variable():
    assert cc.generar("revelar", _por_defecto("revelar", mensaje="Hola", variable="")) == "revelar('Hola')!"
    assert cc.generar("revelar", _por_defecto("revelar", mensaje="Edad:", variable="edad")) == "revelar('Edad:', edad)!"
    assert cc.generar("revelar", _por_defecto("revelar", mensaje="", variable="edad")) == "revelar(edad)!"


def test_un_apostrofe_en_el_mensaje_no_rompe_el_codigo():
    codigo = cc.generar("revelar", _por_defecto("revelar", mensaje="no es el 'culpable'"))
    assert cc.validar(codigo) is None


def test_condicional_con_y_sin_sino():
    con = cc.generar("condicional", _por_defecto("condicional", con_sino=True))
    sin = cc.generar("condicional", _por_defecto("condicional", con_sino=False))
    assert "sino inicio" in con and "sino" not in sin
    assert cc.validar(con) is None and cc.validar(sin) is None


def test_agrega_el_signo_de_exclamacion_que_falte():
    codigo = cc.generar("rastrear", _por_defecto("rastrear", cuerpo="revelar(paso)"))
    assert "    revelar(paso)!" in codigo
    assert cc.validar(codigo) is None


def test_varias_instrucciones_en_un_bloque():
    codigo = cc.generar("mientras", _por_defecto("mientras", cuerpo="revelar(n)!\nn = descartar(n, 1)"))
    assert codigo.count("!") >= 3 and cc.validar(codigo) is None


def test_esqueleto_de_caso_completo_se_puede_ejecutar():
    from core.interpreter import ejecutar
    from core.lexer import tokenizar
    from core.parser import parsear
    from core.semantic import analizar

    codigo = cc.generar("caso", _por_defecto("caso"))
    programa = parsear(tokenizar(codigo, "c.eng"), "c.eng")
    analizar(programa)
    ejecutar(programa)


def test_error_de_sintaxis_se_reporta():
    mensaje = cc.validar("evaluar si (a > 1) inicio\n  revelar('x')!\n")  # falta fin!
    assert mensaje


def test_nombre_invalido_se_reporta():
    codigo = cc.generar("declarar", _por_defecto("declarar", nombre="1abc"))
    assert cc.validar(codigo) is not None


def test_no_reporta_variables_que_existen_en_el_archivo_destino():
    # el formulario puede usar una pista declarada mas arriba en el archivo
    assert cc.validar("revelar('Edad:', edad)!") is None


def test_importar_genera_la_directiva():
    assert cc.generar("importar", _por_defecto("importar", archivo="util.eng")) == "#expediente <util.eng>"
    assert cc.validar("#expediente <util.eng>") is None


def test_los_mensajes_de_error_no_usan_nombres_internos_ni_lineas():
    from gui.indicios import es_orientadora
    for codigo in ("evaluar si (a >>> 1) inicio\n  revelar(1)!\nfin!", "pista x = entero(valor: 1.5)!", "pista = 3!"):
        mensaje = cc.validar(codigo)
        assert mensaje and es_orientadora(mensaje), (codigo, mensaje)
