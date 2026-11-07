"""Corre los 20 programas de prueba del enunciado (seccion 18) y compara con lo esperado."""
import pytest

from tests.programas_prueba.casos import CASOS
from tests.programas_prueba.ejecutor import correr


def test_hay_los_casos_que_pide_el_enunciado():
    por_categoria = {}
    for caso in CASOS:
        por_categoria[caso.categoria] = por_categoria.get(caso.categoria, 0) + 1
    assert por_categoria == {
        "Programa válido": 5,
        "Error sintáctico": 5,
        "Error semántico": 5,
        "Importación": 4,  # 3 pruebas de importacion + 1 circular
        "Prueba completa": 1,
    }


@pytest.mark.parametrize("caso", CASOS, ids=[c.id for c in CASOS])
def test_programa_de_prueba(caso):
    resultado = correr(caso.principal, caso.entradas)

    if caso.es_valido:
        assert resultado.exito, f"{caso.id} debia ejecutarse, pero falló: {resultado.descripcion}"
        assert tuple(resultado.salida) == caso.salida
        return

    assert not resultado.exito, f"{caso.id} debia fallar y se ejecutó sin errores"
    assert resultado.error == caso.error
    assert resultado.archivo == caso.archivo
    assert resultado.linea == caso.linea
    assert caso.fragmento in resultado.descripcion
