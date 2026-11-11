"""El proyecto de ejemplo con varios archivos (ejemplos/investigacion_caso) debe compilar y ejecutarse."""
import json
import os

from core.advertencias import buscar_advertencias
from core.lexer import tokenizar
from core.module_resolver import resolver_importaciones
from core.parser import parsear
from tests.programas_prueba.ejecutor import correr

RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CARPETA = os.path.join(RAIZ, "ejemplos", "investigacion_caso")


def test_el_proyecto_tiene_varios_archivos_y_marca_su_principal():
    archivos = sorted(f for f in os.listdir(CARPETA) if f.endswith(".eng"))
    assert archivos == ["analisis.eng", "principal.eng"]
    with open(os.path.join(CARPETA, ".enigma_proyecto.json"), encoding="utf-8") as f:
        assert json.load(f)["principal"] == "principal.eng"


def test_el_proyecto_de_ejemplo_compila_y_se_ejecuta():
    resultado = correr("../../ejemplos/investigacion_caso/principal.eng")
    assert resultado.exito, resultado.descripcion
    assert resultado.salida == [
        "Ronda de interrogatorio numero:  1",
        "Ronda de interrogatorio numero:  2",
        "Ronda de interrogatorio numero:  3",
        "El sospechoso es mayor de edad:  Carlos",
    ]


def test_el_proyecto_de_ejemplo_importa_su_biblioteca_y_no_da_advertencias():
    ruta = os.path.join(CARPETA, "principal.eng")
    programa = parsear(tokenizar(open(ruta, encoding="utf-8").read(), "principal.eng"), "principal.eng")
    resolver_importaciones(programa, CARPETA)
    assert "EsMayorDeEdad" in programa.funciones          # viene de analisis.eng
    assert "resolver EsMayorDeEdad" in open(ruta, encoding="utf-8").read()   # y el principal la usa de verdad
    assert buscar_advertencias(programa) == []
