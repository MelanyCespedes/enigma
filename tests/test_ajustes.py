import pytest

from gui import ajustes


@pytest.mark.parametrize("valor,esperado", [
    (11, 11), (9, 9), (20, 20), (5, 9), (99, 20), ("14", 14), ("x", 11), (None, 11), (12.7, 12),
])
def test_limitar_fuente(valor, esperado):
    assert ajustes.limitar_fuente(valor) == esperado


def test_guardar_y_cargar(tmp_path):
    ruta = str(tmp_path / "config.json")
    ajustes.guardar({"tam_fuente": 15}, ruta)
    assert ajustes.cargar(ruta) == {"tam_fuente": 15}


def test_cargar_archivo_inexistente_o_roto(tmp_path):
    assert ajustes.cargar(str(tmp_path / "no_existe.json")) == {}
    roto = tmp_path / "roto.json"
    roto.write_text("{ no es json", encoding="utf-8")
    assert ajustes.cargar(str(roto)) == {}
    lista = tmp_path / "lista.json"
    lista.write_text("[1, 2]", encoding="utf-8")
    assert ajustes.cargar(str(lista)) == {}


def test_la_ruta_por_defecto_se_resuelve_al_llamar(tmp_path, monkeypatch):
    """Antes la ruta se fijaba al definir la funcion y las pruebas escribian en el archivo real del usuario."""
    ruta = str(tmp_path / "otra.json")
    monkeypatch.setattr(ajustes, "ARCHIVO", ruta)
    ajustes.guardar({"tam_fuente": 13})
    assert ajustes.cargar() == {"tam_fuente": 13}
